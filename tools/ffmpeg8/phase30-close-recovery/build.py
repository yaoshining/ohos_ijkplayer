#!/usr/bin/env python3
"""从固定 Phase30 A 全量源码构建关闭错误恢复版 FFmpeg SDK。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
LOCK = json.loads((HERE / "inputs.lock.json").read_text())
LIBRARIES = ("libavcodec.so.62", "libavformat.so.62", "libavutil.so.60",
             "libavfilter.so.11", "libswscale.so.9", "libswresample.so.6")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def inventory(root):
    return [{"path": p.relative_to(root).as_posix(), "size": p.stat().st_size, "sha256": sha(p)}
            for p in sorted(root.rglob("*")) if p.is_file()]

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--dependencies", required=True, type=Path)
    parser.add_argument("--ndk", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--jobs", type=int, default=8)
    args = parser.parse_args()
    source, deps, ndk, out = [p.resolve() for p in
                              (args.source, args.dependencies, args.ndk, args.output)]
    if out.exists() or args.jobs < 1:
        raise SystemExit("输出目录必须不存在，jobs 必须为正数")
    if not (deps / "lib/pkgconfig/smbclient.pc").is_file():
        raise SystemExit("缺少静态 SMB 依赖")
    compiler = ndk / "llvm/bin/aarch64-unknown-linux-ohos-clang"
    if not compiler.is_file():
        raise SystemExit("缺少 OpenHarmony arm64 编译器")
    rows = inventory(source)
    digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if digest != LOCK["sourceInventorySHA256"] or len(rows) != LOCK["sourceFileCount"]:
        raise SystemExit("Phase30 A 全量源码摘要不匹配")
    if sha(HERE / "recover.patch") != LOCK["patchSHA256"]:
        raise SystemExit("修复补丁摘要不匹配")

    dependency_rows = inventory(deps)
    dependency_digest = hashlib.sha256(json.dumps(
        dependency_rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if dependency_digest != LOCK["dependencyInventorySHA256"]:
        raise SystemExit("Phase30 静态依赖摘要不匹配")
    for row in LOCK["dependencyLicenses"]:
        if sha(HERE / "licenses" / row["path"]) != row["sha256"]:
            raise SystemExit("依赖许可摘要不匹配")

    out.mkdir(parents=True)
    build = out / "build"
    build.mkdir()
    shutil.copytree(source, out / "source", symlinks=True)
    write_json(out / "baseline-inputs.json", rows)
    subprocess.run(["patch", "-p1", "-i", str(HERE / "recover.patch")],
                   cwd=out / "source", check=True)
    if sha(out / "source/libavcodec/ohdec.c") != LOCK["ohdecPatchedSHA256"]:
        raise SystemExit("修复后的源码摘要不匹配")
    write_json(out / "source-inputs.json", inventory(out / "source"))
    write_json(out / "dependency-inputs.json", dependency_rows)
    write_json(out / "toolchain.json", {
        "path": str(ndk), "compilerSHA256": sha(compiler),
        "compilerVersion": subprocess.check_output([str(compiler), "--version"], text=True),
    })
    (build / "src").symlink_to("../source", target_is_directory=True)
    (build / "deps").symlink_to(deps, target_is_directory=True)
    (build / "toolchain").symlink_to(ndk, target_is_directory=True)
    env = dict(os.environ)
    for key in ("CFLAGS", "CXXFLAGS", "CPPFLAGS", "LDFLAGS", "CPATH", "LIBRARY_PATH",
                "C_INCLUDE_PATH", "CPLUS_INCLUDE_PATH", "SDKROOT", "MACOSX_DEPLOYMENT_TARGET"):
        env.pop(key, None)
    env.update(revision="8.0", REVISION="8.0", SOURCE_DATE_EPOCH="1755820644",
               LC_ALL="C", TZ="UTC", PKG_CONFIG_PATH="./deps/lib/pkgconfig",
               PKG_CONFIG_LIBDIR="./deps/lib/pkgconfig", PKG_CONFIG_SYSROOT_DIR="")
    configure = [
        "src/configure", "--prefix=/opt/ohos-ffmpeg8", "--arch=aarch64",
        "--target-os=linux", "--enable-cross-compile",
        "--cc=./toolchain/llvm/bin/aarch64-unknown-linux-ohos-clang",
        "--cxx=./toolchain/llvm/bin/aarch64-unknown-linux-ohos-clang++",
        "--ar=./toolchain/llvm/bin/llvm-ar", "--nm=./toolchain/llvm/bin/llvm-nm",
        "--ranlib=./toolchain/llvm/bin/llvm-ranlib", "--strip=./toolchain/llvm/bin/llvm-strip",
        "--sysroot=./toolchain/sysroot", "--extra-cflags=-fPIC -I./deps/include",
        "--extra-ldflags=-L./deps/lib", "--pkg-config-flags=--static",
        "--disable-static", "--enable-shared", "--enable-pic", "--disable-programs",
        "--disable-doc", "--disable-avdevice", "--disable-autodetect", "--disable-xlib",
        "--disable-sdl2", "--enable-network", "--enable-gnutls", "--enable-libsmbclient",
        "--enable-gpl", "--enable-version3", "--disable-nonfree", "--enable-ohcodec",
    ]
    commands = [configure, ["make", f"-j{args.jobs}"],
                ["make", "install", f"DESTDIR={out / 'install'}"]]
    write_json(out / "commands.json", commands)
    for i, command in enumerate(commands):
        with (out / f"build-{i}.log").open("w") as log:
            subprocess.run(command, cwd=build, env=env, stdout=log,
                           stderr=subprocess.STDOUT, check=True)
    sdk = out / "sdk"
    (out / "install/opt/ohos-ffmpeg8").rename(sdk)
    # Public opaque-token API belongs to this FFmpeg producer.
    shutil.copyfile(out / "source/libavcodec/ohcodec_buffer.h",
                    sdk / "include/libavcodec/ohcodec_buffer.h")
    licenses = sdk / "licenses"
    licenses.mkdir()
    for p in (out / "source").glob("COPYING*"):
        shutil.copyfile(p, licenses / p.name)
    shutil.copytree(HERE / "licenses", licenses / "static-dependencies")
    evidence = sdk / "evidence"
    evidence.mkdir()
    for name in ("baseline-inputs.json", "source-inputs.json", "dependency-inputs.json", "toolchain.json", "commands.json"):
        shutil.copyfile(out / name, evidence / name)
    shutil.copyfile(HERE / "recover.patch", evidence / "recover.patch")
    shutil.copyfile(HERE / "inputs.lock.json", evidence / "inputs.lock.json")
    config = (build / "config.h").read_text()
    if "MP_OHCODEC_" in config:
        raise SystemExit("正常构建出现诊断编译参数")
    for name in LIBRARIES:
        if not (sdk / "lib" / name).is_file():
            raise SystemExit("缺少 SDK 库 " + name)
    write_json(sdk / "manifest.json", {
        "schemaVersion": 1, "id": "phase30-close-recovery",
        "producer": "ohos_ijkplayer", "targetAbi": "arm64-v8a",
        "source": LOCK, "diagnosticInjection": False,
        "buildOrigin": "local", "files": inventory(sdk),
    })
    print(sdk)

if __name__ == "__main__":
    main()

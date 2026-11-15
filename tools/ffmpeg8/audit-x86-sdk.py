#!/usr/bin/env python3
"""核验 OHOS x86_64 软件 FFmpeg SDK；不声称目标运行验收。"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

LIBRARIES = {'avcodec': 62, 'avformat': 62, 'avfilter': 11,
             'avutil': 60, 'swresample': 6, 'swscale': 9}


def check_header(data):
    if len(data) < 64 or data[:7] != b'\x7fELF\x02\x01\x01':
        raise ValueError('必须是 little-endian ELF64')
    if struct.unpack_from('<H', data, 18)[0] != 62:
        raise ValueError('必须是 x86_64 ELF Machine')


def check_needed(needed, available):
    missing = set(needed) - set(available)
    if missing:
        raise ValueError(f'缺少 OHOS 依赖: {sorted(missing)}')


def check_software_exports(exports):
    if any(name.startswith('av_ohcodec_') for name in exports):
        raise ValueError('软件能力合同不允许意外 OHCodec 导出')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def audit(sdk, ndk):
    readelf = ndk / 'llvm/bin/llvm-readelf'
    nm = ndk / 'llvm/bin/llvm-nm'
    def run(*args):
        return subprocess.check_output(list(map(str, args)), text=True)
    def exports(path):
        return {line.split()[-1].split('@')[0]
                for line in run(nm, '-D', '--defined-only', path).splitlines() if line.split()}
    packaged = {f'lib{name}.so.{major}' for name, major in LIBRARIES.items()}
    platform = ndk / 'sysroot/usr/lib/x86_64-linux-ohos'
    report = []
    for name, major in LIBRARIES.items():
        soname = f'lib{name}.so.{major}'
        library = sdk / 'lib' / soname
        if not library.resolve().is_relative_to(sdk.resolve()):
            raise ValueError(f'库链接逃出 SDK: {library}')
        check_header(library.read_bytes()[:64])
        dynamic = run(readelf, '-d', library)
        if re.findall(r'\(SONAME\).*?\[(.*?)\]', dynamic) != [soname]:
            raise ValueError(f'SONAME 不匹配: {soname}')
        needed = re.findall(r'\(NEEDED\).*?\[(.*?)\]', dynamic)
        check_needed(needed, packaged | {p.name for p in platform.glob('*.so')})
        symbols = exports(library)
        check_software_exports(symbols)
        if name + '_version' not in symbols:
            raise ValueError(f'缺少公共版本接口: {name}')
        system = []
        for dep in needed:
            if dep in packaged:
                continue
            path = platform / dep
            check_header(path.read_bytes()[:64])
            system.append({'name': dep, 'sha256': sha(path)})
        for path in [sdk / 'include' / ('lib' + name) / 'version.h',
                     sdk / 'lib/pkgconfig' / ('lib' + name + '.pc')]:
            if not path.is_file():
                raise ValueError(f'缺少开发文件: {path}')
        pc = (sdk / 'lib/pkgconfig' / ('lib' + name + '.pc')).read_text()
        if 'prefix=${pcfiledir}/../..' not in pc or str(sdk.resolve()) in pc:
            raise ValueError(f'pkg-config 不可重定位: {name}')
        report.append({'soname': soname, 'sha256': sha(library),
                       'needed': needed, 'platformDependencies': system,
                       'exportedSymbols': sorted(symbols)})
    return {'schemaVersion': 1, 'targetAbi': 'x86_64', 'ohcodec': False,
            'libraries': report, 'deviceAcceptanceStatus': 'pending',
            'limitations': ['ELF/接口静态审计不代表设备运行通过',
                            '平台依赖身份来自本次 NDK；较低 API 兼容性未验证']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--ndk', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.sdk.resolve(), args.ndk.resolve())
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


if __name__ == '__main__':
    main()

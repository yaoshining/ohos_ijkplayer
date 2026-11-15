#!/usr/bin/env python3
"""为本次源码构建增加来源、许可证、SBOM 和完整摘要；输出必须是新目录。"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import shlex
import subprocess
import tarfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('x86audit', HERE / 'audit-x86-sdk.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def inventory(root):
    return [{'path': str(p.relative_to(root)), 'sizeBytes': p.stat().st_size,
             'sha256': audit.sha(p), **({'symlink': str(p.readlink())} if p.is_symlink() else {})}
            for p in sorted(root.rglob('*')) if p.is_file()]


def copy_and_audit(sdk, output, ndk):
    shutil.copytree(sdk, output, symlinks=True)
    return audit.audit(output, ndk)


def check_sbom_relationships(sbom):
    packages = [row['SPDXID'] for row in sbom['packages']]
    describes = sbom.get('documentDescribes', [])
    relationships = sbom.get('relationships', [])
    targets = [row['relatedSpdxElement'] for row in relationships
               if row.get('spdxElementId') == sbom['SPDXID']
               and row.get('relationshipType') == 'DESCRIBES']
    if (not packages or len(packages) != len(set(packages))
            or sorted(describes) != sorted(packages) or sorted(targets) != sorted(packages)):
        raise ValueError('SPDX 描述声明和关系必须完整对应唯一包 ID')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', required=True, type=Path)
    parser.add_argument('--ndk', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    checkout, ndk, output = args.checkout.resolve(), args.ndk.resolve(), args.output.resolve()
    if output.exists():
        raise ValueError('拒绝覆盖已有输出')
    recipe = checkout / 'tools/ffmpeg8'
    work = checkout / 'out/ffmpeg8-work'
    deps = work / 'samba-x86_64'
    prefix = work / 'smb-sysroot-x86_64'
    sdk = checkout / 'out/ffmpeg8/x86_64'
    audit.audit(sdk, ndk)
    lock = json.loads((recipe / 'dependency-sources.lock.json').read_text())
    for row in lock['sources']:
        source = deps / 'downloads' / row['archiveFile']
        if audit.sha(source) != row['sha256']:
            raise ValueError(f'来源摘要不匹配: {source}')
    ffmpeg = work / 'downloads/ffmpeg-8.0.tar.xz'
    if audit.sha(ffmpeg) != 'b2751fccb6cc4c77708113cd78b561059b6fa904b24162fa0be2d60273d27b8e':
        raise ValueError('FFmpeg 来源摘要不匹配')
    archives = []
    for name in ['z', 'popt', 'gmp', 'nettle', 'hogweed', 'tasn1', 'gnutls', 'smbclient']:
        file = prefix / 'lib' / f'lib{name}.a'
        header = subprocess.check_output([str(ndk / 'llvm/bin/llvm-readelf'), '-h', str(file)], text=True)
        machines = [line for line in header.splitlines() if 'Machine:' in line]
        if not machines or any('X86-64' not in line for line in machines):
            raise ValueError(f'静态依赖不是完整 x86_64 archive: {file}')
        archives.append({'name': file.name, 'sha256': audit.sha(file)})
    result = copy_and_audit(sdk, output, ndk)
    evidence = output / 'evidence'
    evidence.mkdir()
    write(evidence / 'elf-audit.json', result)
    consumer = evidence / 'x86-sdk-consumer.c'
    shutil.copy2(HERE / 'tests/x86-sdk-consumer.c', consumer)
    env = dict(os.environ, PKG_CONFIG_LIBDIR=str(output / 'lib/pkgconfig'),
               PKG_CONFIG_PATH='', PKG_CONFIG_SYSROOT_DIR='')
    flags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', '--libs',
            *('lib' + name for name in audit.LIBRARIES)], env=env, text=True))
    command = [str(ndk / 'llvm/bin/x86_64-unknown-linux-ohos-clang'),
               '--sysroot=' + str(ndk / 'sysroot'), str(consumer), *flags,
               '-Wl,--no-allow-shlib-undefined', '-Wl,-rpath-link,' + str(output / 'lib'),
               '-o', str(evidence / 'x86-sdk-consumer')]
    linked = subprocess.run(command, capture_output=True, text=True)
    write(evidence / 'consumer-link.json', {'command': command, 'returncode': linked.returncode,
           'stdout': linked.stdout, 'stderr': linked.stderr, 'targetRun': 'not-executed'})
    if linked.returncode:
        raise ValueError('重定位消费者链接失败，见 consumer-link.json')
    shutil.copytree(recipe, evidence / 'recipe', ignore=shutil.ignore_patterns('__pycache__', 'baseline-evidence', 'phase30-close-recovery'))
    for name in ['audit-x86-sdk.py', 'package-x86-sdk.py']:
        shutil.copy2(HERE / name, evidence / name)
    sources = list(lock['sources']) + [{'name': 'FFmpeg-8.0', 'url': 'https://ffmpeg.org/releases/ffmpeg-8.0.tar.xz', 'sha256': audit.sha(ffmpeg)}]
    directories = ['zlib-1.3.1', 'popt-1.19', 'gmp-6.3.0', 'nettle-3.9.1', 'libtasn1-4.19.0', 'gnutls-3.8.7', 'samba', 'bison-3.8.2']
    for name in directories:
        root = deps / name
        licenses = sorted(set(list(root.glob('COPYING*')) + list(root.glob('LICENSE*')) + list((root / 'doc').glob('COPYING*'))))
        if not licenses:
            raise ValueError(f'缺少许可证: {name}')
        for file in licenses:
            if file.is_file():
                dest = output / 'licenses' / name / file.relative_to(root)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, dest)
        for rel in ['config.log', 'config.h', 'config.status', 'bin/default/include/config.h', 'bin/config.log']:
            file = root / rel
            if file.is_file():
                dest = evidence / 'dependencies' / name / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, dest)
    ffbuild = work / 'build-x86_64'
    for name in ['config.h', 'config_components.h', 'ffbuild/config.mak']:
        dest = evidence / 'ffmpeg' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ffbuild / name, dest)
    decoder_lines = [line for line in (ffbuild / 'config_components.h').read_text().splitlines()
                     if line.startswith('#define CONFIG_') and '_DECODER 1' in line]
    (output / 'DECODERS.txt').write_text('\n'.join(decoder_lines) + '\n')
    write(evidence / 'ndk-sysroot.json', inventory(ndk / 'sysroot'))
    write(evidence / 'clang-resources.json', inventory(ndk / 'llvm/lib/clang'))
    tools = [{'name': name, 'sha256': audit.sha(ndk / 'llvm/bin' / name)}
             for name in ['clang', 'ld.lld', 'llvm-ar', 'llvm-ranlib', 'llvm-nm', 'llvm-readelf']]
    created = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    commit = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
    sbom = {'spdxVersion': 'SPDX-2.3', 'dataLicense': 'CC0-1.0', 'SPDXID': 'SPDXRef-DOCUMENT',
            'name': 'OHOS x86_64 FFmpeg 8 SDK',
            'documentNamespace': 'https://github.com/yaoshining/ohos_ijkplayer/sbom/' + commit + '/' + created.replace(':', '-'),
            'creationInfo': {'created': created, 'creators': ['Tool: package-x86-sdk.py']},
            'packages': [{'SPDXID': 'SPDXRef-Package-' + str(i), 'name': row['name'],
                          'downloadLocation': row['url'], 'filesAnalyzed': False,
                          'licenseConcluded': 'NOASSERTION', 'licenseDeclared': 'NOASSERTION',
                          'copyrightText': 'NOASSERTION',
                          'checksums': [{'algorithm': 'SHA256', 'checksumValue': row['sha256']}]}
                         for i, row in enumerate(sources)]}
    sbom['documentDescribes'] = [row['SPDXID'] for row in sbom['packages']]
    sbom['relationships'] = [{'spdxElementId': sbom['SPDXID'],
                              'relationshipType': 'DESCRIBES', 'relatedSpdxElement': package_id}
                             for package_id in sbom['documentDescribes']]
    check_sbom_relationships(sbom)
    write(output / 'SBOM.spdx.json', sbom)
    write(output / 'capabilities.json', {'softwareDecoding': True, 'ohcodec': False,
          'ohcodecConsumerRequirement': '必须禁用 OHCodec 编译分支，不链接 av_ohcodec_*。',
          'targetRuntime': 'pending', 'httpsAndSmbRuntime': 'pending',
          'protocols': (sdk / 'PROTOCOLS.txt').read_text().splitlines()})
    write(output / 'manifest.json', {'schemaVersion': 1, 'artifactKind': 'software-source-build',
          'targetAbi': 'x86_64', 'created': created, 'producerCommit': commit,
          'buildHost': platform.platform(), 'ndk': json.loads((ndk / 'oh-uni-package.json').read_text()),
          'tools': tools, 'sources': sources, 'staticDependencies': archives,
          'fullyVerified': False, 'deviceAcceptanceStatus': 'pending',
          'limitations': ['单次源码构建，未证明双 clean 字节重复性', '未执行目标设备播放验收', 'API26 构建的低 API 兼容性未验证'],
          'files': inventory(output)})
    (output / 'SHA256SUMS').write_text(''.join(f"{row['sha256']}  {row['path']}\n" for row in inventory(output)))
    archive = output.parent / (output.name + '.tar.gz')
    with tarfile.open(archive, 'x:gz') as tar:
        tar.add(output, arcname=output.name)
    archive.with_suffix(archive.suffix + '.sha256').write_text(f'{audit.sha(archive)}  {archive.name}\n')
    print(archive)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""TV 基线 FFmpeg/OHCodec SDK：导入、固定输入重建、摘要核验。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LOCK = json.loads((HERE / 'baseline-lock.json').read_text())
NAMES = set(LOCK['libraries'])


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def run(args, **kwargs):
    return subprocess.check_output([str(x) for x in args], **kwargs)


def record(path, root):
    return {'path': str(path.relative_to(root)), 'sha256': sha(path), 'sizeBytes': path.stat().st_size}


def inventory(root, subdir):
    return [record(p, root) for p in sorted((root / subdir).rglob('*')) if p.is_file()]


def checked_path(root, relative):
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts or not p.parts:
        raise ValueError(f'非法 SDK 相对路径: {relative}')
    target = (root / p).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f'SDK 路径逃逸: {relative}')
    return target


def check_files(root, records):
    root = Path(root)
    for row in records:
        p = checked_path(root, row['path'])
        if not p.is_file() or sha(p) != row['sha256'] or p.stat().st_size != row['sizeBytes']:
            raise ValueError(f'文件摘要或尺寸不匹配: {row["path"]}')


def fresh_output(path):
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise ValueError(f'拒绝覆盖已有输出目录: {path}')
    path.mkdir(parents=True)


def verify_static(root, expected):
    records = []
    for name, digest in expected.items():
        p = checked_path(Path(root), name)
        if not p.is_file() or sha(p) != digest:
            raise ValueError(f'静态输入 SHA256 不匹配: {name}')
        records.append(record(p, Path(root)))
    return records


def compare_libraries(root, expected):
    rows = []
    for name, digest in expected.items():
        actual = sha(root / 'lib' / name)
        rows.append({'name': name, 'baselineSha256': digest, 'rebuiltSha256': actual, 'matches': actual == digest})
    return {'status': 'compared', 'allMatch': all(r['matches'] for r in rows), 'libraries': rows}


def verify_manifest(root, pinned=None):
    root = Path(root)
    if pinned and sha(root / 'manifest.json') != pinned:
        raise ValueError('manifest SHA256 与消费者固定值不符')
    m = json.loads((root / 'manifest.json').read_text())
    required = {'schemaVersion','artifactKind','producer','baseline','targetAbi','sources','patches','tools','staticDependencies','libraries','headers','pkgconfig','licenses','sbom','rebuildComparison','deviceAcceptanceStatus','files'}
    if not required <= m.keys() or m['schemaVersion'] != 1:
        raise ValueError('manifest 必填字段不完整或 schema 不支持')
    if m['artifactKind'] not in ('imported-baseline', 'source-build') or m['deviceAcceptanceStatus'] != 'pending':
        raise ValueError('来源/设备状态不符合本次合同')
    if m['targetAbi'] != 'arm64-v8a' or len(m['libraries']) != 6 or {r['name'] for r in m['libraries']} != NAMES:
        raise ValueError('目标 ABI 或六库集合不完整')
    if m['baseline']['tvCommit'] != LOCK['tvCommit'] or m['baseline']['harSha256'] != LOCK['harSha256']:
        raise ValueError('TV 基线标识不符')
    producer = m['producer']
    if (not producer.get('repository') or not re.fullmatch(r'[0-9a-f]{40}', producer.get('revision', ''))
            or not re.fullmatch(r'[0-9a-f]{64}', producer.get('workingTreePatchSha256', ''))
            or not producer.get('workingTreePatchPath')):
        raise ValueError('producer 身份或工作树补丁摘要缺失')
    sources = {r.get('name'): r for r in m['sources']}
    if any(sources.get(name, {}).get('revision') != LOCK[key] for name, key in
           [('FFmpeg', 'ffmpegCommit'), ('libmpv-ohos-build', 'builderCommit')]):
        raise ValueError('source records 未绑定锁定提交')
    expected_patches = {Path(n).name: h for n, h in LOCK['patches'].items()}
    if {Path(r['path']).name: r['sha256'] for r in m['patches']} != expected_patches:
        raise ValueError('patch records 与锁定摘要不符')
    if m['staticDependencies'].get('fullyVerified') is not False:
        raise ValueError('本迁移流程不能声称已从源码验证完整静态依赖闭包')
    for group in ('headers', 'pkgconfig'):
        if m[group].get('status') == 'ready' and not m[group]['files']:
            raise ValueError(f'{group} ready 但文件列表为空')
    if m['artifactKind'] == 'source-build':
        if not re.fullmatch(r'[0-9a-f]{64}', sources['FFmpeg'].get('archiveSha256', '')):
            raise ValueError('source-build 缺少源码归档摘要')
        if m['rebuildComparison'] != compare_libraries(root, LOCK['libraries']):
            raise ValueError('重建比较与实际库摘要不符')
    check_files(root, m['files'])
    indexed = {r['path']: r for r in m['files']}
    if len(indexed) != len(m['files']):
        raise ValueError('重复文件路径')
    proof = indexed.get(producer['workingTreePatchPath'])
    if not proof or proof['sha256'] != producer['workingTreePatchSha256']:
        raise ValueError('producer 补丁引用未绑定文件 inventory')
    if m['staticDependencies'].get('rebuiltFromSource') is True:
        deps = m['staticDependencies']
        proof = indexed.get(deps.get('sourceManifestPath'))
        if not proof or proof['sha256'] != deps.get('sourceManifestSha256'):
            raise ValueError('源码依赖声明缺少固定摘要的来源清单')
    if m['artifactKind'] == 'source-build' and m['tools'].get('currentBuild') not in indexed:
        raise ValueError('source-build 缺少工具摘要清单')
    refs = m['libraries'] + m['patches'] + m['headers']['files'] + m['pkgconfig']['files'] + m['licenses'] + [m['sbom']]
    for row in refs:
        if any(indexed.get(row['path'], {}).get(k) != row[k] for k in ('sha256', 'sizeBytes')):
            raise ValueError(f'文件引用不在 inventory: {row["path"]}')
    check_files(root, refs)
    if m['artifactKind'] == 'imported-baseline':
        if any(r['sha256'] != LOCK['libraries'][r['name']] for r in m['libraries']):
            raise ValueError('导入包不是固定 TV 六库')
    return m


def producer_proof(root):
    scope = ['tools/ffmpeg8', '.github/workflows/build-ffmpeg8.yml']
    # 不读取无关的工作树改动或 keys；包含未跟踪的 producer 实现。
    patch = run(['git', '-c', 'core.fsmonitor=false', 'diff', '--binary', 'HEAD', '--', *scope], cwd=REPO)
    untracked = run(['git', '-c', 'core.fsmonitor=false', 'ls-files', '--others', '--exclude-standard', '-z', '--', *scope], cwd=REPO)
    for name in sorted(filter(None, untracked.decode().split('\0'))):
        if '__pycache__' in name or name.endswith('.pyc'):
            continue
        result = subprocess.run(['git', 'diff', '--no-index', '--binary', '--', '/dev/null', name], cwd=REPO, stdout=subprocess.PIPE, check=False)
        if result.returncode not in (0, 1):
            raise ValueError(f'无法记录 producer 工作树补丁: {name}')
        patch += result.stdout
    p = root / 'evidence/producer-working-tree.patch'
    p.parent.mkdir(exist_ok=True)
    p.write_bytes(patch)
    return {'repository': 'https://github.com/yaoshining/ohos_ijkplayer.git',
            'revision': run(['git', 'rev-parse', 'HEAD'], cwd=REPO).decode().strip(),
            'workingTreePatchSha256': sha(p), 'workingTreePatchPath': str(p.relative_to(root)), 'workingTreePatchScope': scope}


def copy_delivery(delivery, root):
    for name, digest in LOCK['deliveryFiles'].items():
        source = checked_path(delivery, name)
        if not source.is_file() or sha(source) != digest:
            raise ValueError(f'交付证据 SHA256 不匹配: {name}')
    for name in LOCK['deliveryFiles']:
        target = root / ('licenses/' + Path(name).name if name.startswith('licenses/') else 'evidence/original/' + name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(delivery / name, target)
    for name, digest in LOCK['patches'].items():
        if sha(HERE / name) != digest:
            raise ValueError(f'producer 补丁不匹配: {name}')
        target = root / 'evidence/patches' / Path(name).name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE / name, target)
    shutil.copy2(HERE / 'baseline-lock.json', root / 'evidence/baseline-lock.json')


def manifest(root, kind, extra=None):
    producer = producer_proof(root)
    sources = [{'name': 'FFmpeg', 'repository': 'https://code.ffmpeg.org/FFmpeg/FFmpeg.git', 'revision': LOCK['ffmpegCommit']},
               {'name': 'libmpv-ohos-build', 'repository': 'https://github.com/mpv-ohos/libmpv-ohos-build.git', 'revision': LOCK['builderCommit'], 'role': 'AV3A/OHCodec patches'}]
    sbom = {'format': 'producer-inventory-v1', 'complete': False,
            'limitations': ['SMB/TLS 静态闭包未从全部依赖源码重建', '历史构建工具链字节身份未知'],
            'sources': (extra or {}).get('sources', sources), 'staticInputs': ({r['path']:r['sha256'] for r in extra['staticDependencies']['archives']} if extra and 'archives' in extra.get('staticDependencies', {}) else LOCK['staticInputs']), 'licenseFiles': inventory(root, 'licenses')}
    write_json(root / 'sbom.json', sbom)
    m = {'schemaVersion': 1, 'artifactKind': kind, 'producer': producer,
         'baseline': {k: LOCK[k] for k in ('tvCommit','harSha256','mpvSha256')},
         'targetAbi': 'arm64-v8a', 'sources': sources,
         'patches': inventory(root, 'evidence/patches'),
         'tools': {'historicalBuild': 'unknown', 'currentBuild': 'not-applicable'},
         'staticDependencies': {'status': 'historical-digest-evidence', 'rebuiltFromSource': False, 'fullyVerified': False, 'expectedSha256': LOCK['staticInputs']},
         'libraries': [dict(record(root / 'lib' / n, root), name=n) for n in sorted(NAMES)],
         'headers': {'status': 'pending', 'origin': 'historical headers unavailable', 'files': inventory(root, 'include')},
         'pkgconfig': {'status': 'pending', 'origin': 'historical pkgconfig unavailable', 'files': inventory(root, 'lib/pkgconfig')},
         'licenses': inventory(root, 'licenses'), 'sbom': record(root / 'sbom.json', root),
         'rebuildComparison': {'status': 'not-rebuilt'}, 'deviceAcceptanceStatus': 'pending'}
    if extra:
        m.update(extra)
    m['files'] = [record(p, root) for p in sorted(root.rglob('*')) if p.is_file() and p.name != 'manifest.json']
    write_json(root / 'manifest.json', m)
    verify_manifest(root)
    return m


def handoff(root, status, **extra):
    path = REPO / 'docs/vidall-tv-baseline-handoff.json'
    old = json.loads(path.read_text()) if path.exists() else {}
    old.update({'schemaVersion': 1, 'status': status, 'sdkRoot': str(root.resolve()),
                'manifestPath': str((root / 'manifest.json').resolve()), 'manifestSha256': sha(root / 'manifest.json'),
                'artifactKind': 'imported-baseline', 'deviceAcceptanceStatus': 'pending',
                'specKit': {n: str(REPO / 'specs/001-ffmpeg-ohcodec-producer' / (n + '.md')) for n in ('spec','plan','tasks','research','data-model','quickstart')}})
    old.update(extra)
    write_json(path, old)


def import_baseline(args):
    tv, delivery, root = args.tv.resolve(), args.delivery.resolve(), args.output.resolve()
    actual = run(['git', '-C', tv, 'rev-parse', 'HEAD']).decode().strip()
    if actual != LOCK['tvCommit'] or sha(tv / 'entry/libs/vidall_player.har') != LOCK['harSha256']:
        raise ValueError('当前 TV HEAD/HAR 与基线不一致')
    with tarfile.open(tv / 'entry/libs/vidall_player.har') as archive:
        members = [m for m in archive.getmembers() if m.name.endswith('/libs/arm64-v8a/libmpv.so')]
        if len(members) != 1 or hashlib.sha256(archive.extractfile(members[0]).read()).hexdigest() != LOCK['mpvSha256']:
            raise ValueError('HAR 内 ARM64 libmpv 摘要不一致')
    for name, digest in LOCK['libraries'].items():
        for p in (tv / 'entry/libs/arm64-v8a' / name, delivery / 'arm64-v8a' / name):
            if sha(p) != digest:
                raise ValueError(f'TV/delivery 六库不一致: {name}')
    fresh_output(root)
    copy_delivery(delivery, root)
    (root / 'lib').mkdir()
    for name in sorted(NAMES):
        shutil.copy2(delivery / 'arm64-v8a' / name, root / 'lib' / name)
        (root / 'lib' / name.split('.so.')[0]).with_suffix('.so').symlink_to(name)
    manifest(root, 'imported-baseline')
    handoff(root, 'runtime-ready', remainingGaps=['开发头文件待锁定源码构建', '完整静态依赖源码重建未完成', '真机 pending'])
    print(f'imported-baseline: {root}')


def static_input(args):
    source_manifest = getattr(args, 'static_manifest', None)
    if source_manifest:
        if not getattr(args, 'static_manifest_sha256', None) or sha(source_manifest) != args.static_manifest_sha256:
            raise ValueError('新源码依赖 manifest SHA256 未锁定或不匹配')
        m = json.loads(source_manifest.read_text())
        if m.get('targetAbi') != 'arm64-v8a' or m.get('sourceBuildComplete') is not True or m.get('fullyVerified') is not False:
            raise ValueError('新源码静态依赖状态不符合诊断构建合同')
        expected = {r['path']: r['sha256'] for r in m['archives']}
        if len(m['archives']) != len(LOCK['staticInputs']) or set(expected) != set(LOCK['staticInputs']):
            raise ValueError('新源码依赖必须包含准确八库集合')
        if 'headers' not in m or 'pkgconfig' not in m:
            raise ValueError('新源码依赖清单未绑定 headers/pkgconfig')
        check_files(args.smb, m['archives'] + m['headers'] + m['pkgconfig'])
        return expected
    return LOCK['staticInputs']


def capture_inputs(args, root):
    records = verify_static(args.smb, static_input(args))
    static = {'status': 'digest-verified-cache', 'rebuiltFromSource': False, 'fullyVerified': False,
              'root': str(args.smb), 'archives': records, 'files': inventory(args.smb, 'include') + inventory(args.smb, 'lib/pkgconfig')}
    if getattr(args, 'static_manifest', None):
        shutil.copy2(args.static_manifest, root / 'dependency-source-manifest.json')
        static.update(status='source-rebuilt-diagnostic', rebuiltFromSource=True,
                      sourceManifestSha256=args.static_manifest_sha256,
                      sourceManifestPath='evidence/dependency-source-manifest.json')
    write_json(root / 'static-inputs.json', static)
    ndk_files = inventory(args.ndk, 'sysroot')
    write_json(root / 'ndk-sysroot.json', {'root': str(args.ndk), 'files': ndk_files})
    paths = [args.ndk / 'llvm/bin' / n for n in ('aarch64-unknown-linux-ohos-clang','aarch64-unknown-linux-ohos-clang++','clang','clang-15','ld.lld','llvm-ar','llvm-nm','llvm-ranlib','llvm-strip','llvm-readelf')]
    paths += [Path(shutil.which(n)) for n in ('make','pkg-config','patch','git','python3','sh','perl') if shutil.which(n)]
    tools = [{'path': str(p), 'resolvedPath': str(p.resolve()), 'sha256': sha(p), 'sizeBytes': p.stat().st_size} for p in paths if p.is_file()]
    # clang resource headers/builtins are outside the NDK sysroot.
    resource = args.ndk / 'llvm/lib/clang'
    write_json(root / 'clang-resources.json', {'root': str(resource), 'files': inventory(resource, '.')})
    write_json(root / 'tools.json', {'files': tools, 'compilerVersion': run([args.ndk / 'llvm/bin/aarch64-unknown-linux-ohos-clang', '--version']).decode()})
    return static


def audit(root, ndk):
    reports = []
    for name in sorted(NAMES):
        p = root / 'lib' / name
        header = run([ndk / 'llvm/bin/llvm-readelf', '-h', p]).decode()
        dynamic = run([ndk / 'llvm/bin/llvm-readelf', '-d', p]).decode()
        if 'ELF64' not in header or 'AArch64' not in header or f'[{name}]' not in dynamic:
            raise ValueError(f'ELF/SONAME 不匹配: {name}')
        needed = re.findall(r'\(NEEDED\).*?\[(.*?)\]', dynamic)
        if any(re.match(r'lib(smbclient|gnutls|tasn1|nettle|hogweed|gmp|popt|z)\.so', n) for n in needed):
            raise ValueError(f'静态依赖意外变为动态依赖: {name}')
        reports.append({'name': name, 'needed': needed})
    codec = (root / 'lib/libavcodec.so.62').read_bytes()
    if any(n not in codec for n in (b'h264_ohcodec\0', b'hevc_ohcodec\0')):
        raise ValueError('缺少 H264/HEVC OHCodec decoder')
    symbols = '\n'.join(run([ndk / 'llvm/bin/llvm-nm', '-D', '--defined-only', root / 'lib' / name]).decode()
                        for name in ('libavutil.so.60', 'libavcodec.so.62'))
    if not re.search(r'\bav_ohcodec_release_buffer(?:@@?\S+)?$', symbols, re.M):
        raise ValueError('缺少 av_ohcodec_release_buffer 导出')
    fmt = root / 'lib/libavformat.so.62'
    data = fmt.read_bytes()
    if any(n not in data for n in (b'libsmbclient',b'https',b'GnuTLS')):
        raise ValueError('缺少 SMB/HTTPS/GnuTLS 实现标记')
    undefined = run([ndk / 'llvm/bin/llvm-nm', '-D', '--undefined-only', fmt]).decode()
    if re.search(r'\b(gnutls_|smbc_|nettle_|hogweed_|__gmp|asn1_)', undefined):
        raise ValueError('SMB/TLS 静态闭包存在未解析符号')
    write_json(root / 'evidence/elf-audit.json', {'status': 'passed', 'libraries': reports, 'deviceAcceptanceStatus': 'pending'})


def build(args):
    root = args.output.resolve()
    args.ndk, args.smb = args.ndk.resolve(), args.smb.resolve()
    verify_static(args.smb, static_input(args))
    for name, digest in LOCK['patches'].items():
        if sha(HERE / name) != digest:
            raise ValueError(f'补丁摘要不符: {name}')
        if '/ohcodec/' in name:
            original = run(['git', '-C', args.builder_repo, 'show', LOCK['builderCommit'] + ':patches/ffmpeg/' + Path(name).name])
            if hashlib.sha256(original).hexdigest() != digest:
                raise ValueError('上游锁定提交补丁与 producer 不一致')
    fresh_output(root)
    static = capture_inputs(args, root)
    shutil.copy2(HERE / 'producer-sdk.py', root / 'producer-sdk.used.py')
    shutil.copy2(HERE / 'build-ohcodec.sh', root / 'build-ohcodec.used.sh')
    shutil.copy2(HERE / 'build-env.sh', root / 'build-env.used.sh')
    env = os.environ.copy()
    env.update({'OHOS_NDK': str(args.ndk), 'SMB_PREFIX': str(args.smb), 'FFMPEG_SOURCE_REPO': str(args.ffmpeg_repo.resolve()), 'OUTPUT_ROOT': str(root / 'work'), 'JOBS': str(args.jobs)})
    with (root / 'build.log').open('w') as log:
        subprocess.run(['bash', str(HERE / 'build-ohcodec.sh')], env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    package_build(args)


def package_build(args):
    root = args.output.resolve()
    sdk = root / 'work/prefix'
    if (sdk / 'manifest.json').exists():
        raise ValueError('拒绝重新打包已有 manifest 的源码 SDK')
    args.ndk, args.smb = args.ndk.resolve(), args.smb.resolve()
    static = json.loads((root / 'static-inputs.json').read_text())
    archive_digest = hashlib.sha256(run(['git', '-C', args.ffmpeg_repo, 'archive', LOCK['ffmpegCommit']])).hexdigest()
    if sha(root / 'work/source.tar') != archive_digest:
        raise ValueError('源码归档与固定 FFmpeg 提交不匹配')
    for filename, base in [('ndk-sysroot.json', args.ndk), ('clang-resources.json', args.ndk / 'llvm/lib/clang')]:
        check_files(base, json.loads((root / filename).read_text())['files'])
    for tool in json.loads((root / 'tools.json').read_text())['files']:
        if sha(tool['path']) != tool['sha256']:
            raise ValueError('工具链在构建期间发生变化')
    # 构建后复核缓存摘要，防止构建期间输入被修改。
    verify_static(args.smb, {r['path']: r['sha256'] for r in static['archives']})
    for row in static['files']:
        check_files(args.smb, [row])
    sdk = root / 'work/prefix'
    copy_delivery(args.delivery.resolve(), sdk)
    for name in ('static-inputs.json','ndk-sysroot.json','clang-resources.json','tools.json','build.log','producer-sdk.used.py','build-ohcodec.used.sh','build-env.used.sh'):
        shutil.copy2(root / name, sdk / 'evidence' / name)
    if (root / 'dependency-source-manifest.json').exists():
        shutil.copy2(root / 'dependency-source-manifest.json', sdk / 'evidence/dependency-source-manifest.json')
        if (args.smb / 'licenses').is_dir():
            shutil.copytree(args.smb / 'licenses', sdk / 'licenses/source-dependencies')
    shutil.copy2(root / 'work/build/config.h', sdk / 'evidence/ffmpeg-config.h')
    shutil.copy2(root / 'work/build/ffbuild/config.mak', sdk / 'evidence/ffmpeg-config.mak')
    for pc in (sdk / 'lib/pkgconfig').glob('*.pc'):
        text = pc.read_text()
        for key, value in {'prefix':'${pcfiledir}/../..','exec_prefix':'${prefix}','libdir':'${exec_prefix}/lib','includedir':'${prefix}/include'}.items():
            text = re.sub(r'^' + key + '=.*$', key + '=' + value, text, flags=re.M)
        pc.write_text(text)
    audit(sdk, args.ndk)
    comparison = compare_libraries(sdk, LOCK['libraries'])
    write_json(root / 'rebuild-comparison.json', comparison)
    extra = {'buildRecipe': [record(sdk / 'evidence' / n, sdk) for n in ('producer-sdk.used.py', 'build-ohcodec.used.sh', 'build-env.used.sh')],
             'tools': {'historicalBuild': 'unknown', 'currentBuild': 'evidence/tools.json', 'sysrootInventory': 'evidence/ndk-sysroot.json', 'clangResourceInventory': 'evidence/clang-resources.json'},
             'staticDependencies': dict(static, inventoryPath='evidence/static-inputs.json'),
             'headers': {'status':'ready','origin':'source-build','files':inventory(sdk,'include')},
             'pkgconfig': {'status':'ready','origin':'source-build-relocatable','files':inventory(sdk,'lib/pkgconfig')},
             'rebuildComparison':comparison,
             'sources':[{'name':'FFmpeg','revision':LOCK['ffmpegCommit'],'archiveSha256':sha(root/'work/source.tar'),'repository':'https://code.ffmpeg.org/FFmpeg/FFmpeg.git'},
                        {'name':'libmpv-ohos-build','repository':'https://github.com/mpv-ohos/libmpv-ohos-build.git','revision':LOCK['builderCommit'],'role':'locked patches verified against git objects'}]}
    manifest(sdk, 'source-build', extra)
    print(json.dumps({'sdkRoot':str(sdk),'rebuildComparison':comparison}, ensure_ascii=False, indent=2))


def attach_headers(args):
    baseline = args.sdk.resolve()
    original = verify_manifest(baseline, args.manifest_sha256)
    rebuilt = verify_manifest(args.rebuilt_sdk, args.rebuilt_manifest_sha256)
    if original['artifactKind'] != 'imported-baseline' or rebuilt['artifactKind'] != 'source-build':
        raise ValueError('只能给导入基线附加锁定源码重建的开发文件')
    for dest, source in [('include','include'), ('lib/pkgconfig','lib/pkgconfig')]:
        if (baseline / dest).exists():
            raise ValueError(f'拒绝覆盖已有开发文件: {dest}')
        shutil.copytree(args.rebuilt_sdk / source, baseline / dest)
    shutil.copy2(args.rebuilt_sdk / 'manifest.json', baseline / 'evidence/header-source-manifest.json')
    extra = {'headers': {'status':'ready','origin':'source-build (not historical imported headers)', 'files':inventory(baseline,'include')},
             'pkgconfig': {'status':'ready','origin':'source-build-relocatable (not historical imported pkgconfig)','files':inventory(baseline,'lib/pkgconfig')},
             'rebuildComparison': rebuilt['rebuildComparison']}
    if 'derivation' in original:
        extra['derivation'] = original['derivation']
    manifest(baseline, 'imported-baseline', extra)
    handoff(baseline, 'sdk-ready', sourceBuild={'sdkRoot':str(args.rebuilt_sdk.resolve()), 'manifestPath':str((args.rebuilt_sdk/'manifest.json').resolve()), 'manifestSha256':sha(args.rebuilt_sdk/'manifest.json'), 'rebuildComparison':rebuilt['rebuildComparison']}, remainingGaps=['重建库与基线差异详见 sourceBuild，未替换导入 runtime','SMB/TLS 未全依赖源码重建','原始构建工具链字节身份未知','真机 pending'])


def derive_imported(args):
    source = args.sdk.resolve()
    original = verify_manifest(source, args.manifest_sha256)
    verify_manifest(args.rebuilt_sdk, args.rebuilt_manifest_sha256)
    if original['artifactKind'] != 'imported-baseline':
        raise ValueError('只能从固定的 imported-baseline 派生')
    root = args.output.resolve()
    fresh_output(root)
    for folder in ('lib', 'evidence', 'licenses'):
        shutil.copytree(source / folder, root / folder, symlinks=True,
                        ignore=(lambda directory, names: ['pkgconfig'] if Path(directory) == source / 'lib' else []))
    shutil.copy2(source / 'manifest.json', root / 'evidence/imported-source-manifest.json')
    manifest(root, 'imported-baseline', {'derivation': {
        'sourceManifestSha256': args.manifest_sha256,
        'sourceManifestPath': 'evidence/imported-source-manifest.json',
        'runtimeRebuilt': False, 'originalBaselineCommit': LOCK['tvCommit']}})
    args.sdk = root
    args.manifest_sha256 = sha(root / 'manifest.json')
    attach_headers(args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('import-baseline')
    for name in ('tv','delivery','output'): p.add_argument('--'+name, type=Path, required=True)
    p.set_defaults(func=import_baseline)
    for command, func in [('build', build), ('package-build', package_build)]:
        p = sub.add_parser(command)
        for name in ('ndk','smb','ffmpeg-repo','builder-repo','delivery','output'): p.add_argument('--'+name, type=Path, required=True)
        p.add_argument('--static-manifest',type=Path)
        p.add_argument('--static-manifest-sha256')
        p.add_argument('--jobs',type=int,default=8)
        p.set_defaults(func=func)
    p = sub.add_parser('verify')
    p.add_argument('--sdk',type=Path,required=True)
    p.add_argument('--manifest-sha256',required=True)
    p.set_defaults(func=lambda a: (verify_manifest(a.sdk,a.manifest_sha256), print('SDK 摘要核验通过')))
    p = sub.add_parser('attach-headers')
    for name in ('sdk','rebuilt-sdk'): p.add_argument('--'+name,type=Path,required=True)
    for name in ('manifest-sha256','rebuilt-manifest-sha256'): p.add_argument('--'+name,required=True)
    p.set_defaults(func=attach_headers)
    p = sub.add_parser('derive-imported')
    for name in ('sdk','rebuilt-sdk','output'): p.add_argument('--'+name,type=Path,required=True)
    for name in ('manifest-sha256','rebuilt-manifest-sha256'): p.add_argument('--'+name,required=True)
    p.set_defaults(func=derive_imported)
    args = parser.parse_args()
    if getattr(args,'jobs',1) < 1: parser.error('jobs 必须为正数')
    args.func(args)

if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError, KeyError) as error:
        print(f'error: {error}', file=sys.stderr)
        sys.exit(1)

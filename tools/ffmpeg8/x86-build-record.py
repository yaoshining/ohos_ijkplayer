#!/usr/bin/env python3
"""绑定实际 x86 SDK/静态 sysroot 的源码输入与产物，拒绝缓存来源漂移。"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inputs(repo, ndk):
    recipe = repo / 'tools/ffmpeg8'
    paths = [p for p in recipe.iterdir() if p.is_file() and p.suffix in ('.sh', '.py', '.json')]
    paths += [p for p in (recipe / 'patches').rglob('*') if p.is_file()]
    paths += [repo / 'tools/phase20/apply.py']
    paths += [p for p in (repo / 'tools/phase20/runtime').iterdir() if p.is_file()]
    if (repo / '.git').exists():
        commit = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
        relative = [str(p.relative_to(repo)) for p in paths]
        subprocess.run(['git', '-C', str(repo), 'diff', '--exit-code', 'HEAD', '--', *relative], check=True,
                       stdout=subprocess.DEVNULL)
    else:
        commit = json.loads((repo / 'SOURCE.json').read_text())['commit']
    return {'producerCommit': commit,
            'recipeSha256': {str(p.relative_to(repo)): sha(p) for p in sorted(paths)},
            'toolchain': {name: sha(ndk / name) for name in
                          ['oh-uni-package.json', 'llvm/bin/clang', 'llvm/bin/ld.lld', 'llvm/bin/llvm-ar']}}


def artifact_files(prefix):
    return {str(p.relative_to(prefix)): sha(p) for directory in ('lib', 'include')
            for p in sorted((prefix / directory).rglob('*')) if p.is_file()}


def validate(record, current, prefix):
    if record['inputs'] != current:
        raise ValueError('构建输入与源码提交不匹配，必须使用新目录完整重建')
    if not record.get('files') or record['files'] != artifact_files(prefix):
        raise ValueError('构建产物缺失或摘要漂移，必须完整重建')


def verify_record(record_path, repo, ndk, prefix):
    record = json.loads(record_path.read_text())
    validate(record, inputs(repo, ndk), prefix)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['begin', 'seal', 'verify'])
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--ndk', type=Path, required=True)
    parser.add_argument('--record', type=Path, required=True)
    parser.add_argument('--prefix', type=Path)
    parser.add_argument('--start', type=Path)
    args = parser.parse_args()
    current = inputs(args.repo.resolve(), args.ndk.resolve())
    if args.operation == 'begin':
        result = current
    elif args.operation == 'seal':
        if args.prefix is None or args.start is None:
            parser.error('seal 需要 --prefix 与 --start')
        if json.loads(args.start.read_text()) != current:
            raise ValueError('构建期间输入漂移')
        result = {'inputs': current, 'files': artifact_files(args.prefix)}
        validate(result, current, args.prefix)
    else:
        if args.prefix is None:
            parser.error('verify 需要 --prefix')
        validate(json.loads(args.record.read_text()), current, args.prefix)
        return
    args.record.parent.mkdir(parents=True, exist_ok=True)
    args.record.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Phase27 固定源码与真实函数回归；仅上传显式选择的文本证据。"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import urllib.request

SUFFIXES = {'.c', '.h', '.py', '.json', '.md', '.patch', '.yml', '.yaml', '.txt'}

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def verify(base):
    base = Path(base).resolve()
    rows = json.loads((base / 'source-index.json').read_text())
    seen = set()
    for row in rows:
        name = row['path']; rel = PurePosixPath(name)
        if rel.is_absolute() or '..' in rel.parts or str(rel) != name or '\\' in name:
            raise ValueError('invalid path: ' + name)
        if name in seen or rel.suffix not in SUFFIXES:
            raise ValueError('duplicate or forbidden source: ' + name)
        seen.add(name); p = base / name
        if any(x.is_symlink() for x in [p, *p.parents] if x != base.parent):
            raise ValueError('symlink: ' + name)
        if not p.is_file() or p.stat().st_size != row['size'] or sha(p) != row['sha256']:
            raise ValueError('source drift: ' + name)
    source = base / 'source'
    actual = {p.relative_to(base).as_posix() for p in source.rglob('*') if p.is_file() or p.is_symlink()}
    if actual != {n for n in seen if n.startswith('source/')}:
        raise ValueError('source file set drift')
    return rows

def exact_source(root, rows):
    expected = {r['path']: r for r in rows}
    files = {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file() or p.is_symlink()}
    if files.keys() != expected.keys():
        raise ValueError('FFmpeg file set drift: ' + str(sorted(files.keys() ^ expected.keys())))
    for name, p in files.items():
        if p.is_symlink() or p.stat().st_size != expected[name]['size'] or sha(p) != expected[name]['sha256']:
            raise ValueError('FFmpeg bytes drift: ' + name)

def artifact_audit(root):
    rows = []
    for p in sorted(root.rglob('*')):
        if p.is_symlink(): raise ValueError('artifact symlink')
        if not p.is_file(): continue
        if p.suffix not in SUFFIXES | {'.log'} or p.stat().st_size > 8 * 1024 * 1024:
            raise ValueError('forbidden artifact: ' + str(p))
        if p.name == 'artifact-index.json': continue
        rows.append({'path': p.relative_to(root).as_posix(), 'size': p.stat().st_size, 'sha256': sha(p)})
    return rows

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, required=True); ap.add_argument('--archive', type=Path); ap.add_argument('--allow-dirty', action='store_true')
    a = ap.parse_args(); here = Path(__file__).resolve().parent
    rows = verify(here)
    index_sha = sha(here / 'source-index.json')
    repo = here.parents[1]
    def git(*args): return subprocess.check_output(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', *args], cwd=repo, text=True).strip()
    provenance = {'head': git('rev-parse', 'HEAD'), 'dirty': git('status', '--porcelain', '--untracked-files=all'), 'sourceIndexSHA256': index_sha}
    if provenance['dirty'] and not a.allow_dirty: raise ValueError('dirty checkout; development override must be explicit')
    workflow = repo / '.github/workflows/phase27-validation.yml'
    workflow_sha = sha(workflow)
    if workflow_sha != sha(here / 'source/workflow.yml'): raise ValueError('workflow input drift')
    provenance['workflowSHA256'] = workflow_sha
    out = a.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    artifact = out / 'artifact'; artifact.mkdir()
    commands = []; tests_passed = False; host_built = False
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', ASAN_OPTIONS='halt_on_error=1:detect_leaks=' + ('0' if sys.platform == 'darwin' else '1'), UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    def run(label, argv, cwd=None):
        with (artifact / (label + '.log')).open('w') as log:
            r = subprocess.run([str(x) for x in argv], cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
        commands.append({'label': label, 'argv': [str(x) for x in argv], 'exitCode': r.returncode})
        (artifact / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        if r.returncode: raise RuntimeError(label + ' failed')
    try:
        (artifact / 'provenance-before.json').write_text(json.dumps(provenance, indent=2)+'\n')
        tool_rows = []
        for tool in ['clang', 'make', 'git']:
            path = Path(shutil.which(tool)).resolve(); tool_rows.append({'name':tool,'path':str(path),'sha256':sha(path)})
            run('tool-'+tool, [tool, '--version'])
        path = Path(sys.executable).resolve(); tool_rows.append({'name':'python','path':str(path),'sha256':sha(path),'version':sys.version})
        (artifact/'host-tools.json').write_text(json.dumps(tool_rows,indent=2)+'\n')
        run('runner-tests', [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', here / 'tests', '-v'])
        phase = out / 'work/out/phase27'; phase.mkdir(parents=True)
        upstream = json.loads((here / 'source/ffmpeg-upstream.json').read_text())
        archive = out / 'ffmpeg-base.tar.gz'
        if a.archive: shutil.copyfile(a.archive, archive)
        else:
            with urllib.request.urlopen(upstream['url'], timeout=120) as r, archive.open('wb') as f: shutil.copyfileobj(r, f)
        if archive.stat().st_size != upstream['size'] or sha(archive) != upstream['sha256']: raise ValueError('archive pin mismatch')
        src = phase / 'ffmpeg-input/source'; src.mkdir(parents=True)
        with tarfile.open(archive) as tar:
            names = set()
            for m in tar:
                p = PurePosixPath(m.name)
                if p.is_absolute() or '..' in p.parts or not (m.isfile() or m.isdir()): raise ValueError('unsafe archive member')
                if len(p.parts) < 2: continue
                rel = PurePosixPath(*p.parts[1:]); target = src / str(rel)
                if str(rel) in names: raise ValueError('duplicate archive member')
                names.add(str(rel))
                if m.isdir(): target.mkdir(parents=True, exist_ok=True); continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(m) as r, target.open('wb') as f: shutil.copyfileobj(r, f)
                target.chmod(0o755 if m.mode & 0o111 else 0o644)
        run('apply-ffmpeg', ['git', 'apply', '--no-index', here / 'source/ffmpeg.patch'], src)
        pins = json.loads((here / 'source/ffmpeg-index.json').read_text()); exact_source(src, pins)
        (artifact / 'ffmpeg-source-check.json').write_text(json.dumps({'files': len(pins), 'exactSetAndBytes': True, 'archiveSHA256': sha(archive)}, indent=2))
        for name in ['tests/ffmpeg', 'tests/mpv', 'input-package/sources/mpv']:
            shutil.copytree(here / 'source' / name, phase / name)
        host = phase / 'research/host-sei'
        run('host-build', [sys.executable, '-B', here / 'source/host/build_host.py', '--source', src, '--out', host])
        host_built = True
        run('mpv', [sys.executable, '-B', phase / 'tests/mpv/run.py', 'ci-green'])
        run('ffmpeg-helper', [sys.executable, '-B', phase / 'tests/ffmpeg/run.py', 'ci-green'])
        run('ohdec-integration', [sys.executable, '-B', phase / 'tests/ffmpeg/integration.py', 'ci-integration'])
        review = phase / 'tests/ffmpeg/review_test'
        run('review-compile', ['clang', '-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-I'+str(host/'build'), '-I'+str(src), phase/'tests/ffmpeg/review_test.c', src/'libavcodec/ohcodec_hdr.c', host/'build/libavcodec/libavcodec.a', host/'build/libavutil/libavutil.a', '-lm', '-pthread', '-o', review])
        for case in ['unknown-normalized-zero', 'duplicate-third', 'output-oom', 'existing-cll-dovi', 'capacity', 'irap-multislice']:
            run('review-' + case, [review, case])
        for name, cases in [('annexb', ['prefix-before-irap', 'non-irap', 'extradata-only', 'sei-before-ps', 'sei-after-ps']), ('preference', ['default', 'prefer-packet'])]:
            exe = phase/'tests/ffmpeg'/name
            run(name+'-compile', ['clang', '-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-I'+str(host/'build'), '-I'+str(src), '-I'+str(src/'libavcodec'), phase/'tests/ffmpeg'/(name+'_test.c'), src/'libavcodec/ohcodec_hdr.c', host/'build/libavcodec/libavcodec.a', host/'build/libavutil/libavutil.a', '-lm', '-pthread', '-o', exe])
            for case in cases: run(name+'-'+case, [exe, case])
        exact_source(src, pins); verify(here)
        for root in [phase/'tests/mpv/ci-green', phase/'tests/ffmpeg/ci-green', phase/'tests/ffmpeg/ci-integration', host]:
            for p in root.iterdir():
                if p.is_file() and p.suffix in {'.json', '.log'}:
                    q = artifact / 'results' / root.relative_to(phase) / p.name; q.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(p, q)
        tests_passed = True
    finally:
        for row in rows:
            q = artifact / 'execution/tools/phase27' / row['path']; q.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(here / row['path'], q)
        shutil.copyfile(here/'source-index.json', artifact/'source-index.json')
        if workflow.is_file():
            q = artifact/'execution/.github/workflows/phase27-validation.yml'; q.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(workflow, q)
        after = {'head': git('rev-parse', 'HEAD'), 'dirty': git('status', '--porcelain', '--untracked-files=all'), 'sourceIndexSHA256': sha(here/'source-index.json'), 'workflowSHA256': sha(workflow)}
        (artifact/'provenance-after.json').write_text(json.dumps(after, indent=2)+'\n')
        verify(here)
        stable = provenance == after
        artifact_audit(artifact)
        (artifact/'result.json').write_text(json.dumps({'testsPassed': tests_passed, 'collectionPassed': True, 'inputsStable': stable, 'passed': tests_passed and stable, 'targetExecuted': False, 'deviceAcceptance': 'separate', 'realUpstreamSEIObjects': host_built}, indent=2)+'\n')
        index = artifact_audit(artifact)
        (artifact/'artifact-index.json').write_text(json.dumps(index, indent=2)+'\n')
        if not stable: raise ValueError('execution inputs or git state changed')

if __name__ == '__main__': main()

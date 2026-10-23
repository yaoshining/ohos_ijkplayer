#!/usr/bin/env python3
"""Phase28 fixed-source lifecycle + HDR regression CI.

Downloads the pinned FFmpeg archive, applies the Phase27 portable patch then the
Phase28 ohdec delta, verifies the exact source set/bytes, and runs the real
function RED/GREEN lifecycle suites plus HDR/SEI/AnnexB/preference regressions.
Only text logs and JSON are uploaded.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, tarfile, urllib.request
from pathlib import Path, PurePosixPath

SUFFIXES = {'.c', '.h', '.py', '.json', '.md', '.patch', '.yml', '.yaml', '.txt'}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def verify(base):
    base = Path(base).resolve(); rows = json.loads((base/'source-index.json').read_text()); seen=set()
    for row in rows:
        name=row['path']; rel=PurePosixPath(name)
        if rel.is_absolute() or '..' in rel.parts or str(rel)!=name or '\\' in name: raise ValueError('invalid path: '+name)
        if name in seen or rel.suffix not in SUFFIXES: raise ValueError('duplicate/forbidden: '+name)
        seen.add(name); p=base/name
        if any(x.is_symlink() for x in [p,*p.parents] if x!=base.parent): raise ValueError('symlink: '+name)
        if not p.is_file() or p.stat().st_size!=row['size'] or sha(p)!=row['sha256']: raise ValueError('source drift: '+name)
    actual={p.relative_to(base).as_posix() for p in (base/'source').rglob('*') if p.is_file() or p.is_symlink()}
    if actual != {n for n in seen if n.startswith('source/')}: raise ValueError('source file set drift')
    return rows

def exact_source(root, rows):
    expected={r['path']:r for r in rows}
    files={p.relative_to(root).as_posix():p for p in Path(root).rglob('*') if p.is_file() or p.is_symlink()}
    if files.keys()!=expected.keys():
        raise ValueError('FFmpeg file set drift: '+str(sorted(files.keys()^expected.keys())[:10]))
    for name,p in files.items():
        if p.is_symlink() or p.stat().st_size!=expected[name]['size'] or sha(p)!=expected[name]['sha256']:
            raise ValueError('FFmpeg bytes drift: '+name)

def artifact_audit(root):
    rows=[]
    for p in sorted(Path(root).rglob('*')):
        if p.is_symlink(): raise ValueError('artifact symlink')
        if not p.is_file(): continue
        if p.suffix not in SUFFIXES|{'.log'} or p.stat().st_size>8*1024*1024: raise ValueError('forbidden artifact: '+str(p))
        if p.name=='artifact-index.json': continue
        rows.append({'path':p.relative_to(root).as_posix(),'size':p.stat().st_size,'sha256':sha(p)})
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--archive',type=Path); ap.add_argument('--allow-dirty',action='store_true')
    a=ap.parse_args(); here=Path(__file__).resolve().parent; rows=verify(here)
    repo=here.parents[1]
    def git(*args): return subprocess.check_output(['git','--no-optional-locks','-c','core.fsmonitor=false',*args],cwd=repo,text=True).strip()
    before={'head':git('rev-parse','HEAD'),'dirty':git('status','--porcelain','--untracked-files=all'),'sourceIndexSHA256':sha(here/'source-index.json')}
    if before['dirty'] and not a.allow_dirty: raise ValueError('dirty checkout')
    workflow=repo/'.github/workflows/phase28-validation.yml'; wf_sha=sha(workflow)
    if wf_sha!=sha(here/'source/workflow.yml'): raise ValueError('workflow drift')
    before['workflowSHA256']=wf_sha
    out=a.out.resolve(); repo=repo.resolve()
    if out==repo or repo in out.parents: raise ValueError('output must be outside checkout')
    out.mkdir(parents=True,exist_ok=False); artifact=out/'artifact'; artifact.mkdir()
    work=out/'work/out/phase28'; work.mkdir(parents=True)
    src=work/'ffmpeg-input/source'; src.mkdir(parents=True)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',ASAN_OPTIONS='halt_on_error=1:detect_leaks='+('0' if sys.platform=='darwin' else '1'),UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1',PHASE28_BINDING_ROOT=str(work),PHASE28_BASELINE_ROOT=str(work/'tests/lifecycle/baseline'),PHASE28_MPV_ROOT=str(work/'input-package/sources/mpv'),PHASE28_FFMPEG_ROOT=str(src),PHASE28_HOST_BUILD=str(work/'research/host-phase28'))
    commands=[]
    def run(label,argv,cwd=None):
        with (artifact/(label+'.log')).open('w') as log:
            r=subprocess.run([str(x) for x in argv],cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
        commands.append({'label':label,'argv':[str(x) for x in argv],'exitCode':r.returncode}); (artifact/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        if r.returncode: raise RuntimeError(label+' failed')
    tests_passed=False
    try:
        (artifact/'provenance-before.json').write_text(json.dumps(before,indent=2)+'\n')
        tools=[]
        for tool in ['clang','make','git']:
            path=Path(shutil.which(tool)).resolve(); tools.append({'name':tool,'path':str(path),'sha256':sha(path)}); run('tool-'+tool,[tool,'--version'])
        tools.append({'name':'python','path':str(Path(sys.executable).resolve()),'version':sys.version}); (artifact/'host-tools.json').write_text(json.dumps(tools,indent=2)+'\n')
        upstream=json.loads((here/'source/ffmpeg-upstream.json').read_text()); archive=out/'ffmpeg-base.tar.gz'
        if a.archive: shutil.copyfile(a.archive,archive)
        else:
            with urllib.request.urlopen(upstream['url'],timeout=180) as r, archive.open('wb') as f: shutil.copyfileobj(r,f)
        if archive.stat().st_size!=upstream['size'] or sha(archive)!=upstream['sha256']: raise ValueError('archive pin mismatch')
        with tarfile.open(archive) as tar:
            names=set()
            for m in tar:
                p=PurePosixPath(m.name)
                if p.is_absolute() or '..' in p.parts or not (m.isfile() or m.isdir()): raise ValueError('unsafe archive member')
                if len(p.parts)<2: continue
                rel=PurePosixPath(*p.parts[1:]); target=src/str(rel)
                if str(rel) in names: raise ValueError('duplicate archive member')
                names.add(str(rel))
                if m.isdir(): target.mkdir(parents=True,exist_ok=True); continue
                target.parent.mkdir(parents=True,exist_ok=True)
                with tar.extractfile(m) as rf, target.open('wb') as wf: shutil.copyfileobj(rf,wf)
                target.chmod(0o755 if m.mode&0o111 else 0o644)
        run('apply-phase27',['git','apply','--no-index',here/'source/ffmpeg.patch'],cwd=src)
        run('apply-phase28',['git','apply','--no-index',here/'source/phase28.patch'],cwd=src)
        pins=json.loads((here/'source/ffmpeg-index.json').read_text()); exact_source(src,pins)
        (artifact/'ffmpeg-source-check.json').write_text(json.dumps({'files':len(pins),'exactSetAndBytes':True,'phase27PatchSHA256':sha(here/'source/ffmpeg.patch'),'phase28PatchSHA256':sha(here/'source/phase28.patch'),'archiveSHA256':sha(archive)},indent=2)+'\n')
        shutil.copytree(here/'source/tests/lifecycle',work/'tests/lifecycle')
        shutil.copytree(here/'source/tests/regression',work/'tests/regression')
        shutil.copytree(here/'source/input-package/sources/mpv',work/'input-package/sources/mpv')
        lc=work/'tests/lifecycle'
        run('t005-red',[sys.executable,'-B',lc/'run_mpv.py','--source','baseline','--out',out/'t005-red'])
        run('t005-green',[sys.executable,'-B',lc/'run_mpv.py','--source','phase28','--out',out/'t005-green'])
        run('t008-red',[sys.executable,'-B',lc/'run_ohdec.py','--source','baseline','--out',out/'t008-red'])
        run('t008-green',[sys.executable,'-B',lc/'run_ohdec.py','--source','phase28','--out',out/'t008-green'])
        run('t011-watchdog',[sys.executable,'-B',lc/'run_watchdog.py','--out',out/'t011-watchdog'])
        host=work/'research/host-phase28'
        run('host-build',[sys.executable,'-B',here/'source/host/build_host.py','--source',src,'--out',host])
        run('t013-regression',[sys.executable,'-B',work/'tests/regression/ffmpeg/run.py',out/'t013-regression'])
        exact_source(src,pins); verify(here); tests_passed=True
    finally:
        # Collect only logs/JSON from the known test roots; never copy binaries/inc.
        for root in [out/'t005-red',out/'t005-green',out/'t008-red',out/'t008-green',out/'t011-watchdog',out/'t013-regression']:
            if not root.exists(): continue
            for p in sorted(root.rglob('*')):
                if p.is_file() and p.suffix in {'.log','.json'} and p.stat().st_size<=8*1024*1024:
                    q=artifact/'results'/p.relative_to(out); q.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,q)
        for row in rows:
            q=artifact/'execution/tools/phase28'/row['path']; q.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(here/row['path'],q)
        shutil.copyfile(here/'source-index.json',artifact/'source-index.json')
        q=artifact/'execution/.github/workflows/phase28-validation.yml'; q.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(workflow,q)
        after={'head':git('rev-parse','HEAD'),'dirty':git('status','--porcelain','--untracked-files=all'),'sourceIndexSHA256':sha(here/'source-index.json'),'workflowSHA256':sha(workflow)}
        (artifact/'provenance-after.json').write_text(json.dumps(after,indent=2)+'\n')
        verify(here); stable=before==after
        (artifact/'result.json').write_text(json.dumps({'testsPassed':tests_passed,'collectionPassed':True,'inputsStable':stable,'passed':tests_passed and stable,'targetExecuted':False,'deviceAcceptance':'separate','realUpstreamObjects':True},indent=2)+'\n')
        artifact_audit(artifact); (artifact/'artifact-index.json').write_text(json.dumps(artifact_audit(artifact),indent=2)+'\n')
        if not stable: raise ValueError('inputs or git state changed')
if __name__=='__main__': main()

"""只执行宿主合同；实际设备与 HDR 验收保持独立。"""
import argparse, hashlib, json, os, platform, shutil, subprocess, sys
from pathlib import Path, PurePosixPath
BASE = Path(__file__).resolve().parent

def verify_sources(base):
    records = json.loads((base/'sources.json').read_text())['files']
    if not records: raise ValueError('empty source manifest')
    seen=set()
    for row in records:
        rel=PurePosixPath(row['path'])
        if rel.is_absolute() or '..' in rel.parts or not rel.parts or rel.parts[0]!='phase25' or str(rel) in seen:
            raise ValueError('invalid source path')
        seen.add(str(rel))
        if any(p in ('private','keys','credentials.json','nas.bin','__pycache__') for p in rel.parts) or rel.suffix not in ('.py','.h','.cpp','.inc','.ets','.ts'):
            raise ValueError('source not allowed')
        p=base/rel
        if any((base/Path(*rel.parts[:i])).is_symlink() for i in range(1,len(rel.parts)+1)) or not p.is_file():
            raise ValueError('source missing or symlink: '+str(rel))
        b=p.read_bytes()
        if len(b)!=row['size'] or hashlib.sha256(b).hexdigest()!=row['sha256']:
            raise ValueError('source drift: '+str(rel))
    return records

def run_step(name, argv, out, record, env=None):
    with (out/(name+'.log')).open('w') as f:
        try: rc=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,env=env).returncode
        except OSError as e: f.write(str(e));rc=127
    record['commands'].append({'name':name,'argv':argv,'returncode':rc,'log':name+'.log'})
    return rc

def collect(base,out,dest):
    if not (out/'record.json').is_file(): raise ValueError('missing run record')
    records=verify_sources(base)
    record=json.loads((out/'record.json').read_text())
    dest.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(out/'record.json',dest/'record.json')
    shutil.copyfile(base/'sources.json',dest/'sources.json')
    for row in records:
        target=dest/'source'/row['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/row['path'],target)
    allowed={'versions','runner-tests','phase25-python','native-build','native-test','getter-build','getter-test'}
    for step in record['commands']:
        if step['name'] not in allowed or step['log']!=step['name']+'.log': raise ValueError('unexpected log')
        src=out/step['log']
        if not src.is_file() or src.is_symlink(): raise ValueError('missing log')
        shutil.copyfile(src,dest/step['log'])
    for row in record.get('executionSources',[]):
        rel=PurePosixPath(row['path']);source=base.parents[1]/rel
        if rel.is_absolute() or '..' in rel.parts or source.is_symlink():raise ValueError('invalid execution input')
        data=source.read_bytes()
        if hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('execution input drift')
        target=dest/'execution'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    index=[{'path':str(p.relative_to(dest)),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(dest.rglob('*')) if p.is_file()]
    (dest/'index.json').write_text(json.dumps(index,indent=2)+'\n')

def execution_sources(base):
    repo=base.parents[1]
    paths=['tools/phase26/runner.py','tools/phase26/tests/test_runner.py','tools/phase26/tests/test_getter.cpp','tools/phase26/README.md','tools/phase26/sources.json','.github/workflows/phase26-validation.yml','specs/001-ffmpeg-ohcodec-producer/phase26/spec.md','specs/001-ffmpeg-ohcodec-producer/phase26/plan.md','specs/001-ffmpeg-ohcodec-producer/phase26/contracts/validation.md']
    rows=[]
    for rel in paths:
        p=repo/rel
        if not p.is_file() or p.is_symlink(): raise ValueError('execution source missing: '+rel)
        data=p.read_bytes();sha=hashlib.sha256(data).hexdigest()
        result=subprocess.run(['git','show','HEAD:'+rel],cwd=repo,capture_output=True)
        head_sha=hashlib.sha256(result.stdout).hexdigest() if result.returncode==0 else None
        rows.append({'path':rel,'size':len(data),'sha256':sha,'headSHA256':head_sha,'matchesHEAD':sha==head_sha})
    return rows

def write_index(dest):
    rows=[{'path':str(p.relative_to(dest)),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(dest.rglob('*')) if p.is_file() and p.name!='index.json']
    (dest/'index.json').write_text(json.dumps(rows,indent=2)+'\n')

def finalize(base,out,record,rc):
    record['collectionComplete']=False
    (out/'record.json').write_text(json.dumps(record,indent=2)+'\n')
    try:
        collect(base,out,out/'artifact')
        record['collectionComplete']=True
    except Exception as e:
        record['collectionError']=str(e);record['status']='failed';rc=rc or 1
        (out/'collection-error.txt').write_text(str(e))
    (out/'record.json').write_text(json.dumps(record,indent=2)+'\n')
    if record['collectionComplete']:
        shutil.copyfile(out/'record.json',out/'artifact/record.json');write_index(out/'artifact')
    return rc

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    record={'schema':1,'status':'failed','platform':platform.platform(),'python':sys.version,'commands':[],'targetExecutedByCI':False,'HDRComplete':False,'formalArtifactAllowed':False,'phase25PythonTests':16,'sourceFiles':[],'testsPassed':False,'collectionComplete':False,'github':{k:os.environ.get(k) for k in ('GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','GITHUB_SHA','GITHUB_JOB')}}
    rc=1
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',ASAN_OPTIONS='halt_on_error=1:detect_leaks='+('1' if sys.platform.startswith('linux') else '0'),UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    record['sanitizerEnvironment']={k:env[k] for k in ('ASAN_OPTIONS','UBSAN_OPTIONS')}
    try:
        record['commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=BASE,text=True).strip()
        record['sourceFiles']=verify_sources(BASE)
        record['executionSources']=execution_sources(BASE)
        record['workingTreeStatus']=subprocess.check_output(['git','-c','core.fsmonitor=false','status','--porcelain','--untracked-files=all'],cwd=BASE,text=True).splitlines()
        record['executionInputsMatchHEAD']=all(r['matchesHEAD'] for r in record['executionSources'])
        if os.environ.get('GITHUB_ACTIONS')=='true' and (record['workingTreeStatus'] or not record['executionInputsMatchHEAD'] or record['commit']!=os.environ.get('GITHUB_SHA')):raise ValueError('CI checkout binding mismatch')
        cpp=BASE/'phase25/app/entry/src/main/cpp';cxx=shutil.which('clang++')
        if not cxx: raise ValueError('clang++ missing')
        flags=[cxx,'-std=c++17','-pthread','-Wall','-Wextra','-g','-O1','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(cpp),'-I'+str(cpp/'include')]
        for name in ('native-output','getter-output'):(out/name).mkdir()
        steps=[('versions',[cxx,'--version']),('runner-tests',[sys.executable,'-B','-m','unittest','discover','-s',str(BASE/'tests'),'-v']),('phase25-python',[sys.executable,'-B','-m','unittest','discover','-s',str(BASE/'phase25/tests'),'-v']),('native-build',flags+[str(BASE/'phase25/tests/test_timeline.cpp'),'-o',str(out/'test_timeline')]),('native-test',[str(out/'test_timeline'),str(out/'native-output')]),('getter-build',flags+[str(BASE/'tests/test_getter.cpp'),str(cpp/'sampling.cpp'),'-o',str(out/'test_getter')]),('getter-test',[str(out/'test_getter'),str(out/'getter-output')])]
        for name,argv in steps:
            rc=run_step(name,argv,out,record,env)
            if rc:break
        if rc==0:record['status']='passed';record['testsPassed']=True
    except Exception as e:record['error']=str(e);rc=1
    finally:
        rc=finalize(BASE,out,record,rc)
    print(json.dumps({'status':record['status'],'returncode':rc,'output':str(out)}));return rc
if __name__=='__main__':sys.exit(main())

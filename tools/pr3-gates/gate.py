#!/usr/bin/env python3
"""PR3 宿主门禁；不构建目标库、不连接设备。"""
import argparse,hashlib,json,os,re,signal,subprocess,sys,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CASES=('21','22','23','24','26','27','28','parent','29','30','31')
DIRS={'parent':'phase28-parent-chain','29':'phase29-normal-terminal','30':'phase30-consumer-handoff','31':'phase31-normal-validation'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def execute(argv,cwd,timeout):
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
 try:
  p=subprocess.Popen(argv,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True)
  try:text=p.communicate(timeout=timeout)[0];rc=p.returncode
  except subprocess.TimeoutExpired:
   os.killpg(p.pid,signal.SIGKILL);text=p.communicate()[0];rc=124
 except OSError as e:text=str(e);rc=127
 return {'command':argv,'returncode':rc,'passed':rc==0,'output':text}
def unittest_ok(text):return bool(re.search(r'^Ran [1-9][0-9]* tests? in ',text,re.M) and re.search(r'^OK$',text,re.M))
def verify_artifact(root):
 index=next((root/n for n in ('artifact-index.json','index.json') if (root/n).is_file()),None)
 if not index:raise ValueError('missing artifact index')
 data=json.loads(index.read_text());rows=data if isinstance(data,list) else data.get('files',[])
 if not rows:raise ValueError('empty artifact index')
 names=set()
 for row in rows:
  p=root/row['path']
  if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()) or row['path'] in names:raise ValueError('invalid artifact path')
  names.add(row['path'])
  if not p.is_file() or p.stat().st_size!=row['size'] or sha(p)!=row['sha256']:raise ValueError('artifact mismatch')
 actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p!=index}
 if actual!=names:raise ValueError('artifact set mismatch')
 return sha(index)
def aggregate(rows):return len(rows)==len(CASES) and {r['case'] for r in rows}==set(CASES) and all(r.get('accepted') is True for r in rows)
def git(*args):return subprocess.check_output(['git','--no-optional-locks','-c','core.fsmonitor=false',*args],cwd=ROOT,text=True).strip()
def identity():
 d={'checkout':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'parents':git('show','-s','--format=%P','HEAD'),'status':git('status','--porcelain','--untracked-files=all'),'event':os.environ.get('GITHUB_EVENT_NAME','local')}
 if d['status']:raise ValueError('dirty checkout')
 if os.environ.get('GITHUB_ACTIONS')=='true':
  if d['checkout']!=os.environ.get('GITHUB_SHA'):raise ValueError('checkout/GITHUB_SHA mismatch')
  if d['event']=='pull_request':
   event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text());pr=event['pull_request'];d.update(prHead=pr['head']['sha'],prBase=pr['base']['sha'],prNumber=event['number'])
   if d['parents'].split()!=[d['prBase'],d['prHead']]:raise ValueError('PR merge parents mismatch')
 return d
def run(case,out):
 out.mkdir(parents=True,exist_ok=False);result={'case':case,'accepted':False,'formalArtifactAllowed':False,'deviceExecuted':False,'targetLibrariesBuilt':False};commands=[]
 try:
  result['identity']=identity();py=sys.executable
  if case in ('21','22','23','24'):
   dirs=[f'tools/phase{case}/tests']+(['tools/phase23/diagnostic/tests'] if case=='23' else [])
   for n,d in enumerate(dirs):
    if not (ROOT/d).is_dir():raise ValueError('missing tests')
    r=execute([py,'-B','-m','unittest','discover','-s',d,'-v'],ROOT,1200);commands.append({k:v for k,v in r.items() if k!='output'});(out/f'command-{n}.log').write_text(r['output'])
    if not r['passed'] or not unittest_ok(r['output']):raise ValueError('test execution rejected')
  else:
   directory=DIRS.get(case,'phase'+case);runner=ROOT/'tools'/directory/'runner.py'
   if not runner.is_file():raise ValueError('missing runner')
   r=execute([py,'-B',str(runner),'--output' if case=='26' else '--out',str(out/'child')],ROOT,2400);commands.append({k:v for k,v in r.items() if k!='output'});(out/'runner.log').write_text(r['output'])
   if not r['passed']:raise ValueError('runner failed')
   result['artifactIndexSHA256']=verify_artifact(out/'child/artifact')
  if identity()!=result['identity']:raise ValueError('checkout changed')
  result['accepted']=True
 except Exception as e:result['error']=str(e);(out/'failure.log').write_text(traceback.format_exc())
 result['commands']=commands;write(out/'result.json',result)
 # 上传仅受控文本，不包含编译目录、下载源码或目标产物。
 artifact=out/'artifact';artifact.mkdir()
 for p in out.glob('*.json'): (artifact/p.name).write_bytes(p.read_bytes())
 for p in out.glob('*.log'): (artifact/p.name).write_bytes(p.read_bytes())
 child=out/'child/artifact'
 if child.exists():
  for p in child.rglob('*'):
   if p.is_file() and not p.is_symlink() and p.suffix in ('.json','.log','.txt'):
    q=artifact/'child'/p.relative_to(child);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
 write(artifact/'artifact-index.json',{'files':[{'path':str(p.relative_to(artifact)),'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(artifact.rglob('*')) if p.is_file()]})
 return result['accepted']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--case',choices=CASES);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--aggregate',type=Path);a=ap.parse_args()
 if a.aggregate:
  rows=[json.loads(p.read_text()) for p in a.aggregate.glob('*/result.json')];ok=aggregate(rows);write(a.out,{'accepted':ok,'cases':rows,'formalArtifactAllowed':False});return 0 if ok else 1
 if not a.case:ap.error('--case required')
 if a.out.resolve().is_relative_to(ROOT):ap.error('output must be outside checkout')
 return 0 if run(a.case,a.out.resolve()) else 1
if __name__=='__main__':sys.exit(main())

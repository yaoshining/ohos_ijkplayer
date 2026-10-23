#!/usr/bin/env python3
"""正常操作控制、真实 ArkTS 方法与离线门禁宿主 CI；不执行目标构建、NAS连接或设备操作。"""
import argparse,hashlib,json,os,platform,shutil,subprocess,sys,traceback,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
def output_text(x):return x.decode(errors='replace') if isinstance(x,bytes) else (x or '')
def identity(repo,out,allow_dirty):
 if out.resolve().is_relative_to(repo.resolve()):raise ValueError('output must be outside checkout')
 def git(*a):return subprocess.check_output(['git','--no-optional-locks','-c','core.fsmonitor=false','-C',str(repo),*a],text=True).strip()
 status=git('status','--porcelain=v1','--untracked-files=all')
 if status and not allow_dirty:raise ValueError('dirty checkout rejected for exact replay')
 return {'head':git('rev-parse','HEAD'),'status':status,'clean':not bool(status),'exactCommitReplay':not bool(status) and not allow_dirty}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def verify_inputs(root):
 idx=json.loads((root/'source-index.json').read_text());expected={r['path'] for r in idx['files']}
 actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='source-index.json'}
 if expected!=actual:raise ValueError('input path set mismatch')
 for row in idx['files']:
  p=root/row['path']
  if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()) or p.stat().st_size!=row['size'] or sha(p)!=row['sha256']:raise ValueError('input digest mismatch: '+row['path'])
 for row in idx.get('externalFiles',[]):
  p=root.parents[1]/row['path']
  if p.is_symlink() or sha(p)!=row['sha256']:raise ValueError('external input digest mismatch')
 return idx

def accepted_result(d,n):return d.get('accepted') is True and len(d.get('cases',[]))==n and all(x.get('passed',x.get('expected')) is True for x in d['cases'])
def export_evidence(src,out):
 out.mkdir(parents=True,exist_ok=True)
 total=0
 for p in sorted(src.rglob('*')):
  if not p.is_file() or p.is_symlink() or p.suffix not in ('.log','.json'):continue
  raw=p.read_bytes()
  if b'\x00' in raw:raise ValueError('binary data in required evidence: '+str(p))
  total+=len(raw)
  if len(raw)>16*1024*1024 or total>128*1024*1024:raise ValueError('evidence size limit exceeded')
  try:raw.decode('utf-8')
  except UnicodeDecodeError:raise ValueError('non-UTF8 evidence: '+str(p))
  q=out/p.relative_to(src);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw)
def finalize(work,artifact,result,cmds):
 passed=result.get('accepted') is True
 result.update(validationPassed=passed,accepted=False,collectionPassed=False)
 write(work/'commands.json',cmds);write(work/'result.json',result)
 try:
  export_evidence(work,artifact)
  result.update(accepted=passed,collectionPassed=True)
  write(work/'result.json',result);write(artifact/'result.json',result)
  write(artifact/'artifact-index.json',{'formalArtifactAllowed':False,'files':[{'path':str(p.relative_to(artifact)),'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(artifact.rglob('*')) if p.is_file()]})
 except Exception as e:
  result.update(accepted=False,collectionPassed=False,collectionError=str(e))
  write(work/'result.json',result);write(artifact/'result.json',result)
  (artifact/'collection-failure.log').write_text(traceback.format_exc())
  (artifact/'artifact-index.json').unlink(missing_ok=True)
def unittest_passed(exit_code,text,expected):
 return exit_code==0 and re.search(r'^Ran '+str(expected)+r' tests in ',text,re.M) is not None and re.search(r'^OK$',text,re.M) is not None and 'FAILED (' not in text

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);ap.add_argument('--allow-dirty',action='store_true');a=ap.parse_args();out=a.out.resolve()
 if out.is_relative_to(REPO.resolve()) or out.exists():raise SystemExit('fresh output outside checkout required')
 work=out/'work';work.mkdir(parents=True);artifact=out/'artifact';commands=[]
 result={'accepted':False,'formalArtifactAllowed':False,'deviceExecuted':False,'targetLibrariesBuilt':False,'host':platform.platform(),'steps':[]}
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1');env.pop('PHASE31_RAW_EVIDENCE',None)
 def run(name,cmd,timeout=300):
  try:p=subprocess.run(cmd,capture_output=True,text=True,cwd=REPO,env=env,timeout=timeout);rc=p.returncode;txt=p.stdout+p.stderr
  except subprocess.TimeoutExpired as e:rc=124;txt='TIMEOUT\n'+output_text(e.stdout)+output_text(e.stderr)
  (work/(name+'.log')).write_text(txt);commands.append({'name':name,'command':cmd,'exitCode':rc})
  if rc!=0:raise RuntimeError(name+' failed: '+str(rc))
  result['steps'].append({'name':name,'accepted':True})
 try:
  result['identityBefore']=identity(REPO,out,a.allow_dirty);idx=verify_inputs(HERE);write(work/'source-index.json',idx)
  result['inputIndexSHA256']=sha(HERE/'source-index.json');result['workflowSHA256']=sha(REPO/'.github/workflows/phase31-normal-validation.yml')
  run('ci-gate',[sys.executable,'-B',str(HERE/'test_ci_gate.py')]);run('host-clang',['clang++','--version']);run('host-python',[sys.executable,'--version'])
  run('current-binding-tests',[sys.executable,'-B',str(HERE/'test_current_binding.py')])
  if not unittest_passed(0,(work/'current-binding-tests.log').read_text(),8):raise RuntimeError('current binding test count/result invalid')
  run('current-binding',[sys.executable,'-B',str(HERE/'verify_current_binding.py')])
  if json.loads((work/'current-binding.log').read_text()).get('accepted') is not True:raise RuntimeError('current binding rejected')
  run('actions',[sys.executable,'-B',str(HERE/'tests/run_actions.py'),'--out',str(work/'actions')]);ar=json.loads((work/'actions/results.json').read_text())
  if ar.get('accepted') is not True or ar.get('cases')!=13:raise RuntimeError('actual C++ actions result invalid')
  run('offline-gates',[sys.executable,'-B','-m','unittest','discover','-s',str(HERE/'tests'),'-p','test_*.py'])
  if not unittest_passed(0,(work/'offline-gates.log').read_text(),46):raise RuntimeError('offline test count/result invalid')
  ui=out/'ui-runtime';shutil.copytree(HERE/'ui-runtime',ui)
  run('typescript-install',['npm','ci','--ignore-scripts','--no-audit','--no-fund','--prefix',str(ui)])
  ts=ui/'node_modules/typescript/lib/typescript.js';write(work/'typescript-identity.json',{'version':json.loads((ui/'node_modules/typescript/package.json').read_text())['version'],'sha256':sha(ts),'lockSHA256':sha(HERE/'ui-runtime/package-lock.json')})
  for name,n,script,inputs in [('entry-mode',7,'entry_mode_test.js',['entryability/EntryAbility.ets','pages/Index.ets']),('close-order',4,'close_order_test.js',['pages/Index.ets'])]:
   run(name,['node',str(HERE/'tests'/script),str(ts),*[str(HERE/'app/entry/src/main/ets'/p) for p in inputs]])
   if not accepted_result(json.loads((work/(name+'.log')).read_text()),n):raise RuntimeError(name+' semantic gate failed')
  result['identityAfter']=identity(REPO,out,a.allow_dirty)
  if result['identityAfter']!=result['identityBefore']:raise RuntimeError('checkout changed during replay')
  result['accepted']=True
 except Exception as e:
  result['error']=str(e);(work/'failure.log').write_text(traceback.format_exc())
 finally:finalize(work,artifact,result,commands)
 print(json.dumps(result,ensure_ascii=False));raise SystemExit(0 if result['accepted'] else 1)
if __name__=='__main__':main()

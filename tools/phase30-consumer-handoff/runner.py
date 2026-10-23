#!/usr/bin/env python3
"""同 consumer 交接观测、真实同步函数与解析门禁独立宿主 CI，不执行目标构建或设备操作。"""
import argparse,hashlib,json,os,platform,shutil,subprocess,sys,traceback
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
def mutant_rejected(rc,d):
 case=next((c for c in d.get('cases',[]) if c.get('case')=='callback-inflight-close'),{})
 return rc==1 and d.get('compileExit')==0 and d.get('accepted') is False and case.get('exitCode')==1 and case.get('expected') is False and 'FAIL callback-inflight-close: Close did not wait for callback completion' in case.get('stdout','')
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
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);ap.add_argument('--allow-dirty',action='store_true');a=ap.parse_args()
 out=a.out.resolve()
 if out.resolve().is_relative_to(REPO.resolve()):raise SystemExit('output must be outside checkout')
 if out.exists():raise SystemExit('refusing existing output')
 work=out/'work';work.mkdir(parents=True);artifact=out/'artifact'
 cmds=[];result={'accepted':False,'formalArtifactAllowed':False,'deviceExecuted':False,'targetLibrariesBuilt':False,'host':platform.platform(),'steps':[]}
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',PHASE28_BINDING_ROOT=str(HERE),PHASE28_FFMPEG_ROOT=str(HERE/'ffmpeg-input/source'))
 def run(name,cmd,ok=(0,),timeout=300):
  try:
   p=subprocess.run(cmd,capture_output=True,text=True,env=env,cwd=REPO,timeout=timeout)
   rc=p.returncode;text=p.stdout+p.stderr
  except subprocess.TimeoutExpired as e:
   rc=124;text='TIMEOUT\n'+output_text(e.stdout)+output_text(e.stderr)
  (work/(name+'.log')).write_text(text);cmds.append({'name':name,'command':cmd,'exitCode':rc})
  if rc not in ok:raise RuntimeError(name+' failed: '+str(rc))
  return rc
 def check(name,path,n):
  d=json.loads(path.read_text())
  if not accepted_result(d,n):raise RuntimeError(name+' result gate failed')
  result['steps'].append({'name':name,'accepted':True,'cases':n})
 try:
  result['identityBefore']=identity(REPO,out,a.allow_dirty)
  result['workflowSHA256']=sha(REPO/'.github/workflows/phase30-consumer-handoff.yml')
  result['inputIndexSHA256']=sha(HERE/'source-index.json')
  idx=verify_inputs(HERE);write(work/'source-index.json',idx)
  run('git-head',['git','rev-parse','HEAD']);run('host-clang',['clang','--version']);run('host-python',[sys.executable,'--version'])
  run('ci-gate',[sys.executable,'-B',str(HERE/'test_ci_gate.py')])
  ui=out/'ui-runtime';shutil.copytree(HERE/'ui-runtime',ui)
  run('typescript-install',['npm','ci','--ignore-scripts','--no-audit','--no-fund','--prefix',str(ui)])
  ts=ui/'node_modules/typescript/lib/typescript.js';write(work/'typescript-identity.json',{'version':json.loads((ui/'node_modules/typescript/package.json').read_text())['version'],'sha256':sha(ts),'lockSHA256':sha(HERE/'ui-runtime/package-lock.json')})
  for name,n in [('analyze_a',16),('analyze_b',16),('relocation',8)]:
   run(name,[sys.executable,'-B',str(HERE/'tests/handoff'/('test_'+name+'.py')),str(work/name)])
   check(name,work/name/'results.json',n)
  run('completion',[sys.executable,'-B',str(HERE/'tests/handoff/test_completion.py')])
  check('completion',work/'completion.log',5)
  run('entry-mode',['node',str(HERE/'tests/handoff/entry_mode_test.js'),str(ts),str(HERE/'application/entry/src/main/ets/entryability/EntryAbility.ets'),str(HERE/'application/entry/src/main/ets/pages/Index.ets')])
  check('entry-mode',work/'entry-mode.log',2)
  run('dispatch',[sys.executable,'-B',str(HERE/'tests/handoff/test_dispatch.py'),str(work/'dispatch')])
  if json.loads((work/'dispatch/results.json').read_text()).get('accepted') is not True:raise RuntimeError('actual dispatch gate failed')
  result['steps'].append({'name':'actual-dispatch-two-waits-and-fast-path','accepted':True})
  hook=out/'hook'
  run('hook-compile',['clang','-std=c11','-D_GNU_SOURCE','-pthread','-I'+str(HERE/'ffmpeg-test-input/source/libavcodec'),str(HERE/'tests/handoff/test_hook.c'),'-o',str(hook)])
  run('hook',[str(hook)],timeout=10)
  if 'PASS' not in (work/'hook.log').read_text():raise RuntimeError('hook gate missing PASS')
  result['steps'].append({'name':'hook-state-identity-and-terminal-preservation','accepted':True})
  run('ffmpeg-normal',[sys.executable,'-B',str(HERE/'tests/lifecycle/run_ohdec.py'),'--source','phase28','--out',str(work/'ffmpeg-normal')])
  check('ffmpeg-normal',work/'ffmpeg-normal/results.json',8)
  mutant=out/'mutant-source';shutil.copytree(HERE/'ffmpeg-input/source',mutant)
  p=mutant/'libavcodec/ohdec.c';old=p.read_text()
  block='            while (ref->active > 0) {\n                p30_codec_trace(avctx, ref, "close-active-wait", ref->active);\n                ff_cond_wait(&ref->gate_cond, &ref->gate);\n            }\n'
  if old.count(block)!=1:raise RuntimeError('Close active wait mutation anchor mismatch')
  p.write_text(old.replace(block,'',1));write(work/'mutation.json',{'file':'libavcodec/ohdec.c','beforeSHA256':hashlib.sha256(old.encode()).hexdigest(),'afterSHA256':sha(p),'rule':'remove actual Close active wait, test only'})
  env['PHASE28_FFMPEG_ROOT']=str(mutant)
  rc=run('no-active-wait-mutant',[sys.executable,'-B',str(HERE/'tests/lifecycle/run_ohdec.py'),'--source','phase28','--out',str(work/'no-active-wait-mutant')],ok=(0,1))
  d=json.loads((work/'no-active-wait-mutant/results.json').read_text())
  if not mutant_rejected(rc,d):raise RuntimeError('actual Close wait mutant was not semantically rejected')
  result['steps'].append({'name':'actual-close-wait-mutant-rejected','accepted':True})
  verify_inputs(HERE)
  result['identityAfter']=identity(REPO,out,a.allow_dirty)
  if result['identityBefore']!=result['identityAfter']:raise RuntimeError('checkout identity changed during replay')
  if sha(REPO/'.github/workflows/phase30-consumer-handoff.yml')!=result['workflowSHA256'] or sha(HERE/'source-index.json')!=result['inputIndexSHA256']:raise RuntimeError('workflow/index changed during replay')
  result['exactCommitReplay']=result['identityBefore']['exactCommitReplay']
  result['accepted']=True
 except Exception as e:
  result['error']=str(e);(work/'failure.log').write_text(traceback.format_exc())
 finally:
  finalize(work,artifact,result,cmds)
 print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['accepted'] else 1
if __name__=='__main__':sys.exit(main())

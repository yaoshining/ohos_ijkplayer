#!/usr/bin/env python3
"""公共终局接口与应用适配器独立宿主 CI，不执行目标构建或设备操作。"""
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
 late=next((c for c in d.get('cases',[]) if c.get('case')=='late-unsafe'),{})
 return rc!=0 and d.get('accepted') is False and late.get('passed') is False and 'EVENT destroy-queue' in late.get('forbiddenEvents',[])
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
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',PHASE28_BINDING_ROOT=str(HERE),PHASE28_FFMPEG_ROOT=str(HERE/'sources/ffmpeg'))
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
  result['workflowSHA256']=sha(REPO/'.github/workflows/phase29-normal-terminal.yml')
  result['inputIndexSHA256']=sha(HERE/'source-index.json')
  idx=verify_inputs(HERE);write(work/'source-index.json',idx)
  run('git-head',['git','rev-parse','HEAD']);run('host-clang',['clang','--version']);run('host-python',[sys.executable,'--version'])
  run('ci-gate',[sys.executable,'-B',str(HERE/'test_ci_gate.py')])
  ui=out/'ui-runtime';shutil.copytree(HERE/'ui-runtime',ui)
  run('typescript-install',['npm','ci','--ignore-scripts','--no-audit','--no-fund','--prefix',str(ui)])
  ts=ui/'node_modules/typescript/lib/typescript.js';write(work/'typescript-identity.json',{'version':json.loads((ui/'node_modules/typescript/package.json').read_text())['version'],'sha256':sha(ts),'lockSHA256':sha(HERE/'ui-runtime/package-lock.json')})
  for name,source in [('keep_awake','lifecycle/Timeline.ets'),('ui_fault','pages/Index.ets')]:
   run(name,['node',str(HERE/'tests'/(name+'_test.js')),str(ts),str(HERE/'application/entry/src/main/ets'/source)])
   if json.loads((work/(name+'.log')).read_text()).get('passed') is not True:raise RuntimeError(name+' actual method gate failed')
   result['steps'].append({'name':name,'accepted':True})
  for mode,n in [('red',3),('green',5)]:
   run('abi-'+mode,[sys.executable,'-B',str(HERE/'tests/run_abi.py'),'--phase',mode,'--out',str(work/('abi-'+mode))])
   check('abi-'+mode,work/('abi-'+mode)/'results.json',n)
  run('adapter',[sys.executable,'-B',str(HERE/'tests/run_adapter_green.py'),'--out',str(work/'adapter'),'--abi-dir',str(work/'abi-green')])
  check('adapter',work/'adapter/results.json',5)
  run('parent-normal',[sys.executable,'-B',str(HERE/'parent-tests/run_prototype.py'),'--out',str(work/'parent-normal')])
  check('parent-normal',work/'parent-normal/results.json',23)
  mutant=out/'mutant-source';shutil.copytree(HERE/'input-package/sources/mpv',mutant)
  p=mutant/'video/out/vo_gpu_next.c';old=p.read_text();line='    pl_renderer_destroy(&p->rr);\n'
  start=old.index('static void uninit(struct vo *vo)\n{');end=old.index('\n}',start)+2;body=old[start:end]
  if body.count(line)!=1:raise RuntimeError('renderer mutation anchor mismatch')
  changed=body.replace(line,'',1).replace('    struct priv *p = vo->priv;\n','    struct priv *p = vo->priv;\n'+line,1)
  p.write_text(old[:start]+changed+old[end:]);write(work/'mutation.json',{'file':'video/out/vo_gpu_next.c','beforeSHA256':hashlib.sha256(old.encode()).hexdigest(),'afterSHA256':sha(p),'rule':'move real renderer destroy before drain; test only'})
  rc=run('external-renderer-mutant',[sys.executable,'-B',str(HERE/'parent-tests/run_prototype.py'),'--mpv-root',str(mutant),'--out',str(work/'external-renderer-mutant')],ok=(0,1))
  d=json.loads((work/'external-renderer-mutant/results.json').read_text());late=next(c for c in d['cases'] if c['name']=='parent-late-unsafe')
  if rc!=1 or d['accepted'] is not False or late['passed'] is not False or 'EVENT destroy-renderer' not in late['forbiddenEvents']:raise RuntimeError('real full runner failed to reject early renderer destroy')
  result['steps'].append({'name':'external-renderer-mutant-rejected','accepted':True})
  verify_inputs(HERE)
  result['identityAfter']=identity(REPO,out,a.allow_dirty)
  if result['identityBefore']!=result['identityAfter']:raise RuntimeError('checkout identity changed during replay')
  if sha(REPO/'.github/workflows/phase29-normal-terminal.yml')!=result['workflowSHA256'] or sha(HERE/'source-index.json')!=result['inputIndexSHA256']:raise RuntimeError('workflow/index changed during replay')
  result['exactCommitReplay']=result['identityBefore']['exactCommitReplay']
  result['accepted']=True
 except Exception as e:
  result['error']=str(e);(work/'failure.log').write_text(traceback.format_exc())
 finally:
  finalize(work,artifact,result,cmds)
 print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['accepted'] else 1
if __name__=='__main__':sys.exit(main())

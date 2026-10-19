"""Collect exact diagnostic evidence; missing success inputs fail closed."""
from pathlib import Path
import os,json,shutil,stat,argparse
import build
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def need(p):
 if not p.is_file() or p.stat().st_size==0:raise ValueError('required evidence missing/empty: '+str(p))
def validate_success(base,kind):
 if kind=='native':
  from native import CASES
  root=base/'native';status=read(root/'status.json');r=read(root/'results.json')
  if status.get('status')!='passed' or status.get('caseCount')!=len(CASES) or {x['case'] for x in r['cases']}!=set(CASES):raise ValueError('incomplete native test results')
  exe=r['executable'];build.require_sha(exe['path'],exe['sha256'])
  for c in r['cases']:
   if not c.get('pass') or not c.get('freshSambaLibrariesBound'):raise ValueError('native binding missing')
   for path,digest in c['loadedLibraries'].items():build.require_sha(path,digest)
   build.require_sha(root/'cases'/c['case']/'files.trace',c['traceSHA256'])
  for n in ['configure.log','build.log','runtime-patch.json','executable-elf.log']:need(root/n)
 else:
  root=base/'target';status=read(root/'status.json');comp=read(root/'comparison.json');verification=read(root/'verification.json')
  if status.get('status')!='builds_complete' or not comp.get('ffmpegBytesEqual') or not comp.get('smbBytesEqual') or len(verification['runs'])!=2:raise ValueError('target completion missing')
  need(base/'unit-tests.log');need(root/'host-lock.json');need(root/'source-pins.json')
  for run in comp['runs']:
   r=Path(run['root'])
   if set(run['ffmpeg'])!=build.EXPECTED_LIBRARIES:raise ValueError('incomplete six libraries')
   for name,digest in run['ffmpeg'].items():build.require_sha(r/'ffmpeg/prefix/lib'/name,digest);need(r/(name+'.elf.txt'))
   build.require_sha(r/'dependencies/sysroot/lib/libsmbclient.a',run['smb'])
   caller=read(r/'api-caller-link.json');build.require_sha(r/'api-caller.so',caller['callerSHA256'])
   for n in ['build-complete.json','dependency-features.json','samba-defined-symbols.txt','ffmpeg/build/input-bindings.json','ffmpeg/build/config.h','ffmpeg/build/ffbuild/config.mak','ffmpeg/prefix/include/libavformat/ohcodec_smb_runtime.h']:need(r/n)
def select_file(rel):
 if 'inputs' in rel.parts:return False
 name=rel.name
 return (name.endswith(('.log','.json','.trace','.txt')) or name in ['config.h','config.mak','api-caller.so','phase20_runtime_integration','phase20_runtime_integration.c'] or
 ('prefix' in rel.parts and (name.startswith('lib') and '.so.' in name or name=='ohcodec_smb_runtime.h')) or
 ('sysroot' in rel.parts and name.endswith('.a')) or
 ('native' in rel.parts and 'bin' in rel.parts and '.so' in name) or
 (name.startswith('dynconfig.c.') and name.endswith('.o')) or name in ['libsmbclient.o','libsmb_context.c.0.o','libsmb_setget.c.0.o','loadparm.c.0.o','gencache.c.0.o'])
def main():
 p=argparse.ArgumentParser();p.add_argument('--kind',choices=['native','target'],required=True);p.add_argument('--job-status',choices=['success','failure','cancelled'],required=True);a=p.parse_args();base=Path('out/phase20-ci');out=Path('out/phase20-artifact-'+a.kind);out.mkdir(parents=True,exist_ok=False)
 failure=None
 if a.job_status=='success':
  try:validate_success(base,a.kind)
  except Exception as e:failure=str(e)
 selected=[]
 for src in base.rglob('*'):
  if not src.is_file() or src.is_symlink():continue
  rel=src.relative_to(base)
  if '__pycache__' in rel.parts:raise ValueError('Python bytecode contamination: '+str(src))
  if select_file(rel):
   dest=out/'execution'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest);selected.append(str(rel))
 for name in ['sdk-binding.json','overlay/target-sdk.json']:
  src=base/'inputs'/name
  if src.is_file():dest=out/'input-bindings'/Path(name).name;dest.parent.mkdir(exist_ok=True);shutil.copy2(src,dest)
 shutil.copytree(HERE,out/'recipe')
 identity={k:os.getenv(k) for k in ['GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','GITHUB_SHA','GITHUB_REPOSITORY','GITHUB_WORKFLOW_REF']};identity.update(kind=a.kind,formalArtifactAllowed=False,targetExecuted=False,deviceAcceptanceStatus='pending',jobStatus=a.job_status,successEvidenceValidated=a.job_status=='success' and failure is None,collectionFailure=failure)
 build.write(out/'identity.json',identity);build.write(out/'collection.json',{'selectedExecutionFiles':selected,'scope':'diagnostic logs, configs, tests, actual binaries and selected objects; SDK/source archives excluded, identified by pins'})
 entries=[{'path':str(f.relative_to(out)),'size':f.stat().st_size,'mode':stat.S_IMODE(f.stat().st_mode),'sha256':build.sha(f)} for f in sorted(out.rglob('*')) if f.is_file()]
 build.write(out/'evidence-index.json',{'files':entries});print('collected',len(entries),'files')
 if failure:raise ValueError(failure)
if __name__=='__main__':main()

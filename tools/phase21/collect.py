"""只收集本轮必要实物/记录，成功缺项或源码字节码污染即拒绝。"""
from common import *
import argparse,shutil,stat

CASES=['init','repeat','conflict','late','cache-write','cache-denied','render','readonly','missing-directory','empty-fonts','corrupt-font','font-unreadable','cache-unwritable','symlink','no-font','cjk']
def validate_cases(rows):
 if len(rows)!=len(CASES) or {r['case'] for r in rows}!=set(CASES) or not all(r.get('passed') is True for r in rows):raise ValueError('native场景集合缺失、重复或失败')
def validate_libraries(root,expected):
 actual={p.name for p in Path(root).glob('*.so*') if p.is_file()}
 if actual!=set(expected):raise ValueError('target库集合不完整')
 for name,digest in expected.items():require(Path(root)/name,digest)
def select_file(rel,kind):
 return rel.suffix in ['.json','.log','.txt','.trace','.ppm','.ass','.map','.ttf'] or rel.name in ['phase21-probe','config.h','config_components.h','config.mak','smb.conf'] or 'prefix' in rel.parts or (kind=='target' and 'lib' in rel.parts)

def main():
 p=argparse.ArgumentParser();p.add_argument('--kind',choices=['native','target'],required=True);p.add_argument('--job-status',required=True);a=p.parse_args();base=Path('out/phase21-ci');out=Path('out/phase21-artifact-'+a.kind);out.mkdir(parents=True,exist_ok=False);failure=None
 try:
  if a.job_status=='success':
   if a.kind=='native':
    status=json.loads((base/'native/status.json').read_text());results=json.loads((base/'native/results.json').read_text());assert status=={'passed':True,'caseCount':16} ;validate_cases(results['cases'])
    for case in results['cases']:
     assert case['passed'];require(base/'native/cases'/case['case']/'files.trace',case['traceSHA256']);require(base/'native/cases'/case['case']/'result.log',case['logSHA256'])
     for path,digest in case['loadedLibraries'].items():require(path,digest)
   else:
    v=json.loads((base/'target/verification.json').read_text());assert v['crossRootProbeBytesEqual'] and v['inputsUnchanged'] and not v['targetExecuted']
    for r in v['runs']:
     require(r['probe']['path'],r['probe']['sha256'])
     validate_libraries(base/'target'/r['root']/'lib',r['libraries'])
 except Exception as e:failure=repr(e)
 for root in [HERE,base/'native/source']:
  if root.exists() and (list(root.rglob('*.pyc')) or list(root.rglob('__pycache__'))):failure='source Python bytecode contamination: '+str(root)
 def copy(src,rel):
  dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);dest.chmod(stat.S_IMODE(src.stat().st_mode))
 for src in sorted(base.rglob('*')):
  if not src.is_file() or src.is_symlink():continue
  rel=src.relative_to(base)
  if 'inputs' in rel.parts or 'venv' in rel.parts:continue
  if 'source' in rel.parts:continue
  keep=select_file(rel,a.kind)
  if keep:copy(src,Path('execution')/rel)
 # 只复制实际加载的旧Samba实物；系统DSO仅记录宿主观测摘要。
 if (base/'native/results.json').is_file():
  results=json.loads((base/'native/results.json').read_text());loaded={p:h for c in results['cases'] for p,h in c['loadedLibraries'].items() if '/inputs/native/' in p}
  for path,digest in loaded.items():
   src=Path(path);require(src,digest);copy(src,Path('reused-native')/src.relative_to((base/'inputs/native').resolve()))
 for src in (base/'inputs').glob('*-verification.json'):copy(src,Path('input-bindings')/src.name)
 for name in ['source-binding.json','sdk-binding.json','native-source-lock.json']:
  src=base/'inputs'/name
  if src.is_file():copy(src,Path('input-bindings')/name)
 shutil.copytree(HERE,out/'recipe')
 write(out/'identity.json',{'kind':a.kind,'jobStatus':a.job_status,'successEvidenceValidated':a.job_status=='success' and failure is None,'collectionFailure':failure,'commit':os.getenv('GITHUB_SHA'),'runId':os.getenv('GITHUB_RUN_ID'),'formalArtifactAllowed':False,'targetExecuted':False,'deviceAcceptanceStatus':'pending'})
 write(out/'evidence-index.json',{'files':tree(out)});print('collected',len(tree(out)))
 if failure:raise ValueError(failure)
if __name__=='__main__':main()

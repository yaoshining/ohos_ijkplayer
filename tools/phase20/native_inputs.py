"""Observed native compiler, header and recipe inputs; not a source bootstrap."""
from pathlib import Path
import os,shutil,subprocess,sys
import build

def capture(src):
 paths={};versions={}
 def pin(p,role):
  p=Path(p)
  if p.is_file():paths[str(p.resolve())]={'path':str(p.resolve()),'sha256':build.sha(p),'size':p.stat().st_size,'role':role}
 for name in ['gcc','g++','cc','ld','as','ar','ranlib','make','python3','perl','bison','flex','pkg-config','m4']:
  path=shutil.which(name)
  if not path:raise ValueError('missing native tool '+name)
  pin(path,'observed native tool');versions[name]=subprocess.run([path,'-v' if name=='perl' else '--version'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True).stdout[:3000]
 for name in ['cc1','cc1plus','collect2','libgcc.a','crtbeginS.o']:
  path=subprocess.check_output(['gcc','-print-file-name='+name],text=True).strip();pin(path,'native GCC internal')
 for p in Path('/usr/include').rglob('*'):pin(p,'observed native header')
 for p in Path(__file__).resolve().parent.rglob('*'):pin(p,'published phase20 recipe')
 for p in src.rglob('*.py'):
  if 'bin' not in p.relative_to(src).parts:pin(p,'Samba build Python')
 for n in ['dynconfig/dynconfig.c','source3/libsmb/libsmb_context.c','source3/libsmb/libsmb_setget.c','source3/param/loadparm.c','source3/lib/gencache.c','source3/wscript_build','source3/torture/phase20_runtime_integration.c','source3/libsmb/libsmb_thread_posix.c','lib/util/smb_threads.h','source3/torture/phase20_thread_adapter.c']:pin(src/n,'patched source')
 for p in (src/'dynconfig').glob('smb_*'):pin(p,'runtime implementation')
 return {'files':sorted(paths.values(),key=lambda r:r['path']),'versions':versions,'environment':{k:os.environ.get(k) for k in ['PATH','PYTHONHASHSEED','PYTHONDONTWRITEBYTECODE','PYTHONNOUSERSITE','LC_ALL','TZ']},'scope':'Observed compiler/tools, native headers, Samba build Python and reviewed source/recipe; not every host OS file or reproducible host bootstrap'}
def verify(lock):
 for row in lock['files']:build.require_sha(row['path'],row['sha256'])
 for key,value in lock['environment'].items():
  if os.environ.get(key)!=value:raise ValueError('native environment changed '+key)

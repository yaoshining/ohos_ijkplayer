"""Build and run real Linux Samba in isolated roots. No target runtime claim."""
from pathlib import Path
import argparse,json,os,shutil,subprocess,tarfile,sys,hashlib
import build
HERE=Path(__file__).resolve().parent
CASES=['explicit','append-only','aliases','parse-failure','pending','init-failure','last-free','legacy-null','legacy-auth','cache-write','cache-denied','unconfigured-home','unconfigured-append','unconfigured-reload','callback-reentry','posix-threads']
def run(argv,path,cwd=None,env=None):
 with Path(path).open('w') as f:r=subprocess.run(list(map(str,argv)),cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
 if r.returncode:raise RuntimeError(str(path)+' exit '+str(r.returncode))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--archive',type=Path,required=True);a=ap.parse_args()
 out=a.out.resolve();build.require_fresh(out);assert sys.platform=='linux' and os.geteuid()!=0
 row=next(r for r in json.loads((HERE/'recipe/dependency-sources.lock.json').read_text())['sources'] if r['name']=='samba-4.20.7');build.require_sha(a.archive,row['sha256']);out.mkdir(parents=True)
 with tarfile.open(a.archive) as t:
  for m in t:
   if Path(m.name).is_absolute() or '..' in Path(m.name).parts:raise ValueError('source path escape')
  t.extractall(out,filter='data')
 src=out/row['archivePrefix'].rstrip('/');assert src.is_dir()
 run([sys.executable,'-B',HERE/'apply.py','samba',src,'--evidence',out/'runtime-patch.json'],out/'patch.log')
 shutil.copyfile(HERE/'tests/native_integration.c',src/'source3/torture/phase20_runtime_integration.c')
 with (src/'source3/wscript_build').open('a') as f:f.write("\nbld.SAMBA3_BINARY('phase20_runtime_integration', source='torture/phase20_runtime_integration.c', deps='smbclient smbconf samba3-util samba-util talloc', cflags='-UNDEBUG', install=False)\n")
 options=['--bundled-libraries=ALL','--private-libraries=ALL','--disable-python','--without-ad-dc','--disable-fault-handling','--without-ldb-lmdb','--without-gettext','--without-json','--without-systemd','--without-libarchive','--without-acl-support','--without-ldap','--without-ads','--without-pam','--disable-cups','--disable-avahi','--with-static-modules=ALL,!vfs_snapper','--with-shared-modules=!DEFAULT,!vfs_snapper']
 run(['./configure','--prefix='+str(out/'install'),*options],out/'configure.log',src)
 run([sys.executable,'-B','buildtools/bin/waf','build','--targets=smbclient,phase20_runtime_integration','-j4','-v'],out/'build.log',src)
 exe=src/'bin/phase20_runtime_integration';assert exe.exists()
 run(['readelf','-dWs',exe],out/'executable-elf.log')
 results=[]
 for case in CASES:
  root=out/'cases'/case;root.mkdir(parents=True);home=root/'home';state=root/'state';cache=root/'cache';res=root/'resources'
  for p in [home,home/'.smb',state,state/'private',state/'state',state/'lock',cache,res]:p.mkdir()
  if case not in ['append-only','unconfigured-append']:(home/'.smb/smb.conf').write_text('[global]\nworkgroup = WRONG_HOME\n')
  (home/'.smb/smb.conf.append').write_text('[global]\nworkgroup = WRONG_APPEND\n')
  config=root/'smb.conf';text='[global]\nworkgroup = PHASE20\n'
  if case=='aliases':
   inc=root/'included.conf';inc.write_text('[global]\nLoCk DiR = /must-not-win\nstate directory = /must-not-win\nprivate dir = /must-not-win\ncache directory = /must-not-win\npid directory = /must-not-win\nsmb passwd file = /must-not-win\n');text+='include = '+str(inc)+'\n'
  if case=='parse-failure':text='[unterminated section\n'
  config.write_text(text);env=dict(os.environ,HOME=str(home),USER='phase20',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
  if case.startswith('unconfigured-'):
   global_config=out/'install/etc/smb.conf';global_config.parent.mkdir(parents=True,exist_ok=True);global_config.write_text('[global]\nworkgroup = GLOBAL\n')
  trace=root/'files.trace';run(['strace','-f','-e','trace=%file','-o',trace,exe,case,config,state,cache,res],root/'result.log',src,env)
  log=(root/'result.log').read_text();assert 'PHASE20_PASS '+case in log
  actual=trace.read_text()
  if not case.startswith('unconfigured-'):assert str(home/'.smb/smb.conf') not in actual
  else:assert str(home/'.smb/smb.conf') in actual
  assert not (home/'.cache/samba').exists()
  if case=='cache-write':assert (state/'lock/gencache.tdb').is_file()
  libs={}
  for line in log.splitlines():
   fields=line.split();p=Path(fields[-1]) if fields else Path('.')
   if p.is_absolute() and p.is_file() and '.so' in p.name:libs[str(p)]=build.sha(p)
  for required in ['libsmbclient','libsamba-util']:
   owned=[Path(p) for p in libs if required in Path(p).name];assert owned and all(p.resolve().is_relative_to(src) for p in owned),(required,owned)
  results.append({'case':case,'pass':True,'loadedLibraries':libs,'traceSHA256':build.sha(trace),'freshSambaLibrariesBound':True})
  build.write(out/'results.json',{'cases':results,'actualSamba':True,'targetExecuted':False,'formalArtifactAllowed':False,'executable':{'path':str(exe.resolve()),'sha256':build.sha(exe)},'testSourceSHA256':build.sha(src/'source3/torture/phase20_runtime_integration.c')})
 build.require_sha(a.archive,row['sha256']);build.write(out/'status.json',{'status':'passed','caseCount':len(results),'formalArtifactAllowed':False})
if __name__=='__main__':main()

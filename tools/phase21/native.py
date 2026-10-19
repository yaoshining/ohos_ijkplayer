"""固定源码 Linux 软件管线；不代表 OHOS/GPU/设备执行。"""
from pathlib import Path
import argparse,json,os,shutil,subprocess,tarfile,sys,importlib.util,re,signal
from common import *
from resources import prepare

def build_stack(out,inputs):
 assert sys.platform=='linux' and os.geteuid()!=0
 prefix=out/'prefix';src=out/'source';src.mkdir();sources=inputs/'sources';original=[]
 for n,rel in [('mpv','integration/base/sources/mpv'),('libplacebo','integration/base/sources/libplacebo'),('libass','source-package/source/libass')]:shutil.copytree(sources/rel,src/n)
 with tarfile.open(inputs/'ffmpeg.tar') as t:
  for m in t.getmembers():
   if Path(m.name).is_absolute() or '..' in Path(m.name).parts:raise ValueError('unsafe FFmpeg')
  t.extractall(src/'ffmpeg',filter='data')
 # 已验收的新API patch，只用于本轮新源码。
 run([sys.executable,'-B',HERE.parent/'phase20/apply.py','ffmpeg',src/'ffmpeg','--evidence',out/'ffmpeg-patch.json'],out/'patch.log')
 write(out/'source-before.json',{'files':tree(src),'binding':pin(inputs/'source-binding.json')})
 original=tree(src)
 samba_root=inputs/'native/execution/native';samba_dsos=sorted(p for p in samba_root.rglob('*.so*') if p.is_file());assert len(samba_dsos)>=80
 dirs=sorted({str(p.parent) for p in samba_dsos});loader=':'.join([str(prefix/'lib'),*dirs]);env=dict(ENV,LD_LIBRARY_PATH=loader,PKG_CONFIG_PATH=str(prefix/'lib/pkgconfig'),PYTHONHASHSEED='1')
 write(out/'loader-inputs.json',{'samba':[pin(p) for p in samba_dsos],'LD_LIBRARY_PATH':loader})
 # 固定公共Samba头来自原始归档，DSO来自已复验native06；不编第二份runtime。
 slock=json.loads((inputs/'native-source-lock.json').read_text())['samba'];header=prefix/'include/libsmbclient.h';header.parent.mkdir(parents=True)
 with tarfile.open(inputs/'cache'/slock['archiveFile']) as t:
  matches=[m for m in t.getmembers() if m.name.endswith('/source3/include/libsmbclient.h')];assert len(matches)==1;header.write_bytes(t.extractfile(matches[0]).read())
 smb=next(p for p in samba_dsos if p.name=='libsmbclient-private-samba.so');util=next(p for p in samba_dsos if p.name=='libsamba-util-private-samba.so')
 pc=prefix/'lib/pkgconfig/smbclient.pc';pc.parent.mkdir(parents=True)
 pc.write_text('prefix='+str(prefix)+'\nName: smbclient\nDescription: Phase20 real Samba\nVersion: 0.7.0\nCflags: -I'+str(header.parent)+'\nLibs: '+str(smb)+' '+str(util)+' '+ ' '.join('-Wl,-rpath-link,'+d for d in dirs)+'\n')
 meson=shutil.which('meson');ninja=shutil.which('ninja');assert meson and ninja
 for name,extra in [('libass',['-Dfontconfig=enabled']),('libplacebo',['-Ddemos=false','-Dtests=false','-Dbench=false'])]:
  b=out/(name+'-build');run([meson,'setup',b,src/name,'--prefix='+str(prefix),'--libdir=lib','--default-library=static','-Dauto_features=disabled','--wrap-mode=nodownload',*extra],out/(name+'-configure.log'),env=env)
  run([ninja,'-C',b,'-j4'],out/(name+'-build.log'),env=env);run([ninja,'-C',b,'install'],out/(name+'-install.log'),env=env)
 ffbuild=out/'ffmpeg-build';ffbuild.mkdir()
 ffargs=[src/'ffmpeg/configure','--prefix='+str(prefix),'--enable-shared','--disable-static','--disable-programs','--disable-doc','--disable-autodetect','--disable-x86asm','--enable-gpl','--enable-version3','--enable-libsmbclient','--disable-everything','--enable-protocol=file,libsmbclient','--enable-demuxer=image2,ass','--enable-decoder=ppm,ass,rawvideo','--enable-filter=buffer,buffersink,format,scale','--extra-ldflags='+' '.join('-Wl,-rpath-link,'+d for d in dirs)]
 run(ffargs,out/'ffmpeg-configure.log',ffbuild,env);run(['make','-j4'],out/'ffmpeg-build.log',ffbuild,env);run(['make','install'],out/'ffmpeg-install.log',ffbuild,env)
 mpvb=out/'mpv-build';run([meson,'setup',mpvb,src/'mpv','--prefix='+str(prefix),'--libdir=lib','--default-library=shared','-Dauto_features=disabled','-Dlibmpv=true','-Dcplayer=false','-Dbuild-date=false','-Dmanpage-build=disabled','-Dohos=disabled','-Degl-ohos=disabled','--wrap-mode=nodownload'],out/'mpv-configure.log',env=env)
 run([ninja,'-C',mpvb,'-j4'],out/'mpv-build.log',env=env);run([ninja,'-C',mpvb,'install'],out/'mpv-install.log',env=env)
 flags=subprocess.check_output(['pkg-config','--cflags','--libs','mpv','libavformat','libavutil'],env=env,text=True).split()
 exe=out/'phase21-probe';run(['cc','-std=c11','-O2','-DP21_HOST','-pthread',HERE/'integration.c',HERE/'preflight.c',HERE/'probe.c',*flags,'-ldl','-Wl,-rpath,'+str(prefix/'lib'),*['-Wl,-rpath-link,'+d for d in dirs],'-Wl,-Map,'+str(out/'probe.map'),'-o',exe],out/'probe-build.log',env=env)
 run(['readelf','-dWs',exe],out/'probe-elf.txt',env=env)
 after=tree(src);assert original==after,'source inputs changed by build';assert not list(src.rglob('*.pyc'))
 write(out/'source-after.json',{'unchanged':True,'sourceBeforeSHA256':sha(out/'source-before.json')})
 write(out/'capabilities.json',{'hostSoftwareRender':True,'OHCodec':False,'GPU':False,'Dovi':False,'targetExecuted':False,'deviceAcceptanceStatus':'pending','systemDependencies':'Observed apt headers/static/runtime libraries; not full source closure'})
 return exe,env

def execute(exe,root,mode,env,extra=()):
 trace=root/'files.trace';cmd=['strace','-f','-e','trace=%file','-o',str(trace),str(exe),str(root),mode,*map(str,extra)]
 with (root/'result.log').open('w') as f:
  p=subprocess.Popen(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:rc=p.wait(timeout=40)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();rc=-9
 return rc

def run_cases(out,exe,env):
 results=[]
 cases=['init','repeat','conflict','late','cache-write','cache-denied','render','readonly','missing-directory','empty-fonts','corrupt-font','font-unreadable','cache-unwritable','symlink','no-font','cjk']
 for name in cases:
  root=out/'cases'/name;prepare(root);root=root.resolve();caseenv=dict(env);extra=[];mode=name
  # Poisoned settings are passed only to this diagnostic child, never changed by adapter.
  home=root/'home';home.mkdir();(home/'.smb').mkdir();(home/'.smb/smb.conf').write_text('[global]\nworkgroup=WRONG_HOME\n')
  poison=root/'poison-fonts.conf';poison.write_text('<fontconfig><dir>/must-not-load-system-fonts</dir></fontconfig>')
  caseenv.update(HOME=str(home),FONTCONFIG_FILE=str(poison),FONTCONFIG_PATH=str(root/'poison-fontdir'))
  if name=='conflict':other=out/'cases/conflict-other';prepare(other);extra=[other.resolve()]
  if name=='readonly':
   for p in [root/'resources/fonts/font1.ttf',root/'resources/fonts',root/'resources']:p.chmod(0o444 if p.is_file() else 0o555)
   mode='render'
  if name=='missing-directory':shutil.rmtree(root/'state/private');mode='init'
  if name=='empty-fonts':(root/'resources/fonts/font1.ttf').unlink();mode='init'
  if name=='corrupt-font':(root/'resources/fonts/font1.ttf').write_bytes(b'bad');mode='init'
  if name=='font-unreadable':(root/'resources/fonts/font1.ttf').chmod(0);mode='init'
  if name=='cache-unwritable':(root/'cache/demux').chmod(0o500);mode='init'
  if name=='symlink':p=root/'resources/fonts/font1.ttf';p.rename(root/'original-font.ttf');p.symlink_to(root/'original-font.ttf');mode='init'
  print('real native case',name,flush=True);rc=execute(exe,root,mode,caseenv,extra);log=(root/'result.log').read_text();trace=(root/'files.trace').read_text()
  negative=name in ['missing-directory','empty-fonts','corrupt-font','font-unreadable','cache-unwritable','symlink']
  assert rc==(1 if negative else 0),(name,rc,log[-2500:])
  if negative:assert 'create stage=resources' in log
  if name not in ['late']:
   assert str(home/'.smb/smb.conf') not in trace and str(poison) not in trace,(name,'default configuration read')
  assert not (home/'.cache').exists()
  images={}
  if mode in ['render','no-font','cjk']:
   for n in ['baseline','subtitle','osd']:
    p=root/(n+'.ppm');data=p.read_bytes().split(b'\n',3)[3];assert len(data)==640*360*3;images[n]={'sha256':sha(p),'nonzeroComponents':sum(v!=0 for v in data)}
   if mode=='render':
    assert images['baseline']['nonzeroComponents']==0,images
    assert images['subtitle']['nonzeroComponents']>100 and images['osd']['nonzeroComponents']>100
    assert images['subtitle']['sha256']!=images['osd']['sha256']
    assert 'PixelOperatorMono-Bold' in log and log.count('fontselect:')>=2
    assert str(root/'resources/fonts/font1.ttf') in trace
   if mode=='no-font':assert 'failed to find any fallback' in log
   if mode=='cjk':assert '0x4E2D' in log or '0x4e2d' in log
   for forbidden in ['/etc/fonts','/usr/share/fonts','/usr/local/share/fonts','/must-not-load-system-fonts']:
    assert forbidden not in trace,(name,forbidden)
   assert 'Using font provider fontconfig' not in log
  loaded={}
  if (root/'maps.txt').is_file():
   for line in (root/'maps.txt').read_text().splitlines():
    fields=line.split();path=fields[-1]
    if path.startswith('/') and Path(path).is_file():loaded[path]=sha(path)
   # Six own FFmpeg and own mpv, no same-SONAME system substitutions.
   for n in ['libmpv.so','libavcodec.so','libavfilter.so','libavformat.so','libavutil.so','libswresample.so','libswscale.so']:
    matches=[p for p in loaded if Path(p).name.startswith(n+'.') or Path(p).name==n];assert len(matches)==1 and Path(matches[0]).is_relative_to(out/'prefix'),(name,n,matches)
   samba=[p for p in loaded if 'samba' in Path(p).name];assert samba and all('/inputs/native/' in p for p in samba),(name,samba)
  elif not negative:raise ValueError('maps missing '+name)
  if name=='cache-write':assert (root/'state/lock/gencache.tdb').is_file()
  if name=='cache-denied':assert 'EACCES' in trace and not (root/'state/lock/gencache.tdb').exists()
  results.append({'case':name,'returncode':rc,'passed':True,'images':images,'loadedLibraries':loaded,'traceSHA256':sha(root/'files.trace'),'logSHA256':sha(root/'result.log')})
  write(out/'results.json',{'cases':results,'executable':pin(exe),'actualHostLibraries':True,'targetExecuted':False})
 write(out/'status.json',{'passed':True,'caseCount':len(results)})

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);exe,env=build_stack(out,a.inputs.resolve());run_cases(out,exe,env)
if __name__=='__main__':main()

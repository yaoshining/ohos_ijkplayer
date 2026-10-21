#!/usr/bin/env python3
"""Reproduce the host SEI object experiment in a fresh output directory."""
import argparse,hashlib,json,os,platform,shutil,subprocess
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--cc',default='clang');ap.add_argument('--jobs',default='8');a=ap.parse_args()
source=a.source.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
shutil.copytree(source,out/'source');(out/'build').mkdir();shutil.copyfile(Path(__file__).with_name('probe.c'),out/'probe.c')
rows=[{'path':p.relative_to(source).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(source.rglob('*')) if p.is_file()]
(out/'source-pins.json').write_text(json.dumps(rows,indent=2)+'\n')
env={**os.environ,'revision':'8.0','REVISION':'8.0','SOURCE_DATE_EPOCH':'1755820644','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','LC_ALL':'C','TZ':'UTC'}
for key in ['CFLAGS','CXXFLAGS','CPPFLAGS','LDFLAGS','CPATH','LIBRARY_PATH','C_INCLUDE_PATH','CPLUS_INCLUDE_PATH']:env.pop(key,None)
commands=[]
def run(label,argv,cwd):
 with (out/(label+'.log')).open('w') as f:p=subprocess.run(argv,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
 commands.append({'label':label,'argv':argv,'cwd':str(cwd),'exitCode':p.returncode});(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 if p.returncode:raise SystemExit(p.returncode)
flags='-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer'
run('configure',['../source/configure','--disable-everything','--disable-autodetect','--disable-asm','--disable-programs','--disable-doc','--disable-debug','--disable-network','--disable-shared','--enable-static','--disable-avformat','--disable-avfilter','--disable-avdevice','--disable-swscale','--disable-swresample','--enable-parser=hevc','--enable-parser=h264','--cc='+a.cc,'--extra-cflags='+flags,'--extra-ldflags=-fsanitize=address,undefined'],out/'build')
run('make',['make','-j'+a.jobs,'libavcodec/libavcodec.a','libavutil/libavutil.a'],out/'build')
linkmap=('-Wl,-map,' if platform.system()=='Darwin' else '-Wl,-Map,')+str(out/'link.map')
run('link',[a.cc,'-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(out/'build'),'-I'+str(out/'source'),str(out/'probe.c'),str(out/'build/libavcodec/libavcodec.a'),str(out/'build/libavutil/libavutil.a'),'-lm','-pthread',linkmap,'-o',str(out/'probe')],out)
env['ASAN_OPTIONS']='detect_leaks='+('0' if platform.system()=='Darwin' else '1')+':halt_on_error=1';env['UBSAN_OPTIONS']='halt_on_error=1:print_stacktrace=1'
run('probe',[str(out/'probe')],out)
for row in rows:
 for base in [source,out/'source']:
  assert hashlib.sha256((base/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
(out/'result.json').write_text(json.dumps({'passed':True,'system':platform.system(),'asanOptions':env['ASAN_OPTIONS'],'ubsanOptions':env['UBSAN_OPTIONS'],'completeUpstreamObjects':True,'sourceUnchanged':True},indent=2)+'\n')

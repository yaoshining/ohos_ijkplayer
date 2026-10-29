from pathlib import Path
import argparse,hashlib,json,shutil,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
base=ROOT/'out/phase21/attempts/04/target-download';lock=json.loads((base/'recipe/binding-lock.json').read_text());libs=base/'execution/target/origin-a/lib';expected={**lock['Linux']['ffmpeg'],'libmpv.so':lock['Linux']['mpv']}
ndk=Path('/Applications/DevEco-Studio.app/Contents/sdk/default/openharmony/native');headers=ROOT/'out/phase20/local-v3/origin-a/ffmpeg/prefix/include';mpvheaders=ROOT/'out/phase18/integration/runs/origin-a/install/usr/local/include'
for n,h in expected.items():assert sha(libs/n)==h
for n,h in lock['headers'].items():assert sha(headers/n)==h
for n,h in lock['mpvHeaders'].items():assert sha(mpvheaders/'mpv'/n)==h
runs=[]
for label in ['origin-a','longer-absolute-directory-b']:
 r=a.output/label;r.mkdir();shutil.copytree(libs,r/'lib')
 for n in ['integration.c','integration.h','preflight.c','probe.c','modes.c']:shutil.copyfile(HERE/n,r/n)
 args=[str(ndk/'llvm/bin/clang'),'--target=aarch64-linux-ohos','--sysroot='+str(ndk/'sysroot'),'-std=c11','-O2','-fPIE','-pie','-pthread','-D__MUSL__=1','-I'+str(headers),'-I'+str(mpvheaders),'integration.c','preflight.c','probe.c','modes.c','-Wl,--no-undefined','-Wl,--no-allow-shlib-undefined','-Wl,--no-as-needed','-Wl,-rpath,$ORIGIN/lib','-Wl,-rpath-link,lib','-Wl,-rpath-link,'+str(ndk/'sysroot/usr/lib/aarch64-linux-ohos'),'-Wl,-Map,link.map']+['lib/'+n for n in expected]+['-o','phase22-probe']
 (r/'command.json').write_text(json.dumps(args,indent=2)+'\n')
 with (r/'build.log').open('w') as f:subprocess.run(args,cwd=r,stdout=f,stderr=subprocess.STDOUT,check=True)
 dump=subprocess.check_output([str(ndk/'llvm/bin/llvm-readelf'),'-h','-d','--wide','--dyn-syms',str(r/'phase22-probe')],text=True);(r/'probe-elf.txt').write_text(dump);assert 'AArch64' in dump and 'ohcodec_smb_runtime_configure_v1@LIBAVFORMAT_62' in dump
 runs.append({'root':label,'probeSHA256':sha(r/'phase22-probe'),'libraries':expected})
assert runs[0]['probeSHA256']==runs[1]['probeSHA256']
(a.output/'verification.json').write_text(json.dumps({'runs':runs,'crossRootProbeBytesEqual':True,'inputProfile':'Phase21 Linux CI approved','compilerSHA256':sha(ndk/'llvm/bin/clang')},indent=2)+'\n');print(json.dumps(runs))

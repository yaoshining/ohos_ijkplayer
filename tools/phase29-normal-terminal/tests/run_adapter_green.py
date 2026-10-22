from pathlib import Path
import subprocess,json,os,time,argparse,sys
R=Path(__file__).resolve().parent.parent;p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--abi-dir',type=Path,required=True);a=p.parse_args();out=a.out;out.mkdir(exist_ok=False);inc=a.abi_dir/'include';lib=a.abi_dir/('libterminal.dylib' if sys.platform=='darwin' else 'libterminal.so')
flags=['clang++','-std=c++17','-fsanitize=address,undefined','-pthread','-DTERMINAL_APP_HOST_TEST','-I'+str(R/'app-adapter'),'-I'+str(inc)]
p=subprocess.run(flags+['-Dwrite=probe_write','-c',str(R/'app-adapter/terminal_adapter.cpp'),'-o',str(out/'adapter.o')],capture_output=True,text=True,timeout=30);(out/'compile-adapter.log').write_text(p.stdout+p.stderr);assert p.returncode==0
p=subprocess.run(flags+[str(R/'tests/adapter_contract.cpp'),str(R/'tests/logger_hooks.cpp'),str(out/'adapter.o'),str(lib),'-o',str(out/'probe')],capture_output=True,text=True,timeout=30);(out/'compile.log').write_text(p.stdout+p.stderr);assert p.returncode==0
rows=[]
for case in ['no-registration','healthy-repeat','fault','callback-hang','logger-hang']:
 folder=out/case;folder.mkdir();t=time.monotonic();p=subprocess.run([str(out/'probe'),case],env=dict(os.environ,APP_TEST_ROOT=str(folder),APP_TEST_MODE=case),capture_output=True,text=True,timeout=6);elapsed=time.monotonic()-t;log=(folder/'terminal-events.log').read_text() if (folder/'terminal-events.log').exists() else ''
 (folder/'run.log').write_text(p.stdout+p.stderr)
 wanted=86 if case in ['fault','callback-hang','logger-hang'] else 0;okay=p.returncode==wanted
 if wanted==86:okay=okay and 2.9<elapsed<4.5 and (case=='logger-hang' or 'event=terminal-ready code=-4' in log)
 if case=='logger-hang':okay=okay and 'LOGGER_REAL_WRITE_BLOCKED' in p.stderr
 rows.append({'case':case,'exit':p.returncode,'elapsedSeconds':elapsed,'passed':okay})
res={'scope':'host adapter subprocess only','cases':rows,'accepted':all(r['passed'] for r in rows)};(out/'results.json').write_text(json.dumps(res,indent=2));print(json.dumps(res));assert res['accepted']

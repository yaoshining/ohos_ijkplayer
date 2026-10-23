from pathlib import Path
import sys,subprocess,json,os
p=Path(__file__).resolve().parent;phase=p.parents[1];src=phase/'ffmpeg-input/source';host=phase/'research/host-sei'
out=p/sys.argv[1];out.mkdir(exist_ok=False)
cmd=['clang','-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(host/'build'),'-I'+str(src),str(p/'hdr_test.c'),str(src/'libavcodec/ohcodec_hdr.c'),str(host/'build/libavcodec/libavcodec.a'),str(host/'build/libavutil/libavutil.a'),'-lm','-pthread','-o',str(out/'hdr_test')]
r=subprocess.run(cmd,capture_output=True,text=True);(out/'compile.log').write_text(r.stdout+r.stderr)
result={'compileCommand':cmd,'compileExit':r.returncode}
if not r.returncode:
 r=subprocess.run([str(out/'hdr_test')],capture_output=True,text=True,env=dict(os.environ,ASAN_OPTIONS='halt_on_error=1:detect_leaks='+('0'if sys.platform=='darwin'else'1'),UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1'));(out/'run.log').write_text(r.stdout+r.stderr);result.update(runExit=r.returncode,stdout=r.stdout,stderr=r.stderr)
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));raise SystemExit(r.returncode)

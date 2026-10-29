from pathlib import Path
import os,sys,json,subprocess,hashlib,re,shutil
p=Path(__file__).resolve().parent;phase=p.parents[1];src=phase/'ffmpeg-input/source';host=phase/'research/host-sei';out=p/sys.argv[1];out.mkdir(exist_ok=False)
s=(src/'libavcodec/ohdec.c').read_text();parts=[];bind=[]
for name in ['oh_decode_output_frame','oh_decode_send_pkt']:
 m=re.search(r'^static int '+name+r'\(',s,re.M);start=m.start();i=s.index('{',start)+1;depth=1
 while depth:depth+=(s[i]=='{')-(s[i]=='}');i+=1
 part=s[start:i];parts.append(part);bind.append(dict(name=name,sha256=hashlib.sha256(part.encode()).hexdigest()))
(out/'ohdec-functions.inc').write_text('\n'.join(parts));(out/'binding.json').write_text(json.dumps(bind,indent=2))
for n in ['integration.c','hdr_test.c']:shutil.copy2(p/n,out/n)
cmd=['clang','-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(host/'build'),'-I'+str(src),str(out/'integration.c'),str(src/'libavcodec/ohcodec_hdr.c'),str(host/'build/libavcodec/libavcodec.a'),str(host/'build/libavutil/libavutil.a'),'-lm','-pthread','-o',str(out/'integration')]
r=subprocess.run(cmd,capture_output=True,text=True);(out/'compile.log').write_text(r.stdout+r.stderr)
if r.returncode:print(r.stderr);raise SystemExit(r.returncode)
rows=[]
for case in ['publication','hardware','software']:
 r=subprocess.run([str(out/'integration'),case],capture_output=True,text=True,env=dict(os.environ,ASAN_OPTIONS='halt_on_error=1:detect_leaks='+('0'if sys.platform=='darwin'else'1'),UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1'))
 rows.append(dict(case=case,exitCode=r.returncode,stdout=r.stdout,stderr=r.stderr));(out/(case+'.log')).write_text(r.stdout+r.stderr)
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows));raise SystemExit(any(x['exitCode']for x in rows))

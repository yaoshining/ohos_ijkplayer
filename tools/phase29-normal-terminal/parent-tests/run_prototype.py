"""真实 normal 源码宿主原型重放；不代表目标构建或应用已接入。"""
import argparse,json,subprocess,os,sys,shutil,hashlib,re
from pathlib import Path
from event_gate import forbidden_events,observer_destroy_events
from extract import find_body
ROOT=Path(__file__).resolve().parent.parent;HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--mpv-root',type=Path);p.add_argument('--out',type=Path,default=ROOT/'evidence/prototype-02');a=p.parse_args();out=a.out
src=a.mpv_root or ROOT/'input-package/sources/mpv';mgr=src/'video/out/hwdec'
if out.exists():raise SystemExit('refuse overwrite')
out.mkdir(parents=True);results={'normalMacros':True,'formalArtifactAllowed':False,'cases':[],'productAdapterIntegrated':False,'scope':'host actual-function prototype only'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs=[p for base in (src,HERE) for p in base.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
identity={(('mpv/'+str(p.relative_to(src))) if p.is_relative_to(src) else ('tests/'+str(p.relative_to(HERE)))):sha(p) for p in inputs};(out/'input-sha.json').write_text(json.dumps(identity,indent=2)+'\n')
def command(name,args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=30);(out/(name+'.log')).write_text(p.stdout+p.stderr)
 if p.returncode:raise RuntimeError(name+' compile/extract failed; not semantic RED')
 return p
flags=['clang','-std=c11','-D_POSIX_C_SOURCE=200809L','-UMP_OHCODEC_DIAGNOSTIC','-UMP_OHCODEC_LIFECYCLE_EXPERIMENT','-g','-O0','-fsanitize=address,undefined','-I',str(mgr),'-pthread']
command('manager',flags+['-Dpthread_create=probe_thread_create','-c',str(mgr/'ohcodec_terminal.c'),'-o',str(out/'manager.o')])
command('unit',flags+[str(HERE/'terminal_unit.c'),str(out/'manager.o'),'-o',str(out/'unit')])
env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
def run(label,args,want,checker=lambda text:True):
 try:p=subprocess.run(args,capture_output=True,text=True,timeout=6,env=env);rc,text=p.returncode,p.stdout+p.stderr
 except subprocess.TimeoutExpired as e:
  norm=lambda v:v.decode(errors='replace') if isinstance(v,bytes) else v or ''
  rc,text=124,norm(e.stdout)+norm(e.stderr)+'\nTIMEOUT'
 (out/(label+'.log')).write_text(text);detail=checker(text)
 if not isinstance(detail,dict):detail={'semanticPassed':detail}
 row={'name':label,'exit':rc,'expectedExit':want,'passed':rc==want and detail.get('semanticPassed',False),**detail};results['cases'].append(row)
 return row
for c in ('unregistered','registration-failure','concurrent-register','concurrent-fault'):run('unit-'+c,[str(out/'unit'),c],0)
command('extract',[sys.executable,'-B',str(HERE/'extract.py'),'--mpv-root',str(src),'--out',str(out/'extracted')])
h=(HERE/'harness.c').read_text().replace('#include <assert.h>','#include <assert.h>\n#include "ohcodec_terminal.h"')
h=h.replace('static void run_case(const char *mode)','#include "terminal_adapter.h"\nstatic void run_case(const char *mode)')
h=h.replace('    if (!strcmp(argv[1], "normal-state-probes")) return normal_state_probes();','''    adapter_callback_hang=!strcmp(argv[1],"callback-hang");
    adapter_skip_callback=!strcmp(argv[1],"missing-ui-notice");
    adapter_start();
    if (adapter_callback_hang || adapter_skip_callback) { run_case("preflight-unsafe"); return 0; }''')
(out/'harness.c').write_text(h)
command('parent',flags+['-I',str(HERE),'-I',str(out/'extracted'),str(out/'harness.c'),str(out/'manager.o'),'-o',str(out/'parent')])
def unsafe_gate(t,case):
 canonical='late-unsafe' if case in ('late-unsafe','owner-retained-no-mapper') else 'preflight-unsafe'
 bad=forbidden_events(t,canonical)
 ready=re.findall(r'EVENT terminal-ready error=(-?\d+) stage=(\d+) notices=(\d+) admission=(\d+)',t)
 notices=re.findall(r'EVENT terminal-notification count=(\d+) error=(-?\d+) stage=(\d+)',t)
 valid=len(ready)==1 and len(notices)==1 and ready[0][2:]==('1','0') and notices[0][0]=='1' and ready[0][:2]==(notices[0][1],notices[0][2]) and int(ready[0][1]) in (1,2,3)
 prompt='EVENT app-simulated-fault-prompt' in t
 want_prompt=case not in ('callback-hang','missing-ui-notice')
 return {'semanticPassed':not bad and valid and prompt==want_prompt and 'EVENT app-deadline-exit cached-progress-only' in t,'forbiddenEvents':bad,'ready':ready,'notifications':notices,'observerSnapshots':observer_destroy_events(t),'promptSimulated':prompt}
for c in ('preflight-unsafe','late-unsafe','owner-retained-no-mapper','callback-hang','missing-ui-notice'):
 run('parent-'+c,[str(out/'parent'),c],86,lambda t,c=c:unsafe_gate(t,c))
for c in ('normal','late-normal','release-error','late-release-error','normal-no-mapper'):
 run('parent-'+c,[str(out/'parent'),c],0,lambda t:'EVENT all-done' in t and 'queue_destroy=1' in t and 'registry_destroy=1' in t and 'mpctx_free=1' in t and 'EVENT app-deadline-exit' not in t)
# 真实 owner 创建入口；不冒充 decoder Create/Start 或整个宿主会话门禁。
owner_text=(mgr/'hwdec_ohcodec_pl.c').read_text();i,j=find_body(owner_text,'bool ohcodec_interop_pl_init(struct ra_hwdec *hw)')
(out/'actual-owner-init.inc').write_text(owner_text[i:j]+'\n')
command('admission',flags+['-I',str(HERE),'-I',str(out),str(HERE/'admission.c'),str(out/'manager.o'),'-o',str(out/'admission')])
for c in ('unregistered','register-failed','non-vulkan','normal','native-failed'):run('owner-'+c,[str(out/'admission'),c],0)
for c in ('inflight-blocked','inflight-finishes'):
 run('owner-'+c,[str(out/'admission'),c],86,lambda t:'EVENT blocked-create-terminal-visible error=-4 new-permit=denied' in t and 'EVENT inflight-owner-unpublished returned=0 surface=0 cleanups=0' in t and 'EVENT terminal-ready error=-4 stage=1 notices=1 admission=0' in t and 'EVENT app-deadline-exit' in t and t.count('EVENT owner-platform-create')==1 and 'EVENT owner-init-return' not in t)
# 去保护负例：真正父级恢复释放会精确触发registry断言。
mut=out/'mutant';shutil.copytree(out/'extracted',mut)
for name in ('actual-generic.inc','actual-vo_gpu_next.inc'):
 q=mut/name;s=q.read_text();s=re.sub(r'mp_ohcodec_terminal_enter\([^;]+;', '(void)0;',s);q.write_text(s)
command('mutant',flags+['-I',str(HERE),'-I',str(mut),str(out/'harness.c'),str(out/'manager.o'),'-o',str(out/'mutant-parent')])
run('negative-remove-protection',[str(out/'mutant-parent'),'preflight-unsafe'],-6,lambda t:'!devs->num_hwctxs' in t and 'EVENT destroy-queue' in t)
# 单项真实 renderer 销毁提前：同一完整UNSAFE判定必须拒绝，非仅检查标签。
mut=out/'renderer-mutant';shutil.copytree(out/'extracted',mut);q=mut/'actual-vo_gpu_next.inc';s=q.read_text()
line='    pl_renderer_destroy(&p->rr);';assert s.count(line)==1
s=s.replace(line,'');anchor='    struct priv *p = vo->priv;';assert s.count(anchor)>=1
# actual-vo_gpu_next.inc 的首个函数是 uninit；绑定其函数体内位置。
a0=s.index('static void uninit(struct vo *vo)');loc=s.index(anchor,a0)+len(anchor);s=s[:loc]+'\n'+line+s[loc:];q.write_text(s)
command('renderer-mutant',flags+['-I',str(HERE),'-I',str(mut),str(out/'harness.c'),str(out/'manager.o'),'-o',str(out/'renderer-mutant-parent')])
def negative_gate(t):
 check=unsafe_gate(t,'late-unsafe')
 return {'semanticPassed':not check['semanticPassed'] and check['forbiddenEvents']==['EVENT destroy-renderer'],'ordinaryUnsafeAccepted':check['semanticPassed'],'forbiddenEvents':check['forbiddenEvents']}
run('negative-renderer-before-drain',[str(out/'renderer-mutant-parent'),'late-unsafe'],86,negative_gate)
results['inputStable']=all(p.exists() and sha(p)==identity[(('mpv/'+str(p.relative_to(src))) if p.is_relative_to(src) else ('tests/'+str(p.relative_to(HERE))))] for p in inputs)
results['accepted']=results['inputStable'] and all(x['passed'] for x in results['cases']);(out/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2));sys.exit(0 if results['accepted'] else 1)

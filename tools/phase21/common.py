from pathlib import Path
import hashlib,json,subprocess,os,time
HERE=Path(__file__).resolve().parent
ENV=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',LC_ALL='C',TZ='UTC',SOURCE_DATE_EPOCH='1755820644')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def require(p,digest):
 if sha(p)!=digest:raise ValueError('SHA mismatch: '+str(p))
def write(p,d):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def pin(p):p=Path(p);return {'path':str(p),'size':p.stat().st_size,'sha256':sha(p)}
def run(args,log,cwd=None,env=None,timeout=1200):
 args=list(map(str,args));log=Path(log);log.parent.mkdir(parents=True,exist_ok=True)
 with log.open('w') as f:r=subprocess.run(args,cwd=cwd,env=env or ENV,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 write(log.with_suffix(log.suffix+'.command.json'),{'argv':args,'cwd':str(cwd),'returncode':r.returncode})
 if r.returncode:raise RuntimeError(str(log)+' failed '+str(r.returncode))
 return log.read_text(errors='replace')
def tree(root):return [dict(pin(p),path=str(p.relative_to(root))) for p in sorted(Path(root).rglob('*')) if p.is_file()]

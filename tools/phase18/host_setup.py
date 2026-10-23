"""Observed runner identity plus isolated, digest-checked Meson installation."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
from evidence_contract import host_package_file
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];D=REPO/'out/phase18-host';D.mkdir(parents=True,exist_ok=False)
def run(name,args):
 with (D/(name+'.log')).open('w') as f:r=subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT)
 if r.returncode:raise RuntimeError(name+' failed: '+str(D/(name+'.log')))
 return (D/(name+'.log')).read_text()
identity={k:os.getenv(k) for k in ['ImageOS','ImageVersion','RUNNER_OS','RUNNER_ARCH','RUNNER_NAME','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','GITHUB_SHA','GITHUB_REPOSITORY','GITHUB_WORKFLOW_REF']}
identity['osRelease']=Path('/etc/os-release').read_text();identity['scope']='Runner, apt and existing host tools are observed inputs, not repository expected SHA locks'
(D/'identity-before.json').write_text(json.dumps(identity,indent=2)+'\n')
(D/'debs/partial').mkdir(parents=True)
run('apt-update',['sudo','apt-get','update'])
run('apt-install',['sudo','apt-get','-o','Dir::Cache::archives='+str(D/'debs'),'-o','APT::Keep-Downloaded-Packages=true','install','-y','gperf'])
assert shutil.which('pkg-config'), 'runner must provide pkg-config'
run('dpkg-packages',['dpkg-query','-W','-f=${binary:Package}\t${Version}\t${Architecture}\t${source:Package}\t${source:Version}\n'])
run('apt-policy',['apt-cache','policy','gperf','pkg-config','pkgconf','gcc','python3'])
venv=D/'venv';run('venv',[sys.executable,'-m','venv',venv]);python=venv/'bin/python'
run('pip-version',[python,'-m','pip','--version'])
run('meson-download',[python,'-m','pip','download','--disable-pip-version-check','--require-hashes','--only-binary=:all:','--no-deps','-r',HERE/'host-requirements.txt','-d',D/'wheels'])
run('meson-install',[python,'-m','pip','install','--disable-pip-version-check','--no-index','--no-compile','--find-links',D/'wheels','--require-hashes','--no-deps','-r',HERE/'host-requirements.txt'])
run('pip-freeze',[python,'-m','pip','freeze','--all'])
packages=[]
for folder in ['debs','wheels']:
 for p in (D/folder).glob('*'):
  if host_package_file(str(p.relative_to(D))) and p.is_file():packages.append({'path':str(p.relative_to(D)),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(D/'package-observations.json').write_text(json.dumps({'runner':identity,'downloadedPackages':packages,'mesonRequirementSHA256':hashlib.sha256((HERE/'host-requirements.txt').read_bytes()).hexdigest()},indent=2)+'\n')
with Path(os.environ['GITHUB_PATH']).open('a') as f:f.write(str(venv/'bin')+'\n')
print('Isolated Meson installed; observed host package identity recorded')

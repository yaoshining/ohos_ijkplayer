"""Record observed runner and packages; no claim of a source bootstrap."""
from pathlib import Path
import os,json,subprocess,hashlib
OUT=Path('out/phase20-ci/host');OUT.mkdir(parents=True,exist_ok=False)
identity={k:os.getenv(k) for k in ['ImageOS','ImageVersion','RUNNER_OS','RUNNER_ARCH','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','GITHUB_SHA','GITHUB_REPOSITORY','GITHUB_WORKFLOW_REF']}
identity['osRelease']=Path('/etc/os-release').read_text();identity['boundary']='Observed Ubuntu runner and apt packages, not an immutable host bootstrap'
(OUT/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
packages=['build-essential','binutils','clang','pkg-config','python3','perl','libparse-yapp-perl','bison','flex','libgnutls28-dev','libpopt-dev','zlib1g-dev','xsltproc','strace','autoconf','automake','libtool']
for name,args in [('apt-update',['sudo','apt-get','update']),('apt-install',['sudo','apt-get','install','-y',*packages]),('dpkg',['dpkg-query','-W','-f=${binary:Package}\t${Version}\t${Architecture}\n'])]:
 with (OUT/(name+'.log')).open('w') as f:subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,check=True)

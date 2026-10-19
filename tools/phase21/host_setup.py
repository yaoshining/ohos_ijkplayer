"""记录宿主身份，在隔离venv安装已有固定Meson；系统依赖为观测边界。"""
from common import *
import sys
out=Path('out/phase21-ci/host').resolve();out.mkdir(parents=True,exist_ok=False)
write(out/'identity.json',{k:os.getenv(k) for k in ['ImageOS','ImageVersion','RUNNER_OS','RUNNER_ARCH','GITHUB_SHA','GITHUB_RUN_ID']})
packages=['build-essential','binutils','pkg-config','ninja-build','python3-venv','python3-jinja2','python3-markupsafe','libfreetype6-dev','libfribidi-dev','libharfbuzz-dev','libfontconfig1-dev','libgnutls28-dev','libpopt-dev','zlib1g-dev','strace','nasm']
run(['sudo','apt-get','update'],out/'apt-update.log');run(['sudo','apt-get','install','-y',*packages],out/'apt-install.log');run(['dpkg-query','-W','-f=${binary:Package}\t${Version}\t${Architecture}\n'],out/'dpkg.log')
run([sys.executable,'-m','venv','--system-site-packages',out/'venv'],out/'venv.log');python=out/'venv/bin/python';req=HERE.parent/'phase18/host-requirements.txt'
run([python,'-m','pip','download','--require-hashes','--only-binary=:all:','--no-deps','-r',req,'-d',out/'wheels'],out/'wheel-download.log')
run([python,'-m','pip','install','--no-index','--no-compile','--find-links',out/'wheels','--require-hashes','--no-deps','-r',req],out/'meson-install.log')
write(out/'packages.json',{'wheelFiles':tree(out/'wheels'),'requirement':pin(req),'boundary':'Observed apt/runner/system Python modules, not source bootstrap'})
with Path(os.environ['GITHUB_PATH']).open('a') as f:f.write(str(out/'venv/bin')+'\n')

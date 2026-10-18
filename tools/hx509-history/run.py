#!/usr/bin/env python3
"""新建两条完整诊断链；不更新候选或默认指针。"""
import argparse, concurrent.futures, importlib.util, json, os, platform, shutil, subprocess, sys, tarfile, time
from pathlib import Path
import profile as hp
import waf_select
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def write(p,data):
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


def prepare(root,profile):
    hp.require_profile(profile)
    if root.exists():raise ValueError('拒绝复用任何构建根目录')
    root.mkdir(parents=True)


def recipe(base,dest,profile):
    hp.materialize(base,dest,profile)
    for name in ['run.py','sources.lock.json']:shutil.copy2(HERE/name,dest/name)


def extract(archive,dest,digest):
    if hp.sha(archive)!=digest:raise ValueError('来源归档摘要不符')
    if dest.exists():raise ValueError('拒绝复用源码树')
    dest.mkdir(parents=True)
    with tarfile.open(archive) as tar:
        # Fixed archives; reject paths escaping extraction root even on older Python.
        for m in tar.getmembers():
            p=(dest/m.name).resolve()
            if not p.is_relative_to(dest.resolve()):raise ValueError('非法归档路径')
            if not (m.isfile() or m.isdir() or m.issym() or m.islnk()):raise ValueError('不支持的归档成员类型')
            if m.issym() or m.islnk():
                target=(p.parent/m.linkname).resolve() if m.issym() else (dest/m.linkname).resolve()
                if not target.is_relative_to(dest.resolve()):raise ValueError('非法归档链接')
        # Debian 固定 Python 3.11.2 尚无 filter 参数；固定SHA + 前置成员校验。
        tar.extractall(dest)
    roots=list(dest.iterdir())
    if len(roots)!=1 or not roots[0].is_dir():raise ValueError('归档根目录不唯一')
    return roots[0]


def command(args,log,env=None,cwd=None):
    with log.open('w') as stream:
        result=subprocess.run([str(x) for x in args],env=env,cwd=cwd,stdout=stream,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError('命令失败 '+str(result.returncode)+'；日志 '+str(log))


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def native_environment(home):
    env={k:os.environ[k] for k in ['PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','TOOLCHAINS'] if k in os.environ}
    env.update(HOME=str(home),LANG='C',LC_ALL='C',TZ='UTC',SOURCE_DATE_EPOCH='1755820644',PYTHONHASHSEED='1',PYTHONDONTWRITEBYTECODE='1',CFLAGS='-O2')
    for key,name in [('CC','clang'),('CXX','c++'),('M4','m4'),('INSTALL','install')]:
        path=shutil.which(name)
        if not path:raise ValueError('宿主工具缺失: '+name)
        env[key]=path
    if platform.system()=='Darwin':env['CFLAGS']+=' -isysroot '+env['SDKROOT']
    return env


def generators(root,cache,host,lock,ndk,recipe_root,jobs):
    prepare(root,'hx509-history');records=[]
    sources=json.loads((recipe_root/'sources.lock.json').read_text())['sources']
    host.verify(lock);host.verify_binding(lock,ndk,recipe_root)
    trees={row['name']:extract(cache/row['archiveFile'],root/'source'/row['name'],row['sha256']) for row in sources}
    home=root/'home';home.mkdir();env=native_environment(home)
    write(root/'pre-build.json',{'sources':hp.pins(cache/row['archiveFile'] for row in sources),'environment':env,'hostLockSha256':hp.sha(Path(lock['recipeRoot']).parent/'host-lock.json'),'freshSourceTrees':True})
    for name in ['bison','flex']:
        prefix=root/'prefix'/name
        commands=[['/bin/sh','./configure','--prefix='+str(prefix),'--disable-nls'],['make','-j'+str(jobs)],['make','install']]
        for i,cmd in enumerate(commands):
            host.verify(lock);host.verify_binding(lock,ndk,recipe_root)
            started=time.time_ns();log=root/(name+'-'+str(i)+'.log')
            command(cmd,log,env,trees[name]);host.verify(lock);host.verify_binding(lock,ndk,recipe_root)
            records.append({'command':cmd,'cwd':str(trees[name]),'startedNs':started,'finishedNs':time.time_ns(),'log':str(log),'exitCode':0})
            write(root/'build-record.json',{'records':records,'environment':env,'freshSourceTrees':True,'hostLockVerifiedAfter':True})
    data=trees['apple-data']/'data';bison=root/'prefix/bison/bin/bison';flex=root/'prefix/flex/bin/flex'
    descriptor={'profile':'hx509-history','bison':str(bison),'flex':str(flex),'data':str(data),'m4':env['M4'],
       'files':hp.pins([bison,flex,Path(env['M4']),*[p for p in data.rglob('*') if p.is_file()]]),
       'trees':[{'root':str(data),'files':sorted(str(p.relative_to(data)) for p in data.rglob('*') if p.is_file())}],
       'hostLockSha256':hp.sha(recipe_root.parent/'host-lock.json'),'sourceArchives':hp.pins(cache/row['archiveFile'] for row in sources),
       'historicalInstallationIdentityProven':False}
    waf_select.verify(descriptor);write(root/'descriptor.json',descriptor)


def main():
    p=argparse.ArgumentParser();p.add_argument('--profile',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--ndk',type=Path,required=True)
    p.add_argument('--dependency-cache',type=Path,required=True);p.add_argument('--generator-cache',type=Path,required=True);p.add_argument('--ffmpeg-repo',type=Path,required=True);p.add_argument('--builder-repo',type=Path,required=True);p.add_argument('--jobs',type=int,default=4);p.add_argument('--parallel',type=int,default=1)
    a=p.parse_args();out=a.output.resolve();prepare(out,a.profile);base=ROOT/'tools/ffmpeg8';rec=out/'recipe';recipe(base,rec,a.profile)
    os.environ.update(LC_ALL='C',TZ='UTC',SOURCE_DATE_EPOCH='1755820644',PYTHONHASHSEED='1',PYTHONDONTWRITEBYTECODE='1')
    if platform.system()=='Darwin':os.environ['SDKROOT']=subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()
    host=module(rec/'host-lock.py','hx_host');lock=host.capture(a.ndk,rec,'hx509-history-'+platform.system());write(out/'host-lock.json',lock)
    def status(stage,**extra):write(out/'status.json',{'stage':stage,**extra});print(stage,flush=True)
    def build(label):
        root=out/label;root.mkdir();status('building-'+label)
        generators(root/'generators',a.generator_cache.resolve(),host,lock,a.ndk,rec,a.jobs)
        dep=root/'dependencies'
        command([sys.executable,'-B',rec/'run-dependency-build.py','--root',dep,'--recipe',rec,'--host-lock',out/'host-lock.json','--cache',a.dependency_cache.resolve(),'--ndk',a.ndk,'--jobs',a.jobs],root/'dependencies.log')
        command([sys.executable,'-B',base/'dependency-manifest.py','--work',dep/'work','--sysroot',dep/'sysroot','--cache',a.dependency_cache.resolve(),'--ndk',a.ndk,'--recipe',rec],root/'manifest.log')
        manifest=dep/'sysroot/dependency-manifest.json';m=json.loads(manifest.read_text())
        m['hx509Diagnostic']={'profile':'hx509-history','separateEvidence':str(root/'generators'),'files':hp.pins([root/'generators/descriptor.json',root/'generators/build-record.json',*[f for f in (root/'generators/tasks').glob('*.json')],*[f for f in (root/'generators/apply').glob('*')]]),'scope':'独立诊断证据；未提升原清单的完整来源资格'}
        write(manifest,m)
        command([sys.executable,'-B',base/'producer-sdk.py','build','--ndk',a.ndk,'--smb',dep/'sysroot','--static-manifest',manifest,'--static-manifest-sha256',hp.sha(manifest),'--ffmpeg-repo',a.ffmpeg_repo,'--builder-repo',a.builder_repo,'--delivery',base/'baseline-evidence','--output',root/'ffmpeg','--jobs',a.jobs],root/'ffmpeg.log')
        sdk=root/'ffmpeg/work/prefix';command([sys.executable,'-B',base/'producer-sdk.py','verify','--sdk',sdk,'--manifest-sha256',hp.sha(sdk/'manifest.json')],root/'verify.log')
        return {'label':label,'sdkRoot':str(sdk),'manifestSha256':hp.sha(sdk/'manifest.json')}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=a.parallel) as pool:results=list(pool.map(build,['a','b']))
        command([sys.executable,'-B',base/'dependency-repeat.py','--first',out/'a/dependencies/sysroot','--second',out/'b/dependencies/sysroot','--require-build-records','--report',out/'static-repeat.json'],out/'static-repeat.log')
        command([sys.executable,'-B',base/'compare-sdks.py','--first',results[0]['sdkRoot'],'--second',results[1]['sdkRoot'],'--report',out/'ffmpeg-repeat.json'],out/'ffmpeg-repeat.log')
        host.verify(lock);host.verify_binding(lock,a.ndk,rec);status('complete',sdks=results,formalArtifactAllowed=False,deviceAcceptance='pending')
    except Exception as exc:status('failed',error=str(exc));raise

if __name__=='__main__':main()

#!/usr/bin/env python3
"""新建两条完整诊断链；不更新候选或默认指针。"""
import argparse, difflib, shlex, concurrent.futures, importlib.util, json, os, platform, shutil, subprocess, sys, tarfile, time
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
    for name in ['run.py','sources.lock.json','linux-flex-compat.h']:shutil.copy2(HERE/name,dest/name)


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


def flex_environment(env,recipe_root,bsd_library=None):
    selected=dict(env)
    if platform.system()!='Linux':return selected,[]
    library=Path(bsd_library) if bsd_library is not None else Path('/usr/lib/x86_64-linux-gnu/libbsd.so.0')
    header=recipe_root/'linux-flex-compat.h'
    if not library.is_file() or not header.is_file():raise ValueError('Linux Flex 兼容库或头文件缺失')
    selected['CPPFLAGS']='-include '+shlex.quote(str(header))
    selected['LIBS']=str(library.resolve())
    return selected,hp.pins([header,library])


def patch_linux_flex(source,evidence):
    path=source/'src/main.c';old=path.read_text()
    if hp.sha(path)!='d2365c9c2e9457747604021288a37b756d894c085436281fc68f0f44d5d35299':raise ValueError('Apple Flex main.c 与固定源码不符')
    text=hp.replace_once(old,'#include <mach-o/dyld.h>','#ifdef __APPLE__\n#include <mach-o/dyld.h>\n#endif')
    anchor='static int _makerelative(char *path, size_t pathlen, const char *baseprog)\n{'
    text=hp.replace_once(text,anchor,anchor+'\n#ifndef __APPLE__\n\t(void)path; (void)pathlen; (void)baseprog;\n\treturn 1; /* Linux 使用已显式锁定的 M4，保留原有未定位时的回退。 */\n#else')
    text=hp.replace_once(text,'\treturn 1;\n}\n\nvoid usage','\treturn 1;\n#endif\n}\n\nvoid usage')
    patch=evidence/'linux-flex-main.patch'
    patch.write_text(''.join(difflib.unified_diff(old.splitlines(True),text.splitlines(True),fromfile='a/src/main.c',tofile='b/src/main.c')))
    path.write_text(text)
    return hp.pins([path,patch,source/'src/skel.c'])


def verify_extra(pins):
    for row in pins:
        p=Path(row['path'])
        if not p.is_file() or hp.sha(p)!=row['sha256']:raise ValueError('兼容层输入漂移: '+str(p))


def generators(root,cache,host,lock,ndk,recipe_root,jobs):
    prepare(root,'hx509-history');records=[]
    sources=json.loads((recipe_root/'sources.lock.json').read_text())['sources']
    host.verify(lock);host.verify_binding(lock,ndk,recipe_root)
    trees={row['name']:extract(cache/row['archiveFile'],root/'source'/row['name'],row['sha256']) for row in sources}
    home=root/'home';home.mkdir();env=native_environment(home)
    m4_version=hp.m4_version(env['M4']);hp.expected_for_m4(m4_version)
    flex_env,extra=flex_environment(env,recipe_root)
    if platform.system()=='Linux':
        extra+=patch_linux_flex(trees['flex'],root)
        provenance=recipe_root.parent.parent/'host-provenance'
        extra+=hp.pins([Path('/usr/lib/x86_64-linux-gnu/libmd.so.0'),provenance/'packages.tsv',provenance/'deb-sha256.txt',provenance/'sources.list'])
    verify_extra(extra)
    write(root/'pre-build.json',{'sources':hp.pins(cache/row['archiveFile'] for row in sources),'environment':env,'m4Version':m4_version,'hostLockSha256':hp.sha(Path(lock['recipeRoot']).parent/'host-lock.json'),'freshSourceTrees':True,'linuxFlexCompatibility':extra,'flexEnvironment':flex_env})
    for name in ['bison','flex']:
        tool_env=flex_env if name=='flex' else env
        prefix=root/'prefix'/name
        commands=[['/bin/sh','./configure','--prefix='+str(prefix),'--disable-nls'],['make','-j'+str(jobs)],['make','install']]
        for i,cmd in enumerate(commands):
            host.verify(lock);host.verify_binding(lock,ndk,recipe_root)
            started=time.time_ns();log=root/(name+'-'+str(i)+'.log')
            verify_extra(extra);command(cmd,log,tool_env,trees[name]);verify_extra(extra);host.verify(lock);host.verify_binding(lock,ndk,recipe_root)
            records.append({'command':cmd,'cwd':str(trees[name]),'startedNs':started,'finishedNs':time.time_ns(),'log':str(log),'exitCode':0,'environment':tool_env})
            write(root/'build-record.json',{'records':records,'environment':env,'freshSourceTrees':True,'hostLockVerifiedAfter':True})
    data=trees['apple-data']/'data';bison=root/'prefix/bison/bin/bison';flex=root/'prefix/flex/bin/flex'
    descriptor={'profile':'hx509-history','bison':str(bison),'flex':str(flex),'data':str(data),'m4':env['M4'],'m4Version':m4_version,
       'files':hp.pins([bison,flex,Path(env['M4']),*[p for p in data.rglob('*') if p.is_file()]])+extra,'linuxFlexCompatibility':extra,
       'trees':[{'root':str(data),'files':sorted(str(p.relative_to(data)) for p in data.rglob('*') if p.is_file())}],
       'hostLockSha256':hp.sha(recipe_root.parent/'host-lock.json'),'sourceArchives':hp.pins(cache/row['archiveFile'] for row in sources),
       'historicalInstallationIdentityProven':False}
    waf_select.verify(descriptor);write(root/'descriptor.json',descriptor)


def compare_chains(first,second,out,compare,build_fixed):
    paired=compare(first,second);write(out/'ffmpeg-repeat.json',paired)
    result={'pairedAllMatch':paired['allMatch'],'fixedRootAllMatch':None}
    if not paired['allMatch']:
        fixed=build_fixed();proof=compare(first,fixed);write(out/'ffmpeg-fixed-root-repeat.json',proof)
        result.update(fixedRootAllMatch=proof['allMatch'],fixedRootSdk=str(fixed))
        if not proof['allMatch']:raise ValueError('相同静态输入根的两次 FFmpeg 构建仍不一致')
    return result


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
        sdk=ffmpeg(root,dep)
        return {'label':label,'sdkRoot':str(sdk),'manifestSha256':hp.sha(sdk/'manifest.json')}
    def ffmpeg(root,dep):
        manifest=dep/'sysroot/dependency-manifest.json'
        command([sys.executable,'-B',base/'producer-sdk.py','build','--ndk',a.ndk,'--smb',dep/'sysroot','--static-manifest',manifest,'--static-manifest-sha256',hp.sha(manifest),'--ffmpeg-repo',a.ffmpeg_repo,'--builder-repo',a.builder_repo,'--delivery',base/'baseline-evidence','--output',root/'ffmpeg','--jobs',a.jobs],root/'ffmpeg.log')
        sdk=root/'ffmpeg/work/prefix';command([sys.executable,'-B',base/'producer-sdk.py','verify','--sdk',sdk,'--manifest-sha256',hp.sha(sdk/'manifest.json')],root/'verify.log')
        return sdk

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=a.parallel) as pool:results=list(pool.map(build,['a','b']))
        command([sys.executable,'-B',base/'dependency-repeat.py','--first',out/'a/dependencies/sysroot','--second',out/'b/dependencies/sysroot','--require-build-records','--report',out/'static-repeat.json'],out/'static-repeat.log')
        def fixed_control():
            root=out/'fixed-root';root.mkdir();return ffmpeg(root,out/'a/dependencies')
        comparison=module(base/'compare-sdks.py','hx_compare')
        repeat=compare_chains(Path(results[0]['sdkRoot']),Path(results[1]['sdkRoot']),out,comparison.compare,fixed_control)
        host.verify(lock);host.verify_binding(lock,a.ndk,rec);status('complete',sdks=results,repeat=repeat,formalArtifactAllowed=False,deviceAcceptance='pending')
    except Exception as exc:status('failed',error=str(exc));raise

if __name__=='__main__':main()

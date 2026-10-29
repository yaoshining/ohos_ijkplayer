#!/usr/bin/env python3
"""从全新目录执行冻结 recipe，构建前后验证同一输入锁。"""
import argparse,importlib.util,json,os,subprocess,time,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent

def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def controlled_environment(ndk,root,cache,jobs,host_sha):
    # 只保留需要的基础宿主设置；用户环境不能改写目标 NDK、ABI 或编译器。
    env={k:os.environ[k] for k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','TOOLCHAINS'] if k in os.environ}
    env.update(LC_ALL='C',TZ='UTC',SOURCE_DATE_EPOCH='1755820644',PYTHONHASHSEED='1',
      OHOS_NDK=str(ndk.resolve()),OHOS_SYSROOT=str(ndk.resolve()/'sysroot'),OHOS_LLVM_BIN=str(ndk.resolve()/'llvm/bin'),OHOS_ARCH='arm64-v8a',
      HOSTCC=str(Path(shutil.which('clang')).resolve()),M4=str(Path(shutil.which('m4')).resolve()),WORK_DIR=str(root/'work'),PREFIX=str(root/'sysroot'),SOURCE_CACHE=str(cache),JOBS=jobs,
      FFMPEG8_PIN_HOST_BISON='1',FFMPEG8_HOST_LOCK_SHA256=host_sha)
    return env

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--recipe',type=Path,required=True);p.add_argument('--host-lock',type=Path,required=True);p.add_argument('--cache',type=Path,required=True);p.add_argument('--ndk',type=Path,required=True);p.add_argument('--jobs',default='6');a=p.parse_args()
    host=module('host-lock');repeat=module('dependency-repeat');root=a.root.resolve();recipe=a.recipe.resolve();cache=a.cache.resolve()
    if root.exists():raise ValueError('拒绝复用任何构建目录')
    lock=json.loads(a.host_lock.read_text());host.verify(lock);host.verify_binding(lock,a.ndk,recipe)
    sources=json.loads((recipe/'dependency-sources.lock.json').read_text())
    for row in sources['sources']:
        if host.sha(cache/row['archiveFile'])!=row['sha256']:raise ValueError('下载来源摘要不匹配')
    inputs={'hostLockSha256':host.sha(a.host_lock),'sourceLockSha256':host.sha(recipe/'dependency-sources.lock.json'),
      'recipe':{f.name:host.sha(f) for f in sorted(recipe.iterdir()) if f.is_file()}}
    root.mkdir(parents=True);record={'freshOutput':True,'startedNs':time.time_ns(),'inputs':inputs,'hostLockVerifiedAfter':False}
    env=controlled_environment(a.ndk,root,cache,a.jobs,host.sha(a.host_lock))
    record['effectiveEnvironment']=env
    with (root/'build.log').open('w') as log:
        r=subprocess.run(['bash',str(recipe/'build-libsmbclient.sh')],env=env,stdout=log,stderr=subprocess.STDOUT)
        if r.returncode==0:
            r=subprocess.run(['python3',str(recipe/'verify-dependency-features.py'),'--work',str(root/'work'),'--sysroot',str(root/'sysroot'),'--output',str(root/'feature-verification.json')],env=dict(env,PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=subprocess.STDOUT)
            if r.returncode==0:record['featureVerification']=json.loads((root/'feature-verification.json').read_text())
    record.update(exitCode=r.returncode,finishedNs=time.time_ns())
    try:host.verify(lock);host.verify_binding(lock,a.ndk,recipe);record['hostLockVerifiedAfter']=True
    finally:
        if r.returncode==0:
            record['outputs']=repeat.inventory(root/'sysroot')
            generator=module('generator-lock');record['generatedTools']={}
            for file in sorted((root/'work/generator-locks').glob('*.json')):
                row=json.loads(file.read_text());generator.verify(row);record['generatedTools'][file.stem]=row
            if set(record['generatedTools'])!={'bison','heimdal'}:raise ValueError('生成器使用前锁缺失')
        (root/'build-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    raise SystemExit(r.returncode)
if __name__=='__main__':main()

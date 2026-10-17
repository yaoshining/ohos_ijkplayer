#!/usr/bin/env python3
"""CI 从固定公开来源准备输入，不读取 Player 或用户缓存。"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import zipfile
import shutil
HERE=Path(__file__).resolve().parent

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.output.resolve()
    if root.exists():raise ValueError('CI 输入目录必须全新')
    root.mkdir(parents=True);lock=json.loads((HERE/'producer-inputs.lock.json').read_text());baseline=json.loads((HERE/'baseline-lock.json').read_text())
    if sha(HERE/'dependency-sources.lock.json')!=lock['dependenciesLockSha256']:raise ValueError('依赖来源锁摘要不符')
    for name in ['ffmpeg','builder']:
        row=lock[name];repo=root/name
        subprocess.run(['git','init','--bare',str(repo)],check=True)
        subprocess.run(['git','-C',str(repo),'fetch','--depth=1',row['repository'],row['revision']],check=True)
    with (root/'ffmpeg-source.tar').open('wb') as f:subprocess.run(['git','-C',str(root/'ffmpeg'),'archive',lock['ffmpeg']['revision']],stdout=f,check=True)
    if sha(root/'ffmpeg-source.tar')!=lock['ffmpeg']['gitArchiveSha256']:raise ValueError('FFmpeg 源码 archive 摘要不符')
    for name,digest in baseline['patches'].items():
        if sha(HERE/name)!=digest:raise ValueError('本仓补丁被修改但未重新锁定')
        if '/ohcodec/' in name:
            data=subprocess.check_output(['git','-C',str(root/'builder'),'show',lock['builder']['revision']+':patches/ffmpeg/'+Path(name).name])
            if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('锁定上游补丁与本仓不一致')
    archive=root/'toolchain.tar.gz';tool=lock['toolchain']
    subprocess.run(['curl','-fLsS','--retry','2','--max-time','900',tool['url'],'-o',str(archive)],check=True)
    if sha(archive)!=tool['sha256']:raise ValueError('工具链 archive SHA256 不符')
    with tarfile.open(archive) as t:
        matches=[m for m in t.getmembers() if m.name.endswith('.zip') and '/native-linux-x64-' in m.name]
        if len(matches)!=1:raise ValueError('工具链 archive 中 native zip 不唯一')
        with (root/'native.zip').open('wb') as f:shutil.copyfileobj(t.extractfile(matches[0]),f)
    with zipfile.ZipFile(root/'native.zip') as z:
        for name in z.namelist():
            if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('工具链 zip 路径逃逸')
        z.extractall(root/'ndk-unpacked')
    natives=list((root/'ndk-unpacked').rglob('llvm/bin/clang'))
    if len(natives)!=1:raise ValueError('不能唯一识别 native NDK')
    ndk=natives[0].parents[2];ndk.rename(root/'ndk')
    for f in (root/'ndk/llvm/bin').iterdir():
        if f.is_file():f.chmod(f.stat().st_mode | 0o111)
    report={'sourceArchiveVerified':True,'patchesVerified':True,'toolchainArchiveVerified':True,'hostToolsVerified':False,'hostToolsReason':'apt/Python 宿主环境尚未由固定镜像摘要绑定，实际工具摘要由 SDK 记录','toolchain':tool,'dependenciesLockSha256':lock['dependenciesLockSha256'],'formalReleaseAllowed':False}
    (root/'input-verification.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()

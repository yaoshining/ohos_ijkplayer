#!/usr/bin/env python3
"""记录新源码静态依赖产物，保持与历史缓存证明分离。"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

HERE=Path(__file__).resolve().parent

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def rec(p,root):return {'path':str(p.relative_to(root)),'sha256':sha(p),'sizeBytes':p.stat().st_size}

def source_records(lock,cache,sysroot):
    result=[]
    for row in lock['sources']:
        archive=cache/row['archiveFile']
        optional=row.get('role')=='optional-host-tool'
        used=not optional or (sysroot/'bin/bison').is_file()
        if used and not archive.is_file():raise ValueError(f'实际使用的源码归档缺失: {archive}')
        if archive.exists() and sha(archive)!=row['sha256']:raise ValueError(f'源码摘要不符: {archive}')
        result.append(dict(row,useStatus='source-built' if used else 'not-used-external-host-tool',archiveAvailable=archive.is_file()))
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--sysroot',type=Path,required=True);p.add_argument('--cache',type=Path,required=True);p.add_argument('--ndk',type=Path,required=True);p.add_argument('--manifest-name',default='dependency-manifest.json');p.add_argument('--recipe',type=Path,default=HERE);a=p.parse_args()
    root=a.sysroot.resolve();work=a.work.resolve();evidence=root/'evidence'/Path(a.manifest_name).stem;
    if evidence.exists():raise ValueError('拒绝覆盖已有 dependency evidence')
    evidence.mkdir(parents=True)
    expected=json.loads((HERE/'baseline-lock.json').read_text())['staticInputs'];archives=[]
    for rel in expected:
        file=root/rel
        if not file.is_file():raise ValueError(f'尚未构建完成: {rel}')
        header=subprocess.check_output([str(a.ndk/'llvm/bin/llvm-readelf'),'-h',str(file)],text=True)
        machines=[l for l in header.splitlines() if 'Machine:' in l]
        if not machines or any('AArch64' not in l for l in machines):raise ValueError(f'archive 含非 ARM64 对象: {rel}')
        row=rec(file,root);row.update(baselineSha256=expected[rel],matchesHistoricalBytes=sha(file)==expected[rel]);archives.append(row)
    lock=json.loads((HERE/'dependency-sources.lock.json').read_text());sources=source_records(lock,a.cache,root)
    dirs={'zlib':'zlib-1.3.1','popt':'popt-1.19','gmp':'gmp-6.3.0','nettle':'nettle-3.9.1','libtasn1':'libtasn1-4.19.0','gnutls':'gnutls-3.8.7','samba':'samba'}
    licenses=[]
    for name,dirname in dirs.items():
        src=work/dirname
        candidates=sorted(set(list(src.glob('COPYING*'))+list(src.glob('LICENSE*'))+list((src/'doc').glob('COPYING*'))))
        if not candidates:raise ValueError(f'缺少许可证: {name}')
        for file in candidates:
            if not file.is_file():continue
            dest=root/'licenses'/name/file.relative_to(src);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,dest);licenses.append(rec(dest,root))
        for rel in ['config.log','config.status','config.h','bin/config.log','bin/default/include/config.h','build-cache/cross-answers.txt']:
            file=src/rel
            if file.is_file():
                dest=evidence/name/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,dest)
    for name in ['build-libsmbclient.sh','fetch-sources.py','dependency-sources.lock.json','dependency-paths.py','generator-lock.py']:
        
        if (a.recipe/name).exists():shutil.copy2(a.recipe/name,evidence/name)
    samba=next(r for r in sources if r['name']=='samba-4.20.7');patch=[]
    paths=['dynconfig/wscript','wscript','buildtools/wafsamba/samba_cross.py','lib/util/charset/wscript_build','lib/util/charset/iconv.c','lib/socket/interfaces.c','third_party/heimdal_build/wscript_build','lib/replace/wscript','source3/librpc/idl/wscript_build']
    with tarfile.open(a.cache/samba['archiveFile']) as tar:
        for name in paths:
            before=tar.extractfile(samba['archivePrefix']+name).read().decode().splitlines(True);after=(work/'samba'/name).read_text().splitlines(True)
            patch.extend(difflib.unified_diff(before,after,fromfile='a/'+name,tofile='b/'+name))
    (evidence/'samba-source.patch').write_text(''.join(patch))
    tools=[]
    for n in ['clang','ld.lld','llvm-ar','llvm-ranlib']:
        f=(a.ndk/'llvm/bin'/n).resolve();tools.append({'name':n,'path':str(f),'sha256':sha(f)})
    for n in ['bison','make','clang','python3','perl','pkg-config']:
        candidate=(root/'bin'/n) if (root/'bin'/n).exists() else Path(shutil.which(n) or '/nonexistent')
        if candidate.is_file():tools.append({'name':'host-'+n,'path':str(candidate),'sha256':sha(candidate)})
    for n in ['compile_et','asn1_compile']:
        f=work/'samba/bin'/n
        if f.is_file():tools.append({'name':n,'path':str(f),'sha256':sha(f)})
    result={'schemaVersion':1,'targetAbi':'arm64-v8a','sourceBuildComplete':True,'fullyVerified':False,'historicalSourceIdentityProven':False,
      'limitations':['新的 release/git 输入与历史缓存的完整来源绑定仍缺证','本轮未重复构建全部静态依赖','recipe 副本在构建后采集；未冒充逐进程执行证明'],
      'sources':sources,'archives':archives,'headers':[rec(f,root) for f in sorted((root/'include').rglob('*')) if f.is_file()],'pkgconfig':[rec(f,root) for f in sorted((root/'lib/pkgconfig').glob('*.pc'))],'licenses':licenses,'tools':tools,'evidence':[rec(f,root) for f in sorted(evidence.rglob('*')) if f.is_file()]}
    (root/a.manifest_name).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(root/a.manifest_name)
if __name__=='__main__':main()

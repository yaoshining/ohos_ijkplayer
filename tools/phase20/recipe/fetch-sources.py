#!/usr/bin/env python3
"""只下载统一来源锁中的输入；解压前及缓存命中时均验证 SHA256。"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def verify(path,expected):
    if not re.fullmatch('[0-9a-f]{64}',expected or ''):raise ValueError('来源锁缺少合法 SHA256')
    if not Path(path).is_file() or digest(path)!=expected:raise ValueError(f'源码归档 SHA256 不匹配: {path}')

def select(lock,name):
    rows=[r for r in lock['sources'] if r['name']==name]
    if len(rows)!=1:raise ValueError(f'来源未唯一锁定: {name}')
    return rows[0]

def fetch(row,cache,git_repo=None,offline=False):
    cache.mkdir(parents=True,exist_ok=True)
    name=row['archiveFile']
    if Path(name).name!=name:raise ValueError('非法 archiveFile')
    output=cache/name
    if output.exists():verify(output,row['sha256']);return output
    if offline and not (row['kind']=='git-archive' and git_repo is not None):raise ValueError(f'离线输入缺失: {name}')
    temporary=cache/(name+'.partial')
    if temporary.exists() or temporary.is_symlink():raise ValueError(f'已有未完成下载，保留供调查: {temporary}')
    try:
        if row['kind']=='release-archive':
            subprocess.run(['curl','-fLsS','--retry','2','--max-time','600',row['url'],'-o',str(temporary)],check=True)
        elif row['kind']=='git-archive':
            repo=git_repo or cache/(row['name']+'.git')
            if git_repo is None:
                if not repo.exists():subprocess.run(['git','init','--bare',str(repo)],check=True,stdout=sys.stderr)
                subprocess.run(['git','-C',str(repo),'fetch','--depth=1',row['url'],row['revision']],check=True,stdout=sys.stderr)
            with temporary.open('wb') as f:
                subprocess.run(['git','-C',str(repo),'archive','--format=tar','--prefix='+row['archivePrefix'],row['revision']],check=True,stdout=f)
        else:raise ValueError('不支持的来源类型')
        verify(temporary,row['sha256'])
        temporary.rename(output)
    except Exception:
        if temporary.exists():temporary.unlink()
        raise
    return output

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--lock',type=Path,default=Path(__file__).with_name('dependency-sources.lock.json'));p.add_argument('--name',required=True);p.add_argument('--cache',type=Path,required=True);p.add_argument('--git-repo',type=Path);p.add_argument('--offline',action='store_true');a=p.parse_args()
    row=select(json.loads(a.lock.read_text()),a.name)
    print(fetch(row,a.cache.resolve(),a.git_repo,a.offline))
if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.CalledProcessError) as e:print(str(e),file=sys.stderr);sys.exit(1)

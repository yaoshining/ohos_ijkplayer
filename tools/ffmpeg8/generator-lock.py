#!/usr/bin/env python3
"""源码生成的宿主工具在使用前冻结，构建结束再次验证。"""
import argparse,hashlib,json,time
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stamp(files,host_sha):return {'createdNs':time.time_ns(),'hostLockSha256':host_sha,'files':[{'path':str(p.resolve()),'sha256':sha(p)} for p in sorted(set(files))]}
def resource_entries(root):
    if root.is_symlink() or not root.is_dir():raise ValueError('生成器资源根目录无效')
    result=[]
    for p in sorted(root.rglob('*')):
        if p.is_symlink():raise ValueError('生成器资源不接受符号链接: '+str(p))
        result.append({'path':str(p.relative_to(root)),'kind':'directory' if p.is_dir() else 'file'})
    return result

def verify(row):
    for directory in row.get('directories',[]):
        root=Path(directory['root'])
        actual=resource_entries(root)
        if actual!=directory['entries']:raise ValueError('生成器资源集合漂移: '+str(root))
    for f in row['files']:
        p=Path(f['path'])
        if not p.is_file() or sha(p)!=f['sha256']:raise ValueError('已冻结的生成器改变: '+str(p))
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--host-lock-sha256',required=True);p.add_argument('--directory',type=Path);p.add_argument('files',type=Path,nargs='+');a=p.parse_args()
    entries=resource_entries(a.directory) if a.directory else []
    files=a.files+([p for p in sorted(a.directory.rglob('*')) if p.is_file()] if a.directory else [])
    if a.output.exists():raise ValueError('拒绝覆盖生成器预锁')
    row=stamp(files,a.host_lock_sha256)
    row['directories']=([{'root':str(a.directory.resolve()),'entries':entries}] if a.directory else [])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(row,indent=2)+'\n')
if __name__=='__main__':main()

#!/usr/bin/env python3
"""源码生成的宿主工具在使用前冻结，构建结束再次验证。"""
import argparse,hashlib,json,time
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stamp(files,host_sha):return {'createdNs':time.time_ns(),'hostLockSha256':host_sha,'files':[{'path':str(p.resolve()),'sha256':sha(p)} for p in sorted(set(files))]}
def verify(row):
    for f in row['files']:
        p=Path(f['path'])
        if not p.is_file() or sha(p)!=f['sha256']:raise ValueError('已冻结的生成器改变: '+str(p))
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--host-lock-sha256',required=True);p.add_argument('--directory',type=Path);p.add_argument('files',type=Path,nargs='+');a=p.parse_args()
    files=a.files+([p for p in sorted(a.directory.rglob('*')) if p.is_file()] if a.directory else [])
    if a.output.exists():raise ValueError('拒绝覆盖生成器预锁')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(stamp(files,a.host_lock_sha256),indent=2)+'\n')
if __name__=='__main__':main()

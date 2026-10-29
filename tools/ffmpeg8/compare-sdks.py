#!/usr/bin/env python3
"""比较两次独立构建的六库、headers 与 pkgconfig（manifest 元数据本身不要求相同）。"""
import argparse
import hashlib
import json
from pathlib import Path

def hashes(root,paths):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
def compare(first,second):
    lock=json.loads(Path(__file__).with_name('baseline-lock.json').read_text());rows=[]
    for name in lock['libraries']:
        a=hashlib.sha256((first/'lib'/name).read_bytes()).hexdigest();b=hashlib.sha256((second/'lib'/name).read_bytes()).hexdigest();rows.append({'name':name,'firstSha256':a,'secondSha256':b,'matches':a==b})
    development={}
    for folder in ['include','lib/pkgconfig']:
        a=hashes(first,[p for p in sorted((first/folder).rglob('*')) if p.is_file()]);b=hashes(second,[p for p in sorted((second/folder).rglob('*')) if p.is_file()]);development[folder]=bool(a) and a==b
    return {'allMatch':all(r['matches'] for r in rows) and all(development.values()),'libraryCount':len(rows),'libraries':rows,'developmentFiles':development}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--first',type=Path,required=True);p.add_argument('--second',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args();r=compare(a.first,a.second);a.report.write_text(json.dumps(r,indent=2)+'\n');raise SystemExit(0 if r['allMatch'] else 1)

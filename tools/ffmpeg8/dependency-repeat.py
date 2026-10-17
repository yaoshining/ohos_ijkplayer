#!/usr/bin/env python3
"""直接比较两个独立 sysroot；结果绑定输入和清单，不能手填通过。"""
import argparse,hashlib,json
from pathlib import Path
DELIVERED_LIBS=['lib/libgmp.a','lib/libgnutls.a','lib/libhogweed.a','lib/libnettle.a','lib/libpopt.a','lib/libsmbclient.a','lib/libtasn1.a','lib/libz.a']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(root):
    for rel in DELIVERED_LIBS:
        if not (root/rel).is_file():raise ValueError('缺少目标静态库: '+str(root/rel))
    files=[root/r for r in DELIVERED_LIBS]+[p for p in sorted((root/'include').rglob('*')) if p.is_file()]+sorted((root/'lib/pkgconfig').glob('*.pc'))
    if not any('include/' in str(p.relative_to(root)) for p in files):raise ValueError('缺少交付头文件')
    if not any(p.suffix=='.pc' for p in files):raise ValueError('缺少 pkgconfig')
    return {str(p.relative_to(root)):{'sha256':sha(p),'sizeBytes':p.stat().st_size} for p in files}
def compare(first,second):
    if first.resolve()==second.resolve():raise ValueError('相同目录不能证明独立构建')
    a,b=inventory(first),inventory(second);rows=[]
    for rel in sorted(a.keys()|b.keys()):
        if (first/rel).exists() and (second/rel).exists() and (first/rel).samefile(second/rel):raise ValueError('检测到共享产物 inode: '+rel)
        rows.append({'path':rel,'first':a.get(rel),'second':b.get(rel),'matches':rel in a and a.get(rel)==b.get(rel)})
    return {'schemaVersion':1,'allMatch':all(r['matches'] for r in rows),'archivesMatch':all(r['matches'] for r in rows if r['path'] in DELIVERED_LIBS),'rows':rows}
def main():
    p=argparse.ArgumentParser();p.add_argument('--first',type=Path,required=True);p.add_argument('--second',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--require-build-records',action='store_true');a=p.parse_args()
    result=compare(a.first,a.second)
    result['builds']=[]
    for root in [a.first,a.second]:
        record=root.parent/'build-record.json'
        if a.require_build_records and not record.is_file():raise ValueError('缺少独立构建记录')
        if record.exists():
            data=json.loads(record.read_text())
            if data['exitCode']!=0 or not data['freshOutput'] or not data['hostLockVerifiedAfter']:raise ValueError('构建未完整通过')
            if data['outputs']!=inventory(root):raise ValueError('产物与构建完成时不符')
            result['builds'].append({'path':str(record.resolve()),'sha256':sha(record),'inputs':data['inputs']})
    if result['builds'] and (len(result['builds'])!=2 or result['builds'][0]['inputs']!=result['builds'][1]['inputs']):raise ValueError('两次构建输入锁不一致')
    a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['allMatch','archivesMatch']}))
    raise SystemExit(0 if result['allMatch'] else 1)
if __name__=='__main__':main()

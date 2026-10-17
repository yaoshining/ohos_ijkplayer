#!/usr/bin/env python3
"""只读盘点历史缓存源码；不推断其必然生成历史静态库。"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import tarfile

HERE=Path(__file__).resolve().parent

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--cache-source',type=Path,required=True);p.add_argument('--downloads',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True);lock=json.loads((HERE/'dependency-sources.lock.json').read_text());rows=[]
    mapping={'zlib-1.3.1':'zlib','popt-1.19':'popt','gmp-6.3.0':'gmp-6.3.0','nettle-3.9.1':'nettle-3.9.1','libtasn1-4.19.0':'libtasn1-4.19.0','gnutls-3.8.7':'gnutls-3.8.7','samba-4.20.7':'samba'}
    for source in lock['sources']:
        if source['name'] not in mapping:continue
        root=a.cache_source/mapping[source['name']];row={'name':source['name'],'cachePath':str(root),'historicalBinaryBindingProven':False,'selectedRebuildSource':source,'git':None}
        if (root/'.git').exists():
            revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
            diff=subprocess.check_output(['git','-C',str(root),'-c','core.fsmonitor=false','diff','--binary','HEAD'])
            path=a.output/(source['name']+'-cache.patch');path.write_bytes(diff)
            row['git']={'revision':revision,'workingTreePatch':str(path),'patchSha256':sha(path)}
        comparison={'identical':0,'different':[],'missing':[]}
        archive=a.downloads/source['archiveFile']
        with tarfile.open(archive) as t:
            for member in t.getmembers():
                if not member.isfile():continue
                rel=Path(member.name).parts[1:]
                if not rel:continue
                file=root.joinpath(*rel)
                if not file.is_file():comparison['missing'].append('/'.join(rel));continue
                if hashlib.sha256(t.extractfile(member).read()).hexdigest()==sha(file):comparison['identical']+=1
                else:comparison['different'].append('/'.join(rel))
        row['cacheVersusNewArchive']=comparison
        row['configEvidence']=[{'path':str(f.relative_to(root)),'sha256':sha(f)} for rel in ['config.log','config.status','config.h','bin/config.log','bin/default/include/config.h'] if (f:=root/rel).is_file()]
        rows.append(row)
    result={'schemaVersion':1,'fullyVerified':False,'interpretation':'现存缓存源码相似或相同不构成历史静态库来源证明；新 release 不是历史 git 来源的替代证据','sources':rows}
    (a.output/'cache-provenance.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print([(r['name'],r['git']['revision'] if r['git'] else 'no git identity',r['cacheVersusNewArchive']['identical'],len(r['cacheVersusNewArchive']['different'])) for r in rows])
if __name__=='__main__':main()

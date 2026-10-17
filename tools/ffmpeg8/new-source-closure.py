#!/usr/bin/env python3
"""自包含的新选来源证明：逐层验证摘要与实际构建产物，不接受自报通过。"""
import argparse,hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
LIBS=set(json.loads((HERE/'baseline-lock.json').read_text())['staticInputs'])
def digest(text):return hashlib.sha256(text.encode()).hexdigest()
def document(text):return {'sha256':digest(text),'text':text}
def read_document(row):
    if not isinstance(row,dict) or digest(row.get('text',''))!=row.get('sha256'):raise ValueError('闭包证据文档摘要不匹配')
    return row['text']
def verify_pair(a,b,repeat,host_sha):
    for run in (a,b):
        if run.get('exitCode')!=0 or run.get('freshOutput') is not True or run.get('hostLockVerifiedAfter') is not True:raise ValueError('构建记录未证明完整 fresh 执行')
        if run.get('inputs',{}).get('hostLockSha256')!=host_sha:raise ValueError('构建未使用指定宿主预锁')
    if a['inputs']!=b['inputs'] or not a.get('outputs') or a['outputs']!=b.get('outputs'):raise ValueError('实际两次构建输入或输出不一致')
    if not LIBS<=a['outputs'].keys():raise ValueError('八静态库集合不完整')
    rows=repeat.get('rows',[])
    if len(rows)!=len(a['outputs']) or {r['path'] for r in rows}!=set(a['outputs']):raise ValueError('比较报告文件集合不符')
    for row in rows:
        if row.get('first')!=a['outputs'][row['path']] or row.get('second')!=b['outputs'][row['path']]:raise ValueError('比较报告与构建产物不符')
    # 不信任 allMatch/matches；由两侧的真实清单重算。
    return True

def verify(bundle,expected):
    if bundle.get('schemaVersion')!=1 or 'documents' not in bundle:raise ValueError('缺少闭包证据')
    docs=bundle['documents'];texts={k:read_document(v) for k,v in docs.items()}
    required={'host-lock','source-lock','first-record','second-record','static-repeat'}
    if not required<=texts.keys():raise ValueError('闭包证据缺少必要文档')
    parsed={k:json.loads(texts[k]) for k in required};a=parsed['first-record'];b=parsed['second-record'];host=parsed['host-lock'];repeat=parsed['static-repeat']
    verify_pair(a,b,repeat,docs['host-lock']['sha256'])
    if expected!=a['outputs']:raise ValueError('依赖 manifest 与两次产物清单不一致')
    refs=repeat.get('builds',[])
    if len(refs)!=2 or refs[0]['path']==refs[1]['path'] or [r['sha256'] for r in refs]!=[docs[n]['sha256'] for n in ['first-record','second-record']]:raise ValueError('比较报告未绑定独立构建记录')
    if a['inputs'].get('sourceLockSha256')!=docs['source-lock']['sha256']:raise ValueError('源码锁未被构建记录绑定')
    if texts['source-lock']!=(HERE/'dependency-sources.lock.json').read_text():raise ValueError('依赖来源不是已选固定输入')
    recipe=a['inputs'].get('recipe',{});locked={Path(r['path']).name:r['sha256'] for r in host.get('recipeFiles',[])}
    if not recipe or recipe!=locked:raise ValueError('实际 recipe 与预锁集合不符')
    commands={r['name']:r for r in host.get('commands',[])}
    for name in ['cc','clang','make','bison','flex','m4','perl','python3','pkg-config','ld']:
        if not re.fullmatch('[0-9a-f]{64}',commands.get(name,{}).get('sha256','')):raise ValueError('宿主工具未锁定: '+name)
    files={r['path']:r for r in host.get('files',[])}
    if not any('/sysroot/usr/include/' in n for n in files) or not any('/llvm/bin/' in n for n in files):raise ValueError('NDK 文件集未锁定')
    acquired=False
    if host.get('profile')=='linux-debian-bookworm-20250204':
        for run in (a,b):
            env=run.get('effectiveEnvironment',{});ndk=host.get('ndkRoot','')
            if not ndk or env.get('OHOS_NDK')!=ndk or env.get('OHOS_SYSROOT')!=ndk+'/sysroot' or env.get('OHOS_LLVM_BIN')!=ndk+'/llvm/bin' or env.get('OHOS_ARCH')!='arm64-v8a':raise ValueError('实际目标环境不符合 NDK/ABI 预锁')
            stamps=run.get('generatedTools',{})
            if set(stamps)!={'bison','heimdal'}:raise ValueError('缺少生成器使用前冻结证据')
            for stamp in stamps.values():
                if stamp.get('hostLockSha256')!=docs['host-lock']['sha256'] or not stamp.get('files'):raise ValueError('生成器锁未绑定宿主输入')
        needed={'dockerfile','image-inspect','container-inspect','packages','deb-sha256','sources-list'}
        if not needed<=texts.keys():raise ValueError('缺少固定容器获取证据')
        if texts['dockerfile']!=(HERE/'ci/Dockerfile').read_text():raise ValueError('容器 recipe 不是已锁定版本')
        image=json.loads(texts['image-inspect'])[0];container=json.loads(texts['container-inspect'])[0]
        if not re.fullmatch('sha256:[0-9a-f]{64}',image.get('Id','')) or image['Id']!=container.get('Image'):raise ValueError('实际容器 image ID 不匹配')
        if image.get('Architecture')!='amd64' or image.get('Os')!='linux':raise ValueError('容器平台不符')
        if '20250204T000000Z' not in texts['sources-list'] or not texts['deb-sha256'].strip():raise ValueError('包获取证据缺失')
        for name in ['gcc','make','bison','flex','perl','python3','pkgconf']:
            if not re.search('^'+name+r'\t\S+\t',texts['packages'],re.M):raise ValueError('宿主包版本缺失: '+name)
        acquired=True
    elif host.get('profile')!='macos-installed-API24':raise ValueError('未知宿主 profile')
    return {'newSourceClosureVerified':acquired,'staticRepeatVerified':True,'hostToolsPrelocked':True,'hostAcquisitionVerified':acquired,'historicalSourceIdentityProven':False}

def inventory(manifest):
    rows=manifest['archives']+manifest['headers']+manifest['pkgconfig'];r={x['path']:{k:x[k] for k in ['sha256','sizeBytes']} for x in rows}
    if len(r)!=len(rows):raise ValueError('依赖清单重复文件')
    return r

def main():
    p=argparse.ArgumentParser();p.add_argument('--first',type=Path,required=True);p.add_argument('--second',type=Path,required=True);p.add_argument('--repeat',type=Path,required=True);p.add_argument('--host-lock',type=Path,required=True);p.add_argument('--container',type=Path);p.add_argument('--host-provenance',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    paths={'first-record':a.first.parent/'build-record.json','second-record':a.second.parent/'build-record.json','static-repeat':a.repeat,'host-lock':a.host_lock,'source-lock':HERE/'dependency-sources.lock.json'}
    if a.container:
        paths.update({'dockerfile':HERE/'ci/Dockerfile','image-inspect':a.container/'image-inspect.json','container-inspect':a.container/'container-inspect.json','packages':a.host_provenance/'packages.tsv','deb-sha256':a.host_provenance/'deb-sha256.txt','sources-list':a.host_provenance/'sources.list'})
    bundle={'schemaVersion':1,'documents':{k:document(v.read_text()) for k,v in paths.items()}}
    m=json.loads((a.first/'dependency-manifest.json').read_text());result=verify(bundle,inventory(m));bundle['verification']=result
    if a.output.exists():raise ValueError('拒绝覆盖闭包证据')
    a.output.write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n')
    if a.output.resolve().parent!=a.first.resolve():raise ValueError('闭包证据必须保存在依赖 sysroot 中')
    m.update(result,fullyVerified=result['newSourceClosureVerified'])
    m['closureProof']={'path':a.output.name,'sha256':digest(a.output.read_text()),'sizeBytes':a.output.stat().st_size}
    m['limitations']=['历史缓存来源身份仍缺证；与新选来源证明分开','设备验收 pending']+([] if result['hostAcquisitionVerified'] else ['macOS 已安装宿主工具获取来源未重建'])
    dest=a.first/'dependency-manifest-closed.json'
    if dest.exists():raise ValueError('拒绝覆盖已有来源清单')
    dest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()

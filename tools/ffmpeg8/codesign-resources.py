#!/usr/bin/env python3
"""校验 Mach-O CodeDirectory 资源槽与 CodeResources，以及指定子树封存。
CMS/信任链须由系统 codesign 另外验证；本工具不把资源摘要相符升级为发行签名可信。
"""
import argparse,hashlib,json,plistlib,struct
from pathlib import Path


def resource_binding(macho,resources):
    def span(data,off,size):
        if off<0 or size<0 or off+size>len(data):raise ValueError('truncated signature')
        return data[off:off+size]
    if macho[:4]==b'\xca\xfe\xba\xbe':
        count=struct.unpack('>I',span(macho,4,4))[0];result=[]
        for i in range(count):
            cpu,sub,off,size,align=struct.unpack('>5I',span(macho,8+i*20,20))
            result.extend(resource_binding(span(macho,off,size),resources))
        if not result:raise ValueError('no signed slices')
        return result
    if macho[:4]!=b'\xcf\xfa\xed\xfe':raise ValueError('requires Mach-O 64LE or fat32')
    header=struct.unpack('<8I',span(macho,0,32));pos=32;blob=None
    for _ in range(header[4]):
        cmd,size=struct.unpack('<2I',span(macho,pos,8))
        if size<8:raise ValueError('bad load command')
        span(macho,pos,size)
        if cmd==0x1d:
            off,length=struct.unpack('<2I',span(macho,pos+8,8));blob=span(macho,off,length)
        pos+=size
    if blob is None:raise ValueError('missing code signature')
    magic,length,count=struct.unpack('>3I',span(blob,0,12))
    if magic!=0xfade0cc0 or length>len(blob):raise ValueError('bad superblob')
    blob=blob[:length];result=[]
    for i in range(count):
        slot,off=struct.unpack('>2I',span(blob,12+8*i,8));magic,length=struct.unpack('>2I',span(blob,off,8))
        if magic!=0xfade0c02:continue
        cd=span(blob,off,length);fields=struct.unpack('>9I4BI',span(cd,0,44));hashoff,special,hashsize,hashtype=fields[4],fields[6],fields[9],fields[10]
        if special<3:raise ValueError('missing resource slot')
        if hashtype not in (1,2,3):raise ValueError('unsupported CodeDirectory hash')
        algo='sha1' if hashtype==1 else 'sha256';actual=hashlib.new(algo,resources).digest()[:hashsize];expected=span(cd,hashoff-3*hashsize,hashsize)
        if not hashsize or actual!=expected:raise ValueError('CodeResources differs from signed resource slot')
        result.append({'architecture':header[1],'slot':slot,'hashAlgorithm':algo,'resourceHash':actual.hex(),'codeDirectoryHash':hashlib.new(algo,cd).hexdigest(),'matches':True,'cmsTrustCheckedByThisTool':False})
    if not result:raise ValueError('missing CodeDirectory')
    return result


def subtree_inventory(contents,resource_bytes,prefix):
    files=plistlib.loads(resource_bytes)['files2'];sealed={k:v for k,v in files.items() if k.startswith(prefix+'/')};actual={str(p.relative_to(contents)):p for p in (contents/prefix).rglob('*') if p.is_file() or p.is_symlink()};rows=[]
    for name,entry in sealed.items():
        p=actual.get(name);match=False;digest=None
        if p is not None:
            if 'symlink' in entry:match=p.is_symlink() and str(p.readlink())==entry['symlink']
            elif not p.is_symlink():
                algo='sha256' if 'hash2' in entry else 'sha1';digest=hashlib.new(algo,p.read_bytes()).digest();match=digest==entry.get('hash2',entry.get('hash'))
        rows.append({'path':name,'matches':match,'sha256':digest.hex() if digest and len(digest)==32 else None,'symlink':entry.get('symlink')})
    return {'sealedCount':len(sealed),'actualCount':len(actual),'extra':sorted(actual.keys()-sealed.keys()),'missing':sorted(sealed.keys()-actual.keys()),'mismatches':[x['path'] for x in rows if not x['matches']],'files':rows}


def main():
    p=argparse.ArgumentParser();p.add_argument('--app',required=True,type=Path);p.add_argument('--executable',required=True);p.add_argument('--subtree',required=True);p.add_argument('--output',required=True,type=Path);a=p.parse_args();contents=a.app/'Contents';resources=(contents/'_CodeSignature/CodeResources').read_bytes();bind=resource_binding((contents/'MacOS'/a.executable).read_bytes(),resources);tree=subtree_inventory(contents,resources,a.subtree)
    result={'app':str(a.app),'codeResourcesSha256':hashlib.sha256(resources).hexdigest(),'signedResourceSlots':bind,'subtree':a.subtree,**tree,'historicalExecutionIdentityProven':False,'wholeApplicationResourcesVerified':False};a.output.write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='files'})
    if tree['extra'] or tree['missing'] or tree['mismatches']:raise SystemExit(1)

if __name__=='__main__':main()

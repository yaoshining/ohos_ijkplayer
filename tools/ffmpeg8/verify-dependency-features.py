#!/usr/bin/env python3
"""GMP基线配置与GnuTLS3.8.7 AArch64真实曲线表门禁，不执行目标代码。"""
import argparse,hashlib,importlib.util,json,re,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(data):return hashlib.sha256(data).hexdigest()
def elf_module():
    s=importlib.util.spec_from_file_location('feature_elf',HERE/'elf-audit.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def archive_member(data,wanted):
    if not data.startswith(b'!<arch>\n'):raise ValueError('非普通ar归档')
    offset=8;names=b'';found=[]
    while offset<len(data):
        h=data[offset:offset+60]
        if len(h)!=60 or h[-2:]!=b'`\n':raise ValueError('损坏ar头')
        try:length=int(h[48:58])
        except ValueError:raise ValueError('损坏ar尺寸')
        if length<0:raise ValueError('负ar尺寸')
        name=h[:16].decode('ascii').strip();body=data[offset+60:offset+60+length]
        if len(body)!=length:raise ValueError('截断ar成员')
        offset+=60+length+(length%2)
        if name=='//':names=body;continue
        if name in ('/','/SYM64/'):continue
        if name.startswith('#1/'):
            n=int(name[3:])
            if n>len(body):raise ValueError('损坏BSD成员名')
            name=body[:n].rstrip(b'\0').decode();body=body[n:]
        elif name.startswith('/') and name[1:].isdigit():
            pos=int(name[1:])
            if pos>=len(names):raise ValueError('损坏GNU成员名')
            name=names[pos:].split(b'/\n',1)[0].decode()
        else:name=name.rstrip('/')
        if name==wanted:found.append(body)
    if len(found)!=1:raise ValueError('能力对象缺失或重复: '+wanted)
    return found[0]

def curve_entries(data):
    elf=elf_module().inventory(data);h=struct.unpack('<16sHHIQQQIHHHHHH',data[:64])
    if h[1]!=1:raise ValueError('必须核验可重定位对象')
    symbols=[s for s in elf['symbols'] if s['name']=='ecc_curves' and s['type']==1 and s['sectionIndex']]
    if len(symbols)!=1:raise ValueError('曲线表符号缺失或重复')
    symbol=symbols[0];index=symbol['sectionIndex']
    if index>=h[12]:raise ValueError('曲线表节索引无效')
    section=struct.unpack('<IIQQQQIIQQ',data[h[6]+index*64:h[6]+(index+1)*64]);size=symbol['size'];offset=symbol['value']
    if section[1]!=1 or size%48 or not size or offset+size>section[5]:raise ValueError('曲线表不符合固定GnuTLS3.8.7 AArch64布局')
    table=data[section[4]+offset:section[4]+offset+size];rows=[]
    for i in range(0,size,48):
        rows.append({'id':struct.unpack_from('<I',table,i+16)[0],'sizeBytes':struct.unpack_from('<I',table,i+24)[0],'supported':bool(table[i+36]),'group':struct.unpack_from('<I',table,i+40)[0]})
    return rows

def require_curves(rows):
    # GnuTLS3.8.7枚举：SECP224R1=1，SECP192R1=5。不能用字符串出现代替表项。
    for curve in (1,5):
        matches=[r for r in rows if r['id']==curve]
        if len(matches)!=1 or matches[0]['supported'] is not True:raise ValueError('缺少启用曲线表项: '+str(curve))
    return True

def macros(text):return dict(re.findall(r'^#define\s+(\w+)\s+([^\n]+)',text,re.M))
def check_macros(gmp,gnutls):
    a,b=macros(gmp),macros(gnutls)
    if a.get('NO_ASM')!='1' or a.get('GMP_MPARAM_H_SUGGEST')!='"./mpn/generic/gmp-mparam.h"':raise ValueError('GMP不符合基线NO_ASM/generic配置')
    if b.get('ENABLE_NON_SUITEB_CURVES')!='1':raise ValueError('GnuTLS静默关闭NON_SUITEB曲线')
    return True

def verify(work,prefix):
    gmp=work/'gmp-6.3.0/config.h';gnutls=work/'gnutls-3.8.7/config.h';archive=prefix/'lib/libgnutls.a';check_macros(gmp.read_text(),gnutls.read_text());obj=archive_member(archive.read_bytes(),'lt8-ecc.o');rows=curve_entries(obj);require_curves(rows)
    return {'schemaVersion':1,'passed':True,'targetAbi':'arm64-v8a','layout':'GnuTLS3.8.7-LP64-stride48','gmpNoAsm':True,'gmpParameterHeader':'generic','nonSuiteBCurves':True,'curveEntries':rows,'curveObjectSha256':sha(obj),'inputs':{str(p):sha(p.read_bytes()) for p in (gmp,gnutls,archive)},'unresolvedObservations':{'HAVE_ICONV':macros(gnutls.read_text()).get('HAVE_ICONV','undefined'),'Samba':'既有平台/运行目录差异未在本次改变'},'deviceAcceptanceStatus':'pending'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True,type=Path);p.add_argument('--sysroot',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if a.output.exists():raise ValueError('拒绝覆盖已有能力证据')
    result=verify(a.work,a.sysroot);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('GMP NO_ASM/generic + GnuTLS NON_SUITEB/真实曲线表通过')
if __name__=='__main__':main()

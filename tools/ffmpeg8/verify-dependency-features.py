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

def require_symbol(inventory,name,defined):
    rows=[s for s in inventory['symbols'] if s['name']==name and bool(s['sectionIndex'])==defined]
    if len(rows)!=1:raise ValueError('能力符号定义/引用不符合预期: '+name)
    if defined and rows[0].get('type')==2 and not rows[0].get('size'):raise ValueError('能力函数为空: '+name)
    return True

def elf_pointer_string(data,name):
    # 从实际指针符号及R_AARCH64_ABS64重定位解析字符串，不接受任意字符串命中。
    elf_module().inventory(data)
    h=struct.unpack('<16sHHIQQQIHHHHHH',data[:64])
    sh=[struct.unpack_from('<IIQQQQIIQQ',data,h[6]+i*64) for i in range(h[12])]
    tables={}
    for i,section in enumerate(sh):
        if section[1]!=2:continue
        stringsec=sh[section[6]];strings=data[stringsec[4]:stringsec[4]+stringsec[5]];rows=[]
        for pos in range(section[4],section[4]+section[5],24):
            n,info,other,idx,value,size=struct.unpack_from('<IBBHQQ',data,pos)
            rows.append((strings[n:].split(b'\0',1)[0].decode(),idx,value,size,info&15))
        tables[i]=rows
    matches=[(ti,idx,sym) for ti,rows in tables.items() for idx,sym in enumerate(rows) if sym[0]==name and sym[1]]
    if len(matches)!=1:raise ValueError('路径指针符号缺失/重复: '+name)
    ti,idx,sym=matches[0]
    if sym[3]!=8 or sym[4]!=1:raise ValueError('路径不是LP64指针: '+name)
    values=[]
    for section in sh:
        if section[1]!=4 or section[7]!=sym[1] or section[6]!=ti:continue
        for pos in range(section[4],section[4]+section[5],24):
            off,info,addend=struct.unpack_from('<QQq',data,pos)
            if off!=sym[2]:continue
            if info&0xffffffff!=257:raise ValueError('路径重定位不是AArch64 ABS64')
            target=tables[ti][info>>32];targetsec=sh[target[1]];offset=target[2]+addend
            if not target[1] or offset<0 or offset>=targetsec[5]:raise ValueError('路径目标越界')
            buf=data[targetsec[4]+offset:targetsec[4]+targetsec[5]];end=buf.find(b'\0')
            if end<0:raise ValueError('路径无终止符')
            values.append(buf[:end].decode())
    if len(values)!=1:raise ValueError('路径重定位缺失/重复: '+name)
    return values[0]

def verify_alignment(work,prefix):
    gc=work/'gnutls-3.8.7/config.h';sc=work/'samba/bin/default/include/config.h';g=macros(gc.read_text());s=macros(sc.read_text())
    if g.get('HAVE_ICONV')!='1':raise ValueError('真实iconv探测未通过')
    if any(g.get(k)=='1' for k in ('HAVE_LIBBROTLI','HAVE_LIBZSTD')):raise ValueError('意外启用未锁定压缩依赖')
    if s.get('SAMBA_TARGET_OHOS')!='1' or 'DARWINOS' in s or 'LINUX' in s:raise ValueError('Samba目标平台探测污染')
    if 'HAVE_ETHTOOL' in s:raise ValueError('当前固定OHOS SDK不应启用未通过接口链接的ethtool')
    for k in ('USING_SYSTEM_COMPILE_ET','USING_SYSTEM_ASN1_COMPILE','SAMBA_SKIP_HOSTCC'):
        if s.get(k)!='1':raise ValueError('独立宿主生成器使用记录缺失: '+k)
    archive=prefix/'lib/libgnutls.a';data=archive.read_bytes();objects={}
    requirements={
      'accelerated.o': [('register_aarch64_crypto',False)],
      'aarch64-common.o':[('register_aarch64_crypto',True),('_gnutls_aes_gcm_aarch64',False),('_gnutls_sha_aarch64',False),('getauxval',False)],
      'aes-aarch64.o':[('aes_v8_encrypt',True)],
      'aes-gcm-aarch64.o':[('_gnutls_aes_gcm_aarch64',True),('gcm_ghash_v8',False)],
      'ghash-aarch64.o':[('gcm_ghash_v8',True)],
      'sha1-armv8.o':[('sha1_block_data_order',True)],
      'sha256-armv8.o':[('sha256_block_data_order',True)],
      'sha512-armv8.o':[('sha512_block_data_order',True)]}
    for name,checks in requirements.items():
        obj=archive_member(data,name);inv=elf_module().inventory(obj)
        for symbol,defined in checks:require_symbol(inv,symbol,defined)
        objects[name]={'sha256':sha(obj),'symbolChecksPassed':True}
    compress=archive_member(data,'compress.o');inv=elf_module().inventory(compress)
    if any(('Brotli' in v['name'] or 'ZSTD' in v['name'] or 'gnutls_brotli' in v['name'] or 'gnutls_zstd' in v['name']) for v in inv['symbols']):raise ValueError('compress.o引用了禁用的压缩算法')
    for name,prefix_name in [('brotlienc.o','gnutls_brotlienc'),('brotlidec.o','gnutls_brotlidec'),('zstd.o','gnutls_zstd')]:
        obj=archive_member(data,name);inv=elf_module().inventory(obj)
        for suffix in ('ensure_library','unload_library','is_usable'):require_symbol(inv,prefix_name+'_'+suffix,True)
        objects[name]={'sha256':sha(obj),'disabledCompressionWrapper':True}
    samba=prefix/'lib/libsmbclient.a';dyn=archive_member(samba.read_bytes(),'dynconfig.c.1.o')
    paths={name:elf_pointer_string(dyn,'dyn_'+name) for name in ('MODULESDIR','PRIVATE_DIR','LOCKDIR','CONFIGFILE')}
    if any(not v.startswith('/usr/local/samba/') or '/bin/default/' in v or '/.cache/' in v or '/out/' in v for v in paths.values()):raise ValueError('Samba运行路径泄漏构建树')
    return {'passed':True,'gnutlsHardwareAcceleration':objects,'iconvProbePassed':True,'compressionAlgorithmsEnabled':False,'sambaTarget':'ohos','ethtoolEnabled':False,'nativeGeneratorsExplicit':True,'runtimePaths':paths,'historicalRuntimePathsRestored':False,'inputs':{str(p):sha(p.read_bytes()) for p in (gc,sc,archive,samba)}}

def verify(work,prefix):
    gmp=work/'gmp-6.3.0/config.h';gnutls=work/'gnutls-3.8.7/config.h';archive=prefix/'lib/libgnutls.a';check_macros(gmp.read_text(),gnutls.read_text());obj=archive_member(archive.read_bytes(),'lt8-ecc.o');rows=curve_entries(obj);require_curves(rows)
    return {'schemaVersion':1,'passed':True,'targetAbi':'arm64-v8a','layout':'GnuTLS3.8.7-LP64-stride48','gmpNoAsm':True,'gmpParameterHeader':'generic','nonSuiteBCurves':True,'curveEntries':rows,'curveObjectSha256':sha(obj),'inputs':{str(p):sha(p.read_bytes()) for p in (gmp,gnutls,archive)},'configurationAlignment':verify_alignment(work,prefix),'deviceAcceptanceStatus':'pending'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True,type=Path);p.add_argument('--sysroot',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if a.output.exists():raise ValueError('拒绝覆盖已有能力证据')
    result=verify(a.work,a.sysroot);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('GMP NO_ASM/generic + GnuTLS NON_SUITEB/真实曲线表通过')
if __name__=='__main__':main()

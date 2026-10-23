#!/usr/bin/env python3
"""只读 AArch64 ELF64 节与符号审计；不以字节比较宣称行为等价。"""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def inventory(data):
    def span(off,size):
        if off<0 or size<0 or off+size>len(data):raise ValueError('truncated ELF')
        return data[off:off+size]
    if len(data)<64 or data[:7]!=b'\x7fELF\x02\x01\x01':raise ValueError('requires little-endian ELF64')
    h=struct.unpack('<16sHHIQQQIHHHHHH',data[:64])
    if h[2]!=183:raise ValueError('requires AArch64')
    shoff,entsize,count,namesidx=h[6],h[11],h[12],h[13]
    if entsize!=64 or not count or namesidx>=count:raise ValueError('unsupported section table')
    raw=[struct.unpack('<IIQQQQIIQQ',span(shoff+i*64,64)) for i in range(count)]
    names=span(raw[namesidx][4],raw[namesidx][5])
    def string(table,off):
        if off>=len(table):raise ValueError('bad string offset')
        end=table.find(b'\0',off)
        if end<0:raise ValueError('unterminated string')
        return table[off:end].decode('utf-8','replace')
    sections={};symbols=[]
    for idx,s in enumerate(raw):
        name=string(names,s[0]);payload=b'' if s[1]==8 else span(s[4],s[5])
        if idx:
            if name in sections:raise ValueError('duplicate section names unsupported')
            sections[name]={'type':s[1],'flags':s[2],'address':s[3],'size':s[5],'allocated':bool(s[2]&2),'sha256':None if s[1]==8 else hashlib.sha256(payload).hexdigest()}
        if s[1] in (2,11):
            if s[6]>=count or s[9]!=24 or s[5]%24:raise ValueError('bad symbol table')
            link=raw[s[6]];strings=span(link[4],link[5])
            for pos in range(0,len(payload),24):
                n,info,other,section,value,size=struct.unpack('<IBBHQQ',payload[pos:pos+24])
                symbol=string(strings,n)
                if symbol:symbols.append({'name':symbol,'table':name,'bind':info>>4,'type':info&15,'visibility':other&3,'sectionIndex':section,'value':value,'size':size})
    return {'sha256':hashlib.sha256(data).hexdigest(),'size':len(data),'sections':sections,'symbols':symbols}


def compare(a,b):
    changed=[];allocated=[]
    for name in sorted(a['sections'].keys()|b['sections'].keys()):
        x=a['sections'].get(name);y=b['sections'].get(name)
        # Addresses are reported separately: payload equality alone is not layout equality.
        if x!=y:
            changed.append(name)
            if (x and x['allocated']) or (y and y['allocated']):allocated.append(name)
    def exports(inv):
        return {s['name']:(s['bind'],s['type'],s['visibility'],s['size']) for s in inv['symbols'] if s['table']=='.dynsym' and s['sectionIndex'] and s['bind'] in (1,2)}
    ea,eb=exports(a),exports(b)
    return {'sameFile':a['sha256']==b['sha256'],'changedSections':changed,'changedAllocatedSections':allocated,'sectionDetails':{n:{'a':a['sections'].get(n),'b':b['sections'].get(n)} for n in changed},'exportedNamesAdded':sorted(eb.keys()-ea.keys()),'exportedNamesRemoved':sorted(ea.keys()-eb.keys()),'exportedMetadataChanged':sorted(n for n in ea.keys()&eb.keys() if ea[n]!=eb[n]),'behaviorEquivalenceProven':False}


def main():
    p=argparse.ArgumentParser();p.add_argument('a',type=Path);p.add_argument('b',type=Path);p.add_argument('--output',required=True,type=Path);args=p.parse_args()
    args.output.write_text(json.dumps({'a':str(args.a.resolve()),'b':str(args.b.resolve()),**compare(inventory(args.a.read_bytes()),inventory(args.b.read_bytes()))},indent=2)+'\n')

if __name__=='__main__':main()

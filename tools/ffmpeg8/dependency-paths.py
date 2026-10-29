#!/usr/bin/env python3
"""规范开发元数据中的临时路径；不改已编译对象或 ABI 声明。"""
from pathlib import Path
import argparse,re

def normalize(prefix,work):
    for pc in (prefix/'lib/pkgconfig').glob('*.pc'):
        text=pc.read_text();text=re.sub(r'^prefix=.*$',r'prefix=${pcfiledir}/../..',text,flags=re.M)
        # libtasn1 等 release pc 可能在 private flags 内直接展开 prefix。
        text=text.replace(str(prefix),'${prefix}');pc.write_text(text)
    header=prefix/'include/gmp.h';lines=header.read_text().splitlines(True)
    for i,line in enumerate(lines):
        if line.startswith(('#define __GMP_CC ','#define __GMP_CFLAGS ')):
            lines[i]=line.replace(str(prefix),'/opt/ohcodec-deps').replace(str(work),'/usr/src/ohcodec-deps')
    header.write_text(''.join(lines))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prefix',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();normalize(a.prefix,a.work)

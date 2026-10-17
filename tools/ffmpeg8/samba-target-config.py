#!/usr/bin/env python3
"""修正Samba4.20.7宿主/目标探测边界；不伪造目标运行能力。"""
import argparse
from pathlib import Path

def patch_platform(text):
    old='host_os = sys.platform'
    if text.count(old)!=2:raise ValueError('Samba平台探测位置变化')
    new="host_os = ('ohos' if conf.env.CROSS_COMPILE and conf.CHECK_CODE('\\n#ifndef __OHOS__\\n#error not OpenHarmony target\\n#endif\\n', 'SAMBA_TARGET_OHOS', addmain=True, msg='Checking target compiler is OpenHarmony') else sys.platform)"
    return text.replace(old,new)

def patch_replace(text):
    old="if sys.platform.rfind('linux') > -1:"
    if text.count(old)!=1:raise ValueError('libreplace平台探测位置变化')
    new="if sys.platform.rfind('linux') > -1 and not (conf.env.CROSS_COMPILE and conf.CHECK_CODE('\\n#ifndef __OHOS__\\n#error not OpenHarmony target\\n#endif\\n', 'SAMBA_TARGET_OHOS', addmain=True, add_headers=False, msg='Checking libreplace target compiler is OpenHarmony')):"
    return text.replace(old,new)

def patch_socket(text):
    old="        conf.DEFINE('HAVE_ETHTOOL', 1)"
    if text.count(old)!=1:raise ValueError('Samba ethtool探测位置变化')
    new="""        conf.CHECK_CODE('struct ethtool_cmd command = {0}; return (int)ethtool_cmd_speed(&command);',
                        'HAVE_ETHTOOL', headers='linux/sockios.h linux/ethtool.h',
                        addmain=True, link=True, cflags='-Werror=implicit-function-declaration',
                        msg='Checking usable ethtool_cmd_speed')"""
    return text.replace(old,new)

def patch(source):
    for rel,fn in [('source3/wscript',patch_platform),('lib/socket/wscript',patch_socket),('lib/replace/wscript',patch_replace)]:
        p=source/rel;p.write_text(fn(p.read_text()))
    # 工具已经在独立native树构建并复制，先验证存在，再记录实际使用；不是目标库能力宏。
    p=source/'third_party/heimdal_build/wscript_configure';s=p.read_text()
    s+='''\n# Frozen native generators supplied before target configure.
if conf.env.CROSS_COMPILE:
    import os
    for tool in ('compile_et', 'asn1_compile'):
        executable = os.path.join(conf.srcnode.abspath(), 'bin', tool)
        if not os.path.isfile(executable) or not os.access(executable, os.X_OK):
            conf.fatal('Missing prebuilt native generator: ' + tool)
    conf.DEFINE('USING_SYSTEM_COMPILE_ET', 1)
    conf.DEFINE('USING_SYSTEM_ASN1_COMPILE', 1)
    conf.DEFINE('SAMBA_SKIP_HOSTCC', 1)
''';p.write_text(s)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);a=p.parse_args();patch(a.source)
if __name__=='__main__':main()

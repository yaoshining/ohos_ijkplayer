#!/usr/bin/env python3
"""正式 SDK 失败关闭门禁；不会把诊断构建或缓存闭包当正式产物。"""
import argparse
import json
from pathlib import Path
import sys

def failures(sdk,repeat,inputs):
    errors=[]
    if sdk.get('artifactKind')!='source-build':errors.append('正式 SDK 必须来自源码构建')
    deps=sdk.get('staticDependencies',{})
    if deps.get('fullyVerified') is not True or deps.get('rebuiltFromSource') is not True:errors.append('静态依赖完整源码闭包未验证，禁止正式 SDK')
    if repeat.get('allMatch') is not True or repeat.get('libraryCount')!=6:errors.append('两次 clean 六库字节一致性未通过')
    for key in ('sourceArchiveVerified','patchesVerified','toolchainArchiveVerified','hostToolsVerified'):
        if inputs.get(key) is not True:errors.append(f'输入门禁未通过: {key}')
    return errors

def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--repeat',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    errors=failures(*[json.loads(x.read_text()) for x in (a.manifest,a.repeat,a.inputs)])
    a.report.write_text(json.dumps({'formalArtifactAllowed':not errors,'errors':errors,'deviceAcceptanceStatus':'pending'},ensure_ascii=False,indent=2)+'\n')
    if errors:print('\n'.join(errors),file=sys.stderr);sys.exit(1)
if __name__=='__main__':main()

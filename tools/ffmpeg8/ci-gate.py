#!/usr/bin/env python3
"""正式 SDK 失败关闭门禁；不会把诊断构建或缓存闭包当正式产物。"""
import argparse
import importlib.util
import hashlib
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

def release_failures(lock,sdk):
    errors=[]
    if lock.get('formalReleaseAllowed') is not True:errors.append('当前来源 profile 只允许验证，不允许正式发布或基线替换')
    if lock.get('toolchain',{}).get('historicalToolchainIdentityProven') is not True:errors.append('历史工具链身份未证明')
    if sdk.get('deviceAcceptanceStatus')!='passed':errors.append('设备验收未通过')
    return errors

def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--repeat',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--manifest-sha256',required=True);p.add_argument('--second-sdk',type=Path,required=True);p.add_argument('--second-manifest-sha256',required=True);p.add_argument('--input-root',type=Path,required=True);p.add_argument('--verification-only',action='store_true');a=p.parse_args()
    def module(name):
        spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    producer=module('producer-sdk');compare=module('compare-sdks')
    sdk=producer.verify_manifest(a.manifest.parent,a.manifest_sha256)
    producer.verify_manifest(a.second_sdk,a.second_manifest_sha256)
    actual=compare.compare(a.manifest.parent,a.second_sdk)
    if actual!=json.loads(a.repeat.read_text()):raise ValueError('FFmpeg 重复性报告与实际 SDK 不符')
    inputs=json.loads(a.inputs.read_text());lock=json.loads(Path(__file__).with_name('producer-inputs.lock.json').read_text())
    inputs['sourceArchiveVerified']=producer.sha(a.input_root/'ffmpeg-source.tar')==lock['ffmpeg']['gitArchiveSha256']
    inputs['toolchainArchiveVerified']=producer.sha(a.input_root/'toolchain.tar.gz')==lock['toolchain']['sha256']
    # verify_manifest 已重算并校验闭包证据；不使用输入 JSON 自报的宿主布尔字段。
    inputs['hostToolsVerified']=sdk['staticDependencies'].get('newSourceClosureVerified') is True
    inputs['patchesVerified']={Path(r['path']).name:r['sha256'] for r in sdk['patches']}=={Path(n).name:h for n,h in producer.LOCK['patches'].items()}
    errors=failures(sdk,actual,inputs)
    release_errors=release_failures(lock,sdk)
    a.report.write_text(json.dumps({'sourceVerificationPassed':not errors,'formalArtifactAllowed':not errors and not release_errors,'errors':errors,'releaseBlockers':release_errors,'deviceAcceptanceStatus':'pending'},ensure_ascii=False,indent=2)+'\n')
    if not a.verification_only:errors+=release_errors
    if errors:print('\n'.join(errors),file=sys.stderr);sys.exit(1)
if __name__=='__main__':main()

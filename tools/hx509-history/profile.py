#!/usr/bin/env python3
"""HX509 历史诊断：只能显式选择；仅在新 recipe/Samba 树生效。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import waf_select

HERE = Path(__file__).resolve().parent
RECIPE = ['build-libsmbclient.sh', 'fetch-sources.py', 'dependency-sources.lock.json',
          'dependency-paths.py', 'generator-lock.py', 'verify-dependency-features.py',
          'elf-audit.py', 'samba-target-config.py', 'host-lock.py', 'run-dependency-build.py', 'dependency-repeat.py']
INPUTS = {'third_party/heimdal/lib/hx509/sel-gram.y':'658ce001018b872ba914a47a076483a2c0293afac09a5d3ae698e1720278ba43',
          'third_party/heimdal/lib/hx509/sel-lex.l':'d33805413141548f8ef3fe843f284e23ac1ea3edac88556ba7cadaaa2f400880'}
MODULES = {'third_party/waf/waflib/Tools/bison.py':'25701d3b92ca62994f31ebb965657c49670f9f84c57aae0c676026adb6a70f20',
           'buildtools/wafsamba/samba_waf18.py':'3c131a4c4d49af508aa8dd0b8de1f351767bf0a726105347999612c62778ecb7'}
EXPECTED = {'sel-gram.tab.c':'cabc0ce2710b7a26508b47934710a5a07d87a0a2f336bfde64cddae8d557dd18',
            'sel-gram.tab.h':'5c2e827b6f9e35e7845b8601327e09a7066bdb858515586248a18cd52bec51c2',
            'sel-lex.lex.c':'c5a76e4a4e4078eba9c1e04ac6a060dc7db934077d34a978c61ac06eed4d07a4'}
sha = waf_select.sha


def require_profile(value):
    if value != 'hx509-history':
        raise ValueError('必须显式选择 hx509-history')
    return value


def pins(paths):
    return [{'path':str(Path(p).resolve()), 'sha256':sha(p), 'sizeBytes':Path(p).stat().st_size} for p in paths]


def materialize(base, dest, profile):
    require_profile(profile)
    if dest.exists():
        raise ValueError('拒绝复用 recipe 目录')
    dest.mkdir(parents=True)
    for name in RECIPE:
        shutil.copy2(base / name, dest / name)
    shutil.copy2(HERE / 'profile.py', dest / 'hx509-profile.py')
    shutil.copy2(HERE / 'waf_select.py', dest / 'waf_select.py')
    p = dest / 'build-libsmbclient.sh'; text = p.read_text()
    anchor = '\n  configure_samba\n'
    if text.count(anchor) != 1:
        raise ValueError('默认 recipe 锚点不唯一')
    hook = '\n  PYTHONDONTWRITEBYTECODE=1 python3 "$SCRIPT_DIR/hx509-profile.py" apply --profile hx509-history --source "$SAMBA_DIR" --descriptor "$WORK_DIR/../../generators/descriptor.json"\n'
    p.write_text(text.replace(anchor, hook + anchor))


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Waf 补丁锚点不唯一')
    return text.replace(old, new)


def apply(source, descriptor, profile):
    require_profile(profile); source = source.resolve()
    binding = json.loads(descriptor.read_text()); waf_select.verify(binding)
    for rel, digest in {**INPUTS, **MODULES}.items():
        if sha(source / rel) != digest:
            raise ValueError('Samba 输入或 Waf 模块不符: ' + rel)
    dest = source / 'buildtools/wafsamba'
    if (dest / 'hx509-binding.json').exists():
        raise ValueError('拒绝重复应用 profile')
    binding.update(sourceRoot=str(source), expected=EXPECTED, evidence=str(descriptor.parent / 'tasks'))
    binding['files'] += pins(source / p for p in INPUTS)
    bison = source / 'third_party/waf/waflib/Tools/bison.py'
    flex = dest / 'samba_waf18.py'
    old_bison = bison.read_text(); old_flex = flex.read_text()
    new_bison = replace_once(old_bison, 'from waflib import Task', 'from waflib import Task\nfrom hx509_select import select_env, finish')
    new_bison = replace_once(new_bison, '\ttsk.cwd = node.parent.get_bld()', '\ttsk.cwd = node.parent.get_bld()\n\tselect_env(tsk, "bison")')
    new_bison += '\n_original_hx509_bison_run = bison.run\ndef _hx509_bison_run(task):\n\tselect_env(task, "bison")\n\tstatus = _original_hx509_bison_run(task)\n\tif not status: finish(task, "bison")\n\treturn status\nbison.run = _hx509_bison_run\n'
    new_flex = replace_once(old_flex, '    env = tsk.env\n', '    from hx509_select import select_env, finish\n    env = select_env(tsk, "flex")\n')
    anchor = "    tsk.outputs[0].write(txt.replace('\\r\\n', '\\n').replace('\\r', '\\n')) # issue #1207"
    new_flex = replace_once(new_flex, anchor, anchor + '\n    finish(tsk, "flex")')
    import difflib
    evidence = descriptor.parent / 'apply'; evidence.mkdir()
    for p, old, new in [(bison, old_bison, new_bison), (flex, old_flex, new_flex)]:
        (evidence / (p.name + '.patch')).write_text(''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile=str(p), tofile=str(p))))
        p.write_text(new)
    (dest / 'hx509-binding.json').write_text(json.dumps(binding, indent=2) + '\n')
    helper = (HERE / 'waf_select.py').read_text() + '\nBINDING_SHA256 = ' + repr(sha(dest / 'hx509-binding.json')) + '\n'
    (dest / 'hx509_select.py').write_text(helper)
    (evidence / 'record.json').write_text(json.dumps({'descriptor':pins([descriptor]),'inputs':INPUTS,'modulesBefore':MODULES,'outputs':pins([bison,flex,dest/'hx509-binding.json',dest/'hx509_select.py'])},indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(); p.add_argument('command',choices=['apply']); p.add_argument('--profile',required=True)
    p.add_argument('--source',type=Path,required=True); p.add_argument('--descriptor',type=Path,required=True)
    a=p.parse_args(); apply(a.source,a.descriptor,a.profile)

if __name__=='__main__': main()

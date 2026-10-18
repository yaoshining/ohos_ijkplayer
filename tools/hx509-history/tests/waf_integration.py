#!/usr/bin/env python3
"""普通生成流程集成检查：执行实际 Waf bison.run 与 Samba flexfun。"""
import argparse, ast, importlib.util, json, os, shutil, sys, tempfile, types
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import profile as hp

def exercise(source, descriptor, output):
    output=output.resolve();source=source.resolve();descriptor=descriptor.resolve()
    output.mkdir(parents=True)
    s=output/'samba'; s.mkdir()
    for rel in list(hp.INPUTS)+list(hp.MODULES):
        p=s/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/rel,p)
    # Waf itself remains unmodified except the actual bison module being tested.
    shutil.copytree(source/'third_party/waf/waflib',s/'third_party/waf/waflib',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
    d=output/'descriptor.json';shutil.copy2(descriptor,d);hp.apply(s,d,'hx509-history')
    sys.path.insert(0,str(s/'third_party/waf'));sys.path.insert(0,str(s/'buildtools/wafsamba'))
    from waflib import Context, Node, ConfigSet, Logs
    Logs.init_log()
    from waflib.Tools.bison import bison
    ctx=Context.Context();cwd=output/'generated';cwd.mkdir();ctx.variant_dir=str(cwd)
    def node(p):
        n=types.SimpleNamespace(abspath=lambda:str(p),path_from=lambda base:str(p),name=p.name)
        n.write=lambda text:Node.Node.write(n,text)
        return n
    env=ConfigSet.ConfigSet();env.env=dict(os.environ);env.BISON=['not-used'];env.BISONFLAGS=['-d'];env.FLEX=['not-used'];env.FLEXFLAGS=['-t'];env.FLEX_MSYS=False
    gen=types.SimpleNamespace(bld=ctx)
    t=bison(env=env,generator=gen);t.inputs=[node(s/'third_party/heimdal/lib/hx509/sel-gram.y')];t.outputs=[node(cwd/'sel-gram.tab.c'),node(cwd/'sel-gram.tab.h')];t.get_cwd=lambda:node(cwd)
    assert t.run()==0
    tree=ast.parse((s/'buildtools/wafsamba/samba_waf18.py').read_text());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='flexfun')
    scope={'os':os};exec(compile(ast.Module(body=[f],type_ignores=[]),str(s/'buildtools/wafsamba/samba_waf18.py'),'exec'),scope)
    t=types.SimpleNamespace(env=env,generator=gen,inputs=[node(s/'third_party/heimdal/lib/hx509/sel-lex.l')],outputs=[node(cwd/'sel-lex.lex.c')],get_cwd=lambda:node(cwd))
    scope['flexfun'](t)
    assert env.BISON==['not-used'] and env.FLEX==['not-used']
    binding=json.loads((s/'buildtools/wafsamba/hx509-binding.json').read_text())
    assert all(hp.sha(cwd/n)==v for n,v in binding['expected'].items())
    print('实际 Waf 两任务输出、私有环境和默认工具隔离检查通过')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--descriptor',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();exercise(a.source,a.descriptor,a.output)

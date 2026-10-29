from pathlib import Path
import ast,difflib,json
from input_gate import inventory,verify_tree,sha
R=Path(__file__).resolve().parents[1];P=R/'source-package';verify_tree(P/'source',json.loads((P/'source-original.json').read_text()),source=True)
patches=P/'patches';patches.mkdir()
for rel in ['shaderc/utils/update_build_version.py','shaderc/third_party/spirv-tools/utils/update_build_version.py']:
 p=P/'source'/rel;old=p.read_text();node=next(n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef) and n.name=='describe');arg=node.args.args[0].arg
 body='''def describe(%s):
    # Phase18: source identity is a locked build input, never ambient Git/time.
    marker = os.path.join(%s, '.phase18-source-version')
    try:
        with open(marker) as source: value = source.read()
    except OSError as error:
        raise RuntimeError('Missing fixed source version: ' + marker) from error
    if not re.fullmatch(r'[0-9a-f]{40}\\n', value):
        raise RuntimeError('Invalid fixed source version: ' + marker)
    return value.strip()
'''%(arg,arg)
 lines=old.splitlines(keepends=True);new=''.join(lines[:node.lineno-1])+body+''.join(lines[node.end_lineno:]);new=new.replace('os.getenv("FORCED_BUILD_VERSION_DESCRIPTION", describe(repo_path))','describe(repo_path)')
 p.write_text(new);(patches/(rel.replace('/','_')+'.patch')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),'a/'+rel,'b/'+rel)))
for c in json.loads((R/'research/shaderc/recipe.json').read_text())['components']:
 (P/'source/shaderc'/c['extractRelative']/'.phase18-source-version').write_text(c['commit']+'\n')
rows=inventory(P/'source');verify_tree(P/'source',rows,source=True);(P/'source-final.json').write_text(json.dumps(rows,indent=2)+'\n')
(R/'locks/source-lock.json').write_text(json.dumps({'sources':str(P/'source-final.json'),'sourcesSHA256':sha(P/'source-final.json'),'originsSHA256':sha(P/'source-origins.json'),'patches':inventory(patches),'oldHistoricalCacheFullyVerified':False},indent=2)+'\n')

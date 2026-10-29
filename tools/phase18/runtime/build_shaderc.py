from pathlib import Path
import json,os,subprocess,sys,shutil,time
from input_gate import sha,inventory,verify_tree,require_fresh
R=Path(__file__).resolve().parents[1];P=R/'source-package';RUN=require_fresh(Path(sys.argv[1]));RUN.mkdir(parents=True)
tools=json.loads((R/'locks/tools-before.json').read_text());S=Path(tools['SDK'])
for row in tools['tools']:
 if sha(row['path'])!=row['sha256']:raise ValueError('tool drift '+row['path'])
for x in ['logs','home','tmp','cache','prefix/lib/pkgconfig','prefix/include/shaderc']:(RUN/x).mkdir(parents=True,exist_ok=True)
shutil.copytree(P/'source/shaderc',RUN/'source');SRC=RUN/'source';BUILD=RUN/'build';PREFIX=RUN/'prefix'
rows=[{**v,'path':v['path'][len('shaderc/'):]} for v in json.loads((P/'source-final.json').read_text()) if v['path'].startswith('shaderc/')];verify_tree(SRC,rows,source=True)
env={'PATH':':'.join([str(S/'build-tools/cmake/bin'),str(Path(sys.executable).parent),str(S/'llvm/bin'),'/usr/bin','/bin']),'HOME':str(RUN/'home'),'TMPDIR':str(RUN/'tmp'),'XDG_CACHE_HOME':str(RUN/'cache'),'LANG':'C','LC_ALL':'C','TZ':'UTC','SOURCE_DATE_EPOCH':'1760000000','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','GIT_CEILING_DIRECTORIES':str(RUN),'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':os.devnull,'GIT_OPTIONAL_LOCKS':'0'}
recipe=json.loads((R/'research/shaderc/recipe.json').read_text());repl={'${SDK}':str(S),'${SRC}':str(SRC),'${BUILD}':str(BUILD),'${PREFIX}':'/usr/local','${PYTHON}':sys.executable}
def render(s):
 for k,v in repl.items():s=s.replace(k,v)
 return s
commands=[]
def run(name,argv):
 start=time.time()
 with (RUN/'logs'/(name+'.log')).open('w') as out:p=subprocess.run(list(map(str,argv)),env=env,cwd=RUN,stdout=out,stderr=subprocess.STDOUT)
 commands.append({'name':name,'argv':list(map(str,argv)),'environment':env,'cwd':str(RUN),'returncode':p.returncode,'elapsedSeconds':time.time()-start});(RUN/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');print(name,p.returncode,flush=True)
 if p.returncode:raise RuntimeError(name)
(RUN/'input-binding.json').write_text(json.dumps({'sourceLockSHA256':sha(R/'locks/source-lock.json'),'toolLockSHA256':sha(R/'locks/tools-before.json'),'recipeSHA256':sha(R/'research/shaderc/recipe.json'),'scriptSHA256':sha(__file__)},indent=2)+'\n')
for stage in ['configure','build']:
 c=recipe[stage];cmd=[render(c['executable']),*[render(v) for v in c['args']]]
 if stage=='configure':cmd+=['-DCMAKE_C_FLAGS=-fmacro-prefix-map='+str(RUN)+'=.','-DCMAKE_CXX_FLAGS=-fmacro-prefix-map='+str(RUN)+'=.']
 run(stage,cmd)
run('deps',[S/'build-tools/cmake/bin/ninja','-C',BUILD,'-t','deps']);run('commands',[S/'build-tools/cmake/bin/ninja','-C',BUILD,'-t','commands','shaderc_combined'])
repl['${PREFIX}']=str(PREFIX);installed=[]
for rec in recipe['install']:
 src=Path(render(rec['from']));dest=Path(render(rec['to']));shutil.copyfile(src,dest)
 if dest.suffix=='.pc':dest.write_text(dest.read_text().replace('prefix=/usr/local','prefix=${pcfiledir}/../..'))
 installed.append({'source':str(src),'sourceSHA256':sha(src),'installed':str(dest),'installedSHA256':sha(dest)})
(RUN/'install-binding.json').write_text(json.dumps(installed,indent=2)+'\n');(RUN/'prefix-files.json').write_text(json.dumps(inventory(PREFIX),indent=2)+'\n');verify_tree(SRC,rows,source=True);print('Shaderc complete',flush=True)

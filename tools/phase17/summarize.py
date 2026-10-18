from pathlib import Path
import json,sys,os,platform,hashlib
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE/'repeat'))
from repro_gate import compare_runs
from ci_contract import validate_claim
from compile_inputs import collect_compile_inputs,compare_compile_inputs
out=HERE.parents[1]/'out/phase17-ci';roots=[out/'clean-a',out/'longer-ci-absolute-directory/clean-b'];summaries=[json.loads((p/'run-summary.json').read_text())for p in roots];comparison=compare_runs(*summaries);(out/'comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
compiler_inputs=[]
for root in roots:
 evidence=collect_compile_inputs(root,out/'sdk');(root/'compile-inputs.json').write_text(json.dumps(evidence,indent=2)+'\n');compiler_inputs.append(evidence)
compiler_comparison=compare_compile_inputs(*compiler_inputs);(out/'compile-input-comparison.json').write_text(json.dumps(compiler_comparison,indent=2)+'\n');assert compiler_comparison['passed'],'actual compiler input mismatch'
report={'runUrl':os.environ['GITHUB_SERVER_URL']+'/'+os.environ['GITHUB_REPOSITORY']+'/actions/runs/'+os.environ['GITHUB_RUN_ID'],'commit':os.environ['GITHUB_SHA'],'platform':platform.system(),'runner':'ubuntu-22.04','coverage':'actual-cross-build','compileInputComparisonPassed':compiler_comparison['passed'],'comparisonPassed':comparison['passed'],'runs':[],'formalArtifactAllowed':False,'deviceAcceptanceStatus':'pending'}
for p,s in zip(roots,summaries):
 commands=json.loads((p/'commands.json').read_text());report['runs'].append({'root':str(p),'fresh':s['freshRootVerified'],'artifactSha256':s['artifactHashes']['mpv'],'libplaceboSha256':s['artifactHashes']['libplacebo'],'steps':{c['name']:c['returncode']for c in commands}})
(out/'ci-result.json').write_text(json.dumps(report,indent=2)+'\n');validate_claim(report);print(json.dumps(report,indent=2))

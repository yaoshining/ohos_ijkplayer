from pathlib import Path
import json,sys,hashlib,subprocess
HERE=Path(__file__).resolve().parent;R=HERE.parents[1]/'out/phase18-ci';sys.path.insert(0,str(R/'integration/runtime'));from feature_gate import check_run
expected=json.loads((R/'integration/expected-features.json').read_text());results=[]
for name in ['origin-a','longer-ci-absolute-directory/origin-b']:
 run=R/'integration/runs'/name;v=check_run(run,expected);(run/'feature-comparison.json').write_text(json.dumps(v,indent=2)+'\n');results.append({'run':name,'featuresMatched':sum(len(x) for x in v['features'].values())})
subprocess.run([sys.executable,'-B',str(R/'integration/runtime/compare_runs.py'),'--run-a',str(R/'integration/runs/origin-a'),'--run-b',str(R/'integration/runs/longer-ci-absolute-directory/origin-b'),'--output',str(R/'integration/comparison.json')],check=True)
for n,run in enumerate(['origin-a','longer-ci-absolute-directory/origin-b']):
 subprocess.run([sys.executable,'-B',str(R/'integration/runtime/compile_inputs.py'),'collect','--run-root',str(R/'integration/runs'/run),'--sdk',str(R/'sdk'),'--output',str(R/'integration'/('compile-inputs-'+str(n)+'.json'))],check=True)
subprocess.run([sys.executable,'-B',str(R/'integration/runtime/compile_inputs.py'),'compare','--a',str(R/'integration/compile-inputs-0.json'),'--b',str(R/'integration/compile-inputs-1.json'),'--output',str(R/'integration/compile-inputs-comparison.json')],check=True)
# All ten actual link inputs must match this CI's newly built staged archives.
orig=json.loads((R/'integration/input-package/provenance/new-dependencies.json').read_text());archives={v['packagePath'].removeprefix('deps/'):v['packageSHA256'] for v in orig if v['packagePath'].endswith('.a')};assert len(archives)==10
for run in ['origin-a','longer-ci-absolute-directory/origin-b']:
 inputs=json.loads((R/'integration/runs'/run/'link-inputs.json').read_text());actual={v['path'].removeprefix('run/deps/'):v['sha256'] for v in inputs if v['path'].startswith('run/deps/') and v['path'].endswith('.a')};assert actual==archives
for rel in ['integration/input-package/package.json','source-package/source-final.json','locks/tools-before.json']:
 assert (R/rel).is_file()
subprocess.run([sys.executable,'-B',str(HERE/'verify_evidence.py')],check=True)
(R/'phase18-verification.json').write_text(json.dumps({'allPassed':True,'features':results,'newDependenciesLinked':10,'formalArtifactAllowed':False,'deviceAcceptanceStatus':'pending','oldHistoricalCacheFullyVerified':False,'provenanceScope':'new source builds only; Rust compiler/std and SDK remain prebuilt tool/platform boundaries'},indent=2)+'\n')

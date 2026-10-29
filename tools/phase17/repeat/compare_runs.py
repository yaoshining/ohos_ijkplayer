#!/usr/bin/env python3
from pathlib import Path
import argparse,json,sys
from repro_gate import compare_runs
p=argparse.ArgumentParser();p.add_argument('--run-a',type=Path,required=True);p.add_argument('--run-b',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
a=json.loads((args.run_a/'run-summary.json').read_text());b=json.loads((args.run_b/'run-summary.json').read_text());result=compare_runs(a,b)
result.update({'runA':str(args.run_a.resolve()),'runB':str(args.run_b.resolve()),'artifactHashesA':a['artifactHashes'],'artifactHashesB':b['artifactHashes'],'differentAllocatedSections':[k for k in a['allocatedSections'] if a['allocatedSections'][k]!=b['allocatedSections'].get(k)],'linkInputCountA':len(a['linkInputs']),'linkInputCountB':len(b['linkInputs']),'archiveMembersA':len(a['archiveMembers']),'archiveMembersB':len(b['archiveMembers'])})
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)

from pathlib import Path
import argparse,json,os,sys
from engine import execute
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--allow-dirty',action='store_true');a=p.parse_args();here=Path(__file__).resolve().parent;repo=here.parents[1]
rows=json.loads((here/'commands.json').read_text())['commands'];commands=[(r['name'],[sys.executable if x=='{python}' else x for x in r['argv']]) for r in rows]
passed=execute(repo,a.out,commands,os.environ,allow_dirty=a.allow_dirty)
print('PASS' if passed else 'FAIL');raise SystemExit(0 if passed else 1)

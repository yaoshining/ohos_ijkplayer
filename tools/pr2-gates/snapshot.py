"""为既有真实构建绑定输入与合并身份；不发布二进制。"""
from pathlib import Path
import argparse
import json
import os
import sys
from engine import identity, inventory, write, collect, failure_package

parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=['begin', 'end'])
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--job-status', default='success', choices=['success', 'failure', 'cancelled'])
args = parser.parse_args()
repo = Path(__file__).resolve().parents[2]
out = args.out.resolve()
if out.is_relative_to(repo):
    raise ValueError('snapshot outside checkout required')
if args.mode == 'begin':
    if out.exists():
        raise ValueError('snapshot output already exists')
    out.mkdir(parents=True)
    for name in ['identity.json', 'input-before.json', 'input-after.json']:
        write(out / name, {'captureError': 'not yet captured'})
    try:
        ident = identity(repo, os.environ)
        write(out / 'identity.json', ident)
        write(out / 'input-before.json', inventory(repo))
    except Exception as error:
        write(out / 'result.json', {'accepted': False, 'error': str(error), 'formalArtifactAllowed': False})
        collect(out)
        raise SystemExit(1)
else:
    passed = False
    result = {'accepted': False, 'jobStatus': args.job_status, 'inputsUnchanged': False,
              'identityUnchanged': False, 'formalArtifactAllowed': False,
              'scope': 'existing job identity; build success also requires original commands and validation'}
    out.mkdir(parents=True, exist_ok=True)
    for name in ['identity.json', 'input-before.json', 'input-after.json']:
        if not (out / name).exists():
            write(out / name, {'captureError': 'begin did not complete'})
    try:
        before = json.loads((out / 'input-before.json').read_text())
        ident = json.loads((out / 'identity.json').read_text())
        after = inventory(repo)
        write(out / 'input-after.json', after)
        current = identity(repo, os.environ)
        write(out / 'identity-after.json', current)
        result['inputsUnchanged'] = before == after
        result['identityUnchanged'] = ident == current
        passed = result['inputsUnchanged'] and result['identityUnchanged'] and args.job_status == 'success'
    except Exception as error:
        result['error'] = str(error)
    result['accepted'] = passed
    write(out / 'result.json', result)
    try:
        collect(out)
    except Exception as error:
        passed = False
        result['accepted'] = False
        result['collectionError'] = str(error)
        write(out / 'result.json', result)
        failure_package(out, error)
    raise SystemExit(0 if passed else 1)

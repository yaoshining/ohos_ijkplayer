"""绑定实际 checkout 输入，真实命令失败即拒绝；不操作设备。"""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import time


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def git(repo, *args):
    return subprocess.check_output(
        ['git', '--no-optional-locks', '-C', str(repo), *args], stderr=subprocess.STDOUT
    ).decode().strip()


def inventory(repo):
    repo = Path(repo)
    rows = {}
    for name in git(repo, 'ls-files', '--cached', '--others', '--exclude-standard', '-z').split('\0'):
        if not name:
            continue
        path = repo / name
        if path.is_symlink():
            data = os.readlink(path).encode()
            kind = 'symlink-target'
        elif path.is_file():
            data = path.read_bytes()
            kind = 'regular'
        else:
            raise ValueError('source input missing: ' + name)
        rows[name] = {'sha256': sha(data), 'bytes': len(data), 'kind': kind}
    return rows


def identity(repo, env, allow_dirty=False):
    ci = env.get('GITHUB_ACTIONS') == 'true'
    if ci and allow_dirty:
        raise ValueError('CI cannot use dirty-preview mode')
    head = git(repo, 'rev-parse', 'HEAD')
    parents = git(repo, 'show', '-s', '--format=%P', 'HEAD').split()
    status = git(repo, 'status', '--porcelain=v1', '--untracked-files=normal')
    if status and not allow_dirty:
        raise ValueError('dirty checkout: explicit local preview required')
    event = env.get('GITHUB_EVENT_NAME', 'local')
    claimed = env.get('GITHUB_SHA')
    if ci and not claimed:
        raise ValueError('CI SHA missing')
    if claimed and claimed != head:
        raise ValueError('event SHA is not actual tested HEAD')
    if event not in ['local', 'push', 'pull_request', 'workflow_dispatch', 'merge_group']:
        raise ValueError('unsupported event')
    result = {
        'testedHEAD': head, 'parents': parents, 'event': event, 'githubSHA': claimed,
        'exactCommitReplay': not bool(status), 'clean': not bool(status),
        'previewOnly': bool(status), 'formalArtifactAllowed': False, 'deviceExecuted': False,
        'runId': env.get('GITHUB_RUN_ID'), 'runAttempt': env.get('GITHUB_RUN_ATTEMPT'),
    }
    if event in ['pull_request', 'merge_group']:
        path = env.get('GITHUB_EVENT_PATH')
        if not path:
            raise ValueError('event payload missing')
        payload = json.loads(Path(path).read_text())
        if event == 'pull_request':
            pr = payload['pull_request']
            base, source = pr['base']['sha'], pr['head']['sha']
            if parents != [base, source]:
                raise ValueError('actual merge parents do not match PR base/head')
            result.update(pullRequestBase=base, pullRequestHead=source, testedMergeSHA=head)
        else:
            group = payload['merge_group']
            if group['head_sha'] != head:
                raise ValueError('merge group HEAD mismatch')
            base = group.get('base_sha', '')
            if not re.fullmatch('[0-9a-f]{40}', base):
                raise ValueError('merge group base missing or invalid')
            check = subprocess.run(
                ['git', '-C', str(repo), 'merge-base', '--is-ancestor', base, head],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            if check.returncode != 0:
                raise ValueError('merge group base is not a reachable ancestor')
            result.update(mergeGroupBase=base, testedMergeSHA=head)
    return result


def run_command(argv, log, cwd, timeout=600):
    start = time.monotonic()
    timed_out = False
    with Path(log).open('wb') as stream:
        stream.write(('COMMAND ' + json.dumps(list(map(str, argv))) + '\n').encode())
        stream.flush()
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', SPECIFY_FEATURE_NO_PERSIST='1')
        process = subprocess.Popen(
            list(map(str, argv)), cwd=cwd, env=env, stdout=stream,
            stderr=subprocess.STDOUT, start_new_session=True,
        )
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGKILL)
            code = process.wait()
    is_unittest = any(argv[i:i + 2] == ['-m', 'unittest'] for i in range(len(argv) - 1))
    counts = re.findall(r'^Ran (\d+) tests? in ', Path(log).read_text(errors='replace'), re.M)
    tests_run = int(counts[-1]) if counts else None
    passed = code == 0 and not timed_out and (not is_unittest or (tests_run is not None and tests_run > 0))
    return {
        'argv': list(map(str, argv)), 'returncode': code, 'timedOut': timed_out,
        'durationSeconds': round(time.monotonic() - start, 3), 'unittestCommand': is_unittest,
        'testsRun': tests_run if is_unittest else None, 'passed': passed,
    }


REQUIRED = {'identity.json', 'input-before.json', 'input-after.json', 'result.json'}


def clear_package(out):
    index = out / 'artifact-index.json'
    if index.exists() or index.is_symlink():
        index.unlink()
    artifact = out / 'artifact'
    if artifact.is_symlink():
        artifact.unlink()
        raise ValueError('artifact output cannot be symlink')
    if artifact.exists():
        if not artifact.is_dir():
            raise ValueError('artifact output is not a directory')
        shutil.rmtree(artifact)


def publish_package(out, names):
    rows = []
    for name in sorted(names):
        path = out / name
        if path.is_symlink() or not path.is_file() or path.suffix not in ['.json', '.log']:
            raise ValueError('unexpected artifact entry: ' + name)
        data = path.read_bytes()
        if len(data) > 20 * 1024 * 1024 or not data or b'\x00' in data:
            raise ValueError('empty/binary/oversized artifact: ' + name)
        data.decode('utf8')
        if path.suffix == '.json':
            json.loads(data)
        rows.append({'path': name, 'bytes': len(data), 'sha256': sha(data)})
    artifact = out / 'artifact'
    artifact.mkdir()
    for row in rows:
        shutil.copyfile(out / row['path'], artifact / row['path'])
    index = {'files': rows, 'formalArtifactAllowed': False}
    write(artifact / 'artifact-index.json', index)
    write(out / 'artifact-index.json', index)
    return rows


def collect(out):
    out = Path(out)
    clear_package(out)
    if not all((out / p).is_file() and not (out / p).is_symlink() for p in REQUIRED):
        raise ValueError('missing required gate evidence')
    return publish_package(out, [p.name for p in out.iterdir()])


def failure_package(out, error):
    # 收集失败后只发布 runner 自身的 JSON；被拒原件留在本地，不进入上传目录。
    clear_package(out)
    write(out / 'collection-error.json', {'error': str(error), 'accepted': False})
    return publish_package(out, REQUIRED | {'collection-error.json'})


def execute(repo, out, commands, env, allow_dirty=False, timeout=600):
    repo, out = Path(repo), Path(out)
    if not commands or len({row[0] for row in commands}) != len(commands):
        raise ValueError('empty/duplicate command plan')
    if any(not re.fullmatch('[a-z0-9-]+', name) or not argv for name, argv in commands):
        raise ValueError('invalid command name or argv')
    if out.exists():
        raise ValueError('output must be fresh')
    if out.resolve().is_relative_to(repo.resolve()):
        raise ValueError('gate output must be outside checkout')
    out.mkdir(parents=True)
    result = {
        'accepted': False, 'formalArtifactAllowed': False, 'deviceExecuted': False,
        'targetLibrariesBuilt': False, 'commands': [], 'inputsUnchanged': False,
        'identityUnchanged': False, 'exactCommitReplay': False,
    }
    for name in REQUIRED - {'result.json'}:
        write(out / name, {'captureError': 'not yet captured'})
    try:
        ident = identity(repo, env, allow_dirty)
        write(out / 'identity.json', ident)
        result['exactCommitReplay'] = ident['exactCommitReplay']
        before = inventory(repo)
        write(out / 'input-before.json', before)
        for name, argv in commands:
            row = run_command(argv, out / (name + '.log'), repo, timeout)
            row['name'] = name
            result['commands'].append(row)
        after = inventory(repo)
        write(out / 'input-after.json', after)
        result['inputsUnchanged'] = before == after
        final = identity(repo, env, allow_dirty)
        write(out / 'identity-after.json', final)
        result['identityUnchanged'] = ident == final
        result['accepted'] = (
            result['inputsUnchanged'] and result['identityUnchanged']
            and all(row['passed'] for row in result['commands'])
        )
    except Exception as error:
        result['error'] = str(error)
    write(out / 'result.json', result)
    try:
        collect(out)
    except Exception as error:
        result['accepted'] = False
        result['collectionError'] = str(error)
        write(out / 'result.json', result)
        failure_package(out, error)
    return result['accepted']

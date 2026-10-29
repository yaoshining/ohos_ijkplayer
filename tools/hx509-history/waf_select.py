"""仅 HX509 两个 Waf 任务使用独立、经校验的历史生成器。"""
import hashlib
import json
import os
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(binding):
    if binding.get('profile') != 'hx509-history' or not binding.get('files'):
        raise ValueError('无效的 HX509 绑定')
    for row in binding['files']:
        p = Path(row['path'])
        if not p.is_file() or sha(p) != row['sha256']:
            raise ValueError('HX509 输入或工具漂移: ' + str(p))
    for tree in binding.get('trees', []):
        actual = sorted(str(p.relative_to(tree['root'])) for p in Path(tree['root']).rglob('*') if p.is_file())
        if actual != tree['files']:
            raise ValueError('HX509 资源文件集合漂移')


def load_binding():
    path = Path(__file__).with_name('hx509-binding.json')
    # apply 写入的独立模块常量；绑定自身也不可漂移。
    if sha(path) != BINDING_SHA256:
        raise ValueError('HX509 绑定摘要漂移')
    return json.loads(path.read_text())


def selected(task, kind, binding):
    names = {'bison': 'sel-gram.y', 'flex': 'sel-lex.l'}
    return kind in names and len(task.inputs) == 1 and Path(task.inputs[0].abspath()).resolve() == (Path(binding['sourceRoot']) / 'third_party/heimdal/lib/hx509' / names[kind]).resolve()


def select_env(task, kind, binding=None):
    binding = binding if binding is not None else load_binding()
    if not selected(task, kind, binding):
        return task.env
    verify(binding)
    env = task.env.derive()
    env.env = dict(task.env.env or os.environ)
    env.env.update(M4=binding['m4'], LC_ALL='C', TZ='UTC')
    if kind == 'bison':
        env.BISON = [binding['bison']]
        env.BISONFLAGS = ['-d', '--no-line']
        env.env['BISON_PKGDATADIR'] = binding['data']
    else:
        env.FLEX = [binding['flex']]
        env.FLEXFLAGS = ['-t', '--noline']
    task.env = env
    return env


def finish(task, kind, binding=None):
    binding = binding if binding is not None else load_binding()
    if not selected(task, kind, binding):
        return
    verify(binding)
    outputs = []
    for node in task.outputs:
        p = Path(node.abspath()); digest = sha(p)
        if digest != binding['expected'][p.name]:
            raise ValueError('HX509 生成输出不符: ' + str(p))
        outputs.append({'path': str(p), 'sha256': digest, 'sizeBytes': p.stat().st_size})
    record = {'kind': kind, 'input': task.inputs[0].abspath(), 'outputs': outputs,
              'tool': binding[kind], 'environment': dict(task.env.env), 'verifiedAfter': True}
    dest = Path(binding['evidence']); dest.mkdir(parents=True, exist_ok=True)
    (dest / (kind + '.json')).write_text(json.dumps(record, indent=2) + '\n')

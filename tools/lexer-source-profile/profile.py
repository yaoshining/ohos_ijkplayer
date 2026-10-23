#!/usr/bin/env python3
"""核验来源/执行证据和原始输出；不执行命令，不证明历史安装身份。"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse


def fail(message):
    raise ValueError(message)


def required(data, names):
    if not isinstance(data, dict):
        fail('record must be an object')
    for name in names:
        if name not in data:
            fail('missing field: ' + name)


def verify_pin(row):
    required(row, ['path', 'sha256'])
    if not isinstance(row['path'], str) or not Path(row['path']).is_absolute():
        fail('pin path must be absolute')
    if not isinstance(row['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', row['sha256']):
        fail('invalid SHA256: ' + row['path'])
    try:
        data = Path(row['path']).read_bytes()
    except OSError as error:
        fail('unreadable pin: ' + str(error))
    if hashlib.sha256(data).hexdigest() != row['sha256']:
        fail('SHA256 drift: ' + row['path'])
    if 'sizeBytes' in row and len(data) != row['sizeBytes']:
        fail('size drift: ' + row['path'])
    return data


def pins(rows):
    if not isinstance(rows, list) or not rows:
        fail('input pins must be nonempty')
    seen = set()
    for row in rows:
        verify_pin(row)
        path = str(Path(row['path']).resolve())
        if path in seen:
            fail('duplicate input pin: ' + path)
        seen.add(path)


def source_url(value):
    if not isinstance(value, str):
        fail('source URL must be text')
    parsed = urlparse(value)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        fail('source URL must be HTTPS without credentials')


def verify_source(source):
    required(source, ['url', 'revision', 'release', 'archive', 'patches',
                      'buildInputs', 'buildRecord', 'builtTool'])
    source_url(source['url'])
    if not isinstance(source['revision'], str) or not re.fullmatch('[0-9a-f]{40}', source['revision']):
        fail('source revision must be a full 40-character Git revision')
    if not isinstance(source['release'], str) or not source['release'].strip():
        fail('release/tag must be recorded')
    verify_pin(source['archive']); verify_pin(source['buildRecord']); verify_pin(source['builtTool'])
    pins(source['buildInputs'])
    if not any(Path(p['path']).name in ('skel.c', 'flex.skl') for p in source['buildInputs']):
        fail('actual scanner skeleton build input is required')
    if not isinstance(source['patches'], list):
        fail('patches must be an explicit ordered list')
    for patch in source['patches']:
        required(patch, ['url', 'file']); source_url(patch['url']); verify_pin(patch['file'])
    return True


def scanner_features(text):
    # 排除注释和字符串中的示例；这是特征诊断，不是完整 C 语法分析器。
    text = re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                  ' ', text, flags=re.S)

    def one(pattern, name, optional=False):
        values = set(re.findall(pattern, text))
        if not values and optional:
            return None
        if len(values) != 1:
            fail('missing or conflicting scanner declaration: ' + name)
        return values.pop()

    result = {name: one(r'\b(int|yy_size_t)\s+' + name + r'\s*;', name)
              for name in ('yyleng', 'yy_n_chars', 'yy_buf_size')}
    result['scan_bytes_len'] = one(
        r'\byy_scan_bytes\s*\(\s*const\s+char\s*\*\s*\w+\s*,\s*(int|yy_size_t)\s+\w+',
        'yy_scan_bytes')
    result['grow_new_size'] = one(r'\b(int|yy_size_t)\s+new_size\s*=', 'new_size', optional=True)
    result['uint64_typedef'] = bool(re.search(r'\btypedef\s+[^;]+\bflex_uint64_t\s*;', text))
    result['size_max_guard'] = bool(re.search(r'\bif\s*\([^;{}]*\bSIZE_MAX\b', text))
    return result


def waf_output(stdout):
    return stdout.decode('utf-8', errors='replace').replace('\r\n', '\n').replace('\r', '\n').encode('latin-1')


def verify_command(record, tool_key):
    required(record, [tool_key, 'inputs', 'command', 'cwd', 'exitCode'])
    verify_pin(record[tool_key]); pins(record['inputs'])
    command = record['command']
    if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
        fail('command must be a nonempty argument array')
    if command[0] != record[tool_key]['path']:
        fail('command executable differs from pinned tool')
    if not isinstance(record['cwd'], str) or not Path(record['cwd']).is_absolute():
        fail('cwd must be absolute')
    if type(record['exitCode']) is not int or record['exitCode'] != 0:
        fail('recorded command did not succeed')


def evaluate(record):
    required(record, ['source', 'generation', 'compilation', 'reference'])
    verify_source(record['source'])
    gen, comp, ref = record['generation'], record['compilation'], record['reference']
    verify_command(gen, 'tool'); verify_command(comp, 'compiler')
    if gen['tool'] != record['source']['builtTool']:
        fail('generation tool is not bound to source build')
    required(gen, ['m4', 'environment', 'stdout', 'output', 'postprocess'])
    verify_pin(gen['m4'])
    if not isinstance(gen['environment'], dict) or not all(isinstance(k, str) and isinstance(v, str)
                                                         for k, v in gen['environment'].items()):
        fail('generation environment must be a string mapping')
    if gen['environment'].get('M4') != gen['m4']['path']:
        fail('M4 environment differs from pinned executable')
    if not any(Path(row['path']).suffix == '.l' and row['path'] in gen['command'] for row in gen['inputs']):
        fail('generation command is not bound to pinned lexer grammar')
    if not any(Path(row['path']).suffix == '.h' for row in comp['inputs']):
        fail('target header input inventory is required')
    if gen['postprocess'] != 'waf-utf8-latin1-universal-newlines':
        fail('unknown generated-output transformation')
    stdout, output = verify_pin(gen['stdout']), verify_pin(gen['output'])
    try:
        converted = waf_output(stdout)
    except UnicodeError:
        fail('stdout cannot be written using recorded Waf latin-1 encoding')
    if converted != output:
        fail('generated C differs from recorded Waf stdout transformation')
    required(comp, ['object', 'log']); obj = verify_pin(comp['object']); verify_pin(comp['log'])
    if gen['output'] not in comp['inputs'] or gen['output']['path'] not in comp['command']:
        fail('compiled source not bound to generated output')
    if comp['object']['path'] not in comp['command']:
        fail('compiled object not bound to command')
    required(ref, ['generated', 'object'])
    history = verify_pin(ref['generated']); old_obj = verify_pin(ref['object'])
    actual_features, history_features = scanner_features(output.decode('latin-1')), scanner_features(history.decode('latin-1'))
    generated_match, object_match = output == history, obj == old_obj
    return {'evidencePinsVerified': True, 'generatedMatches': generated_match,
            'objectMatches': object_match, 'featureCombinationMatches': actual_features == history_features,
            'sourceOutputMatches': generated_match and object_match,
            'features': actual_features, 'referenceFeatures': history_features,
            'historicalInstallationProven': False, 'formalArtifactAllowed': False,
            'scope': '核验所记录来源/执行证据的摘要与关联；不是对日志真实性或历史安装身份的独立证明'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--require-match', action='store_true')
    args = parser.parse_args()
    try:
        result = evaluate(json.loads(args.record.read_text()))
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')
    payload = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(payload)
    else:
        print(payload, end='')
    return 2 if args.require_match and not result['sourceOutputMatches'] else 0


if __name__ == '__main__':
    raise SystemExit(main())

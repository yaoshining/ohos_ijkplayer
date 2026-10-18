"""来源证据门禁：测试使用合成文件，不冒称真实生成器构建。"""
import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'profile.py'
HISTORY = '''extern yy_size_t yyleng;
static yy_size_t yy_n_chars;
struct yy_buffer_state { int yy_buf_size; yy_size_t yy_n_chars; };
YY_BUFFER_STATE yy_scan_bytes(const char *bytes, yy_size_t len);
yy_size_t new_size = b->yy_buf_size * 2;
typedef uint64_t flex_uint64_t;
'''
UPSTREAM = HISTORY.replace('yy_size_t', 'int').replace('typedef uint64_t flex_uint64_t;', '')
XCODE = HISTORY.replace('int yy_buf_size;', 'yy_size_t yy_buf_size;') + '\nif (x > SIZE_MAX - 2) exit(1);'


def module():
    spec = importlib.util.spec_from_file_location('lexer_profile', MODULE)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.m = module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def pin(self, name, content=b'fixture'):
        path = self.root / name
        path.write_bytes(content)
        return {'path': str(path), 'sha256': hashlib.sha256(content).hexdigest(), 'sizeBytes': len(content)}

    def source(self):
        return {'url': 'https://example.org/flex-2.6.4.tar.gz', 'revision': 'a' * 40,
                'release': '2.6.4', 'archive': self.pin('source.tar'), 'patches': [],
                'buildInputs': [self.pin('skel.c')], 'buildRecord': self.pin('build.log'),
                'builtTool': self.pin('flex')}

    def record(self):
        source = self.source()
        tool = self.pin('flex'); m4 = self.pin('m4')
        stdout = self.pin('stdout', HISTORY.encode()); output = self.pin('lex.c', HISTORY.encode())
        inp = self.pin('lex.l'); compiler = self.pin('clang'); obj = self.pin('lex.o', b'object')
        return {'source': source, 'generation': {'tool': tool, 'm4': m4,
            'inputs': [inp], 'command': [tool['path'], '-t', inp['path']],
            'cwd': str(self.root), 'environment': {'LC_ALL': 'C', 'M4': m4['path']}, 'exitCode': 0,
            'stdout': stdout, 'output': output, 'postprocess': 'waf-utf8-latin1-universal-newlines'},
            'compilation': {'compiler': compiler, 'inputs': [output, self.pin('header.h')],
            'command': [compiler['path'], '-c', output['path'], '-o', obj['path']],
            'cwd': str(self.root), 'exitCode': 0, 'object': obj, 'log': self.pin('compile.log')},
            'reference': {'generated': self.pin('history.c', HISTORY.encode()),
                          'object': self.pin('history.o', b'object')}}

    def test_three_actual_feature_combinations(self):
        h = self.m.scanner_features(HISTORY)
        u = self.m.scanner_features(UPSTREAM); x = self.m.scanner_features(XCODE)
        self.assertEqual(h['yyleng'], 'yy_size_t')
        self.assertEqual(h['yy_buf_size'], 'int')
        self.assertEqual(h['scan_bytes_len'], 'yy_size_t')
        self.assertFalse(h['size_max_guard'])
        self.assertEqual(u['yyleng'], 'int'); self.assertFalse(u['uint64_typedef'])
        self.assertEqual(x['yy_buf_size'], 'yy_size_t'); self.assertTrue(x['size_max_guard'])

    def test_size_max_definition_is_not_a_buffer_guard(self):
        c = '#ifndef SIZE_MAX\n#define SIZE_MAX (~(size_t)0)\n#endif\n' + HISTORY
        self.assertFalse(self.m.scanner_features(c)['size_max_guard'])

    def test_release_and_generated_version_are_not_identity_gate(self):
        r = self.record(); r['source']['release'] = 'Apple flex-35'
        self.assertTrue(self.m.evaluate(r)['sourceOutputMatches'])

    def test_comments_do_not_supply_features(self):
        with self.assertRaises(ValueError): self.m.scanner_features('/*' + HISTORY + '*/')

    def test_conflicting_declarations_rejected(self):
        with self.assertRaises(ValueError): self.m.scanner_features(HISTORY + '\nint yyleng;')

    def test_missing_sources_and_short_revision_rejected(self):
        for key in ['url', 'archive', 'buildInputs', 'buildRecord', 'release']:
            with self.subTest(key=key):
                s = self.source(); del s[key]
                with self.assertRaises(ValueError): self.m.verify_source(s)
        s = self.source(); s['revision'] = 'abcdef'
        with self.assertRaises(ValueError): self.m.verify_source(s)

    def test_source_archive_patch_and_actual_build_input_drift(self):
        for key in ['archive', 'patch', 'buildInput']:
            with self.subTest(key=key):
                s = self.source(); p = self.pin('original.patch')
                s['patches'] = [{'url': 'https://example.org/original.patch', 'file': p}]
                row = s['archive'] if key == 'archive' else (p if key == 'patch' else s['buildInputs'][0])
                Path(row['path']).write_bytes(b'changed')
                with self.assertRaises(ValueError): self.m.verify_source(s)

    def test_pinned_actual_build_skeleton_is_required(self):
        s = self.source(); s['buildInputs'] = []
        with self.assertRaises(ValueError): self.m.verify_source(s)

    def test_exact_evidence_is_not_historical_installation_or_formal_acceptance(self):
        result = self.m.evaluate(self.record())
        self.assertTrue(result['generatedMatches']); self.assertTrue(result['objectMatches'])
        self.assertTrue(result['sourceOutputMatches'])
        self.assertFalse(result['historicalInstallationProven']); self.assertFalse(result['formalArtifactAllowed'])

    def test_same_version_and_features_do_not_equal_raw_c(self):
        r = self.record(); content = HISTORY.encode() + b'\n/* different output */'
        r['generation']['stdout'] = self.pin('stdout', content)
        r['generation']['output'] = self.pin('lex.c', content)
        r['compilation']['inputs'][0] = r['generation']['output']
        v = self.m.evaluate(r)
        self.assertTrue(v['featureCombinationMatches']); self.assertFalse(v['sourceOutputMatches'])

    def test_matching_c_with_different_object_is_not_source_match(self):
        r = self.record(); r['compilation']['object'] = self.pin('lex.o', b'different object')
        self.assertFalse(self.m.evaluate(r)['sourceOutputMatches'])

    def test_missing_provenance_cannot_pass_even_when_outputs_match(self):
        r = self.record(); del r['source']
        with self.assertRaises(ValueError): self.m.evaluate(r)

    def test_tool_m4_header_output_object_reference_drift(self):
        for location in [('generation','tool'), ('generation','m4'), ('generation','stdout'),
                         ('generation','output'), ('compilation','object'), ('reference','generated')]:
            with self.subTest(location=location):
                r = self.record(); Path(r[location[0]][location[1]]['path']).write_bytes(b'changed')
                with self.assertRaises(ValueError): self.m.evaluate(r)
        r = self.record(); Path(r['compilation']['inputs'][1]['path']).write_bytes(b'changed')
        with self.assertRaises(ValueError): self.m.evaluate(r)

    def test_failed_commands_and_missing_compiler_inputs_rejected(self):
        for section in ['generation','compilation']:
            r = self.record(); r[section]['exitCode'] = 1
            with self.assertRaises(ValueError): self.m.evaluate(r)
        r = self.record(); r['compilation']['inputs'] = []
        with self.assertRaises(ValueError): self.m.evaluate(r)

    def test_command_tool_and_compiled_source_are_bound(self):
        r = self.record(); r['generation']['command'][0] = '/unrecorded/flex'
        with self.assertRaises(ValueError): self.m.evaluate(r)
        r = self.record(); r['compilation']['inputs'] = [self.pin('different.c')]
        with self.assertRaises(ValueError): self.m.evaluate(r)

    def test_waf_encoding_checked_not_arbitrary_generated_edit(self):
        r = self.record(); r['generation']['stdout'] = self.pin('stdout', HISTORY.encode() + b'\xc3\xa9\r\n')
        r['generation']['output'] = self.pin('lex.c', HISTORY.encode() + b'\xe9\n')
        r['compilation']['inputs'][0] = r['generation']['output']
        self.assertFalse(self.m.evaluate(r)['generatedMatches'])
        r['generation']['output'] = self.pin('lex.c', HISTORY.encode() + b'manual edit')
        r['compilation']['inputs'][0] = r['generation']['output']
        with self.assertRaises(ValueError): self.m.evaluate(r)

    def test_tool_must_be_bound_to_source_build(self):
        r = self.record(); r['source']['builtTool'] = self.pin('other-flex', b'other')
        with self.assertRaises(ValueError): self.m.evaluate(r)

    def test_m4_environment_must_match_pinned_executable(self):
        r = self.record(); r['generation']['environment']['M4'] = '/unrecorded/m4'
        with self.assertRaises(ValueError): self.m.evaluate(r)
        del r['generation']['environment']['M4']
        with self.assertRaises(ValueError): self.m.evaluate(r)

    def test_header_inventory_cannot_be_replaced_by_generated_c_only(self):
        r = self.record(); r['compilation']['inputs'] = [r['generation']['output']]
        with self.assertRaises(ValueError): self.m.evaluate(r)

    def test_grammar_invocation_must_reference_a_pinned_lex_input(self):
        r = self.record(); r['generation']['command'][-1] = '/unrecorded/lex.l'
        with self.assertRaises(ValueError): self.m.evaluate(r)

    def test_duplicate_conflicting_pins_rejected(self):
        r = self.record(); bad = copy.deepcopy(r['generation']['inputs'][0]); bad['sha256'] = 'f' * 64
        r['generation']['inputs'].append(bad)
        with self.assertRaises(ValueError): self.m.evaluate(r)


if __name__ == '__main__': unittest.main()

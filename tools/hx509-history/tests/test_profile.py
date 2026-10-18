import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import profile as hp
import waf_select as ws


class Env(dict):
    def derive(self):
        return Env(self)
    def __getattr__(self, key):
        return self.get(key, [])
    def __setattr__(self, key, value):
        self[key] = value


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.source = self.root / 'samba'
        self.file = self.root / 'tool'; self.file.write_bytes(b'locked')
        self.binding = {'profile': 'hx509-history', 'sourceRoot': str(self.source),
            'files': hp.pins([self.file]), 'bison': '/historical/bison', 'flex': '/historical/flex',
            'data': '/historical/data', 'm4': '/locked/m4'}

    def task(self, rel):
        from types import SimpleNamespace
        p = self.source / rel
        return SimpleNamespace(inputs=[SimpleNamespace(abspath=lambda: str(p))],
            env=Env(BISON=['modern'], FLEX=['default-flex'], BISONFLAGS=['-d'], env={'BASE': 'kept'}))

    def test_opt_in_required(self):
        with self.assertRaises(ValueError):
            hp.require_profile(None)
        with self.assertRaises(ValueError):
            hp.require_profile('default')
        self.assertEqual(hp.require_profile('hx509-history'), 'hx509-history')

    def test_only_exact_hx509_task_gets_private_environment(self):
        t = self.task('third_party/heimdal/lib/hx509/sel-gram.y'); original = t.env
        selected = ws.select_env(t, 'bison', self.binding)
        self.assertIsNot(selected, original)
        self.assertEqual(selected.BISON, ['/historical/bison'])
        self.assertEqual(selected.env['BISON_PKGDATADIR'], '/historical/data')
        self.assertEqual(selected.env['BASE'], 'kept')
        self.assertEqual(original.BISON, ['modern'])
        self.assertNotIn('BISON_PKGDATADIR', original.env)

    def test_other_parser_and_same_basename_outside_root_unchanged(self):
        for path in ['third_party/heimdal/lib/asn1/parse.y', '../other/third_party/heimdal/lib/hx509/sel-gram.y']:
            t = self.task(path); self.assertIs(ws.select_env(t, 'bison', self.binding), t.env)

    def test_flex_selected_without_changing_bison_or_parent_environment(self):
        t = self.task('third_party/heimdal/lib/hx509/sel-lex.l'); original=t.env
        e=ws.select_env(t, 'flex', self.binding)
        self.assertEqual(e.FLEX, ['/historical/flex']); self.assertEqual(e.FLEXFLAGS, ['-t','--noline'])
        self.assertEqual(e.BISON, ['modern']); self.assertEqual(original.FLEX, ['default-flex'])

    def test_missing_or_drifted_tool_rejected(self):
        for mode in ['drift','missing']:
            self.file.write_bytes(b'changed') if mode=='drift' else self.file.unlink()
            with self.assertRaises(ValueError):
                ws.select_env(self.task('third_party/heimdal/lib/hx509/sel-gram.y'), 'bison', self.binding)
            self.file.write_bytes(b'locked')

    def test_recipe_copy_is_opt_in_and_original_unchanged(self):
        base=Path(__file__).resolve().parents[2]/'ffmpeg8'; dest=self.root/'recipe'
        before=(base/'build-libsmbclient.sh').read_bytes()
        hp.materialize(base,dest,'hx509-history')
        self.assertEqual(before,(base/'build-libsmbclient.sh').read_bytes())
        text=(dest/'build-libsmbclient.sh').read_text()
        self.assertEqual(text.count('hx509-profile.py" apply'),1)
        self.assertLess(text.index('hx509-profile.py" apply'),text.index('\n  configure_samba\n'))
        with self.assertRaises(ValueError):hp.materialize(base,dest,'hx509-history')


if __name__ == '__main__':
    unittest.main()

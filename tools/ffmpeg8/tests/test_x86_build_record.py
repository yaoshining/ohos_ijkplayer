import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class BuildRecord(unittest.TestCase):
    def test_rejects_recipe_commit_and_library_drift(self):
        mod = load('x86-build-record')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'lib').mkdir(); (root / 'lib/libsmbclient.a').write_bytes(b'real-library')
            current = {'producerCommit': 'a' * 40, 'recipeSha256': {'runtime.c': 'original'}}
            record = {'inputs': current, 'files': mod.artifact_files(root)}
            mod.validate(record, current, root)
            for changed in [dict(current, producerCommit='b'*40), dict(current, recipeSha256={'runtime.c':'changed'})]:
                with self.assertRaisesRegex(ValueError, '构建输入'):
                    mod.validate(record, changed, root)
            (root / 'lib/libsmbclient.a').write_bytes(b'replaced-library')
            with self.assertRaisesRegex(ValueError, '构建产物'):
                mod.validate(record, current, root)

    def test_dotted_source_archive_preserves_complete_name(self):
        mod = load('package-x86-sdk')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); output = root/'sdk-1.2-r3'; evidence=root/'evidence';work=root/'work'
            for d in ['recipe/patches', 'phase20/runtime']:(evidence/d).mkdir(parents=True)
            (work/'downloads').mkdir(parents=True);(work/'downloads/ffmpeg-8.0.tar.xz').write_bytes(b'fixture')
            result=mod.source_bundle(output,root,work,{'sources':[]},evidence,'a'*40)
            self.assertEqual(result['file'],'sdk-1.2-r3-sources.tar.gz')
            self.assertTrue((root/result['file']).is_file())

if __name__ == '__main__':unittest.main()

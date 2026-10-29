import subprocess, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
class CiTests(unittest.TestCase):
    def test_explicit_profile_required_before_any_work(self):
        for args in [[],['default']]:
            p=subprocess.run(['bash',str(HERE/'ci.sh'),*args],capture_output=True,text=True)
            self.assertEqual(p.returncode,2)
            self.assertIn('hx509-history',p.stderr)
    def test_valid_profile_dispatches_only_new_entry(self):
        with __import__('tempfile').TemporaryDirectory() as tmp:
            p=Path(tmp)/'docker';p.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\nexit 41\n');p.chmod(0o755)
            env=dict(__import__('os').environ,PATH=tmp+':'+__import__('os').environ['PATH'])
            r=subprocess.run(['bash',str(HERE/'ci.sh'),'hx509-history'],env=env,capture_output=True,text=True)
            self.assertEqual(r.returncode,41)
            self.assertIn('tools/ffmpeg8/ci/Dockerfile',r.stdout)
if __name__=='__main__':unittest.main()

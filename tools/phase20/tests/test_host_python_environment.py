from pathlib import Path
import json, os, subprocess, sys, tempfile, unittest

R = Path(__file__).resolve().parents[1]

class HostPythonEnvironment(unittest.TestCase):
    def test_sanitized_host_subprocess_disables_bytecode_before_configure(self):
        recipe = (R / 'recipe/build-libsmbclient.sh').read_text()
        command = recipe.split('  env -i ', 1)[1].split('  # HEIMDAL_BINARY', 1)[0]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'buildtools/bin').mkdir(parents=True)
            (root / 'probe.py').write_text('value = 1\n')
            probe = ('import sys, json\n'
                     'from pathlib import Path\n'
                     'sys.path.insert(0, str(Path.cwd()))\n'
                     'import probe\n'
                     'print(json.dumps({"bytecode": sys.dont_write_bytecode, "userSite": sys.flags.no_user_site}))\n')
            configure = root / 'configure'
            configure.write_text('#!' + sys.executable + '\n' + probe)
            configure.chmod(0o755)
            (root / 'buildtools/bin/waf').write_text(probe)
            env = dict(os.environ, SAMBA_HOST_DIR=str(root), PREFIX=str(root), NATIVE_BUILD_PATH=os.environ['PATH'], SOURCE_DATE_EPOCH='0', JOBS='1', host_pc=str(root), PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
            result = subprocess.run(['/bin/bash', '-c', 'host_select_env=(); env -i ' + command], env=env, text=True, capture_output=True, check=True)
            rows = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual(rows, [{'bytecode': True, 'userSite': 1}] * 2)
            self.assertEqual(list(root.rglob('*.pyc')), [])

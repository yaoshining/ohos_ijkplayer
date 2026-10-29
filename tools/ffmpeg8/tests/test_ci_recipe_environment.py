"""运行真实 CI shell 与冻结 runner，验证首个 Python 入口不会污染配方。"""
import json,os,shutil,subprocess,tempfile,unittest
from pathlib import Path

HERE=Path(__file__).parents[1]
class CiRecipeEnvironment(unittest.TestCase):
    def test_ci_entry_keeps_recipe_immutable_and_rejects_extra_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);tool=root/'tools/ffmpeg8';tool.mkdir(parents=True)
            for name in ['ci-build-ohcodec.sh','ci-repo-env.sh']:
                shutil.copy2(HERE/name,tool/name)
            recipe=root/'recipe';recipe.mkdir()
            for name in ['host-lock.py','run-dependency-build.py','dependency-repeat.py']:
                shutil.copy2(HERE/name,recipe/name)
            (recipe/'dependency-sources.lock.json').write_text('{"sources":[]}')
            (recipe/'build-libsmbclient.sh').write_text('#!/bin/bash\nexit 42\n')
            # 首个 CI Python 调用作为探针；仍执行真实 runner 和严格 verify_binding。
            (tool/'ci-prepare-inputs.py').write_text('''import hashlib,json,subprocess,sys
from pathlib import Path
root=Path.cwd();recipe=root/'recipe';ndk=root/'ndk';ndk.mkdir()
def record(p):return {'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'sizeBytes':p.stat().st_size}
lock={'ndkRoot':str(ndk),'recipeRoot':str(recipe),'recipeFiles':[record(p) for p in sorted(recipe.rglob('*')) if p.is_file()],'commands':[],'files':[],'environment':{}}
(root/'lock.json').write_text(json.dumps(lock))
def run(name):
 return subprocess.run([sys.executable,str(recipe/'run-dependency-build.py'),'--root',str(root/name),'--recipe',str(recipe),'--host-lock',str(root/'lock.json'),'--cache',str(root/'cache'),'--ndk',str(ndk)],capture_output=True,text=True)
first=run('first');(root/'first-result.json').write_text(json.dumps({'code':first.returncode,'stderr':first.stderr}))
(recipe/'unexpected.txt').write_text('must be rejected')
second=run('second');(root/'second-result.json').write_text(json.dumps({'code':second.returncode,'stderr':second.stderr}))
raise SystemExit(42)
''')
            env=dict(os.environ);env.pop('PYTHONDONTWRITEBYTECODE',None)
            result=subprocess.run(['bash',str(tool/'ci-build-ohcodec.sh')],cwd=root,env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,42,result.stderr)
            first=json.loads((root/'first-result.json').read_text())
            self.assertTrue((root/'first/build-record.json').is_file(),first)
            self.assertEqual(first['code'],42)
            self.assertFalse(list(recipe.rglob('*.pyc')))
            second=json.loads((root/'second-result.json').read_text())
            self.assertIn('recipe 文件集合或摘要漂移',second['stderr'])
            self.assertFalse((root/'second').exists())

if __name__=='__main__':unittest.main()

"""容器只信任显式挂载的 producer 仓库，不放宽其他目录。"""
import os,subprocess,tempfile,unittest
from pathlib import Path
class GitEnvironment(unittest.TestCase):
    def test_exact_repository_scope(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);a=root/'producer';b=root/'other'
            for p in [a,b]:subprocess.run(['git','init','-q',str(p)],check=True)
            env=dict(os.environ,GIT_TEST_ASSUME_DIFFERENT_OWNER='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_SYSTEM='/dev/null',GIT_CONFIG_COUNT='0')
            script=Path(__file__).parents[1]/'ci-repo-env.sh'
            r=subprocess.run(['bash','-c','source "$1"; lock_git_repository "$2"; git -C "$2" status --porcelain; good=$?; git -C "$3" status --porcelain >/dev/null 2>&1; bad=$?; test "$good" = 0 && test "$bad" != 0','test',str(script),str(a),str(b)],env=env,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
if __name__=='__main__':unittest.main()

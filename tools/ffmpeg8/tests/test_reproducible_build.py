"""防止父 Git 仓库和输出路径污染 FFmpeg 构建身份。"""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
class ReproducibleBuildTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        (self.root/'README').write_text('host repository')
        subprocess.run(['git','-C',str(self.root),'add','README'],check=True)
        subprocess.run(['git','-C',str(self.root),'-c','user.name=test','-c','user.email=test@example.invalid','commit','-qm','host'],check=True)
        self.source=self.root/'nested/source';self.source.mkdir(parents=True)
        (self.source/'RELEASE').write_text('8.0\n')

    def test_parent_git_does_not_supply_ffmpeg_version(self):
        result=subprocess.run(['bash','-c','source "$1"; sh "$2" "$3"', 'test',str(ROOT/'build-env.sh'),str(ROOT/'tests/fixtures/ffmpeg-version.sh'),str(self.source)],capture_output=True,text=True,env=dict(os.environ,revision='wrong',OUTPUT_ROOT=str(self.root/'build')))
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),'8.0')

    def test_default_prefix_independent_of_output(self):
        values=[]
        for output in ('a','different-directory-name'):
            r=subprocess.run(['bash','-c','source "$1"; printf "%s" "$FFMPEG_CONFIGURE_PREFIX"','test',str(ROOT/'build-env.sh')],capture_output=True,text=True,env=dict(os.environ,OUTPUT_ROOT=str(self.root/output)))
            self.assertEqual(r.returncode,0,r.stderr);values.append(r.stdout)
        self.assertEqual(values,['/opt/ohos-ffmpeg8']*2)

    def test_make_recipe_preserves_locked_revision(self):
        makefile=self.root/'Makefile'
        makefile.write_text('all:\n\t@revision=$(REVISION) sh "'+str(ROOT/'tests/fixtures/ffmpeg-version.sh')+'" "'+str(self.source)+'"\n')
        r=subprocess.run(['bash','-c','source "$1"; make -s -f "$2"','test',str(ROOT/'build-env.sh'),str(makefile)],cwd=self.root,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(r.stdout.strip(),'8.0')

    def test_build_source_link_is_relative(self):
        (self.root/'source').mkdir();(self.root/'build').mkdir()
        r=subprocess.run(['bash','-c','source "$1"; prepare_source_link "$2"','test',str(ROOT/'build-env.sh'),str(self.root)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(os.readlink(self.root/'build/src'),'../source')

    def test_prefix_traversal_rejected(self):
        r=subprocess.run(['bash','-c','source "$1"','test',str(ROOT/'build-env.sh')],env=dict(os.environ,FFMPEG_CONFIGURE_PREFIX='/../escape'),capture_output=True)
        self.assertNotEqual(r.returncode,0)

if __name__=='__main__':unittest.main()

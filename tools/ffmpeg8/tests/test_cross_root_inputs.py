"""真实路径入口、pkg-config 和宿主编译/链接；完整目标构建另验。"""
from pathlib import Path
import json, os, platform, shlex, shutil, subprocess, tempfile, unittest

HERE=Path(__file__).resolve().parents[1]

class CrossRootInputs(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.cc=shutil.which('clang')
        if platform.system()=='Darwin':self.cc=subprocess.check_output(['xcrun','--find','clang'],text=True).strip()
        self.target=subprocess.check_output([self.cc,'-dumpmachine'],text=True).strip()
        self.target_flags=['--target='+self.target]
        if platform.system()=='Darwin':self.target_flags+=['-isysroot',subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()]

    def layout(self,name):
        root=self.root/name;build=root/'build';dep=root/'static dependencies';ndk=root/'tool chain'
        for p in [build,dep/'include',dep/'lib/pkgconfig',ndk/'llvm/bin',ndk/'sysroot']:p.mkdir(parents=True,exist_ok=True)
        (ndk/'llvm/bin/aarch64-unknown-linux-ohos-clang').symlink_to(self.cc)
        (dep/'include/probe.h').write_text('#define VALUE 42\n')
        (dep/'lib/pkgconfig/probe.pc').write_text('prefix=${pcfiledir}/../..\nlibdir=${prefix}/lib\nincludedir=${prefix}/include\nName: probe\nDescription: actual selected dependency\nVersion: 1\nLibs: -L${libdir} -lprobe\nCflags: -I${includedir}\n')
        return build,dep,ndk

    def prepare(self,build,dep,ndk):
        return subprocess.run(['bash','-c','set -e; source "$1"; prepare_build_inputs "$2" "$3" "$4"; printf "%s\\n" "$FFMPEG_INPUT_CFLAGS" "$FFMPEG_INPUT_LDFLAGS" "$PKG_CONFIG_LIBDIR"','test',str(HERE/'build-env.sh'),str(build),str(dep),str(ndk)],capture_output=True,text=True)

    def test_different_lengths_and_spaces_use_real_stable_inputs(self):
        configs=[];objects=[]
        for name in ['a','a substantially longer output directory']:
            build,dep,ndk=self.layout(name);p=self.prepare(build,dep,ndk);self.assertEqual(p.returncode,0,p.stderr)
            flags=p.stdout.splitlines();configs.append(flags)
            env=dict(os.environ,PKG_CONFIG_PATH=flags[2],PKG_CONFIG_LIBDIR=flags[2],PKG_CONFIG_SYSROOT_DIR='')
            cflags=subprocess.check_output(['pkg-config','--cflags','probe'],cwd=build,env=env,text=True).strip()
            libs=subprocess.check_output(['pkg-config','--libs','--static','probe'],cwd=build,env=env,text=True).strip()
            self.assertNotIn(str(self.root),cflags+libs);self.assertIn('./deps/',cflags+libs)
            (build/'library.c').write_text('int probe(void){return 42;}\n')
            subprocess.run([self.cc,'-c','library.c','-o',str(dep/'lib/probe.o')],cwd=build,check=True)
            subprocess.run(['ar','rcs',str(dep/'lib/libprobe.a'),str(dep/'lib/probe.o')],check=True,capture_output=True)
            (build/'unit.c').write_text('#include <probe.h>\nextern int probe(void);\nint main(void){return probe()!=VALUE;}\n')
            cc='./toolchain/llvm/bin/aarch64-unknown-linux-ohos-clang'
            subprocess.run([cc,*self.target_flags,*shlex.split(flags[0]),*shlex.split(cflags),'-c','unit.c','-o','unit.o'],cwd=build,check=True)
            subprocess.run([cc,*self.target_flags,'unit.o',*shlex.split(libs),'-o','probe'],cwd=build,check=True)
            subprocess.run([str(build/'probe')],check=True)
            objects.append((build/'unit.o').read_bytes())
            binding=json.loads((build/'input-bindings.json').read_text())
            self.assertEqual({x['role']:x['resolvedPath'] for x in binding['inputs']},{'deps':str(dep.resolve()),'toolchain':str(ndk.resolve())})
        self.assertEqual(configs[0],configs[1]);self.assertEqual(objects[0],objects[1])

    def test_missing_input_rejected_without_links(self):
        build,dep,ndk=self.layout('missing');shutil.rmtree(dep/'include')
        self.assertNotEqual(self.prepare(build,dep,ndk).returncode,0);self.assertFalse((build/'deps').is_symlink())

    def test_occupied_and_broken_links_rejected_without_overwrite(self):
        for role in ['deps','toolchain']:
            build,dep,ndk=self.layout('occupied-'+role);(build/role).symlink_to('/missing-original')
            self.assertNotEqual(self.prepare(build,dep,ndk).returncode,0)
            self.assertEqual(os.readlink(build/role),'/missing-original')
            self.assertFalse((build/'input-bindings.json').exists())

    def test_changed_link_rejected_by_post_verification(self):
        build,dep,ndk=self.layout('changed');p=self.prepare(build,dep,ndk);self.assertEqual(p.returncode,0,p.stderr)
        check=['bash','-c','source "$1"; verify_build_inputs "$2"','test',str(HERE/'build-env.sh'),str(build)]
        self.assertEqual(subprocess.run(check,capture_output=True).returncode,0)
        (build/'deps').unlink();(build/'deps').symlink_to(ndk)
        p=subprocess.run(check,capture_output=True)
        self.assertNotEqual(p.returncode,0)

if __name__=='__main__':unittest.main()

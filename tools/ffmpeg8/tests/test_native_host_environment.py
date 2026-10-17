"""调用真实宿主构建函数，确认 env -i 没有丢失固定日期和 locale。"""
import os,re,shlex,subprocess,tempfile,unittest
from pathlib import Path
class HostEnvironment(unittest.TestCase):
    def test_native_configure_receives_fixed_environment(self):
        text=(Path(__file__).parents[1]/'build-libsmbclient.sh').read_text()
        function=re.search(r'build_host_tools\(\) \{.*?\n\}',text,re.S).group()
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);host=root/'host';(host/'buildtools/bin').mkdir(parents=True);(host/'buildtools/bin/waf').write_text('')
            marker=root/'environment';configure=host/'configure';configure.write_text('#!/bin/sh\nprintf "%s|%s|%s|%s|%s" "$SOURCE_DATE_EPOCH" "$TZ" "$LC_ALL" "$CFLAGS" "$LDFLAGS" > '+shlex.quote(str(marker))+'\nexit 42\n');configure.chmod(0o755)
            env=dict(os.environ,SAMBA_HOST_DIR=str(host),SAMBA_DIR=str(root/'samba'),WORK_DIR=str(root/'work'),PREFIX=str(root/'prefix'),NATIVE_BUILD_PATH=os.environ['PATH'],SOURCE_DATE_EPOCH='1755820644',JOBS='1')
            subprocess.run(['bash','-c','set -e; log() { :; }; '+function+'\nbuild_host_tools'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            self.assertEqual(marker.read_text(),'1755820644|UTC|C|-I'+str(root/'work/host-pkgconfig')+'|')
if __name__=='__main__':unittest.main()

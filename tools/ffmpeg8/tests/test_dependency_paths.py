import importlib.util,tempfile,unittest
from pathlib import Path
class Paths(unittest.TestCase):
    def test_only_build_metadata_is_normalized(self):
        spec=importlib.util.spec_from_file_location('paths',Path(__file__).parents[1]/'dependency-paths.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'include').mkdir();(p/'lib/pkgconfig').mkdir(parents=True)
            (p/'include/gmp.h').write_text('#define __GMP_CFLAGS "-I'+str(p)+'/include -ffile-prefix-map=/build/run=/usr/src/ohcodec-deps"\n#define SOMETHING 1\n')
            (p/'lib/pkgconfig/a.pc').write_text('prefix='+str(p)+'\nLibs: -L${prefix}/lib -la\n')
            m.normalize(p,Path('/build/run'))
            self.assertIn('prefix=${pcfiledir}/../..',(p/'lib/pkgconfig/a.pc').read_text())
            text=(p/'include/gmp.h').read_text();self.assertNotIn(str(p),text);self.assertNotIn('/build/run',text);self.assertIn('#define SOMETHING 1',text)
if __name__=='__main__':unittest.main()

import sys,json,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'device'));from identity_gate import analyze
ROWS=json.loads((Path(__file__).parent/'fixtures/close.json').read_text())['rows']
EXPECTED={name:'a'*64 for name in ('libmpv.so','libavcodec.so.62','libavformat.so.62','libavutil.so.60','libavfilter.so.11','libswscale.so.9','libswresample.so.6')}
TEXT='P24_BEGIN case=vk-close sample=fixture pid=1001 surface=42\n'+'\n'.join('loaded /data/storage/el1/bundle/libs/arm64/'+n+' sha256='+s for n,s in EXPECTED.items())
class Identity(unittest.TestCase):
 def test_positive(self):self.assertTrue(analyze(TEXT,ROWS,['1001'],EXPECTED)['accepted'])
 def test_wrong_sha(self):self.assertFalse(analyze(TEXT.replace('a'*64,'b'*64,1),ROWS,['1001'],EXPECTED)['accepted'])
 def test_missing_library(self):self.assertFalse(analyze('\n'.join(TEXT.splitlines()[:-1]),ROWS,['1001'],EXPECTED)['accepted'])
 def test_multiple_pid(self):self.assertFalse(analyze(TEXT,ROWS,['1001','1002'],EXPECTED)['accepted'])
 def test_mixed_begin(self):self.assertFalse(analyze(TEXT+'\nP24_BEGIN case=vk-close pid=1001',ROWS,['1001'],EXPECTED)['accepted'])
 def test_mismatched_timeline_pid(self):self.assertFalse(analyze(TEXT.replace('pid=1001','pid=1002'),ROWS,['1002'],EXPECTED)['accepted'])
if __name__=='__main__':unittest.main()

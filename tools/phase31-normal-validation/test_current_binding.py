"""当前/历史库材料隔离门禁；只用文本输入，不假装CI含HAP。"""
from pathlib import Path
import json,shutil,tempfile,unittest
from verify_current_binding import verify
ROOT=Path(__file__).resolve().parent
class Binding(unittest.TestCase):
 def replay(self,change=None):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)
   for name in ('normal-library-binding.json','target-artifact-manifest.json','target-source-binding.json','binding-policy.json'):shutil.copyfile(ROOT/name,p/name)
   shutil.copytree(ROOT/'app',p/'app')
   if change:change(p)
   return verify(p)
 def test_current(self):self.assertTrue(self.replay()['accepted'])
 def test_historical_cannot_be_current(self):
  def change(p):
   d=json.loads((p/'app/lib-binding.json').read_text());(p/'normal-library-binding.json').write_text(json.dumps({r['path']:r['sha256'] for r in d['libraries']}))
  with self.assertRaises(ValueError):self.replay(change)
 def test_wrong_expected_header(self):
  def change(p):
   f=p/'app/entry/src/main/cpp/expected.h';f.write_text(f.read_text().replace('1a469850','00000000'))
  with self.assertRaises(ValueError):self.replay(change)
 def test_wrong_hap_library(self):
  def change(p):
   f=p/'target-artifact-manifest.json';d=json.loads(f.read_text());d['libraries']['libs/arm64-v8a/libmpv.so']='0'*64;f.write_text(json.dumps(d))
  with self.assertRaises(ValueError):self.replay(change)
 def test_missing_hap_library(self):
  def change(p):
   f=p/'target-artifact-manifest.json';d=json.loads(f.read_text());d['libraries'].pop('libs/arm64-v8a/libphase22.so');f.write_text(json.dumps(d))
  with self.assertRaises(ValueError):self.replay(change)
 def test_policy_cannot_point_to_history(self):
  def change(p):
   f=p/'binding-policy.json';d=json.loads(f.read_text());d['currentLibraries']='app/lib-binding.json';f.write_text(json.dumps(d))
  with self.assertRaises(ValueError):self.replay(change)
 def test_duplicate_current_key(self):
  def change(p):
   f=p/'normal-library-binding.json';s=f.read_text().strip();f.write_text(s[:-1]+',"libmpv.so":"'+'0'*64+'"}')
  with self.assertRaises(ValueError):self.replay(change)
 def test_duplicate_hap_key(self):
  def change(p):
   f=p/'target-artifact-manifest.json';s=f.read_text().replace('"libraries": {','"libraries": {"libs/arm64-v8a/libmpv.so":"'+'0'*64+'",',1);f.write_text(s)
  with self.assertRaises(ValueError):self.replay(change)
if __name__=='__main__':unittest.main()

from pathlib import Path
import importlib.util,os,shutil,tempfile,unittest
R=Path(__file__).resolve().parents[1]
class SourceHooks(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  spec=importlib.util.spec_from_file_location('runtime_patch',R/'apply.py');cls.mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.mod)
 def test_actual_samba_source_and_reapply_rejected(self):
  source=Path(os.environ['PHASE20_SAMBA_SOURCE'])
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   for n in self.mod.SAMBA_FILES:
    p=root/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/n,p)
   self.mod.samba(root)
   s=(root/'source3/libsmb/libsmb_context.c').read_text();self.assertIn('rt_module_error',s);self.assertIn('else {\n            SMB_THREAD_ONCE(&SMBC_initialized, SMBC_module_init, NULL);',s);self.assertIn('runtime_was_initialized && initialized_ctx_count',s);self.assertIn('smb_context_wrappers.inc',s)
   s=(root/'source3/param/loadparm.c').read_text();self.assertEqual(s.count('pszParmValue = rt_loadparm_value(pszParmName, pszParmValue);'),2);self.assertIn('parm_table[id].offset',s)
   s=(root/'source3/lib/gencache.c').read_text();self.assertIn('!rt_dyn("CONFIGFILE") && cache == NULL',s)
   with self.assertRaises(ValueError):self.mod.samba(root)
 def test_ffmpeg_new_export_header_and_wrapper(self):
  source=Path(os.environ['PHASE20_FFMPEG_SOURCE'])
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   for n in self.mod.FFMPEG_FILES:
    p=root/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/n,p)
   self.mod.ffmpeg(root)
   self.assertEqual((root/'libavformat/libavformat.v').read_text().count('ohcodec_smb_runtime_configure_v1;'),1)
   self.assertIn('ohcodec_smb_runtime.h',(root/'libavformat/Makefile').read_text())
   self.assertIn('ohcodec_smb_runtime_configure_internal(config)',(root/'libavformat/libsmbclient.c').read_text())

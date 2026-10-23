from pathlib import Path
import os

def python_inputs(stdlib,modules):
 for base,dirs,files in os.walk(stdlib,followlinks=False):
  dirs[:]=sorted(d for d in dirs if d not in ['site-packages','dist-packages'])
  for name in sorted(files):
   p=Path(base)/name
   if p.is_file():yield p,'Python standard library (including existing bytecode)'
 for name,root in sorted(modules.items()):
  for p in sorted(Path(root).rglob('*')):
   if p.is_file():yield p,'Python module '+name

"""Strict source and run-root checks; no implicit exclusions."""
import hashlib,re,tarfile
from pathlib import Path,PurePosixPath

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def inventory(root):
 root=Path(root);rows=[]
 for p in sorted(root.rglob('*')):
  if p.is_symlink():
   if not p.resolve().is_relative_to(root.resolve()):raise ValueError('external link '+str(p))
  if p.is_file():
   row={'path':p.relative_to(root).as_posix(),'size':p.stat().st_size,'sha256':sha(p)}
   if p.is_symlink():row['linkTarget']=str(p.readlink())
   rows.append(row)
 return rows

def verify_tree(root,rows,source=False):
 root=Path(root);actual=inventory(root)
 if actual!=rows:raise ValueError('input exact set/bytes differ: '+str(root))
 if source:
  for row in rows:
   p=PurePosixPath(row['path'])
   if p.suffix in ['.o','.a','.so','.pyc'] or any(x in p.parts for x in ['.git','.build','__pycache__','meson-private','target']):raise ValueError('build state in source: '+str(p))
 return True

def require_fresh(p):
 p=Path(p).absolute()
 if p.exists() or p.is_symlink():raise ValueError('run root already exists: '+str(p))
 return p

def safe_extract(archive,destination):
 dest=require_fresh(destination);dest.mkdir(parents=True)
 with tarfile.open(archive) as t:
  members=t.getmembers()
  for m in members:
   p=PurePosixPath(m.name)
   if p.is_absolute() or '..' in p.parts or m.isdev():raise ValueError('unsafe tar member: '+m.name)
   if m.issym() or m.islnk():
    target=PurePosixPath(m.linkname)
    if target.is_absolute() or not ((dest/p.parent/target) if m.issym() else (dest/target)).resolve().is_relative_to(dest.resolve()):raise ValueError('external archive link')
  t.extractall(dest,members=members)
 return dest

def source_version(root):
 try:value=(Path(root)/'.phase18-source-version').read_text()
 except OSError as e:raise ValueError('missing fixed source version') from e
 if not re.fullmatch('[0-9a-f]{40}\n',value):raise ValueError('invalid fixed source version')
 return value.strip()

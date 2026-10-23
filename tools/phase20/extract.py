"""Materialize pinned source archives without ever writing through symlinks."""
from pathlib import Path
import tarfile,shutil,os

def extract_source(archive,dest,allow_external_symlinks=False):
 dest=Path(dest).resolve()
 if dest.exists() and any(dest.iterdir()):raise ValueError('extraction destination is not empty')
 dest.mkdir(parents=True,exist_ok=True)
 with tarfile.open(archive) as t:
  members=t.getmembers();seen=set();links={};external=[]
  for m in members:
   p=Path(m.name)
   if p.is_absolute() or '..' in p.parts or str(p) in seen:raise ValueError('unsafe/duplicate archive path')
   seen.add(str(p))
   if m.issym():
    if Path(m.linkname).is_absolute():raise ValueError('absolute archive symlink')
    links[p]=m.linkname
    if not (dest/p.parent/m.linkname).resolve().is_relative_to(dest):external.append({'path':str(p),'target':m.linkname})
   elif not (m.isfile() or m.isdir()):raise ValueError('unsupported archive entry')
  if external and not allow_external_symlinks:raise ValueError('external archive symlinks')
  for m in members:
   if any(p in links for p in Path(m.name).parents):raise ValueError('archive member writes through symlink')
  for m in members:
   p=dest/m.name
   if m.isdir():p.mkdir(parents=True,exist_ok=True)
   elif m.isfile():
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:shutil.copyfileobj(t.extractfile(m),f)
    p.chmod(m.mode&0o777)
  for p,target in links.items():
   path=dest/p;path.parent.mkdir(parents=True,exist_ok=True);path.symlink_to(target)
 return {'archiveSymlinks':len(links),'externalRelativeSymlinks':external,'writeThroughSymlinks':False}

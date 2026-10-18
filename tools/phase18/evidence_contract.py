"""Small gates shared by CI and independent downloaded evidence verification."""
from pathlib import PurePosixPath

def exact_set(actual,expected):
 if len(set(actual))!=len(actual) or len(set(expected))!=len(expected):raise ValueError('duplicate identity')
 if set(actual)!=set(expected):raise ValueError('set mismatch: missing='+repr(sorted(set(expected)-set(actual)))+' added='+repr(sorted(set(actual)-set(expected))))
 return True

def compare_archive_rows(built,linked,expected):
 exact_set([x['path'] for x in built],expected);exact_set([x['path'] for x in linked],expected)
 b={x['path']:x['sha256'] for x in built};l={x['path']:x['sha256'] for x in linked}
 if b!=l:raise ValueError('archive digest mismatch')
 return True

def verify_index(rows,actual):
 names=[x['path'] for x in rows]
 for n in names:
  p=PurePosixPath(n)
  if p.is_absolute() or '..' in p.parts or str(p)!=n:raise ValueError('unsafe index path')
 exact_set(names,list(actual))
 for r in rows:
  if actual[r['path']]!=(r.get('size',r.get('sizeBytes')),r['sha256']):raise ValueError('indexed bytes mismatch '+r['path'])
 return True

def require_before_pin(path,digest,before):
 if before.get(path)!=digest:raise ValueError('non-generated input missing/changed in before manifest: '+path)
 return True

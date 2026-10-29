import re,json
from pathlib import Path

def feature_macros(text,prefix):
 result={}
 for mode,name,value in re.findall(r'^#(define|undef)[ \t]+('+re.escape(prefix)+r'[A-Z0-9_]+)(?:[ \t]+([^\n]+))?$',text,re.M):
  if name in result:raise ValueError('duplicate feature macro '+name)
  result[name]=None if mode=='undef'else(value or '').strip()
 if not result:raise ValueError('missing feature macros '+prefix)
 return result

def require_expected_features(actual,expected):
 if not expected or actual!=expected:
  differing={stage:sorted(k for k in set(actual.get(stage,{}))|set(expected.get(stage,{}))if actual.get(stage,{}).get(k,'MISSING')!=expected.get(stage,{}).get(k,'MISSING'))for stage in set(actual)|set(expected)}
  raise ValueError('feature configuration differs from fixed local baseline: '+json.dumps(differing,sort_keys=True))
 return True

def check_run(root,expected):
 headers={'mpv':(root/'mpv/build/config.h','HAVE_'),'libplacebo':(root/'libplacebo/build/src/include/libplacebo/config.h','PL_HAVE_')}
 actual={name:feature_macros(p.read_text(),prefix)for name,(p,prefix)in headers.items()};require_expected_features(actual,expected['features']);return {'passed':True,'features':actual,'reference':expected['reference']}

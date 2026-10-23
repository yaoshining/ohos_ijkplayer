"""P24_RESULT 严格键值解析，拒绝重复字段和非规范/非有限数字。"""
import math,re
INTS={'loaded','eof','errors','distinctPtsSamples','continuousPassed','operationsPassed','stopped'}
FLOATS={'wallElapsed','continuousSeconds'}
def parse(text):
 rows=re.findall(r'^P24_RESULT (.*)$',text,re.M)
 if len(rows)!=1:raise ValueError('result_count')
 out={}
 for token in rows[0].split():
  if token.count('=')!=1:raise ValueError('result_token')
  key,value=token.split('=')
  if key in out:raise ValueError('duplicate_result_field')
  if key in INTS:
   if re.fullmatch(r'0|[1-9][0-9]*',value) is None:raise ValueError('integer_result_field')
   out[key]=int(value)
  elif key in FLOATS:
   if re.fullmatch(r'(?:0|[1-9][0-9]*)(?:\.[0-9]+)?',value) is None:raise ValueError('numeric_result_field')
   n=float(value)
   if not math.isfinite(n):raise ValueError('nonfinite_result_field')
   out[key]=n
  elif key=='reason' and re.fullmatch('[a-z0-9_]+',value):out[key]=value
  else:raise ValueError('unknown_result_field')
 if not {'loaded','eof','errors','stopped'}<=out.keys():raise ValueError('missing_result_field')
 return out

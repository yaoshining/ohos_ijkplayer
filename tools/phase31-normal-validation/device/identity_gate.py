"""核对实际加载的七个播放器库，而非仅信 all_sha_match 摘要。"""
import re
def analyze(text,rows,pids,expected):
 problems=[]
 try:
  begins=re.findall(r'^P24_BEGIN .*\bpid=(\d+)\b.*$',text,re.M)
  if len(begins)!=1:problems.append('begin_count')
  if len(pids)!=1 or begins!=pids:problems.append('pid_identity')
  sessions=[r for r in rows if r['event']=='session_begin']
  if len(sessions)!=1 or len(begins)!=1 or str(sessions[0]['rc'])!=begins[0]:problems.append('timeline_pid')
  loaded=re.findall(r'^loaded /data/storage/el1/bundle/libs/arm64/([^ /]+) sha256=([0-9a-f]{64})$',text,re.M)
  expected={k:v for k,v in expected.items() if k!='libc++_shared.so'}
  if len(expected)!=7 or len(loaded)!=7 or len(dict(loaded))!=7 or dict(loaded)!=expected:problems.append('loaded_library_binding')
  return {'accepted':not problems,'problems':problems,'pid':begins[0] if len(begins)==1 else None,'loadedLibraryCount':len(loaded),'loadedLibraries':dict(loaded),'session':sessions[0]['session'] if len(sessions)==1 else None}
 except (TypeError,KeyError,IndexError) as e:return {'accepted':False,'problems':problems+['malformed_'+type(e).__name__]}

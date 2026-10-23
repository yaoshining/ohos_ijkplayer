from pathlib import Path
import re,json,argparse

def parse(text):
 cases=[];current=None
 for line in text.splitlines():
  m=re.search(r'case=(\S+) cycle=(\d+) surface=(\d+)',line)
  if m:
   pid=re.match(r'\S+ \S+\s+(\d+)\s+\d+\s+[A-Z] ',line)
   current={'mode':m[1],'cycle':int(m[2]),'surface':m[3],'pid':int(pid[1]) if pid else None,'samples':{}};cases.append(current)
  if current is None:continue
  m=re.search(r'P23_SAMPLE stage=(\S+) fd=(-?\d+) tasks=(-?\d+)',line)
  if m:current['samples'][m[1]]={'reportedFd':int(m[2]),'tasks':int(m[3]),'fds':[]}
  m=re.search(r'P23_FD stage=(\S+) fd=(\d+) ino=(\d+) dev=(\d+) stat_rc=(-?\d+) target=(.*)',line)
  if m and m[1] in current['samples']:current['samples'][m[1]]['fds'].append({'fd':int(m[2]),'inode':int(m[3]),'dev':int(m[4]),'statRc':int(m[5]),'target':m[6]})
  if 'mapped_expected_libraries=7 all_sha_match=1' in line:current['mappedSevenMatch']=True
  if ': result 'in line:current['result']=line.split(': result ',1)[1]
 return cases

def summarize(cases,mode):
 selected=[c for c in cases if c['mode']==mode and 'result'in c]
 rows=[]
 for c in selected:
  s=c['samples'].get('settled3000');r={'cycle':c['cycle'],'surface':c['surface'],'result':c['result']}
  if s:
   r.update({kind:sum(kind in f['target']for f in s['fds'])for kind in ['ashmem','dmabuf']})
   # usage() keeps its /proc/self/status ifstream alive while countdir()
   # opens /proc/self/fd. Both are gone when snapshot() enumerates details.
   r.update(fdDetails=len(s['fds']),reportedFd=s['reportedFd'],temporarySamplingFdOverhead=2,countsAgree=len(s['fds'])==s['reportedFd']-2)
  rows.append(r)
 one_process=bool(selected) and all(c.get('pid') is not None for c in selected) and len({c['pid'] for c in selected})==1
 unique_cycles=len({c['cycle'] for c in selected})==len(selected)
 complete=len(rows)>=13 and one_process and unique_cycles and all('dmabuf'in x and x['countsAgree'] for x in rows)
 required=['loaded=1','eof=1','seekConfirmed=1','stopped=0','gpu=ohosvk']
 if mode!='vk-sw':required.append('hwdec=ohcodec')
 actual=bool(selected) and all(c.get('mappedSevenMatch') and re.search(r'observedDistinctPlaybackPTSWithFrame=([1-9]\d*)',c['result']) and all(x in c['result'].split() for x in required) for c in selected)
 status='incomplete'
 if complete and actual:
  last=rows[-10:];growth=any(all(b[k]>a[k]for a,b in zip(last,last[1:]))for k in ['dmabuf','ashmem'])
  net_growth=any(last[-1][k]>last[0][k] for k in ['dmabuf','ashmem'])
  stable=all(len({x[k] for x in last})==1 for k in ['dmabuf','ashmem'])
  status='persistent-growth' if growth else 'net-growth' if net_growth else 'stable-observed-counts' if stable else 'variable-counts-needs-review'
 return {'mode':mode,'completedCycles':len(rows),'requiredWarmup':3,'requiredObservation':10,'status':status,'singleProcess':one_process,'uniqueCycles':unique_cycles,'actualPlaybackVerified':actual,'rows':rows,'objectIdentityCaveat':'fstat inode/dev may be non-unique for anonymous buffers; cannot identify objects from those numbers alone; stable descriptor counts are not proof of all memory being leak-free'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('output',type=Path);a=p.parse_args();cases=parse(a.log.read_text());result={'cases':cases,'summary':[summarize(cases,m) for m in ['vk-h264','vk-sw']]};a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))

from pathlib import Path
import json,re,tarfile,argparse,hashlib
p=argparse.ArgumentParser();p.add_argument('experiment');a=p.parse_args();r=Path(a.experiment)
with tarfile.open(r/'device-logs.tar') as t:t.extractall(r/'logs',filter='data')
expected=json.load(open(r/'binding.json'))['libraries'];rows=[]
for p in sorted((r/'logs').glob('*.log')):
 s=p.read_text();result=[l for l in s.splitlines() if l.startswith('P24_RESULT ')];obs=[json.loads(l.partition(' ')[2]) for l in s.splitlines() if l.startswith('P24_OBSERVATION ')];params=[];index=-1
 for l in s.splitlines():
  if l.startswith('P24_LOAD '):index=int(re.search(r'index=(\d+)',l)[1])
  m=re.match(r'P24_PARAMS name=(\S+) rc=(-?\d+) value=(.*)',l)
  if m:params.append({'fileIndex':index,'property':m[1],'rc':int(m[2]),'value':json.loads(m[3])})
 maps=dict(re.findall(r'loaded .*/(lib[^ /]+) sha256=([a-f0-9]{64})',s));assert maps==expected,p.name
 configs=[l for l in s.splitlines() if 'Picked surface configuration' in l or re.search(r'EGL_(RED|GREEN|BLUE|ALPHA)_SIZE=',l)]
 warn=[l for l in s.splitlines() if l.startswith('P24_MPV warn ') or l.startswith('P24_MPV error ')]
 v=[o for o in obs if o['videoSampleRc']>=0];row={'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'mapsMatch':True,'result':result,'sampleCount':len(v),'actualDecoders':sorted(set(o['hwdec'] for o in v)),'gpu':sorted(set(o['gpu'] for o in v)),'outputConfigs':configs,'params':params,'warnings':warn}
 assert len(result)==1,f'incomplete {p.name}'
 assert 'errors=0' in result[0] and 'stopped=0' in result[0],p.name
 rows.append(row)
 print(p.name,result[0],row['actualDecoders']);print('output',configs[:5]);print('warnings',warn[:3])
(r/'analysis.json').write_text(json.dumps({'cases':rows,'manualVisualAccepted':False,'decoderAllocationVerified':False,'nativeWindowReadback':'not-run-non-threadsafe','HDRComplete':False,'formalArtifactAllowed':False},indent=2)+'\n')

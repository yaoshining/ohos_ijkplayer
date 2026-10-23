import math
def accept_libraries(actual,expected):
 return len(expected)==7 and actual==expected
def accept_playback(d,gpu,hardware):
 errors=[]
 for key in ['loaded','eof','seekConfirmed']:
  if d.get(key) is not True:errors.append(key)
 if d.get('frames',0)<=0:errors.append('frames')
 if hardware and d.get('hwdec')!='ohcodec':errors.append('hardware fallback')
 if d.get('ao')!='ohaudio':errors.append('audio output')
 if d.get('gpu')!=gpu:errors.append('GPU context')
 drift=d.get('maxDrift')
 if type(drift) not in (int,float) or not math.isfinite(drift) or drift<0 or drift>.1:errors.append('logical AV drift')
 if type(d.get('driftSamples')) is not int or d['driftSamples']<=0:errors.append('no valid drift samples')
 return {'passed':not errors,'errors':errors,'physicalAVSync':'not measured'}

#!/usr/bin/env python3
import hashlib,json,pathlib,re
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[3]
BASE=ROOT/'out/phase27/input-package/sources/mpv'
units=[('video/out/ohos_common.c',['struct vo_ohos_state','static bool is_hdr','static OH_NativeBuffer_ColorSpace get_color_space','static OH_NativeBuffer_StaticMetadata get_static_metadata','static void set_output_color','bool vo_ohos_set_color','void vo_ohos_invalidate_color']),('video/mp_image.c',['bool mp_image_params_equal','bool mp_image_params_static_equal'])]
units.append(('video/out/vo_gpu_next.c',['static void set_colorspace_hint']))
chunks=[];manifest=[]
for relative,markers in units:
 p=BASE/relative;raw=p.read_bytes();s=raw.decode();items=[]
 if relative.endswith('ohos_common.c') and 'static bool static_metadata_equal(' in s: markers.insert(markers.index('static void set_output_color'),'static bool static_metadata_equal')
 if relative.endswith('ohos_common.c') and 'static int64_t p27_monotonic_us(' in s: markers.insert(markers.index('static void set_output_color'),'static int64_t p27_monotonic_us')
 for marker in markers:
  m=list(re.finditer(r'^'+re.escape(marker)+r'\b',s,re.M));assert len(m)==1,(marker,len(m))
  start=m[0].start();brace=s.index('{',start);depth=1;end=brace+1
  # These specific source functions contain no braces in strings/comments.
  while depth:
   depth+=(s[end]=='{')-(s[end]=='}');end+=1
  if marker.startswith('struct '):assert s[end]==';';end+=1
  text=s[start:end];line=s[:start].count('\n')+1
  chunks.append(f'#line {line} "{relative}"\n{text}\n')
  items.append({'marker':marker,'startLine':line,'endLine':s[:end].count('\n')+1,'sha256':hashlib.sha256(text.encode()).hexdigest()})
 manifest.append({'source':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'functions':items})
(HERE/'actual-functions.inc').write_text('\n'.join(chunks))
(HERE/'source-binding.json').write_text(json.dumps({'extraction':'exact source slices, no algorithm rewrites','sources':manifest,'extractedSHA256':hashlib.sha256((HERE/'actual-functions.inc').read_bytes()).hexdigest()},indent=2)+'\n')
print('extracted',sum(len(x['functions']) for x in manifest),'exact units')

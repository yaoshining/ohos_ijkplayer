"""本轮文本绑定门禁；HAP不在CI中，此处不声称核验其真实字节。"""
from pathlib import Path
import hashlib,json,re
PLAYER={'libavcodec.so.62','libavfilter.so.11','libavformat.so.62','libavutil.so.60','libmpv.so','libswresample.so.6','libswscale.so.9'}
REUSED=PLAYER|{'libc++_shared.so'}
def unique(pairs):
 out={}
 for k,v in pairs:
  if k in out:raise ValueError('duplicate JSON key: '+k)
  out[k]=v
 return out
def read(p):return json.loads(p.read_text(),object_pairs_hook=unique)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(s):return isinstance(s,str) and re.fullmatch('[0-9a-f]{64}',s) is not None
def require(ok,reason):
 if not ok:raise ValueError(reason)
def verify(root):
 root=Path(root);policy=read(root/'binding-policy.json')
 expected={'currentLibraries':'normal-library-binding.json','targetArtifact':'target-artifact-manifest.json','targetSource':'target-source-binding.json','expectedHeader':'app/entry/src/main/cpp/expected.h','ciChecks':'text-consistency-only','localHAPCheck':'separate-real-bytes-verification'}
 require(policy.get('schema')==1 and policy.get('formalArtifactAllowed') is False,'policy boundary')
 require(all(policy.get(k)==v for k,v in expected.items()),'current authority policy')
 history=policy.get('historicalMetadata',{})
 require(history.get('path')=='app/lib-binding.json' and history.get('authority')=='historical-inherited-non-authoritative','history authority')
 require(digest(history.get('sha256')) and sha(root/history['path'])==history['sha256'],'history provenance digest')
 current=read(root/expected['currentLibraries']);artifact=read(root/expected['targetArtifact']);source=read(root/expected['targetSource'])
 require(isinstance(current,dict) and set(current)==REUSED and all(digest(s) for s in current.values()),'current library key/digest set')
 hap=artifact.get('libraries',{});names={'libs/arm64-v8a/'+name for name in REUSED|{'libphase22.so'}}
 require(isinstance(hap,dict) and set(hap)==names and all(digest(s) for s in hap.values()),'HAP library key/digest set')
 require(all(hap['libs/arm64-v8a/'+k]==v for k,v in current.items()),'HAP/current mismatch')
 require(digest(artifact.get('hapSHA')) and artifact['hapSHA']==source.get('targetHAPSHA256'),'HAP identity binding')
 require(digest(artifact.get('appSourceIndexSHA')) and artifact['appSourceIndexSHA']==source.get('frozenSourceIndexSHA256'),'source index identity binding')
 header=(root/expected['expectedHeader']).read_text();pairs=re.findall(r'\{"([^"\n]+)","([0-9a-f]{64})"\}',header)
 require(len(pairs)==7 and len(dict(pairs))==7 and set(dict(pairs))==PLAYER and dict(pairs)=={k:current[k] for k in PLAYER},'runtime expected header mismatch')
 files=source.get('textFiles',[]);paths=[r['path'] for r in files]
 require(paths and len(paths)==len(set(paths)),'duplicate/empty source paths')
 for row in files:
  p=root/'app'/row['path'];require(p.is_file() and not p.is_symlink() and p.resolve().is_relative_to((root/'app').resolve()) and sha(p)==row['sha256'],'target text source mismatch')
 require('lib-binding.json' in paths and 'entry/src/main/cpp/expected.h' in paths,'required snapshot metadata missing')
 return {'accepted':True,'currentReusedLibraries':len(current),'runtimeExpectedLibraries':len(pairs),'declaredHAPLibraries':len(hap),'HAPSHA256':artifact['hapSHA'],'targetSourceIndexSHA256':artifact['appSourceIndexSHA'],'historyOnlySHA256':history['sha256'],'historicalMetadataAuthoritative':False,'ciRealHAPBytesChecked':False,'formalArtifactAllowed':False}
if __name__=='__main__':print(json.dumps(verify(Path(__file__).resolve().parent),ensure_ascii=False,indent=2))

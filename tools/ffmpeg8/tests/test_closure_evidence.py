"""声明不能代替来源、构建前锁、两次实际产物的证据绑定。"""
import importlib.util,json,tempfile,unittest,hashlib
from pathlib import Path

def load():
    s=importlib.util.spec_from_file_location('closure',Path(__file__).parents[1]/'new-source-closure.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def fixture(expected=None,linux=False):
    m=load();source=(Path(__file__).parents[1]/'dependency-sources.lock.json').read_text()
    expected=expected or {n:{'sha256':'1'*64,'sizeBytes':1} for n in m.LIBS}
    recipe={'build-libsmbclient.sh':'2'*64}
    host={'ndkRoot':'/ndk','profile':'linux-debian-bookworm-20250204' if linux else 'macos-installed-API24','recipeFiles':[{'path':'/recipe/'+n,'sha256':h} for n,h in recipe.items()],
      'commands':[{'name':n,'sha256':'3'*64} for n in ['cc','clang','make','bison','flex','m4','perl','python3','pkg-config','ld']],
      'files':[{'path':'/ndk/sysroot/usr/include/header.h'},{'path':'/ndk/llvm/bin/clang'}]}
    docs={'host-lock':m.document(json.dumps(host)),'source-lock':m.document(source)}
    run={'exitCode':0,'freshOutput':True,'hostLockVerifiedAfter':True,'inputs':{'hostLockSha256':docs['host-lock']['sha256'],'sourceLockSha256':docs['source-lock']['sha256'],'recipe':recipe},'outputs':expected}
    if linux:run['effectiveEnvironment']={'OHOS_NDK':'/ndk','OHOS_SYSROOT':'/ndk/sysroot','OHOS_LLVM_BIN':'/ndk/llvm/bin','OHOS_ARCH':'arm64-v8a'}
    if linux:run['generatedTools']={n:{'hostLockSha256':docs['host-lock']['sha256'],'files':[{'path':'/generated/'+n,'sha256':'8'*64}]} for n in ['bison','heimdal']}
    docs.update({'first-record':m.document(json.dumps(run)),'second-record':m.document(json.dumps(run))})
    repeat={'allMatch':True,'rows':[{'path':n,'first':v,'second':v} for n,v in expected.items()],
      'builds':[{'path':'/build/'+n,'sha256':docs[n]['sha256']} for n in ['first-record','second-record']]}
    docs['static-repeat']=m.document(json.dumps(repeat))
    if linux:
        docs.update({n:m.document(v) for n,v in {
          'dockerfile':(Path(__file__).parents[1]/'ci/Dockerfile').read_text(),
          'image-inspect':json.dumps([{'Id':'sha256:'+'4'*64,'Architecture':'amd64','Os':'linux'}]),
          'container-inspect':json.dumps([{'Image':'sha256:'+'4'*64}]),
          'packages':''.join(n+'\t1.0\tamd64\n' for n in ['gcc','make','bison','flex','perl','python3','pkgconf']),
          'deb-sha256':'5'*64+'  /archive/tool.deb\n','sources-list':'20250204T000000Z'}.items()})
    return {'schemaVersion':1,'documents':docs},expected

class Closure(unittest.TestCase):
    def test_new_linux_closure_without_historical_claim(self):
        m=load();bundle,expected=fixture(linux=True);result=m.verify(bundle,expected)
        self.assertTrue(result['newSourceClosureVerified']);self.assertFalse(result['historicalSourceIdentityProven'])
    def test_macos_repeat_does_not_certify_acquisition(self):
        m=load();bundle,expected=fixture();result=m.verify(bundle,expected)
        self.assertTrue(result['staticRepeatVerified']);self.assertFalse(result['newSourceClosureVerified'])
    def test_container_identity_mismatch_rejected(self):
        m=load();bundle,expected=fixture(linux=True)
        bundle['documents']['container-inspect']=m.document(json.dumps([{'Image':'sha256:'+'6'*64}]))
        with self.assertRaises(ValueError):m.verify(bundle,expected)
    def test_changed_outputs_with_recomputed_document_hash_rejected(self):
        m=load();bundle,expected=fixture();run=json.loads(m.read_document(bundle['documents']['second-record']))
        run['outputs']['lib/libgmp.a']['sha256']='7'*64;bundle['documents']['second-record']=m.document(json.dumps(run))
        with self.assertRaises(ValueError):m.verify(bundle,expected)

    def test_claim_only_rejected(self):
        m=load()
        with self.assertRaises(ValueError):m.verify({'fullyVerified':True,'hostToolsVerified':True}, {})
    def test_tampered_document_rejected(self):
        m=load();row=m.document('fixed');row['text']='different'
        with self.assertRaises(ValueError):m.read_document(row)
    def test_pinned_document_roundtrip(self):
        m=load();self.assertEqual(m.read_document(m.document('fixed')),'fixed')
    def test_passing_repeat_requires_real_output_sets(self):
        m=load()
        a={'exitCode':0,'freshOutput':True,'hostLockVerifiedAfter':True,'inputs':{'hostLockSha256':'a'},'outputs':{'lib/a.a':{'sha256':'1','sizeBytes':1}}}
        b=json.loads(json.dumps(a));b['outputs']['lib/a.a']['sha256']='2'
        with self.assertRaises(ValueError):m.verify_pair(a,b,{'allMatch':True,'rows':[]},'a')
    def test_host_lock_digest_must_match_build(self):
        m=load();a={'exitCode':0,'freshOutput':True,'hostLockVerifiedAfter':True,'inputs':{'hostLockSha256':'a'},'outputs':{}}
        with self.assertRaises(ValueError):m.verify_pair(a,a,{'allMatch':True,'rows':[]},'b')
if __name__=='__main__':unittest.main()

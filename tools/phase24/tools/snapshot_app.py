from pathlib import Path
import hashlib,json,shutil,zipfile,datetime,argparse
p=argparse.ArgumentParser();p.add_argument('name');a=p.parse_args()
base=Path(__file__).resolve().parents[1];app=base/'app';out=base/'experiments'/a.name;out.mkdir(parents=True,exist_ok=False)
shutil.copytree(app/'entry/src',out/'source')
hap=app/'entry/build/default/outputs/default/entry-default-signed.hap';target=base/'private'/(a.name+'.hap');shutil.copy2(hap,target);target.chmod(0o600)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
libs={p.name:sha(p) for p in (app/'entry/libs/arm64-v8a').glob('*') if p.is_file()}
with zipfile.ZipFile(hap) as z:packed={Path(n).name:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('libs/arm64-v8a/') and Path(n).name in libs}
assert packed==libs
files={str(p.relative_to(out/'source')):sha(p) for p in (out/'source').rglob('*') if p.is_file()}
(out/'binding.json').write_text(json.dumps({'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hapSHA256':sha(hap),'privateHap':str(target.relative_to(base)),'publicationAllowed':False,'libraries':libs,'packagedEqual':True,'source':files},indent=2)+'\n')
print(a.name,sha(hap))

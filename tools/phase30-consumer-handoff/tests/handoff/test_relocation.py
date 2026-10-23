from pathlib import Path
import sys,tempfile,hashlib,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'build-runtime'))
from relocation_gate import relocated_records
h=lambda b:hashlib.sha256(b).hexdigest()
old=b'prefix=/opt/ffmpeg\n';new=b'prefix=/tmp/isolated\n'
cases=[('declared',True,None),('undeclared',False,'undeclared'),('wrong-before',False,'before'),('wrong-after',False,'after'),('missing',False,'missing'),('extra',False,'extra'),('non-pc',False,'non-pc'),('nonprefix-updated-after',False,'tamper')];results=[]
for name,want,mutation in cases:
 with tempfile.TemporaryDirectory() as td:
  source=Path(td)/'source';(source/'lib/pkgconfig').mkdir(parents=True);(source/'lib/pkgconfig/x.pc').write_bytes(old)
  r=Path(td)/'current';(r/'lib/pkgconfig').mkdir(parents=True);p=r/'lib/pkgconfig/x.pc';p.write_bytes(new);records=[{'path':'lib/pkgconfig/x.pc','sizeBytes':len(old),'sha256':h(old)}];rel=[{'path':'stage/lib/pkgconfig/x.pc','beforeSHA256':h(old),'afterSHA256':h(new)}]
  if mutation=='undeclared':rel=[]
  if mutation=='before':rel[0]['beforeSHA256']='0'*64
  if mutation=='after':rel[0]['afterSHA256']='0'*64
  if mutation=='missing':p.unlink()
  if mutation=='extra':(r/'unexpected').write_text('x')
  if mutation=='tamper':p.write_bytes(new+b'Libs: -levil\n');rel[0]['afterSHA256']=h(p.read_bytes())
  if mutation=='non-pc':records[0]['path']='x.so';p.rename(r/'x.so');rel[0]['path']='stage/x.so'
  try:relocated_records(r,records,rel,'stage',source,[('/opt/ffmpeg','/tmp/isolated')]);actual=True
  except (ValueError,FileNotFoundError):actual=False
  results.append({'name':name,'accepted':actual,'expected':want,'passed':actual==want})
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);(out/'results.json').write_text(json.dumps({'cases':results,'accepted':all(x['passed'] for x in results)},indent=2)+'\n');print(results);sys.exit(not all(x['passed'] for x in results))

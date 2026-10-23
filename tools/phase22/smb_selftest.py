from pathlib import Path
import json,hashlib
from impacket.smbconnection import SMBConnection,SessionError
base=Path(__file__).resolve().parents[1];c=json.loads((base/'private/smb.json').read_text());manifest=json.loads((base/'fixtures/manifest.json').read_text())['files'][-1]
def connect(password):
 s=SMBConnection(c['host'],c['host'],sess_port=c['port'],timeout=10);s.login(c['user'],password);return s
try:
 s=connect('known-wrong-password');s.close();raise AssertionError('wrong password accepted')
except AssertionError:raise
except SessionError as e:
 assert e.getErrorCode()==0xc000006d;wrong=hex(e.getErrorCode())
s=connect(c['password']);tree=s.connectTree('FIXTURE');f=s.openFile(tree,'seek.bin');chunks=[];offset=0
while offset<manifest['size']:
 b=s.readFile(tree,f,offset,min(65536,manifest['size']-offset));assert b;chunks.append(b);offset+=len(b)
assert hashlib.sha256(b''.join(chunks)).hexdigest()==manifest['sha256']
for r in manifest['ranges']:assert hashlib.sha256(s.readFile(tree,f,r['offset'],r['length'])).hexdigest()==r['sha256']
s.closeFile(tree,f);s.close();print(json.dumps({'wrongPasswordRejected':wrong,'bytes':offset,'rangeCount':len(manifest['ranges']),'fullAndRangeHashesMatch':True,'scope':'host Impacket client only; not target FFmpeg or device acceptance'}))

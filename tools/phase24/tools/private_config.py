"""私有配置只由指定路径读取；异常不回显数据。"""
import urllib.parse,struct,json,pathlib,os

def canonical_smb(url):
 try:
  s=urllib.parse.urlsplit(url)
  if s.scheme!='smb' or not s.hostname or s.username is not None or s.password is not None or s.query or s.fragment or any(ord(c)<32 or ord(c)==127 for c in url) or len(s.path.split('/'))<3:raise ValueError()
  path=urllib.parse.unquote(s.path,errors='strict')
  if any(ord(c)<32 for c in path):raise ValueError()
  return urllib.parse.urlunsplit(('smb',s.netloc,urllib.parse.quote(path,safe='/'),'', ''))
 except Exception:raise ValueError('invalid SMB location') from None

def make_device_config(url,auth):
 fields=[canonical_smb(url)]+[auth.get(k,'') for k in ['username','password','domain']]
 if any(not isinstance(s,str) or '\0' in s or len(s.encode())>65536 for s in fields):raise ValueError('invalid private configuration')
 return b''.join(struct.pack('<I',len(s.encode()))+s.encode() for s in fields)

def load_auth(path):
 p=pathlib.Path(path)
 if p.stat().st_mode&0o077:raise ValueError('private configuration permissions must be 0600')
 try:
  d=json.loads(p.read_text())
  if not isinstance(d,dict) or not d.get('username') or not d.get('password'):raise ValueError()
  make_device_config('smb://placeholder/share/file',d)
  return d
 except Exception:raise ValueError('private configuration incomplete') from None

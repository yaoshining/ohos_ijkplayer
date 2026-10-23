"""只读指定SMB文件，经loopback单文件range适配供ffprobe取元数据。禁止目录枚举。"""
import argparse,json,pathlib,threading,http.server,subprocess,urllib.parse,hashlib,logging,time
from private_config import canonical_smb,load_auth

def run(location,credentials):
 from impacket.smbconnection import SMBConnection
 from impacket.smb3structs import FILE_READ_DATA,FILE_READ_ATTRIBUTES,FILE_OPEN,SMB2_FILE_BASIC_INFO,FILE_BASIC_INFORMATION
 auth=load_auth(credentials);url=urllib.parse.urlsplit(canonical_smb(location));parts=urllib.parse.unquote(url.path).lstrip('/').split('/',1)
 conn=None;tid=None;fid=None;server=None
 try:
  conn=SMBConnection(url.hostname,url.hostname,sess_port=url.port or 445,timeout=10)
  conn.login(auth['username'],auth['password'],auth.get('domain',''))
  tid=conn.connectTree(parts[0]);fid=conn.openFile(tid,parts[1].replace('/','\\'),desiredAccess=FILE_READ_DATA|FILE_READ_ATTRIBUTES,creationDisposition=FILE_OPEN)
  info=conn.queryInfo(tid,fid);size=int(info['EndOfFile']);basic=FILE_BASIC_INFORMATION(conn.queryInfo(tid,fid,fileInfoClass=SMB2_FILE_BASIC_INFO));lock=threading.Lock();stats={'readBytes':0,'readCalls':0};deadline=time.monotonic()+60;budget=64*1024*1024
  def read(offset,length):
   with lock:
    if offset<0 or length<0 or offset+length>size or time.monotonic()>deadline or stats['readBytes']+length>budget:raise RuntimeError('metadata_read_budget')
    b=conn.readFile(tid,fid,offset,length);stats['readBytes']+=len(b);stats['readCalls']+=1;return b
  prefix=read(0,min(65536,size));prefixsha=hashlib.sha256(prefix).hexdigest()
  class Handler(http.server.BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_HEAD(self):self.serve(False)
   def do_GET(self):self.serve(True)
   def serve(self,body):
    if self.path!='/sample':self.send_error(404);return
    begin,end=0,size-1;range_=self.headers.get('Range')
    try:
     if range_:
      v=range_.removeprefix('bytes=').split('-');begin=int(v[0]);end=min(end,int(v[1])) if v[1] else end
     if begin<0 or begin>end:raise ValueError()
     self.send_response(206 if range_ else 200);self.send_header('Content-Type','video/mp4');self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(end-begin+1))
     if range_:self.send_header('Content-Range',f'bytes {begin}-{end}/{size}')
     self.end_headers()
     if body:
      while begin<=end:
       b=read(begin,min(65536,end-begin+1))
       if not b:break
       self.wfile.write(b);begin+=len(b)
    except (BrokenPipeError,ConnectionResetError):pass
    except Exception: self.close_connection=True
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
  server.daemon_threads=False;threading.Thread(target=server.serve_forever,daemon=True).start()
  cmd=['ffprobe','-v','error','-rw_timeout','10000000','-analyzeduration','5000000','-probesize','8000000','-show_streams','-show_format','-of','json',f'http://127.0.0.1:{server.server_port}/sample']
  r=subprocess.run(cmd,capture_output=True,timeout=50)
  if r.returncode: return {'sampleId':'nas-media-01','okay':False,'stage':'ffprobe','code':r.returncode,**stats}
  probe=json.loads(r.stdout);whitelist=['index','codec_name','codec_type','profile','level','width','height','pix_fmt','color_range','color_space','color_transfer','color_primaries','chroma_location','r_frame_rate','avg_frame_rate','duration','bit_rate','bits_per_raw_sample','sample_rate','channels','channel_layout','side_data_list']
  streams=[{k:v for k,v in s.items() if k in whitelist} for s in probe['streams']]
  return {'sampleId':'nas-media-01','okay':True,'fileBytes':size,'lastWriteTime':int(basic['LastWriteTime']),'duration':probe.get('format',{}).get('duration'),'format':probe.get('format',{}).get('format_name'),'streams':streams,'prefixBytes':len(prefix),'prefixSHA256':prefixsha,'fullFileSHA256':None,'fullFileHashVerified':False,'smbDialect':str(conn.getDialect()),**stats}
 finally:
  if server:server.shutdown();server.server_close()
  if conn:
   try:
    if fid is not None:conn.closeFile(tid,fid)
    conn.logoff();conn.close()
   except Exception:pass

def main():
 logging.disable(logging.CRITICAL)
 p=argparse.ArgumentParser();p.add_argument('--location-file',required=True);p.add_argument('--credentials',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 try:result=run(pathlib.Path(a.location_file).read_text().strip(),a.credentials)
 except Exception as e:
  code=e.getErrorCode() if hasattr(e,'getErrorCode') else getattr(e,'errno',None)
  result={'sampleId':'nas-media-01','okay':False,'stage':'connect_or_metadata','errorType':type(e).__name__,'code':code}
 pathlib.Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
 if not result['okay']:raise SystemExit(1)
if __name__=='__main__':main()

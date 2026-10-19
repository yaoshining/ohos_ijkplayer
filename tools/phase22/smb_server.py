from pathlib import Path
import argparse,json,logging,time,os
from impacket.smbserver import SimpleSMBServer
from impacket.ntlm import compute_lmhash,compute_nthash
from impacket import smb3structs as s
p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--share',type=Path,required=True);a=p.parse_args();c=json.loads(a.config.read_text())
logging.disable(logging.CRITICAL)
server=SimpleSMBServer(listenAddress=c['host'],listenPort=c['port']);server.addShare('FIXTURE',str(a.share.resolve()),readOnly='yes');server.setSMB2Support(True)
core=server.getServer();cfg=core.getServerConfig();cfg.set('global','anonymous_logon','no');core.setServerConfig(cfg);core.processConfigFile();core.log=lambda *args,**kwargs:None
server.addCredential(c['user'],0,compute_lmhash(c['password']),compute_nthash(c['password']))
def emit(event,**kw):print(json.dumps({'event':event,'time':time.time(),**kw}),flush=True)
def auth(**kw):emit('auth',authenticated=bool(kw['connData'].get('Authenticated')))
server.setAuthCallback(auth)
def read(conn,sv,packet):
 req=s.SMB2Read(packet['Data']);result=original(conn,sv,packet);emit('read',connection=conn,offset=req['Offset'],length=req['Length'],status=result[2]);return result
original=core.hookSmb2Command(s.SMB2_READ,read)
emit('started',pid=os.getpid(),host=c['host'],port=c['port'],readOnly=True,anonymous=False)
server.start()

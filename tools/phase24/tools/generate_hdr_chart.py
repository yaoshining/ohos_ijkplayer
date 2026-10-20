"""原创数学HDR诊断图案；不代表物理校准或标准图案认证。"""
import array,math,pathlib,sys
STEPS={'pq':[0,.005,.1,1,10,100,203,1000],'hlg':[0,.001,.01,.05,1/12,.18,.5,1],'sdr':[0,.001,.01,.05,.18,.5,.75,1]}
def curve(mode,v):
 if mode not in STEPS or not math.isfinite(v) or v<0 or v>(10000 if mode=='pq' else 1):raise ValueError('invalid transfer input')
 if mode=='pq':
  p=(v/10000)**(2610/16384)
  return ((3424/4096+(2413/128)*p)/(1+(2392/128)*p))**(2523/32)
 if mode=='hlg':
  a=.17883277;b=1-4*a;c=.5-a*math.log(4*a)
  return math.sqrt(3*v) if v<=1/12 else a*math.log(12*v-b)+c
 return 4.5*v if v<.018 else 1.099*v**.45-.099
def code(mode,v):return round(64+876*curve(mode,v))
def generate(mode):
 if mode not in STEPS:raise ValueError('invalid mode')
 w,h=640,360;kr,kb=(.2126,.0722) if mode=='sdr' else (.2627,.0593);peak=1000 if mode=='pq' else 1
 colors=[(1,1,1),(1,1,0),(0,1,1),(0,1,0),(1,0,1),(1,0,0),(0,0,1),(0,0,0)]
 Y=[];Cb=[];Cr=[]
 for y in range(h):
  for x in range(w):
   rgb=[peak*x/(w-1)]*3 if y<h//3 else [STEPS[mode][min(7,x*8//w)]]*3 if y<2*h//3 else [c*peak for c in colors[min(7,x*8//w)]]
   r,g,b=[curve(mode,v) for v in rgb];lum=kr*r+(1-kr-kb)*g+kb*b
   Y.append(round(64+876*lum));Cb.append((b-lum)/(2*(1-kb)));Cr.append((r-lum)/(2*(1-kr)))
 out=array.array('H',Y)
 for plane in [Cb,Cr]:
  for y in range(0,h,2):
   for x in range(0,w,2):out.append(round(512+896*sum(plane[(y+dy)*w+x+dx] for dy in (0,1) for dx in (0,1))/4))
 if sys.byteorder!='little':out.byteswap()
 return out.tobytes()
if __name__=='__main__':pathlib.Path(sys.argv[2]).write_bytes(generate(sys.argv[1]))

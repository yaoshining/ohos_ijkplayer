import pathlib,subprocess,json,hashlib,array
root=pathlib.Path('out/phase24/fixtures/hdr')
root.mkdir(parents=True,exist_ok=True)
from generate_hdr_chart import generate
for mode in ['pq','hlg','sdr']:(root/(mode+'.yuv')).write_bytes(generate(mode))
for mode,p,tr,m,cprim,ctrc,cspace in [('pq',9,16,9,'bt2020','smpte2084','bt2020nc'),('hlg',9,18,9,'bt2020','arib-std-b67','bt2020nc'),('sdr',1,1,1,'bt709','bt709','bt709')]:
    params=f'pools=1:frame-threads=1:crf=10:level-idc=3.1:vbv-maxrate=6000:vbv-bufsize=12000:colorprim={p}:transfer={tr}:colormatrix={m}:range=limited:chromaloc=1'
    if mode=='pq': params+=':master-display=G(8500,39850)B(6550,2300)R(35400,14600)WP(15635,16450)L(10000000,0):max-cll=1000,0'
    dst=root/(mode+'-bounded.mp4')
    command=['ffmpeg','-hide_banner','-nostdin','-v','warning','-stream_loop','-1','-f','rawvideo','-pixel_format','yuv420p10le','-video_size','640x360','-framerate','30','-i',str(root/(mode+'.yuv')),'-t','12','-c:v','libx265','-preset','ultrafast','-x265-params',params,'-chroma_sample_location','center','-tag:v','hvc1','-color_range','tv','-color_primaries',cprim,'-color_trc',ctrc,'-colorspace',cspace,'-movflags','+faststart','-y',str(dst)]
    with (root/(mode+'-bounded.log')).open('w') as log: subprocess.run(command,stdout=log,stderr=log,check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_streams','-read_intervals','%+#1','-show_frames','-of','json',str(dst)]))
    (root/(mode+'-probe.json')).write_text(json.dumps(probe,indent=2))
    decoded=subprocess.check_output(['ffmpeg','-v','error','-i',str(dst),'-frames:v','1','-f','rawvideo','-pix_fmt','yuv420p10le','-'])
    a=array.array('H'); a.frombytes(decoded)
    b=array.array('H'); b.frombytes((root/(mode+'.yuv')).read_bytes())
    centers=[180*640+(i*80+40) for i in range(8)]
    stream=probe['streams'][0]
    assert [b[i] for i in centers]==[a[i] for i in centers], 'decoded center mismatch'
    assert stream['profile']=='Main 10' and stream['pix_fmt']=='yuv420p10le'
    print(json.dumps({'mode':mode,'bytes':dst.stat().st_size,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'profile':stream['profile'],'level':stream['level'],'duration':stream['duration'],'frames':stream['nb_frames'],'steps_source':[b[i] for i in centers],'steps_decoded':[a[i] for i in centers],'max_abs_sample_error':max(abs(x-y) for x,y in zip(a,b)),'side_data':probe['frames'][0].get('side_data_list',[])},ensure_ascii=False))

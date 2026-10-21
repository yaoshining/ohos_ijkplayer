#!/usr/bin/env python3
"""T013: rerun Phase27 HDR/SEI/AnnexB/priority regressions from Phase28 source.

Host FFmpeg archives are rebuilt from the Phase28 source tree; the OHCodec HDR
helper is compiled directly from that tree. Results are not inherited from
Phase27.
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('PHASE28_BINDING_ROOT', str(HERE.parents[4])))
SRC = Path(os.environ.get('PHASE28_FFMPEG_ROOT', str(ROOT/'out/phase28/ffmpeg-input/source')))
HOST = Path(os.environ.get('PHASE28_HOST_BUILD', str(ROOT/'out/phase28/research/host-phase28')))
HB = HOST/'build' if (HOST/'build/libavcodec/libavcodec.a').exists() else HOST
OUT = Path(sys.argv[1])
if OUT.exists(): raise SystemExit('refusing to overwrite '+str(OUT))
OUT.mkdir(parents=True)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def build(name, extra_sources):
    cmd = ['clang','-O1','-g','-fsanitize=address,undefined',
           '-fno-omit-frame-pointer','-I'+str(HB),'-I'+str(SRC),'-I'+str(SRC/'libavcodec'),
           str(HERE/(name+'.c')),str(SRC/'libavcodec/ohcodec_hdr.c'),
           *[str(SRC/s) for s in extra_sources],
           str(HB/'libavcodec/libavcodec.a'),str(HB/'libavutil/libavutil.a'),
           '-lm','-pthread','-o',str(OUT/name)]
    r = subprocess.run(cmd,capture_output=True,text=True)
    (OUT/(name+'-compile.log')).write_text(r.stdout+r.stderr)
    return cmd, r.returncode
rows=[]
tests = [
 ('hdr_test', [], None),
 ('annexb_test', [], None),
 ('preference_test', [], None),
]
for name, extra, _ in tests:
    cmd, rc = build(name, extra)
    row = {'name':name,'compileCommand':cmd,'compileExit':rc}
    if rc == 0:
        cases = [None] if name == 'hdr_test' else (
            ['extradata-only','sei-after-ps','sei-before-ps','non-irap'] if name == 'annexb_test'
            else ['prefer-packet','packet-default'])
        runs=[]
        for case in cases:
            argv=[str(OUT/name)] + ([case] if case else [])
            p=subprocess.run(argv,capture_output=True,text=True,
                env=dict(os.environ,ASAN_OPTIONS='halt_on_error=1:detect_leaks=0',
                         UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1'))
            (OUT/(name+('-'+(case or 'default'))+'.log')).write_text(p.stdout+p.stderr)
            runs.append({'case':case or 'default','exitCode':p.returncode,
                         'stdout':p.stdout,'stderr':p.stderr})
        row['runs']=runs
    rows.append(row)
binding = {
 'phase28Source': str(SRC),
 'sourceFiles': {str(p.relative_to(SRC)):sha(p) for p in [
    SRC/'libavcodec/ohcodec_hdr.c', SRC/'libavcodec/bsf/hevc_mp4toannexb.c']},
 'hostArchives': {str(p.relative_to(ROOT)):sha(p) for p in [
    HB/'libavcodec/libavcodec.a', HB/'libavutil/libavutil.a']},
 'testSources': {p.name:sha(p) for p in [HERE/'hdr_test.c',HERE/'annexb_test.c',HERE/'preference_test.c']},
}
ok = all(r.get('compileExit')==0 and all(x['exitCode']==0 for x in r.get('runs',[])) for r in rows)
res={'task':'T013','source':'phase28','binding':binding,'tests':rows,'accepted':ok}
(OUT/'results.json').write_text(json.dumps(res,indent=2)+'\n')
print('ACCEPTED' if ok else 'NOT ACCEPTED')
for r in rows:
 print(r['name'],'compile',r['compileExit'],'runs',[(x['case'],x['exitCode']) for x in r.get('runs',[])])
raise SystemExit(0 if ok else 1)

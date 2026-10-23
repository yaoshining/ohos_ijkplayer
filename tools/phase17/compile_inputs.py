#!/usr/bin/env python3
"""Hash actual Ninja compiler dependencies after a build, without executing targets.
Only --output is written. Compare canonical run/sdk identities, never file content.
"""
from pathlib import Path
import argparse,hashlib,json,re

def parse_ninja_deps(text):
    result={};current=None;expected=None
    def finish():
        if current is not None and len(result[current])!=expected:raise ValueError('Ninja dependency count mismatch: '+current)
    for line in text.splitlines():
        if not line.strip():continue
        match=re.fullmatch(r'(.+): #deps (\d+), deps mtime \d+ \(VALID\)',line)
        if match:
            finish();current=match[1];expected=int(match[2])
            if current in result or expected<1:raise ValueError('duplicate or empty dependency block: '+current)
            result[current]=[]
        elif line.startswith('    ') and current is not None:
            path=line[4:]
            if not path:raise ValueError('empty dependency path')
            result[current].append(path)
        else:raise ValueError('unsupported or stale Ninja dependency line: '+line)
    finish()
    if not result:raise ValueError('missing Ninja dependency evidence')
    return result

def pin(path):
    data=Path(path).read_bytes()
    return {'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def collect_compile_inputs(run_root,sdk_root):
    run=Path(run_root).resolve();sdk=Path(sdk_root).resolve();files={};objects=[];evidence=[];primary=set();stage_counts={};actual_paths={}
    def identity(path):
        path=path.resolve()
        if path.is_relative_to(run):return 'run/'+path.relative_to(run).as_posix()
        if path.is_relative_to(sdk):return 'sdk/'+path.relative_to(sdk).as_posix()
        raise ValueError('compiler dependency outside declared run/sdk: '+str(path))
    for stage in ['libplacebo','mpv']:
        build=run/stage/'build';log=run/'logs'/(stage+'-deps.log');database=build/'compile_commands.json'
        for path in [log,database]:evidence.append({'path':str(path),'before':pin(path)})
        blocks=parse_ninja_deps(log.read_text());compile_rows=json.loads(database.read_text());expected={}
        for row in compile_rows:
            if Path(row['directory']).resolve()!=build.resolve():raise ValueError('compile database directory mismatch')
            obj=identity(build/row['output']);source=identity(build/row['file'])
            if obj in expected:raise ValueError('duplicate compile output')
            expected[obj]=source;primary.add(source)
        observed={identity(build/obj) for obj in blocks}
        if not expected or observed!=set(expected):raise ValueError('dependency objects do not exactly cover compile database: '+stage)
        for obj,dependencies in blocks.items():
            obj_id=identity(build/obj);deps=[]
            for name in dependencies:
                path=(build/name).resolve();key=identity(path)
                record={'path':key,**pin(path),'generated':any(key.startswith('run/'+s+'/build/') for s in ['mpv','libplacebo'])}
                if key in files and files[key]!=record:raise ValueError('input changed during collection: '+key)
                files[key]=record;actual_paths[key]=path;deps.append(key)
            if expected[obj_id] not in deps:raise ValueError('primary source absent from actual dependencies')
            objects.append({'object':obj_id,'source':expected[obj_id],'dependencies':sorted(deps)})
        stage_counts[stage]={'objects':len(expected),'uniqueFiles':len({identity(build/n) for deps in blocks.values() for n in deps})}
    for row in evidence:
        row['after']=pin(row['path'])
        if row['before']!=row['after']:raise ValueError('evidence changed during collection')
    for key,path in actual_paths.items():
        if pin(path)!={k:files[key][k] for k in ['size','sha256']}:raise ValueError('input changed at final pin: '+key)
    for key,row in files.items():row['role']='primary-source' if key in primary else 'included-file'
    return {'schemaVersion':1,'runRoot':str(run),'sdkRoot':str(sdk),'coverageVerified':True,'counts':{'objects':len(objects),'uniqueFiles':len(files),'sources':len(primary),'includedFiles':len(set(files)-primary),'generatedFiles':sum(r['generated'] for r in files.values()),'stages':stage_counts},'files':sorted(files.values(),key=lambda r:r['path']),'objects':sorted(objects,key=lambda r:r['object']),'evidence':evidence,'allObservedFilesUnchangedDuringCollection':True,'scope':'Ninja actual dependency records plus current post-build bytes; not a historical read trace','targetExecuted':False}

def compare_compile_inputs(a,b):
    for row in [a,b]:
        if row.get('coverageVerified') is not True or row.get('allObservedFilesUnchangedDuringCollection') is not True:raise ValueError('missing verified compiler input coverage')
        if not row.get('files') or not row.get('objects') or not row.get('counts'):raise ValueError('missing compiler inputs')
    if Path(a['runRoot']).resolve()==Path(b['runRoot']).resolve():raise ValueError('two distinct roots required')
    different=[key for key in ['counts','files','objects'] if a[key]!=b[key]]
    af={r['path']:r for r in a['files']};bf={r['path']:r for r in b['files']}
    return {'passed':not different,'differentFields':different,'differentFiles':[k for k in sorted(set(af)|set(bf)) if af.get(k)!=bf.get(k)],'countsA':a['counts'],'countsB':b['counts'],'fileContentNormalized':False,'targetExecuted':False}

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
    collect=sub.add_parser('collect');collect.add_argument('--run-root',type=Path,required=True);collect.add_argument('--sdk',type=Path,required=True);collect.add_argument('--output',type=Path,required=True)
    compare=sub.add_parser('compare');compare.add_argument('--a',type=Path,required=True);compare.add_argument('--b',type=Path,required=True);compare.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    result=collect_compile_inputs(args.run_root,args.sdk) if args.mode=='collect' else compare_compile_inputs(json.loads(args.a.read_text()),json.loads(args.b.read_text()))
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['files','objects','evidence']},indent=2))
    if result.get('passed') is False:raise SystemExit(1)
if __name__=='__main__':main()

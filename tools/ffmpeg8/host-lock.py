#!/usr/bin/env python3
"""构建前冻结实际工具；验证阶段只读，漂移即拒绝。来源资格单独表示。"""
import argparse,hashlib,json,os,platform,shutil,subprocess
from pathlib import Path

ENV_KEYS=['PATH','LC_ALL','TZ','SOURCE_DATE_EPOCH','PYTHONHASHSEED','SDKROOT','MACOSX_DEPLOYMENT_TARGET','CC','CXX','CFLAGS','CXXFLAGS','CPPFLAGS','LDFLAGS','PKG_CONFIG_PATH','PKG_CONFIG_LIBDIR','BISON_PKGDATADIR','PERL5LIB','PYTHONPATH']
COMMANDS=['bash','sh','make','cc','c++','clang','bison','flex','m4','perl','python3','pkg-config','sed','awk','tar','gzip','xz','find','sort','patch','git','ar','ld','ranlib','strip','install','cp','ln','env','uname','grep','cut','tr','head','xargs','autoconf','automake','glibtoolize','libtoolize','rsync']
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def record(p):
    p=Path(p).resolve();return {'path':str(p),'sha256':sha(p),'sizeBytes':p.stat().st_size}
def verify(lock):
    for row in lock.get('commands',[]):
        p=shutil.which(row['name'])
        if not p or str(Path(p).resolve())!=row['path']:raise ValueError('工具解析路径漂移: '+row['name'])
    for row in lock['files']+lock.get('commands',[]):
        p=Path(row['path'])
        if not p.is_file() or sha(p)!=row['sha256']:raise ValueError('工具或输入摘要漂移: '+str(p))
    for key,value in lock['environment'].items():
        if os.environ.get(key)!=value:raise ValueError('构建环境漂移: '+key)
    return True

def verify_binding(lock,ndk,recipe):
    if str(ndk.resolve())!=lock.get('ndkRoot'):raise ValueError('实际 NDK 与构建前锁不一致')
    if str(recipe.resolve())!=lock.get('recipeRoot'):raise ValueError('实际 recipe 与构建前锁不一致')
    actual=[record(p) for p in sorted(recipe.rglob('*')) if p.is_file()]
    if actual!=lock.get('recipeFiles'):raise ValueError('recipe 文件集合或摘要漂移')

def capture(ndk,recipe,profile):
    commands=[]
    for name in COMMANDS:
        p=shutil.which(name)
        if not p:continue
        row=dict(record(p),name=name)
        if name in ['make','cc','clang','bison','flex','m4','perl','python3','pkg-config','autoconf','automake']:
            r=subprocess.run([p,'-v' if name=='perl' else '--version'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            row['version']=r.stdout.strip()[:2000]
        commands.append(row)
    # SDK 系统头与 clang resource headers 也是编译输入，不只锁编译器可执行文件。
    files=[record(p) for p in sorted(ndk.rglob('*')) if p.is_file()]
    files.extend(record(p) for p in sorted(recipe.rglob('*')) if p.is_file() and '__pycache__' not in p.parts)
    if platform.system()=='Darwin':
        for n in ['clang','clang++','ld']:
            p=subprocess.check_output(['xcrun','--find',n],text=True).strip();files.append(record(p))
    return {'schemaVersion':1,'profile':profile,'host':platform.platform(),'ndkRoot':str(ndk.resolve()),'recipeRoot':str(recipe.resolve()),'recipeFiles':[record(p) for p in sorted(recipe.rglob('*')) if p.is_file()],'commands':commands,'files':files,
      'environment':{k:os.environ.get(k) for k in ENV_KEYS},'acquisitionVerified':False,
      'acquisitionNote':'本清单在构建前生成并重验；自身不是工具获取来源的证明。Linux 另绑定固定容器构建证据。'}

def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True)
    c=s.add_parser('capture');c.add_argument('--ndk',type=Path,required=True);c.add_argument('--recipe',type=Path,required=True);c.add_argument('--profile',required=True);c.add_argument('--output',type=Path,required=True)
    v=s.add_parser('verify');v.add_argument('--lock',type=Path,required=True)
    a=p.parse_args()
    if a.cmd=='verify':verify(json.loads(a.lock.read_text()));print('host lock verified');return
    if a.output.exists():raise ValueError('拒绝覆盖构建前工具锁')
    a.output.write_text(json.dumps(capture(a.ndk,a.recipe,a.profile),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()

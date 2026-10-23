#!/usr/bin/env python3
"""构建前冻结实际工具；验证阶段只读，漂移即拒绝。来源资格单独表示。"""
import argparse,hashlib,json,os,platform,shutil,subprocess
from pathlib import Path

DISPATCHER_REFERENCE='/usr/bin/cc'
XCRUN='/usr/bin/xcrun'
XCODE_SELECT='/usr/bin/xcode-select'
SELECTOR_KEYS=['DEVELOPER_DIR','SDKROOT','TOOLCHAINS']
ENV_KEYS=SELECTOR_KEYS+['PATH','LC_ALL','TZ','SOURCE_DATE_EPOCH','PYTHONHASHSEED','SDKROOT','MACOSX_DEPLOYMENT_TARGET','CC','CXX','CFLAGS','CXXFLAGS','CPPFLAGS','LDFLAGS','PKG_CONFIG_PATH','PKG_CONFIG_LIBDIR','BISON_PKGDATADIR','PERL5LIB','PYTHONPATH']
COMMANDS=['bash','sh','make','cc','c++','clang','bison','flex','m4','perl','python3','pkg-config','sed','awk','tar','gzip','xz','find','sort','patch','git','ar','ld','ranlib','strip','install','cp','ln','env','uname','grep','cut','tr','head','xargs','autoconf','automake','glibtoolize','libtoolize','rsync']
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def record(p):
    p=Path(p).resolve();return {'path':str(p),'sha256':sha(p),'sizeBytes':p.stat().st_size}
def directory_record(root):
    root=Path(root).absolute();entries=[];files={}
    def visit(path,ancestors):
        try:target=path.resolve(strict=True)
        except (OSError,RuntimeError) as exc:raise ValueError('资源链接悬空或循环: '+str(path)) from exc
        directory=path.is_dir()
        if not directory and not path.is_file():raise ValueError('不支持的工具资源类型: '+str(path))
        entries.append({'relative':str(path.relative_to(root)),'kind':'directory' if directory else 'file','target':str(target),'link':os.readlink(path) if path.is_symlink() else None})
        if directory:
            if target in ancestors:raise ValueError('资源目录链接循环: '+str(path))
            for child in sorted(path.iterdir()):visit(child,ancestors|{target})
        else:files[str(target)]=record(target)
    if not root.is_dir():raise ValueError('工具资源目录缺失: '+str(root))
    visit(root,set())
    return {'root':str(root),'entries':entries,'files':[files[k] for k in sorted(files)]}

def capture_dispatch(commands):
    if platform.system()!='Darwin':return None
    # Apple /usr/bin 中多个名字是同一转发器；仅解析实际PATH选中的转发器。
    signature=sha(DISPATCHER_REFERENCE);resolved=[];resources={};subtools=[]
    for row in commands:
        if row['sha256']!=signature:continue
        target=Path(subprocess.check_output([XCRUN,'--no-cache','--find',row['name']],text=True).strip()).resolve()
        if not target.is_file() or not os.access(target,os.X_OK):raise ValueError('实际Xcode工具缺失/不可执行: '+str(target))
        resolved.append({'name':row['name'],'launcherPath':row['path'],'actual':record(target)})
        if row['name']=='bison':
            directory=target.parent.parent/'share/bison';resources[str(directory)]=directory_record(directory)
        if row['name'] in ('cc','c++','clang','clang++'):
            resource=subprocess.check_output([str(target),'-print-resource-dir'],text=True).strip()
            if resource not in resources:resources[resource]=directory_record(resource)
            linker=Path(subprocess.check_output([XCRUN,'--no-cache','--find','ld'],text=True).strip())
            if not linker.is_file() or not os.access(linker,os.X_OK):raise ValueError('Xcode编译器链接子工具缺失')
            subtools.append(record(linker))
    # 不改变非转发工具的选择；例如Homebrew/Conda程序继续由commands记录。
    return {'schemaVersion':1,'selectorDefault':subprocess.check_output([XCODE_SELECT,'-p'],text=True).strip(),
      'selectorEnvironment':{k:os.environ.get(k) for k in SELECTOR_KEYS},'resolverFiles':[record(XCRUN),record(XCODE_SELECT)],
      'resolvedCommands':resolved,'compilerSubtools':list({x['path']:x for x in subtools}.values()),
      'resourceDirectories':list(resources.values()),
      'scope':'PATH中Apple转发入口、实际工具、编译器resource目录与ld、Bison骨架；Flex内置骨架由二进制绑定，M4由受控环境显式选择。非整套Xcode/SDK或历史来源证明。'}

def verify(lock):
    if lock.get('xcodeDispatch') is not None:
        try:current=capture_dispatch(lock.get('commands',[]))
        except (OSError,subprocess.CalledProcessError) as exc:raise ValueError('无法复验Xcode实际工具解析') from exc
        if current!=lock['xcodeDispatch']:raise ValueError('Xcode实际工具、选择器或资源集合漂移')
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
    dispatch=capture_dispatch(commands)
    return {'schemaVersion':2,'profile':profile,'host':platform.platform(),'ndkRoot':str(ndk.resolve()),'recipeRoot':str(recipe.resolve()),'recipeFiles':[record(p) for p in sorted(recipe.rglob('*')) if p.is_file()],'commands':commands,'files':files,'xcodeDispatch':dispatch,
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

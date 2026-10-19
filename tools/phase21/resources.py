"""仅在全新独立根准备固定资源；不修改调用进程环境。"""
from pathlib import Path
import argparse,hashlib,json,shutil
HERE=Path(__file__).resolve().parent
FONT_SHA='7b8a5f6cfd5fdb06ddac7d976935babf05afa5ef7bf6b8c1b8cf919b481d33e1'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prepare(root,font=None):
 root=Path(root);font=Path(font) if font else HERE/'resources/font1.ttf'
 if font.is_symlink() or digest(font)!=FONT_SHA:raise ValueError('固定字体摘要不符')
 root.mkdir(parents=True,exist_ok=False);root=root.resolve()
 for name in ['state/private','state/state','state/lock','cache/demux','resources/fonts']:(root/name).mkdir(parents=True,exist_ok=True)
 shutil.copyfile(font,root/'resources/fonts/font1.ttf')
 shutil.copyfile(HERE/'resources/LICENSE-font.txt',root/'resources/LICENSE-font.txt')
 (root/'smb.conf').write_text('[global]\nclient min protocol = SMB2\n')
 (root/'black.ppm').write_bytes(b'P6\n640 360\n255\n'+bytes(640*360*3))
 (root/'subtitle.ass').write_text('[Script Info]\nScriptType: v4.00+\nPlayResX: 640\nPlayResY: 360\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Pixel Operator Mono,32,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,1,0,2,10,10,20,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:00.00,0:00:30.00,Default,,0,0,0,,ABC abc 012\n')
 d={'config_file':str(root/'smb.conf'),'state_root':str(root/'state'),'cache_root':str(root/'cache'),'resource_root':str(root/'resources')}
 (root/'config.json').write_text(json.dumps(d,indent=2)+'\n');return d
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();print(json.dumps(prepare(a.root)))

#!/usr/bin/env python3
"""Phase11 独立跨目录验收入口。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hx509-history'))
import run as history

def compare_chains(first, second, out, compare, build_fixed):
    paired = compare(first, second)
    history.write(out / 'ffmpeg-repeat.json', paired)
    if not paired['allMatch']:
        raise ValueError('独立目录的配对六库或开发文件不一致；不能以固定 root 对照替代')
    return {'pairedAllMatch':True, 'fixedRootAllMatch':None}

if __name__ == '__main__':
    history.main(labels=('a', 'longer-build-root-b'), comparison_policy=compare_chains,
                 extra_recipe_files=(Path(__file__).resolve(),))

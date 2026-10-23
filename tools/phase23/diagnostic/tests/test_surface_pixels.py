from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SurfacePixels(unittest.TestCase):
    def test_physical_rect_and_invalid_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            shutil.copyfile(ROOT / "SurfaceSize.ts", path / "SurfaceSize.ts")
            (path / "test.mjs").write_text("""
import assert from 'node:assert/strict';
import { surfacePixels } from './SurfaceSize.ts';
assert.deepEqual(surfacePixels({surfaceWidth:2880,surfaceHeight:1620}),{width:2880,height:1620});
assert.deepEqual(surfacePixels({surfaceWidth:960,surfaceHeight:540}),{width:960,height:540});
for(const n of [0,-1,NaN,Infinity,0.1,2147483648]){
 assert.throws(()=>surfacePixels({surfaceWidth:n,surfaceHeight:540}));
 assert.throws(()=>surfacePixels({surfaceWidth:960,surfaceHeight:n}));
}
""")
            subprocess.run(["node", "--experimental-strip-types", str(path / "test.mjs")], check=True)

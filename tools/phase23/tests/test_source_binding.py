"""验证审阅补丁可由锁定前像还原本次实际编译函数来源。"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Binding(unittest.TestCase):
    def test_locked_preimages_apply_to_exact_tested_sources(self):
        data = json.loads((ROOT / "source-binding.json").read_text())
        for row in data["sourceFiles"]:
            with self.subTest(path=row["path"]):
                for name, digest in [
                    ("path", "sha256"),
                    ("preimage", "preimageSHA256"),
                    ("patch", "patchSHA256"),
                ]:
                    self.assertEqual(
                        hashlib.sha256((ROOT / row[name]).read_bytes()).hexdigest(),
                        row[digest],
                    )
                with tempfile.TemporaryDirectory() as tmp:
                    target = Path(tmp) / Path(row["path"]).name
                    shutil.copyfile(ROOT / row["preimage"], target)
                    subprocess.run(
                        ["patch", "-p1", "-i", str((ROOT / row["patch"]).resolve())],
                        cwd=tmp, check=True, capture_output=True,
                    )
                    self.assertEqual(target.read_bytes(), (ROOT / row["path"]).read_bytes())

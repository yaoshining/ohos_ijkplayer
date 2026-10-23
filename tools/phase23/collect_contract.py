"""只封存提交内源码和本次宿主测试结果，不采集本机私有材料。"""
from pathlib import Path
import hashlib
import json
import os
import shutil

out = Path("out/phase23-contract")
out.mkdir(parents=True, exist_ok=True)
shutil.copytree("tools/phase23", out / "source")
shutil.copytree("specs/001-ffmpeg-ohcodec-producer/phase23", out / "spec")
(out / "identity.json").write_text(json.dumps({
    "commit": os.environ["GITHUB_SHA"],
    "runId": os.environ["GITHUB_RUN_ID"],
    "jobStatus": os.environ["JOB_STATUS"],
    "scope": "host actual-source lifecycle and diagnostic contract regression",
    "targetExecutedByThisCI": False,
    "formalArtifactAllowed": False,
}, indent=2) + "\n")
rows = [{
    "path": str(p.relative_to(out)),
    "size": p.stat().st_size,
    "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
} for p in sorted(out.rglob("*")) if p.is_file()]
(out / "evidence-index.json").write_text(json.dumps({"files": rows}, indent=2) + "\n")

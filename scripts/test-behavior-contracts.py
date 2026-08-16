#!/usr/bin/env python3
"""行为契约守卫回归：正向（真仓库约束在位）+ 反向（fixture 删约束必须失败）。"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER = REPO_ROOT / "scripts" / "check-behavior-contracts.py"
CONTRACTS = REPO_ROOT / "scripts" / "behavior-contracts.json"


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root), "--contracts", str(CONTRACTS)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


fails = 0

# 正向：真仓库全部约束在位
result = run(REPO_ROOT)
if result.returncode != 0:
    print("FAIL: 真仓库契约检查未通过")
    print(result.stderr)
    fails += 1

# 反向：fixture 完整复制仓库文件后删掉第一条约束，必须失败且指向该契约 id
with tempfile.TemporaryDirectory(prefix="behavior-contract-") as tmp:
    root = Path(tmp)
    contracts = json.loads(CONTRACTS.read_text(encoding="utf-8"))["contracts"]
    for contract in contracts:
        src = REPO_ROOT / contract["path"]
        dst = root / contract["path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    target = contracts[0]
    dst = root / target["path"]
    text = dst.read_text(encoding="utf-8")
    assert target["must_contain"] in text, "fixture 前提失败：关键词不在源文件"
    dst.write_text(text.replace(target["must_contain"], "【已删除】"), encoding="utf-8")

    result = run(root)
    if result.returncode == 0:
        print("FAIL: 删除约束后检查仍通过（应失败）")
        fails += 1
    elif target["id"] not in result.stderr:
        print(f"FAIL: 失败信息未指向契约 {target['id']}")
        print(result.stderr)
        fails += 1

# 非法契约清单：path 逃逸必须被拒绝（防御性）
with tempfile.TemporaryDirectory(prefix="behavior-contract-bad-") as tmp:
    bad_contracts = Path(tmp) / "bad.json"
    bad_contracts.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "contracts": [
                    {"id": "evil", "path": "../outside.md", "must_contain": "x", "rationale": "逃逸测试"}
                ],
            }
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(REPO_ROOT), "--contracts", str(bad_contracts)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode == 0:
        print("FAIL: 逃逸 path 的契约清单未被拒绝")
        fails += 1

if fails:
    print(f"Behavior-contract tests FAILED ({fails}).")
    sys.exit(1)
print("Behavior-contract regression tests passed.")

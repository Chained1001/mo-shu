#!/usr/bin/env python3
"""agents_version 一致性守卫回归：正向（真仓库一致）+ 反向（fixture 改一处必须失败）。"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER = REPO_ROOT / "scripts" / "check-agents-version-sync.py"
AUTHORITY = "skills/moshu-setup/UPGRADING.md"
VERSION_RE = re.compile(r"agents_version:\s*(\d+)")


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


fails = 0

# 正向：真仓库全部一致
result = run(REPO_ROOT)
if result.returncode != 0:
    print("FAIL: 真仓库 agents_version 检查未通过")
    print(result.stderr)
    fails += 1

# 反向：fixture 复制后把第一个 SKILL.md 的版本改成 24，必须失败
with tempfile.TemporaryDirectory(prefix="agents-version-") as tmp:
    root = Path(tmp)
    (root / "skills").mkdir(parents=True)
    authority_text = (REPO_ROOT / AUTHORITY).read_text(encoding="utf-8")
    match = VERSION_RE.search(authority_text)
    assert match, "fixture 前提失败：权威文件无 agents_version"
    expected = int(match.group(1))

    # 复制全部 SKILL.md 与权威文件
    for skill_dir in (REPO_ROOT / "skills").iterdir():
        if not skill_dir.is_dir():
            continue
        sk = skill_dir / "SKILL.md"
        if sk.exists():
            dst = root / "skills" / skill_dir.name / "SKILL.md"
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sk, dst)
    authority_dst = root / AUTHORITY
    authority_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / AUTHORITY, authority_dst)

    # 把第一个被扫描的 SKILL.md 的 agents_version 改成 24
    target = root / "skills" / "moshu" / "SKILL.md"
    text = target.read_text(encoding="utf-8")
    target.write_text(text.replace(f"agents_version: {expected}", "agents_version: 24"), encoding="utf-8")

    result = run(root)
    if result.returncode == 0:
        print("FAIL: 改一处版本后检查仍通过（应失败）")
        fails += 1
    elif "agents_version=24" not in result.stderr:
        print("FAIL: 失败信息未指向被改的文件")
        print(result.stderr)
        fails += 1

if fails:
    print(f"Agents-version-sync tests FAILED ({fails}).")
    sys.exit(1)
print("Agents-version-sync regression tests passed.")

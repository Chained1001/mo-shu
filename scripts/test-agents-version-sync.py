#!/usr/bin/env python3
"""agents_version 一致性守卫回归：正向（真仓库一致）+ 反向（fixture 改一处必须失败）。

守护对象：agents_version 三端同步一致性守卫回归。禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。
"""

from __future__ import annotations

import importlib.util
import json
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

    # 把第一个被扫描的 SKILL.md 的 agents_version 改成 24（B96 后 moshu 已删，用存活技能 moshu-write 替代）
    target = root / "skills" / "moshu-write" / "SKILL.md"
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

    # 反向二：references/ 里的活指令行写错版本也必须被抓（审计-V3 IM1 根因回归；moshu 删后迁 moshu-write 存活路径）
    ref = root / "skills" / "moshu-write" / "references" / "fake-workflow.md"
    ref.parent.mkdir(parents=True, exist_ok=True)
    ref.write_text("只有 agents_version: 24 通过后才执行。\n", encoding="utf-8")
    result = run(root)
    if result.returncode == 0:
        print("FAIL: references 里写错版本后检查仍通过（应失败）")
        fails += 1
    elif "fake-workflow.md" not in result.stderr:
        print("FAIL: 失败信息未指向 references 文件")
        print(result.stderr)
        fails += 1

# 指纹反向（bump 义务守卫）：fixture 登记指纹后改部署物 → 必须失败
with tempfile.TemporaryDirectory(prefix="fingerprint-") as tmp:
    root = Path(tmp)
    (root / "skills/moshu-setup/references/templates/agents").mkdir(parents=True)
    (root / "skills/moshu-setup/scripts").mkdir(parents=True)
    (root / "scripts").mkdir(parents=True)
    agent = root / "skills/moshu-setup/references/templates/agents/moshu-architect.md"
    agent.write_text("x", encoding="utf-8")
    authority_dst = root / AUTHORITY
    authority_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / AUTHORITY, authority_dst)
    spec = importlib.util.spec_from_file_location("cas", str(CHECKER))
    cas = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(cas)
    fp = cas.compute_deployment_fingerprint(root)
    contract = root / "scripts" / "current-contract.json"
    contract.write_text(
        json.dumps({"agents_version": expected, "deployment_manifest": {"deployment_fingerprint": fp}}),
        encoding="utf-8",
    )
    # 正向：指纹一致 → 绿
    result = run(root)
    if result.returncode != 0:
        print("FAIL: 指纹一致时检查未通过")
        print(result.stderr)
        fails += 1
    # 反向：改部署物 → 指纹不一致 → 红
    agent.write_text("y", encoding="utf-8")
    result = run(root)
    if result.returncode == 0:
        print("FAIL: 部署物变更而指纹未更新，检查仍通过（应失败）")
        fails += 1
    elif "部署物指纹不一致" not in result.stderr:
        print("FAIL: 指纹失败信息不明确")
        print(result.stderr)
        fails += 1

# CRLF/LF 收敛回归（审核 F1 补）：同一内容两种行尾形态指纹必须相等——CI 全 LF 环境，
# 若归一化被删 CI 照样绿、只有 CRLF 工作区 Windows 本地再次恒红（假绿遮蔽复发面）
with tempfile.TemporaryDirectory(prefix="fingerprint-eol-") as tmp:
    base = Path(tmp)
    crlf_root = base / "crlf"
    lf_root = base / "lf"
    for r in (crlf_root, lf_root):
        (r / "skills/moshu-setup/references/templates/agents").mkdir(parents=True)
        (r / "skills/moshu-setup/scripts").mkdir(parents=True)
    (crlf_root / "skills/moshu-setup/references/templates/agents/a.md").write_bytes(b"line1\r\nline2\r\n")
    (crlf_root / "skills/moshu-setup/scripts/deploy.py").write_bytes(b"x = 1\r\n")
    (lf_root / "skills/moshu-setup/references/templates/agents/a.md").write_bytes(b"line1\nline2\n")
    (lf_root / "skills/moshu-setup/scripts/deploy.py").write_bytes(b"x = 1\n")
    spec = importlib.util.spec_from_file_location("cas2", str(CHECKER))
    cas2 = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(cas2)
    fp_crlf = cas2.compute_deployment_fingerprint(crlf_root)
    fp_lf = cas2.compute_deployment_fingerprint(lf_root)
    if fp_crlf != fp_lf:
        print(f"FAIL: CRLF/LF 两形态指纹不等（归一化缺失?）: {fp_crlf} vs {fp_lf}")
        fails += 1

if fails:
    print(f"Agents-version-sync tests FAILED ({fails}).")
    sys.exit(1)
print("Agents-version-sync regression tests passed.")

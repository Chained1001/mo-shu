#!/usr/bin/env python3
"""agents_version 一致性守卫：所有 SKILL.md 中带数字的 agents_version 声明必须与权威来源一致。

agents_version 是 moshu-setup 部署时写入 .story-deployed 的 bundle 版本号，被 7 个
skill 的 SKILL.md 在 spawn 版本提示中硬编码引用。升级版本号时漏改任一处即误判
降级/误报不匹配。本守卫以 moshu-setup/UPGRADING.md 顶部声明为权威，校验其余全部一致。

第二职责（B48 backlog 落地）：bump 义务守卫——部署物指纹比对。current-contract.json
的 deployment_manifest.deployment_fingerprint 由 bump-agents-version.py --confirm 登记；
部署物（templates/agent-references/deploy.py/merge-claude-settings.py）变更而未 bump
时指纹不一致即红（「该 bump 没 bump」从纪律变机器检查）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r"agents_version:\s*(\d+)")
AUTHORITY_FILE = "skills/moshu-setup/UPGRADING.md"
# 部署物指纹覆盖面（agents_version 的「部署物变更面」——文档/CI/README 变更不 bump，故不在指纹面；
# UPGRADING.md 维持排除：它是版本权威文档，bump 必改其版本头，入面会成「每次 bump 都为它重登记」
# 的无信息循环，且措辞级文档改动会误触发 bump 义务——边界定义，2026-08-25 审核 F1/F3 轮确认）
DEPLOYMENT_PATHS = (
    "skills/moshu-setup/references/templates",
    "skills/moshu-setup/references/agent-references",
    "skills/moshu-setup/scripts/deploy.py",
    "skills/moshu-setup/scripts/merge-claude-settings.py",
)


def compute_deployment_fingerprint(root: Path) -> str:
    """部署物集合的确定性指纹：排序相对路径 + 文件内容 sha256 聚合（跳过 __pycache__/*.pyc）。

    换行归一化（CRLF→LF）：.gitattributes 声明 eol=lf，但 autocrlf=true 的 Windows 工作区
    检出为 CRLF——按原始字节聚合会让登记值绑定本机工作区形态，CI Linux（LF 检出）算出不同
    指纹、推送后必红（2026-08-25 审核 F1 实证：登记值=CRLF 字节，git archive 的 LF 树不同）。
    归一化后两侧收敛，不再依赖工作区行尾形态。
    """
    h = hashlib.sha256()
    files: list[Path] = []
    for rel in DEPLOYMENT_PATHS:
        base = root / rel
        if base.is_dir():
            files.extend(
                p
                for p in sorted(base.rglob("*"))
                if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
            )
        elif base.is_file():
            files.append(base)
    for f in sorted(set(files)):
        h.update(f.relative_to(root).as_posix().encode("utf-8"))
        h.update(b"\0")
        h.update(f.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def collect_mismatches(root: Path, expected: int) -> list[str]:
    failures: list[str] = []
    skills_root = root / "skills"
    if not skills_root.is_dir():
        return [f"skills/ 目录缺失: {skills_root}"]
    # 全 skill 递归扫描（审计-V3 IM1：只扫 SKILL.md 时 references/ 里的活指令行
    # agents_version: 27 能一路绿灯过 v1.3.0 发布——import-workflow.md:70 实据）
    for path in sorted(skills_root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root)
        for match in VERSION_RE.finditer(text):
            actual = int(match.group(1))
            if actual != expected:
                failures.append(f"{rel}: agents_version={actual} ≠ 权威 {expected}")
    # 权威文件自身所有出现也必须一致（防 UPGRADING 内自相矛盾）
    authority = root / AUTHORITY_FILE
    if authority.exists():
        text = authority.read_text(encoding="utf-8")
        for match in VERSION_RE.finditer(text):
            if int(match.group(1)) != expected:
                failures.append(f"{AUTHORITY_FILE}: agents_version={match.group(1)} ≠ 权威 {expected}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(REPO_ROOT), help="仓库根目录（测试用 fixture 根）")
    args = parser.parse_args()
    root = Path(args.root)

    authority = root / AUTHORITY_FILE
    try:
        text = authority.read_text(encoding="utf-8")
    except OSError as error:
        print(f"agents_version 守卫失败：无法读取权威文件 {AUTHORITY_FILE}: {error}", file=sys.stderr)
        return 1
    match = VERSION_RE.search(text)
    if not match:
        print(f"agents_version 守卫失败：权威文件 {AUTHORITY_FILE} 缺少 agents_version 声明", file=sys.stderr)
        return 1
    expected = int(match.group(1))

    failures = collect_mismatches(root, expected)
    if failures:
        print(f"agents_version 不一致（权威 {expected}）：", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1

    print(f"agents_version 一致性通过：{expected} 在全部 skills/**/*.md 一致")

    # bump 义务守卫：部署物指纹比对（登记值来自 bump-agents-version.py --confirm；无登记字段时跳过——兼容旧合约/fixture）
    contract = root / "scripts" / "current-contract.json"
    registered: str | None = None
    if contract.exists():
        try:
            data = json.loads(contract.read_text(encoding="utf-8"))
            registered = data.get("deployment_manifest", {}).get("deployment_fingerprint")
        except (json.JSONDecodeError, OSError):
            registered = None
    if registered:
        actual = compute_deployment_fingerprint(root)
        if actual != registered:
            print(
                f"部署物指纹不一致：登记 {registered[:12]}… ≠ 实测 {actual[:12]}…——"
                "部署物已变更而 agents_version 未 bump（运行 bump-agents-version.py 后重跑）",
                file=sys.stderr,
            )
            return 1
        print(f"部署物指纹一致（{registered[:12]}…）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""agents_version 一致性守卫：所有 SKILL.md 中带数字的 agents_version 声明必须与权威来源一致。

agents_version 是 moshu-setup 部署时写入 .story-deployed 的 bundle 版本号，被 7 个
skill 的 SKILL.md 在 spawn 版本提示中硬编码引用。升级版本号时漏改任一处即误判
降级/误报不匹配。本守卫以 moshu-setup/UPGRADING.md 顶部声明为权威，校验其余全部一致。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r"agents_version:\s*(\d+)")
AUTHORITY_FILE = "skills/moshu-setup/UPGRADING.md"


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
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""check-story-numbers.py — 叙述性 skill 计数静态守卫。

枚举 skills/*/SKILL.md 得 N，扫描固定文档集中「N 个 skill」/「N skills」的叙述，
数字与 N 不一致即收集违规。CHANGELOG 排除（历史条目是事实记录不可改）。
零第三方依赖，仅标准库（pathlib/re/sys）。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 白名单：历史对照性提及豁免。每条豁免必须注释理由（当前为空）。
ALLOWED: dict[str, str] = {}

# 被扫描文档（相对仓库根）；缺文件跳过（测试 fixture 只构造子集）。
SCAN_FILES = [
    "README.md",
    "README_EN.md",
    "CONTRIBUTING.md",
    "scripts/README.md",
    "docs/architecture.md",
]

CN_PATTERN = re.compile(r"(\d+)\s*个\s*[Ss]kill")
EN_PATTERN = re.compile(r"(\d+)\s+skills?\b", re.IGNORECASE)


def scan_doc(root: Path, rel: str, n: int) -> list[str]:
    path = root / rel
    if not path.exists():
        return []
    violations: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # 读失败三分类：缺文件（已跳过）/内容坏——明示，不静默降级。
        violations.append(f"{rel}:<decode error>: 无法按 UTF-8 解码，跳过该文件")
        return violations
    for lineno, line in enumerate(text.splitlines(), 1):
        for match in CN_PATTERN.finditer(line):
            if match.group(1) != str(n) and f"{rel}:{lineno}" not in ALLOWED:
                violations.append(f"{rel}:{lineno}: {line.strip()}")
        for match in EN_PATTERN.finditer(line):
            if match.group(1) != str(n) and f"{rel}:{lineno}" not in ALLOWED:
                violations.append(f"{rel}:{lineno}: {line.strip()}")
    return violations


# 索引表检查（审计-V3 D4 单一真源化）：README/README_EN 的 Skills 表数据行数必须 == 实测 skill 数。
# 此前守卫只锁「N 个 skill」数字口径，表格行数漏登记（moshu-style 缺席整个 v1.3.0）永远不被发现。
SKILLS_TABLE_START = re.compile(r"^\|\s*`?[a-z][\w-]*`?\s*\|")  # 首个 skill 数据行特征


def check_skills_tables(root: Path, n: int) -> list[str]:
    violations: list[str] = []
    for rel in ("README.md", "README_EN.md"):
        path = root / rel
        if not path.exists():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            violations.append(f"{rel}:<decode error>")
            continue
        table_rows = 0
        in_skills_table = False
        for index, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("| Skill ") or stripped.startswith("| `Skill`"):
                in_skills_table = True
                continue
            if not in_skills_table:
                continue
            if not stripped.startswith("|"):
                break
            if stripped.startswith("|:") or set(stripped) <= {"|", ":", "-", " "}:
                continue  # 表头分隔行
            if "|" in stripped[1:]:
                table_rows += 1
        if in_skills_table and table_rows != n:
            violations.append(
                f"{rel}: Skills 表数据行 {table_rows} 行 != 实测 {n} 个 skill（漏登记/多登记）"
            )
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="叙述性 skill 计数守卫：文档中的 skill 数字与索引表行数必须与 skills/ 实测一致",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="仓库根（默认当前目录；测试可指向临时 fixture 仓库）",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        print("story numbers: FAIL (skills/ not found under --root)", file=sys.stderr)
        return 1

    n = len(list(skills_dir.glob("*/SKILL.md")))
    violations: list[str] = []
    for rel in SCAN_FILES:
        violations.extend(scan_doc(root, rel, n))
    violations.extend(check_skills_tables(root, n))

    if violations:
        print("story numbers: FAIL")
        for v in violations:
            print(f"  {v}")
        print(f"expected {n} skills everywhere in scanned docs")
        return 1

    print(f"story numbers: ok ({n} skills，索引表行数与叙述数字一致)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

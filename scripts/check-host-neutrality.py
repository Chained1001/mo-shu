#!/usr/bin/env python3
"""check-host-neutrality.py — 宿主中性守卫（B76.6，12-Factor III/适配器模式）。

skills/** 除 skills/moshu-setup/**（适配面本体）外，禁现 `.claude` 与 `CLAUDE_PROJECT_DIR`
字面量（宿主布局知识只存在于 moshu-setup 适配面一处）。违规列出文件即红（exit 1）；
scripts/ 与 docs/ 不在禁扫范围（开发侧工具本来就宿主感知）。
"""
from __future__ import annotations

import sys
from pathlib import Path

FORBIDDEN = (".claude", "CLAUDE_PROJECT_DIR")
SCAN_ROOT = "skills"
EXEMPT_PREFIX = "skills/moshu-setup/"
SCANNED_SUFFIXES = {".md", ".sh", ".py", ".js", ".json", ".mjs"}


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    skills = root / SCAN_ROOT
    if not skills.is_dir():
        print(f"宿主中性守卫失败：{skills} 不存在", file=sys.stderr)
        return 1
    failures: list[str] = []
    scanned = 0
    for path in sorted(skills.rglob("*")):
        if not path.is_file() or path.suffix not in SCANNED_SUFFIXES:
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith(EXEMPT_PREFIX):
            continue
        scanned += 1
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for needle in FORBIDDEN:
            if needle in text:
                for lineno, line in enumerate(text.splitlines(), 1):
                    if needle in line:
                        failures.append(f"{rel}:{lineno}: 命中「{needle}」")
                        break
    print(f"宿主中性守卫：扫描 {scanned} 文件（豁免 moshu-setup 适配面）")
    if failures:
        print("违规（宿主字面量不得出现在运行时流程，宿主差异收敛于 moshu-setup 适配面）：", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1
    print("宿主中性守卫通过：零宿主字面量")
    return 0


if __name__ == "__main__":
    sys.exit(main())

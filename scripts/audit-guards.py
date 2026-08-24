#!/usr/bin/env python3
"""audit-guards.py — 守卫有效性盘点（一次性工具，用完可删或留作年度审计；不进 CI、不配回归）

行为：列出 scripts/ 下全部 check-*/test-* 脚本；对每个 grep .github/workflows/cross-platform.yml 是否登记；
输出报告：`脚本名 | 是否在 CI | 最近修改日期 | 建议`。只出报告，不做任何修改（作者裁决）。
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    scripts_dir = ROOT / "scripts"
    ci_file = ROOT / ".github" / "workflows" / "cross-platform.yml"
    ci_text = ci_file.read_text(encoding="utf-8") if ci_file.exists() else ""

    guards = sorted(
        [p for p in scripts_dir.iterdir() if p.is_file() and (p.name.startswith("check-") or p.name.startswith("test-"))]
    )
    if not guards:
        print("未发现 check-*/test-* 脚本")
        return 0

    print(f"{'脚本':<38}{'CI':<6}{'修改日期':<12}建议")
    print("-" * 78)
    for g in guards:
        in_ci = g.name in ci_text
        mtime = datetime.fromtimestamp(g.stat().st_mtime).strftime("%Y-%m-%d")
        suggestion = "保留" if in_ci else "候选下线/未接入——检查是否需补 CI 或应删除"
        print(f"{g.name:<38}{'是' if in_ci else '否':<6}{mtime:<12}{suggestion}")

    in_ci_count = sum(1 for g in guards if g.name in ci_text)
    print("-" * 78)
    print(f"合计 {len(guards)} 个守卫：{in_ci_count} 个在 CI，{len(guards) - in_ci_count} 个未接入（含一次性/平台限定工具，需人工核对）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

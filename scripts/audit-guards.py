#!/usr/bin/env python3
"""audit-guards.py — 守卫有效性盘点与注册表校验（一次性工具，不进 CI、不配回归）

行为：
1. 归并口径（B48 Step 0 判因）：.py 实现文件被同名 .sh 包装调用时与 .sh 归并为同一守卫
   条目——旧口径把 8 个实现文件误计为「未接入」独立守卫，修正后为 48 守卫口径。
2. 注册表校验：每个守卫在 scripts/README.md 守卫索引表有行，且「事故出身」「末次能红验证」
   两列非空（缺即红——B48 注册表治理；「—（未登记）/未登记-待体检」为合法占位）。
3. 输出报告：`条目 | 是否在 CI | 最近修改日期 | 建议`。只出报告，不做任何修改（作者裁决）。
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    scripts_dir = ROOT / "scripts"
    ci_file = ROOT / ".github" / "workflows" / "cross-platform.yml"
    ci_text = ci_file.read_text(encoding="utf-8") if ci_file.exists() else ""
    readme_file = scripts_dir / "README.md"
    readme_lines = (
        readme_file.read_text(encoding="utf-8").splitlines() if readme_file.exists() else []
    )

    all_files = sorted(
        [
            p
            for p in scripts_dir.iterdir()
            if p.is_file() and (p.name.startswith("check-") or p.name.startswith("test-"))
        ]
    )
    # 归并：.py 有同名 .sh 包装 → 实现文件，随 .sh 条目（B48 口径修正；旧口径误计未接入）
    sh_names = {p.name for p in all_files if p.suffix == ".sh"}
    guards = [p for p in all_files if not (p.suffix == ".py" and p.with_suffix(".sh").name in sh_names)]
    if not guards:
        print("未发现守卫")
        return 0

    print(f"{'条目':<44}{'CI':<6}{'修改日期':<12}建议")
    print("-" * 84)
    for g in guards:
        in_ci = g.name in ci_text
        mtime = datetime.fromtimestamp(g.stat().st_mtime).strftime("%Y-%m-%d")
        suggestion = "保留" if in_ci else "未接入——人工核对（独立文件，无同名 .sh 包装）"
        print(f"{g.name:<44}{'是' if in_ci else '否':<6}{mtime:<12}{suggestion}")

    # 注册表校验：有行 + 事故出身/末次能红验证两列非空
    missing_rows: list[str] = []
    missing_cols: list[str] = []
    for g in guards:
        row = next(
            (ln for ln in readme_lines if ln.strip().startswith("|") and g.name in ln),
            None,
        )
        if row is None:
            missing_rows.append(g.name)
            continue
        parts = [x.strip() for x in row.strip().strip("|").split("|")]
        if len(parts) < 5 or not parts[3] or not parts[4]:
            missing_cols.append(g.name)

    print("-" * 84)
    in_ci_count = sum(1 for g in guards if g.name in ci_text)
    print(
        f"合计 {len(guards)} 个守卫：{in_ci_count} 个在 CI，"
        f"{len(guards) - in_ci_count} 个未接入（独立文件，需人工核对）"
    )
    if missing_rows:
        print("FAIL: 以下守卫无 README 注册表行（新增守卫必须登记 scripts/README.md 守卫索引表）：", file=sys.stderr)
        for n in missing_rows:
            print(f"  - {n}", file=sys.stderr)
    if missing_cols:
        print("FAIL: 以下守卫注册表行「事故出身/末次能红验证」列有空值：", file=sys.stderr)
        for n in missing_cols:
            print(f"  - {n}", file=sys.stderr)
    return 1 if (missing_rows or missing_cols) else 0


if __name__ == "__main__":
    sys.exit(main())

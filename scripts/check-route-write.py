#!/usr/bin/env python3
"""check-route-write.py — 路由残留守卫（批B8）。

扫描 skills/**/*.md 中第二列=moshu-write（可带 ` 或 / 装饰）的表格行，
对第一列语境词做两级判定（待决答复 2026-08-22 裁决口径）：
  BLOCKING：语境含构建域词（开书/开写/…）→ 报 文件:行号:原行，退出 1
  WHITELIST：语境含写作域词（续写/继续写/…）→ 过（每词一条理由注释）
  未知语境 → [candidate] 呈报，退出 0（未知≠违规——候选永不拦截宪法）

范围锁死（禁止事项）：只锁表格行（| 开头），不扫 prose；只查 moshu-write，
不查其他跳转目标。零第三方依赖，仅标准库（argparse/pathlib/sys）。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 构建域词（BLOCKING）：语境含其一 = 确定性开书语义残留（B1b 缺陷类同族，第 4 例史）。
# 每词一条理由——防静默增删。判定优先级：blocking > whitelist > candidate。
BLOCKING_WORDS: dict[str, str] = {
    "开书": "开书属 build 域（/moshu-build），跳 write 即 B1b 开书语义残留",
    "开写": "开写=开书措辞变体（scan「直接开写」/analyze「准备开写」两例史）",
    "开新": "开新书/开新卷属 build 域（开书变体）",
    "建设定": "建/补设定属 build 域（B1b 拆分后设定建设走 /moshu-build）",
    "改设定": "改设定属 build 域（设定修订走 /moshu-build）",
    "写大纲": "大纲搭建属 build 域（outline 建设走 /moshu-build）",
    "搭大纲": "同写大纲——大纲搭建属 build 域",
    "写卷纲": "卷纲规划属 build 域",
    "定世界观": "世界观设定属 build 域",
}

# 写作域词（WHITELIST）：语境含其一 = 合法 write 跳转。
# 每词一条理由（禁止事项 3：白名单禁无理由注释）；存量行收编依据随词记档。
WHITELIST_WORDS: dict[str, str] = {
    "续写": "存量 analyze:45「已有书续写」——拆完书登记对标开书后的续写路径，write 域合法",
    "继续写": "存量 deslop:105「继续写作」/import:71「导入完想继续写（长篇）」——续写域合法",
    "继续创作": "继续写同族（创作=写作域语义）",
    "写长篇": "write 主意图词（moshu/SKILL.md 路由表「写长篇」写作域语义）",
    "写正文": "正文写作属 write 域",
    "回炉": "回炉修改属 write 域（moshu/SKILL.md 路由表「回炉」写作域语义）",
    "重写": "重写章节属 write 域（moshu/SKILL.md 路由表「重写第X章」写作域语义）",
    "日更": "日更续写属 write 域（import 行命令列「日更」同源语义）",
    "补纲": "中途补纲/扩纲属 write 域（moshu/SKILL.md 判定表第 4 行语义）",
    "修改": "存量 review:71「要修改查出的问题」——修改已写正文回 write 域",
    "改稿": "改稿=修改同族，write 域",
    "去味": "去 AI 味属 write 域（deslop 返 write 场景）",
    "润色": "润色属 write 域",
    "写作": "写作域通用词（覆盖「继续写作」等）",
}


def normalize_target(cell: str) -> str:
    """剥装饰后取跳转目标词：空白/反引号/前导斜杠均可剥（`moshu-write`、/moshu-write）。"""
    s = cell.strip().strip("`")
    if s.startswith("/"):
        s = s[1:].lstrip()
    return s.strip()


def classify(context: str) -> tuple[str, str]:
    """两级判定：返回 (blocking|ok|candidate, 命中词或"")。blocking 优先。"""
    for word in BLOCKING_WORDS:
        if word in context:
            return "blocking", word
    for word in WHITELIST_WORDS:
        if word in context:
            return "ok", word
    return "candidate", ""


def scan_file(path: Path, rel: str) -> list[tuple[str, int, str]]:
    """扫一个 .md：返回 (kind, lineno, 原行) 列表；kind ∈ blocking/candidate/error。"""
    hits: list[tuple[str, int, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # 读失败三分类：缺文件由 rglob 保证不存在；内容坏在此明示，不静默跳过。
        hits.append(("error", 0, f"{rel}:<decode error>: 无法按 UTF-8 解码"))
        return hits
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if len(cells) < 2 or normalize_target(cells[1]) != "moshu-write":
            continue
        kind, _ = classify(cells[0])
        hits.append((kind, lineno, stripped))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(
        description="路由残留守卫：表格行第二列=moshu-write 的语境两级判定（构建域 blocking/写作域白名单/未知 candidate）",
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
        print("route-write: FAIL (skills/ not found under --root)", file=sys.stderr)
        return 1

    blocking: list[tuple[str, int, str]] = []
    candidates: list[tuple[str, int, str]] = []
    errors: list[str] = []
    checked = 0
    for path in sorted(skills_dir.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        for kind, lineno, line in scan_file(path, rel):
            if kind == "error":
                errors.append(line)
                continue
            checked += 1
            if kind == "blocking":
                blocking.append((rel, lineno, line))
            elif kind == "candidate":
                candidates.append((rel, lineno, line))
    for rel, lineno, line in blocking:
        print(f"{rel}:{lineno}: {line}")
    for rel, lineno, line in candidates:
        print(f"[candidate] {rel}:{lineno}: {line}")
    for err in errors:
        print(err, file=sys.stderr)
    if blocking or errors:
        print(
            f"route-write: FAIL ({checked} rows checked, "
            f"{len(blocking)} blocking, {len(candidates)} candidates)"
        )
        return 1
    print(f"route-write: ok ({checked} rows checked, {len(candidates)} candidates)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

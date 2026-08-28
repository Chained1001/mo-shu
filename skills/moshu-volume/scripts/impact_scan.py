#!/usr/bin/env python3
"""impact_scan.py — 构建资产修订的影响分析（纯只读零 LLM）。

对每个关键词/实体名在 {未写细纲, 已写正文, 追踪条目} 三面做确定性命中清点。
分界 = 追踪 state 的 last_committed_chapter（≤它 = 已写事实，>它 = 计划）。
输出单行 JSON，退出 0（无命中 = 空数组，分析工具非判定器）；
追踪未初始化、参数或读文件错误 → 退出 2 并明示（读失败三分类：缺文件/内容坏/类型错）。
零写入，仅标准库。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

CHAPTER_NUMBER = re.compile(r"第(\d+)章")

# 追踪 state 的命中域（事实层四域）
TRACKING_DOMAINS = ("characters", "foreshadow", "timeline", "information_gaps")


class ScanError(ValueError):
    """Expected input/state error."""


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ScanError(f"读取失败（缺文件）：{path} 不存在——追踪未初始化，先 /moshu-outline 开书 → /moshu-volume 首卷（tracking init）") from exc
    except json.JSONDecodeError as exc:
        raise ScanError(f"读取失败（内容坏）：{path} 不是合法 JSON: {exc}") from exc
    except OSError as exc:
        raise ScanError(f"读取失败（IO）：{path}: {exc}") from exc


def chapter_of(filename: str) -> int | None:
    match = CHAPTER_NUMBER.search(filename)
    return int(match.group(1)) if match else None


def hit_lines(path: Path, keyword: str) -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return hits
    for lineno, line in enumerate(text.splitlines(), 1):
        if keyword in line:
            hits.append({"file": str(path), "line": lineno})
    return hits


def scan_outline_dirs(project: Path, keyword: str, boundary: int) -> list[dict[str, object]]:
    """① 未写细纲：章号 > boundary 的 大纲/细纲_第*章.md 命中行。"""
    hits: list[dict[str, object]] = []
    outline_dir = project / "大纲"
    if not outline_dir.is_dir():
        return hits
    for path in sorted(outline_dir.glob("细纲_第*章.md")):
        chapter = chapter_of(path.name)
        if chapter is None or chapter <= boundary:
            continue
        hits.extend(hit_lines(path, keyword))
    return hits


def scan_written_chapters(project: Path, keyword: str, boundary: int) -> list[dict[str, object]]:
    """② 已写正文：章号 ≤ boundary 的 正文/第*章*.md 命中行。"""
    hits: list[dict[str, object]] = []
    prose_dir = project / "正文"
    if not prose_dir.is_dir():
        return hits
    for path in sorted(prose_dir.glob("第*章*.md")):
        chapter = chapter_of(path.name)
        if chapter is None or chapter > boundary:
            continue
        hits.extend(hit_lines(path, keyword))
    return hits


def scan_tracking(state: object, keyword: str) -> list[dict[str, object]]:
    """③ 追踪条目：state 四域 JSON 序列化文本中命中 → {domain, key}。"""
    hits: list[dict[str, object]] = []
    root = state
    if not isinstance(root, dict):
        return hits
    for domain in TRACKING_DOMAINS:
        entries = root.get(domain, {})
        if not isinstance(entries, dict):
            continue
        for key, value in entries.items():
            if keyword in json.dumps(value, ensure_ascii=False):
                hits.append({"domain": domain, "key": str(key)})
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True, help="书项目根（含 追踪/ 与 大纲/）")
    parser.add_argument(
        "--keyword",
        action="append",
        required=True,
        help="关键词/实体名（可多次传；至少一次）",
    )
    args = parser.parse_args()

    project = args.project.resolve()
    state_path = project / "追踪" / "_tracking-state.json"
    try:
        document = read_json(state_path)
        state = document
        if not isinstance(state, dict) or "last_committed_chapter" not in state:
            raise ScanError(
                f"读取失败（类型错）：{state_path} 缺少 last_committed_chapter——"
                "不是合法的追踪 state；先 /moshu-outline 开书 → /moshu-volume 首卷（tracking init）"
            )
        boundary = state["last_committed_chapter"]
        if not isinstance(boundary, int) or isinstance(boundary, bool):
            raise ScanError(f"读取失败（类型错）：last_committed_chapter 非整数")
    except ScanError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    results: dict[str, object] = {}
    for keyword in args.keyword:
        results[keyword] = {
            "unwritten_outlines": scan_outline_dirs(project, keyword, boundary),
            "written_chapters": scan_written_chapters(project, keyword, boundary),
            "tracking_hits": scan_tracking(state, keyword),
        }

    payload = {
        "keywords": results,
        "boundary_chapter": boundary,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

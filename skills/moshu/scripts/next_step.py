#!/usr/bin/env python3
"""下一步判定（moshu 路由用）：S0-S6 写作进度序只读判定，输出单行 JSON DTO。

审计-V3 D5 重估批 4（当年"痛点证据最弱"跳过；现状：路由表每次会话付费且判定质量依赖模型）。
纯只读、零写入、无独立状态存储——判定即文件系统证据（docs/architecture.md §3 状态机）。

用法（按仓库解释器探测形态调用，Windows 禁止裸 python3）:
  for PYBIN in python3 python py; do "$PYBIN" -c "" 2>/dev/null && break; done
  "$PYBIN" next_step.py --project {书项目根}

判定序（按序首个命中即停）：
  P1 .story-deployed 缺失 → S0（未部署）
  P2 拆文库/*/_progress.md 最终状态非 completed → 优先中断：analyze 续跑
  P3 {P}/.moshu-review/ 有未完成 state → 优先中断：review 续批
  S1 P 下无 正文/ 且无 大纲/ 且无 追踪/ → 未开书
  S2 正文/ 无章文件（或全部 0 字节）→ 写第 1 章
  S3 下一章 N 无细纲 → 补纲
  S4 下一章有细纲 → 日更
  S5 卷末已定稿且无卷复盘产物 → 卷复盘
  S6 卷末已定稿且有卷复盘产物 → 下卷规划
退出码：0=判定成功；2=项目根不存在。
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

FINE_OUTLINE_RE = re.compile(r"细纲_第0*(\d+)章")
PROSE_RE = re.compile(r"^第0*(\d+)章.*\.md$")
VOLUME_OUTLINE_RE = re.compile(r"卷纲_第0*(\d+)卷")
VOLUME_REVIEW_RE = re.compile(r"卷复盘_第0*(\d+)卷")
VOLUME_RANGE_RE = re.compile(r"第\s*(\d+)\s*[-—~至]\s*(\d+)\s*章")


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def max_prose_chapter(prose_dir: Path) -> int:
    """正文最大章号；全部空文件视为未写（完成判定只认非空文件）。"""
    best = 0
    if not prose_dir.is_dir():
        return 0
    for path in prose_dir.iterdir():
        match = PROSE_RE.match(path.name)
        if not match:
            continue
        try:
            if path.stat().st_size == 0:
                continue
        except OSError:
            continue
        best = max(best, int(match.group(1)))
    return best


def main() -> int:
    parser = argparse.ArgumentParser(description="下一步判定（S0-S6 只读 DTO）")
    parser.add_argument("--project", required=True, help="书项目根")
    args = parser.parse_args()
    project = Path(args.project)
    if not project.is_dir():
        print(f"[错误] 项目根不存在: {project}", file=sys.stderr)
        return 2

    evidence: list[str] = []

    # P1：未部署
    if not (project / ".story-deployed").is_file():
        emit({
            "step": "S0",
            "evidence": [".story-deployed 缺失"],
            "last_committed_chapter": 0,
            "next_action": "运行 /moshu-setup 部署写作基础设施",
            "suggested_skill": "moshu-setup",
        })
        return 0

    # P2：拆文断点续跑（优先中断，与序位无关——审计-V3 M1）
    library = project.parent / "拆文库"
    if not library.is_dir():
        library = project / "拆文库"
    if library.is_dir():
        for progress in library.glob("*/_progress.md"):
            try:
                text = progress.read_text(encoding="utf-8")
            except OSError:
                continue
            if "最终状态：completed" not in text and "- 最终状态：completed" not in text:
                emit({
                    "step": "INTERRUPT",
                    "interrupt": "analyze",
                    "evidence": [f"{progress} 未完成"],
                    "last_committed_chapter": max_prose_chapter(project / "正文"),
                    "next_action": f"/moshu-analyze 续跑（断点恢复：{progress}）",
                    "suggested_skill": "moshu-analyze",
                })
                return 0

    # P3：审查续批（优先中断——审计-V3 M1）
    review_state = project / ".moshu-review" / "state.md"
    if review_state.is_file():
        try:
            text = review_state.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if text.strip():
            emit({
                "step": "INTERRUPT",
                "interrupt": "review",
                "evidence": [".moshu-review/state.md 存在未完成审查"],
                "last_committed_chapter": max_prose_chapter(project / "正文"),
                "next_action": "/moshu-review 续批（未完成审查状态）",
                "suggested_skill": "moshu-review",
            })
            return 0

    prose_dir = project / "正文"
    outline_dir = project / "大纲"
    tracking_dir = project / "追踪"

    # S1：未开书
    if not prose_dir.is_dir() and not outline_dir.is_dir() and not tracking_dir.is_dir():
        emit({
            "step": "S1",
            "evidence": ["无 正文/ 大纲/ 追踪 任一目录"],
            "last_committed_chapter": 0,
            "next_action": "运行 /moshu-build 开书（构建设定/大纲/卷纲；细纲与正文接力 /moshu-write）",
            "suggested_skill": "moshu-build",
        })
        return 0

    # 章进度权威：state 的 last_committed_chapter；缺失/损坏退回正文最大章号
    last = max_prose_chapter(prose_dir)
    state_path = tracking_dir / "_tracking-state.json"
    state_ok = False
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(state, dict) and isinstance(state.get("last_committed_chapter"), int):
                last = state["last_committed_chapter"]
                state_ok = True
        except (OSError, json.JSONDecodeError):
            pass
    if not state_ok:
        evidence.append("tracking_state_missing_or_invalid")

    # S2：有书但无正文
    if last == 0:
        emit({
            "step": "S2",
            "evidence": evidence + ["正文/ 无章文件或全部为空（完成判定只认非空文件）"],
            "last_committed_chapter": 0,
            "next_action": "首批细纲 + 写第 1 章（/moshu-write，细纲首建见 outline-workflow；设定/卷纲缺失才回 /moshu-build）",
            "suggested_skill": "moshu-write",
        })
        return 0

    next_chapter = last + 1

    # 细纲集合
    fine_outlines: set[int] = set()
    if outline_dir.is_dir():
        for path in outline_dir.iterdir():
            match = FINE_OUTLINE_RE.match(path.name)
            if match:
                fine_outlines.add(int(match.group(1)))

    # S3：下一章无细纲
    if next_chapter not in fine_outlines:
        emit({
            "step": "S3",
            "evidence": evidence + [f"细纲集合缺第 {next_chapter} 章"],
            "last_committed_chapter": last,
            "next_action": f"补第 {next_chapter} 章细纲（/moshu-write 中途补纲/扩纲）",
            "suggested_skill": "moshu-write",
        })
        return 0

    # 卷末判定：最大卷号 X 的卷纲「章节范围」上界 U
    volume_range_unparsed = False
    volume_upper = None
    volume_number = None
    if outline_dir.is_dir():
        volumes: dict[int, Path] = {}
        for path in outline_dir.iterdir():
            match = VOLUME_OUTLINE_RE.match(path.name)
            if match:
                volumes[int(match.group(1))] = path
        if volumes:
            volume_number = max(volumes)
            try:
                text = volumes[volume_number].read_text(encoding="utf-8")
            except OSError:
                text = ""
            range_match = VOLUME_RANGE_RE.search(text)
            if range_match:
                volume_upper = int(range_match.group(2))
            else:
                volume_range_unparsed = True

    if volume_upper is not None and last >= volume_upper:
        review_exists = False
        if outline_dir.is_dir():
            for path in outline_dir.iterdir():
                match = VOLUME_REVIEW_RE.match(path.name)
                if match and int(match.group(1)) == volume_number:
                    review_exists = True
                    break
        if not review_exists:
            emit({
                "step": "S5",
                "evidence": evidence + [f"已写至卷末（第 {volume_upper} 章）且无卷复盘产物"],
                "last_committed_chapter": last,
                "next_action": f"执行第 {volume_number} 卷卷复盘（/moshu-write 卷复盘）",
                "suggested_skill": "moshu-write",
            })
            return 0
        emit({
            "step": "S6",
            "evidence": evidence + [f"第 {volume_number} 卷卷复盘已完成"],
            "last_committed_chapter": last,
            "next_action": "下卷规划（/moshu-build，消费卷复盘方向候选）",
            "suggested_skill": "moshu-build",
        })
        return 0

    # S4：下一章有细纲（含卷界解析失败的降级）
    s4_evidence = list(evidence)
    if volume_range_unparsed:
        s4_evidence.append("volume_range_unparsed（卷纲章节范围格式未识别，已降级停在 S4，请人工核对卷末）")
    emit({
        "step": "S4",
        "evidence": s4_evidence,
        "last_committed_chapter": last,
        "next_action": f"日更写第 {next_chapter} 章（/moshu-write 日更）",
        "suggested_skill": "moshu-write",
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Maintain one structured moshu state and its deterministic Markdown views.

The language model supplies compact semantic JSON.  This tool validates and
merges that input in memory, renders every derived view, then atomically writes
``_tracking-state.json`` last as the single commit point.  One book project has
one serial writer; concurrent commits are intentionally unsupported.
"""

from __future__ import annotations

import argparse
import copy
import datetime
import json
import os
import re
import stat
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Any


INPUT_SCHEMA_VERSION = 2
TRACKING_SCHEMA_VERSION = 5
DELTA_TARGET_BYTES = 1536
DELTA_MAX_BYTES = 3072
CONTEXT_TARGET_BYTES = 8192
CONTEXT_MAX_BYTES = 12288
SNAPSHOT_TARGET_BYTES = 4096
SNAPSHOT_MAX_BYTES = 8192

CONTEXT_HEADINGS = (
    "## 当前位置",
    "## 长期约束",
    "## 核心角色状态",
    "## 活跃伏笔",
    "## 近三章速记",
    "## 下一章承诺",
    "## 连贯性风险",
)
FORESHADOW_STATUSES = ("已埋", "已回收", "已过期", "放弃")
FORESHADOW_IMPORTANCE = ("高", "中", "低")
REVEAL_STATUSES = ("未揭示", "部分揭示", "已揭示")
INVALID_FILE_CHARS = re.compile(r"[<>:\"/\\|?*\x00-\x1f]")
FORESHADOW_ID = re.compile(r"^F\d{3,}$")
EVENT_ID = re.compile(r"^E\d{3,}$")
GAP_ID = re.compile(r"^G\d{3,}$")
READER_KNOWN = ("未知", "部分已知", "已知")
GAP_STATUSES = ("登记", "已兑现", "已放弃")
# 卷报告第④节「对标节奏对照」（批B2）：坐标表固化格式与确定性对照（候选呈报，零 LLM）。
VOLUME_OUTLINE_RE = re.compile(r"卷纲_第0*(\d+)卷")
VOLUME_RANGE_RE = re.compile(r"第\s*(\d+)\s*[-—~至]\s*(\d+)\s*章")
PROSE_CHAPTER_RE = re.compile(r"^第0*(\d+)章.*\.md$")
BENCHMARK_HEADING = "### 对标结构坐标"
BENCHMARK_POINTS = ("1/4 点", "中点", "3/4 点")
BENCHMARK_PLANNED_RE = re.compile(r"第\s*(\d+)\s*章")
# 知情人上限对齐 timeline 事件 characters 上限（12），不自造新数。
KNOWERS_MAX = 12
# 伏笔悬置预警阈值（mo-shu 自定）：status=已埋 且 距最近变动章 >= 阈值 时，
# check 输出 suspension_warnings 候选清单（只呈报，不改变退出码）。
SUSPENSION_WARN_CHAPTERS = 20
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
RETIRED_TRACKING_PATHS = (
    "_tracking-meta.json",
    "阶段摘要.md",
    "角色状态.md",
    "时间线.md",
    "摘要",
    "时间线/事件库.json",
)
RETIRED_ARCHIVE_DIR = "_旧追踪存档"


class TrackingError(ValueError):
    """Expected validation or tracking-state error."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TrackingError(message)


def as_mapping(value: object, label: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def as_list(value: object, label: str) -> list[Any]:
    require(isinstance(value, list), f"{label} must be a JSON array")
    return value


def as_int(value: object, label: str, *, minimum: int = 0) -> int:
    require(isinstance(value, int) and not isinstance(value, bool), f"{label} must be an integer")
    require(value >= minimum, f"{label} must be >= {minimum}")
    return value


def require_known_keys(mapping: dict[str, Any], allowed: set[str], label: str) -> None:
    unknown = set(mapping) - allowed
    require(not unknown, f"{label} contains unsupported fields: {', '.join(sorted(unknown))}")


def clean_text(value: object, label: str, *, allow_empty: bool = False, max_bytes: int = 768) -> str:
    require(isinstance(value, str), f"{label} must be a string")
    cleaned = " ".join(value.replace("|", "｜").split())
    require(allow_empty or bool(cleaned), f"{label} must not be empty")
    require(len(cleaned.encode("utf-8")) <= max_bytes, f"{label} exceeds {max_bytes} bytes")
    return cleaned


def clean_string_list(
    value: object,
    label: str,
    *,
    maximum: int | None = None,
    item_max_bytes: int = 384,
) -> list[str]:
    values = as_list(value, label)
    if maximum is not None:
        require(len(values) <= maximum, f"{label} may contain at most {maximum} items")
    return [clean_text(item, f"{label}[{index}]", max_bytes=item_max_bytes) for index, item in enumerate(values)]


def safe_file_component(value: object, label: str) -> str:
    name = unicodedata.normalize("NFC", clean_text(value, label, max_bytes=180))
    require(not INVALID_FILE_CHARS.search(name), f"{label} contains an invalid filename character")
    require(name not in {".", ".."} and not name.endswith((".", " ")), f"{label} is not a safe filename")
    require(name.split(".", 1)[0].upper() not in WINDOWS_RESERVED_NAMES, f"{label} is reserved on Windows")
    return name


def portable_name_key(name: str) -> str:
    return unicodedata.normalize("NFC", name).casefold()


def byte_size(text: str) -> int:
    return len(text.encode("utf-8"))


def emit(text: str, *, error: bool = False) -> None:
    """Write UTF-8 bytes directly.

    Windows 的文本 stdout 是 cp1252（含中文即 UnicodeEncodeError），stderr 默认
    backslashreplace（中文被转义成反斜杠码位，作者看不懂）。两条路都要绕开。
    """
    stream = sys.stderr if error else sys.stdout
    stream.flush()
    stream.buffer.write((text + "\n").encode("utf-8"))
    stream.buffer.flush()


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TrackingError(f"unable to read JSON {path}: {exc}") from exc


def json_payload(document: object) -> str:
    return json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def atomic_write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_if_changed(path: Path, payload: str) -> None:
    try:
        if path.read_text(encoding="utf-8") == payload:
            return
    except FileNotFoundError:
        pass
    atomic_write_text(path, payload)


def tracking_root(project: Path) -> Path:
    return project.resolve() / "追踪"


def state_path(project: Path) -> Path:
    return tracking_root(project) / "_tracking-state.json"


def delta_path(tracking: Path, chapter: int) -> Path:
    width = max(3, len(str(chapter)))
    return tracking / "逐章记录" / f"第{chapter:0{width}d}章.md"


def find_retired_tracking_paths(tracking: Path) -> list[str]:
    found = [relative for relative in RETIRED_TRACKING_PATHS if (tracking / relative).exists()]
    found.extend(sorted(path.name for path in tracking.glob("基线_截至第*章.md")))
    return found


def require_no_retired_tracking_paths(tracking: Path) -> None:
    found = find_retired_tracking_paths(tracking)
    require(not found, f"retired tracking files are not supported: {', '.join(found)}")


def archive_retired_tracking_paths(tracking: Path) -> list[str]:
    """Move a pre-transaction 追踪/ aside so init can build the current protocol in place.

    Nothing is parsed or converted: the old files are kept verbatim for the author to
    consult, and the new state is reconstructed from the init document alone.
    """
    retired = find_retired_tracking_paths(tracking)
    if not retired:
        return []
    archive = tracking / RETIRED_ARCHIVE_DIR
    for relative in retired:
        require(
            not (archive / relative).exists(),
            f"追踪/{RETIRED_ARCHIVE_DIR}/{relative} already exists; move it away before initializing",
        )
    # 先全量校验再搬运；中断后重跑时已搬走的条目不再出现在待搬列表里，可直接续做。
    for relative in retired:
        target = archive / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(tracking / relative, target)
    return retired


def validate_position(value: object, label: str = "context.position") -> dict[str, Any]:
    position = as_mapping(value, label)
    require_known_keys(position, {"volume", "volume_start_chapter", "story_time", "scene"}, label)
    return {
        "volume": safe_file_component(position.get("volume"), f"{label}.volume"),
        "volume_start_chapter": as_int(
            position.get("volume_start_chapter"), f"{label}.volume_start_chapter", minimum=1
        ),
        "story_time": clean_text(position.get("story_time"), f"{label}.story_time", max_bytes=240),
        "scene": clean_text(position.get("scene"), f"{label}.scene", max_bytes=240),
    }


def normalize_snapshot(value: object, label: str) -> dict[str, Any]:
    snapshot = as_mapping(value, label)
    require_known_keys(
        snapshot,
        {"identity", "location", "goal", "state", "abilities_resources", "relationships", "knowledge", "open_threads"},
        label,
    )
    return {
        "identity": clean_text(snapshot.get("identity"), f"{label}.identity", max_bytes=240),
        "location": clean_text(snapshot.get("location"), f"{label}.location", max_bytes=240),
        "goal": clean_text(snapshot.get("goal"), f"{label}.goal", max_bytes=300),
        "state": clean_text(snapshot.get("state"), f"{label}.state", max_bytes=300),
        "abilities_resources": clean_string_list(
            snapshot.get("abilities_resources", []), f"{label}.abilities_resources"
        ),
        "relationships": clean_string_list(snapshot.get("relationships", []), f"{label}.relationships"),
        "knowledge": clean_string_list(snapshot.get("knowledge", []), f"{label}.knowledge"),
        "open_threads": clean_string_list(snapshot.get("open_threads", []), f"{label}.open_threads"),
    }


def normalize_snapshots(value: object, label: str = "character_snapshots") -> dict[str, dict[str, Any]]:
    snapshots = as_mapping(value, label)
    normalized: dict[str, dict[str, Any]] = {}
    portable_names: set[str] = set()
    for raw_name, raw_snapshot in snapshots.items():
        name = safe_file_component(raw_name, f"{label} character name")
        key = portable_name_key(name)
        require(key not in portable_names, f"{label} contains a cross-platform duplicate character {name}")
        portable_names.add(key)
        normalized[name] = normalize_snapshot(raw_snapshot, f"{label}.{name}")
    return normalized


def render_snapshot(name: str, snapshot: dict[str, Any], through_chapter: int, revision: int) -> str:
    def section(title: str, values: list[str]) -> list[str]:
        return [f"## {title}", *(f"- {item}" for item in values or ["无"]), ""]

    lines = [
        f"# {name}｜当前状态",
        "",
        f"- 状态修订：{revision}",
        f"- 截至章节：第{through_chapter}章",
        f"- 身份：{snapshot['identity']}",
        f"- 位置：{snapshot['location']}",
        f"- 当前目标：{snapshot['goal']}",
        f"- 身心状态：{snapshot['state']}",
        "",
    ]
    lines.extend(section("能力与资源", snapshot["abilities_resources"]))
    lines.extend(section("关键关系", snapshot["relationships"]))
    lines.extend(section("已知信息", snapshot["knowledge"]))
    lines.extend(section("未结事项", snapshot["open_threads"]))
    payload = "\n".join(lines).rstrip() + "\n"
    require(
        byte_size(payload) <= SNAPSHOT_MAX_BYTES,
        f"character snapshot {name} exceeds hard cap of {SNAPSHOT_MAX_BYTES} bytes",
    )
    return payload


def normalize_foreshadow_change(
    value: object,
    label: str,
    *,
    allow_delete: bool,
    through_chapter: int,
) -> dict[str, Any]:
    row = as_mapping(value, label)
    require_known_keys(
        row,
        {"action", "id", "summary", "planted_chapter", "planned_resolution_chapter", "status", "importance"},
        label,
    )
    action = clean_text(row.get("action", "upsert"), f"{label}.action", max_bytes=24)
    require(action in ({"upsert", "delete"} if allow_delete else {"upsert"}), f"{label}.action is invalid")
    identifier = clean_text(row.get("id"), f"{label}.id", max_bytes=24)
    require(FORESHADOW_ID.fullmatch(identifier) is not None, f"{label}.id must look like F001")
    if action == "delete":
        return {"action": action, "id": identifier}
    planted_chapter = as_int(row.get("planted_chapter"), f"{label}.planted_chapter", minimum=1)
    require(planted_chapter <= through_chapter, f"{label}.planted_chapter cannot be in the future")
    planned_raw = row.get("planned_resolution_chapter")
    planned_chapter = (
        None if planned_raw is None else as_int(planned_raw, f"{label}.planned_resolution_chapter", minimum=1)
    )
    require(
        planned_chapter is None or planned_chapter >= planted_chapter,
        f"{label}.planned_resolution_chapter cannot precede planted_chapter",
    )
    status = clean_text(row.get("status"), f"{label}.status", max_bytes=24)
    importance = clean_text(row.get("importance"), f"{label}.importance", max_bytes=12)
    require(status in FORESHADOW_STATUSES, f"{label}.status must be one of {FORESHADOW_STATUSES}")
    require(importance in FORESHADOW_IMPORTANCE, f"{label}.importance must be one of {FORESHADOW_IMPORTANCE}")
    return {
        "action": action,
        "id": identifier,
        "summary": clean_text(row.get("summary"), f"{label}.summary", max_bytes=360),
        "planted_chapter": planted_chapter,
        "planned_resolution_chapter": planned_chapter,
        "status": status,
        "importance": importance,
    }


def normalize_foreshadow_state(value: object, last_chapter: int) -> dict[str, dict[str, Any]]:
    rows = as_mapping(value, "tracking state.foreshadow")
    normalized: dict[str, dict[str, Any]] = {}
    for raw_identifier, raw_row in rows.items():
        identifier = clean_text(raw_identifier, "tracking state.foreshadow ID", max_bytes=24)
        row = as_mapping(raw_row, f"tracking state.foreshadow.{identifier}")
        require_known_keys(
            row,
            {"id", "summary", "planted_chapter", "planned_resolution_chapter", "status", "importance", "updated_chapter"},
            f"tracking state.foreshadow.{identifier}",
        )
        require(row.get("id") == identifier, f"tracking state.foreshadow.{identifier}.id does not match its key")
        change = normalize_foreshadow_change(
            {
                "action": "upsert",
                **{key: value for key, value in row.items() if key != "updated_chapter"},
            },
            f"tracking state.foreshadow.{identifier}",
            allow_delete=False,
            through_chapter=last_chapter,
        )
        change.pop("action")
        updated = as_int(row.get("updated_chapter"), f"tracking state.foreshadow.{identifier}.updated_chapter", minimum=1)
        require(updated <= last_chapter, f"foreshadow {identifier} updates after current chapter")
        change["updated_chapter"] = updated
        normalized[identifier] = change
    return normalized


def render_foreshadow(rows: dict[str, dict[str, Any]], revision: int) -> str:
    lines = [
        "# 伏笔当前状态",
        "",
        f"> 状态修订：{revision}。每个 ID 只保留一行当前状态；历史变化见 `逐章记录/`。",
        "",
        "| ID | 内容 | 埋设章 | 计划回收章 | 状态 | 重要度 | 最近变更章 |",
        "|---|---|---:|---:|---|---|---:|",
    ]
    for identifier in sorted(rows):
        row = rows[identifier]
        planned = f"第{row['planned_resolution_chapter']}章" if row["planned_resolution_chapter"] else "—"
        lines.append(
            f"| {identifier} | {row['summary']} | 第{row['planted_chapter']}章 | {planned} | "
            f"{row['status']} | {row['importance']} | 第{row['updated_chapter']}章 |"
        )
    return "\n".join(lines) + "\n"


def normalize_timeline_change(
    value: object,
    label: str,
    *,
    allow_delete: bool,
    through_chapter: int,
) -> dict[str, Any]:
    event = as_mapping(value, label)
    require_known_keys(
        event,
        {"action", "id", "story_time", "objective_fact", "reader_knowledge", "reveal_status", "reveal_chapter", "characters"},
        label,
    )
    action = clean_text(event.get("action", "upsert"), f"{label}.action", max_bytes=24)
    require(action in ({"upsert", "delete"} if allow_delete else {"upsert"}), f"{label}.action is invalid")
    identifier = clean_text(event.get("id"), f"{label}.id", max_bytes=24)
    require(EVENT_ID.fullmatch(identifier) is not None, f"{label}.id must look like E001")
    if action == "delete":
        return {"action": action, "id": identifier}
    reveal_status = clean_text(event.get("reveal_status"), f"{label}.reveal_status", max_bytes=24)
    require(reveal_status in REVEAL_STATUSES, f"{label}.reveal_status must be one of {REVEAL_STATUSES}")
    reveal_raw = event.get("reveal_chapter")
    reveal_chapter = None if reveal_raw is None else as_int(reveal_raw, f"{label}.reveal_chapter", minimum=1)
    if reveal_status == "未揭示":
        require(reveal_chapter is None, f"{label} must not put a future reveal chapter in established timeline facts")
    else:
        require(reveal_chapter is not None, f"{label}.reveal_chapter is required once revealed")
        require(reveal_chapter <= through_chapter, f"{label}.reveal_chapter cannot be in the future")
    return {
        "action": action,
        "id": identifier,
        "story_time": clean_text(event.get("story_time"), f"{label}.story_time", max_bytes=240),
        "objective_fact": clean_text(event.get("objective_fact"), f"{label}.objective_fact", max_bytes=480),
        "reader_knowledge": clean_text(event.get("reader_knowledge"), f"{label}.reader_knowledge", max_bytes=480),
        "reveal_status": reveal_status,
        "reveal_chapter": reveal_chapter,
        "characters": clean_string_list(event.get("characters", []), f"{label}.characters", maximum=12, item_max_bytes=120),
    }


def normalize_timeline_state(value: object, last_chapter: int) -> dict[str, dict[str, Any]]:
    events = as_mapping(value, "tracking state.timeline")
    normalized: dict[str, dict[str, Any]] = {}
    for raw_identifier, raw_event in events.items():
        identifier = clean_text(raw_identifier, "tracking state.timeline ID", max_bytes=24)
        event = as_mapping(raw_event, f"tracking state.timeline.{identifier}")
        require_known_keys(
            event,
            {
                "id", "story_time", "objective_fact", "reader_knowledge", "reveal_status", "reveal_chapter",
                "characters", "first_recorded_chapter", "updated_chapter",
            },
            f"tracking state.timeline.{identifier}",
        )
        require(event.get("id") == identifier, f"tracking state.timeline.{identifier}.id does not match its key")
        change = normalize_timeline_change(
            {
                "action": "upsert",
                **{
                    key: value
                    for key, value in event.items()
                    if key not in {"first_recorded_chapter", "updated_chapter"}
                },
            },
            f"tracking state.timeline.{identifier}",
            allow_delete=False,
            through_chapter=last_chapter,
        )
        change.pop("action")
        first = as_int(event.get("first_recorded_chapter"), f"tracking state.timeline.{identifier}.first_recorded_chapter", minimum=1)
        updated = as_int(event.get("updated_chapter"), f"tracking state.timeline.{identifier}.updated_chapter", minimum=1)
        require(first <= last_chapter, f"timeline event {identifier} starts after current chapter")
        require(updated <= last_chapter, f"timeline event {identifier} updates after current chapter")
        change["first_recorded_chapter"] = first
        change["updated_chapter"] = updated
        normalized[identifier] = change
    return normalized


def render_timeline_views(events: dict[str, dict[str, Any]], revision: int) -> tuple[str, str]:
    author_lines = [
        "# 作者真相时间线",
        "",
        f"> 状态修订：{revision}。客观事实与读者认知的权威对照；未来揭示计划仍留在大纲。",
        "",
        "| ID | 首次登记章 | 故事时间 | 客观事实 | 读者当前认知 | 揭示状态 | 实际揭示章 |",
        "|---|---:|---|---|---|---|---:|",
    ]
    reader_lines = [
        "# 读者已知时间线",
        "",
        f"> 状态修订：{revision}。只呈现读者截至当前章节已经知道或相信的内容，不泄露作者侧客观真相。",
        "",
        "| ID | 读者当前认知 | 认知截至章 |",
        "|---|---|---:|",
    ]
    for identifier in sorted(events):
        event = events[identifier]
        reveal = f"第{event['reveal_chapter']}章" if event.get("reveal_chapter") else "—"
        characters = "、".join(event.get("characters", []))
        objective = event["objective_fact"] + (f"（涉及：{characters}）" if characters else "")
        author_lines.append(
            f"| {identifier} | 第{event['first_recorded_chapter']}章 | {event['story_time']} | {objective} | "
            f"{event['reader_knowledge']} | {event['reveal_status']} | {reveal} |"
        )
        reader_lines.append(f"| {identifier} | {event['reader_knowledge']} | 第{event['updated_chapter']}章 |")
    return "\n".join(author_lines) + "\n", "\n".join(reader_lines) + "\n"


def normalize_information_gap_change(
    value: object,
    label: str,
    *,
    through_chapter: int,
    default_action: str = "register",
) -> dict[str, Any]:
    """归一化一条信息差变更（register 登记 / update 更新 / retire 撤销登记）。

    仿 normalize_foreshadow_change 的 allow-delete 模式：retire 只带 id，
    其余动作校验完整字段；first/updated 章节由工具维护，不在输入里。
    """
    row = as_mapping(value, label)
    require_known_keys(
        row,
        {"action", "id", "knowers", "reader_known", "keywords", "status", "note"},
        label,
    )
    action = clean_text(row.get("action", default_action), f"{label}.action", max_bytes=24)
    require(action in {"register", "update", "retire"}, f"{label}.action is invalid")
    identifier = clean_text(row.get("id"), f"{label}.id", max_bytes=24)
    require(GAP_ID.fullmatch(identifier) is not None, f"{label}.id must look like G001")
    if action == "retire":
        return {"action": action, "id": identifier}
    reader_known = clean_text(row.get("reader_known"), f"{label}.reader_known", max_bytes=12)
    require(reader_known in READER_KNOWN, f"{label}.reader_known must be one of {READER_KNOWN}")
    status = clean_text(row.get("status"), f"{label}.status", max_bytes=24)
    require(status in GAP_STATUSES, f"{label}.status must be one of {GAP_STATUSES}")
    return {
        "action": action,
        "id": identifier,
        "knowers": clean_string_list(
            row.get("knowers", []), f"{label}.knowers", maximum=KNOWERS_MAX, item_max_bytes=120
        ),
        "reader_known": reader_known,
        "keywords": clean_string_list(row.get("keywords", []), f"{label}.keywords", item_max_bytes=192),
        "status": status,
        "note": clean_text(row.get("note"), f"{label}.note", max_bytes=360),
    }


def normalize_information_gap_state(value: object, last_chapter: int) -> dict[str, dict[str, Any]]:
    gaps = as_mapping(value, "tracking state.information_gaps")
    normalized: dict[str, dict[str, Any]] = {}
    for raw_identifier, raw_row in gaps.items():
        identifier = clean_text(raw_identifier, "tracking state.information_gaps ID", max_bytes=24)
        row = as_mapping(raw_row, f"tracking state.information_gaps.{identifier}")
        require_known_keys(
            row,
            {
                "id", "knowers", "reader_known", "keywords", "status",
                "first_recorded_chapter", "updated_chapter", "note",
            },
            f"tracking state.information_gaps.{identifier}",
        )
        require(
            row.get("id") == identifier,
            f"tracking state.information_gaps.{identifier}.id does not match its key",
        )
        change = normalize_information_gap_change(
            {
                "action": "update",
                **{key: value for key, value in row.items() if key not in {"first_recorded_chapter", "updated_chapter"}},
            },
            f"tracking state.information_gaps.{identifier}",
            through_chapter=last_chapter,
        )
        change.pop("action")
        first = as_int(
            row.get("first_recorded_chapter"),
            f"tracking state.information_gaps.{identifier}.first_recorded_chapter",
            minimum=1,
        )
        updated = as_int(
            row.get("updated_chapter"),
            f"tracking state.information_gaps.{identifier}.updated_chapter",
            minimum=1,
        )
        require(first <= last_chapter, f"information gap {identifier} starts after current chapter")
        require(updated <= last_chapter, f"information gap {identifier} updates after current chapter")
        change["first_recorded_chapter"] = first
        change["updated_chapter"] = updated
        normalized[identifier] = change
    return normalized


def render_information_gaps(gaps: dict[str, dict[str, Any]], revision: int) -> str:
    lines = [
        "# 信息差当前登记",
        "",
        f"> 状态修订：{revision}。登记「谁知道什么」：知情人 × 读者已知 × 关键词；历史变化见 `逐章记录/`。",
        "",
        "| ID | 知情人 | 读者已知 | 关键词 | 状态 | 首次登记章 | 最近变更章 | 备注 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for identifier in sorted(gaps):
        row = gaps[identifier]
        knowers = "、".join(row["knowers"]) or "—"
        keywords = "、".join(row["keywords"]) or "—"
        note = row["note"] or "—"
        lines.append(
            f"| {identifier} | {knowers} | {row['reader_known']} | {keywords} | {row['status']} | "
            f"第{row['first_recorded_chapter']}章 | 第{row['updated_chapter']}章 | {note} |"
        )
    return "\n".join(lines) + "\n"


def validate_context_input(value: object, *, include_initial_fields: bool) -> dict[str, Any]:
    context = as_mapping(value, "context")
    allowed = {"position", "long_term_constraints", "active_character_names", "continuity_risks"}
    if include_initial_fields:
        allowed.update({"recent_chapters", "next_chapter_commitments"})
    require_known_keys(context, allowed, "context")
    normalized: dict[str, Any] = {
        "position": validate_position(context.get("position")),
        "long_term_constraints": clean_string_list(
            context.get("long_term_constraints", []), "context.long_term_constraints", maximum=6
        ),
        "active_character_names": [
            safe_file_component(name, f"context.active_character_names[{index}]")
            for index, name in enumerate(as_list(context.get("active_character_names", []), "context.active_character_names"))
        ],
        "continuity_risks": clean_string_list(
            context.get("continuity_risks", []), "context.continuity_risks", maximum=5
        ),
    }
    require(len(normalized["active_character_names"]) <= 6, "context.active_character_names may contain at most 6 names")
    require(
        len({portable_name_key(name) for name in normalized["active_character_names"]})
        == len(normalized["active_character_names"]),
        "context.active_character_names contains cross-platform duplicates",
    )
    if include_initial_fields:
        recent: list[dict[str, Any]] = []
        for index, raw_item in enumerate(as_list(context.get("recent_chapters", []), "context.recent_chapters")):
            item = as_mapping(raw_item, f"context.recent_chapters[{index}]")
            require_known_keys(item, {"chapter", "summary"}, f"context.recent_chapters[{index}]")
            recent.append(
                {
                    "chapter": as_int(item.get("chapter"), f"context.recent_chapters[{index}].chapter", minimum=1),
                    "summary": clean_text(item.get("summary"), f"context.recent_chapters[{index}].summary", max_bytes=360),
                }
            )
        require(len(recent) <= 3, "context.recent_chapters may contain at most 3 items")
        normalized["recent_chapters"] = recent
        normalized["next_chapter_commitments"] = clean_string_list(
            context.get("next_chapter_commitments", []), "context.next_chapter_commitments", maximum=5
        )
    return normalized


def active_foreshadow_lines(rows: dict[str, dict[str, Any]]) -> list[str]:
    importance = {value: index for index, value in enumerate(FORESHADOW_IMPORTANCE)}
    candidates = [row for row in rows.values() if row["status"] == "已埋"]
    candidates.sort(
        key=lambda row: (importance[row["importance"]], row["planned_resolution_chapter"] or 10**12, row["id"])
    )
    result = []
    for row in candidates[:8]:
        planned = f"第{row['planned_resolution_chapter']}章" if row["planned_resolution_chapter"] else "回收章未定"
        result.append(f"{row['id']}｜{row['summary']}｜埋第{row['planted_chapter']}章｜{planned}｜{row['importance']}")
    return result


def appearing_characters_from_outline(project: Path, state: dict[str, Any]) -> set[str] | None:
    """B57 角色状态分层：读当前章细纲「人物关系和出场顺序」节提取出场角色名。

    以 state.last_committed_chapter+1 为目标章；细纲不存在/无该字段/解析为空 →
    返回 None（调用方维持全展开向后兼容）。只读探测，任何异常都静默降级。
    """
    try:
        chapter = state.get("last_committed_chapter", 0) + 1
        outline_dir = project / "大纲"
        if not outline_dir.is_dir():
            return None
        candidates = sorted(outline_dir.glob(f"细纲_第{chapter:03d}章*.md")) or sorted(
            outline_dir.glob(f"细纲_第{chapter}章*.md")
        )
        if not candidates:
            return None
        text = candidates[0].read_text(encoding="utf-8", errors="ignore")
        # 细纲两种形态都认：同一行「人物关系和出场顺序：A、B」或字段行后另起一行列名
        m = re.search(r"人物关系[和与]出场顺序[：:]\s*([^\n]+)", text) or re.search(
            r"人物关系[和与]出场顺序[^：:\n]*\n\s*[-•]?\s*([^\n##]+)", text
        )
        if not m:
            return None
        names = {
            name.strip()
            for name in re.split(r"[、，,/·]|(?:\s{2,})", m.group(1))
            if 1 < len(name.strip()) <= 12 and not re.search(r"[（）()【】\[\]]", name)
        }
        known = set(state["characters"])
        hit = {n for n in names if any(n in k or k in n for k in known)}
        return hit or None
    except Exception:
        return None


def render_context(state: dict[str, Any], appearing: set[str] | None = None) -> str:
    context = state["context"]
    position = context["position"]
    current_chapter = (
        "尚未开篇" if state["last_committed_chapter"] == 0 else f"第{state['last_committed_chapter']}章"
    )
    active_names = list(context["active_character_names"])
    # B57 分层渲染：有细纲出场信息时「本章出场」展开、「背景角色」仅列名；无则全展开（向后兼容）。
    if appearing:
        on_stage = [n for n in active_names if n in appearing]
        background = [n for n in active_names if n not in appearing]
        character_lines = [
            "### 本章出场（必读）"
        ] + [
            f"{name}｜{state['characters'][name]['identity']}｜{state['characters'][name]['state']}｜"
            f"目标：{state['characters'][name]['goal']}"
            for name in on_stage
        ] + [
            "### 背景角色（仅跟踪，不进正文 prompt）",
            "、".join(background) if background else "无",
        ]
        character_section = ("## 核心角色状态", character_lines)
    else:
        character_section = (
            "## 核心角色状态",
            [
                f"{name}｜{state['characters'][name]['identity']}｜{state['characters'][name]['state']}｜"
                f"目标：{state['characters'][name]['goal']}"
                for name in active_names
            ],
        )
    sections: list[tuple[str, list[str]]] = [
        (
            "## 当前位置",
            [
                f"当前章：{current_chapter}",
                f"卷：{position['volume']}（始于第{position['volume_start_chapter']}章）",
                f"故事时间：{position['story_time']}",
                f"场景：{position['scene']}",
            ],
        ),
        ("## 长期约束", context["long_term_constraints"]),
        character_section,
        ("## 活跃伏笔", active_foreshadow_lines(state["foreshadow"])),
        ("## 近三章速记", [f"第{item['chapter']}章｜{item['summary']}" for item in context["recent_chapters"]]),
        ("## 下一章承诺", context["next_chapter_commitments"]),
        ("## 连贯性风险", context["continuity_risks"]),
    ]
    lines = [
        f"# 写作连续性上下文 — {state['book_title']}",
        "",
        f"> 状态修订：{state['state_revision']}。截至当前章的续写状态卡，只放下一章真正需要的连续性状态。",
        "",
    ]
    for heading, values in sections:
        lines.append(heading)
        lines.extend(f"- {value}" for value in values or ["无"])
        lines.append("")
    payload = "\n".join(lines).rstrip() + "\n"
    headings = tuple(line for line in payload.splitlines() if line.startswith("## "))
    require(headings == CONTEXT_HEADINGS, "generated context headings do not match the seven-section schema")
    require(byte_size(payload) <= CONTEXT_MAX_BYTES, f"hot context exceeds {CONTEXT_MAX_BYTES} bytes")
    return payload


def normalize_delta(
    value: object,
    *,
    through_chapter: int,
    snapshots: dict[str, dict[str, Any]],
    existing_core_names: dict[str, str],
) -> dict[str, Any]:
    delta = as_mapping(value, "delta")
    require_known_keys(
        delta,
        {
            "result", "character_changes", "foreshadow_changes", "timeline_events", "information_gap_changes",
            "constraints", "next_chapter_commitments", "retired_context_items", "retired_characters",
        },
        "delta",
    )
    retired_characters = [
        safe_file_component(name, f"delta.retired_characters[{index}]")
        for index, name in enumerate(as_list(delta.get("retired_characters", []), "delta.retired_characters"))
    ]
    retired_keys = [portable_name_key(name) for name in retired_characters]
    require(len(retired_keys) == len(set(retired_keys)), "delta.retired_characters contains duplicate characters")
    retiring = set(retired_keys)
    character_changes: list[dict[str, Any]] = []
    for index, raw_change in enumerate(as_list(delta.get("character_changes", []), "delta.character_changes")):
        change = as_mapping(raw_change, f"delta.character_changes[{index}]")
        require_known_keys(change, {"name", "change"}, f"delta.character_changes[{index}]")
        name = safe_file_component(change.get("name"), f"delta.character_changes[{index}].name")
        existing = existing_core_names.get(portable_name_key(name))
        is_core = name in snapshots or existing is not None
        # 本章退役的角色记录最后一次变化即可，不必再交一份马上要删的快照。
        require(
            not is_core or name in snapshots or portable_name_key(name) in retiring,
            f"core character {name} changed but has no current snapshot",
        )
        character_changes.append(
            {"name": name, "change": clean_text(change.get("change"), f"delta.character_changes[{index}].change", max_bytes=360)}
        )
    character_keys = [portable_name_key(item["name"]) for item in character_changes]
    require(len(character_keys) == len(set(character_keys)), "delta.character_changes contains duplicate characters")
    foreshadow_changes = [
        normalize_foreshadow_change(
            raw, f"delta.foreshadow_changes[{index}]", allow_delete=True, through_chapter=through_chapter
        )
        for index, raw in enumerate(as_list(delta.get("foreshadow_changes", []), "delta.foreshadow_changes"))
    ]
    timeline_events = [
        normalize_timeline_change(
            raw, f"delta.timeline_events[{index}]", allow_delete=True, through_chapter=through_chapter
        )
        for index, raw in enumerate(as_list(delta.get("timeline_events", []), "delta.timeline_events"))
    ]
    information_gap_changes = [
        normalize_information_gap_change(
            raw, f"delta.information_gap_changes[{index}]", through_chapter=through_chapter
        )
        for index, raw in enumerate(as_list(delta.get("information_gap_changes", []), "delta.information_gap_changes"))
    ]
    require(
        len({item["id"] for item in foreshadow_changes}) == len(foreshadow_changes),
        "delta.foreshadow_changes contains duplicate IDs",
    )
    require(
        len({item["id"] for item in timeline_events}) == len(timeline_events),
        "delta.timeline_events contains duplicate IDs",
    )
    require(
        len({item["id"] for item in information_gap_changes}) == len(information_gap_changes),
        "delta.information_gap_changes contains duplicate IDs",
    )
    require(
        set(snapshots).issubset({item["name"] for item in character_changes}),
        "character_snapshots must contain exactly the core characters changed by this transaction",
    )
    return {
        "result": clean_text(delta.get("result"), "delta.result", max_bytes=480),
        "character_changes": character_changes,
        "foreshadow_changes": foreshadow_changes,
        "timeline_events": timeline_events,
        "information_gap_changes": information_gap_changes,
        "constraints": clean_string_list(delta.get("constraints", []), "delta.constraints", maximum=6),
        "next_chapter_commitments": clean_string_list(
            delta.get("next_chapter_commitments", []), "delta.next_chapter_commitments", maximum=5
        ),
        "retired_context_items": clean_string_list(
            delta.get("retired_context_items", []), "delta.retired_context_items", maximum=11
        ),
        "retired_characters": retired_characters,
    }


def render_delta(chapter: int, title: str, delta: dict[str, Any], core_names: set[str]) -> str:
    lines = [
        f"# 第{chapter:03d}章 · {title}",
        f"- 结果：{delta['result']}",
        "- 下一章承诺：" + ("；".join(delta["next_chapter_commitments"]) or "无"),
        "",
        "## 角色变化",
    ]
    lines.extend(
        f"- {item['name']}｜{'核心' if item['name'] in core_names else '临时'}｜{item['change']}"
        for item in delta["character_changes"]
    )
    if not delta["character_changes"]:
        lines.append("- 无")
    lines.extend(["", "## 伏笔变化"])
    for item in delta["foreshadow_changes"]:
        if item["action"] == "delete":
            lines.append(f"- {item['id']}｜删除当前登记")
        else:
            planned = f"第{item['planned_resolution_chapter']}章" if item["planned_resolution_chapter"] else "未定"
            lines.append(f"- {item['id']}｜{item['status']}｜{item['summary']}｜回收{planned}")
    if not delta["foreshadow_changes"]:
        lines.append("- 无")
    lines.extend(["", "## 时间与揭示"])
    for item in delta["timeline_events"]:
        if item["action"] == "delete":
            lines.append(f"- {item['id']}｜删除当前登记")
        else:
            lines.append(
                f"- {item['id']}｜{item['story_time']}｜事实：{item['objective_fact']}｜"
                f"读者：{item['reader_knowledge']}｜{item['reveal_status']}"
            )
    if not delta["timeline_events"]:
        lines.append("- 无")
    lines.extend(["", "## 连贯性约束"])
    lines.extend(f"- {item}" for item in delta["constraints"])
    if not delta["constraints"]:
        lines.append("- 无")
    retired = delta.get("retired_context_items", []) + [
        f"角色状态：{name}" for name in delta.get("retired_characters", [])
    ]
    if retired:
        # 退役条目在此留档，续写状态卡收缩后仍可回查当初撤下了什么。
        lines.extend(["", "## 本章退役登记"])
        lines.extend(f"- {item}" for item in retired)
    payload = "\n".join(lines) + "\n"
    size = byte_size(payload)
    require(size <= DELTA_MAX_BYTES, f"chapter delta is {size} bytes; hard cap is {DELTA_MAX_BYTES}")
    return payload


def normalize_state(document: object) -> dict[str, Any]:
    root = as_mapping(document, "tracking state")
    require_known_keys(
        root,
        {
            "schema_version", "book_title", "last_committed_chapter", "imported_through_chapter",
            "state_revision", "context", "characters", "foreshadow", "timeline", "information_gaps",
        },
        "tracking state",
    )
    require(root.get("schema_version") == TRACKING_SCHEMA_VERSION, "tracking state schema is unsupported")
    last_chapter = as_int(root.get("last_committed_chapter"), "tracking state.last_committed_chapter")
    imported_through = as_int(root.get("imported_through_chapter"), "tracking state.imported_through_chapter")
    require(imported_through <= last_chapter, "imported chapter cutoff exceeds current chapter")
    context = validate_context_input(root.get("context"), include_initial_fields=True)
    require(
        context["position"]["volume_start_chapter"] <= max(1, last_chapter),
        "context.position.volume_start_chapter is after the current writing position",
    )
    recent_numbers = [item["chapter"] for item in context["recent_chapters"]]
    require(recent_numbers == sorted(recent_numbers), "context.recent_chapters must be ordered")
    require(len(recent_numbers) == len(set(recent_numbers)), "context.recent_chapters contains duplicates")
    require(all(chapter <= last_chapter for chapter in recent_numbers), "context.recent_chapters cannot include future chapters")
    characters = normalize_snapshots(root.get("characters", {}), "tracking state.characters")
    for name in context["active_character_names"]:
        require(name in characters, f"active core character {name} has no current snapshot")
    foreshadow = normalize_foreshadow_state(root.get("foreshadow", {}), last_chapter)
    timeline = normalize_timeline_state(root.get("timeline", {}), last_chapter)
    information_gaps = normalize_information_gap_state(root.get("information_gaps", {}), last_chapter)
    if last_chapter == 0:
        require(not foreshadow, "a chapter-0 project cannot have planted foreshadow facts")
        require(not timeline, "a chapter-0 project cannot have established timeline facts")
        require(not information_gaps, "a chapter-0 project cannot have registered information gaps")
    return {
        "schema_version": TRACKING_SCHEMA_VERSION,
        "book_title": clean_text(root.get("book_title"), "tracking state.book_title", max_bytes=240),
        "last_committed_chapter": last_chapter,
        "imported_through_chapter": imported_through,
        "state_revision": as_int(root.get("state_revision"), "tracking state.state_revision"),
        "context": context,
        "characters": characters,
        "foreshadow": foreshadow,
        "timeline": timeline,
        "information_gaps": information_gaps,
    }


def load_state(project: Path) -> dict[str, Any]:
    path = state_path(project)
    require(path.exists(), "tracking state is missing; run init first")
    return normalize_state(read_json(path))


def migrate_v4_state(project: Path) -> None:
    """写入路径的一次性 v4→v5 迁移：先备份原文件，再原地升版并补空 information_gaps 域。

    仅当 schema_version==4 且缺 information_gaps 域时触发；备份命名
    `追踪/_备份/schema-v4-<YYYYMMDD-HHMMSS>.json`（同秒冲突追加随机后缀）。
    迁移失败不写任何文件；老键原样保留，零丢失。
    """
    path = state_path(project)
    if not path.exists():
        return
    document = read_json(path)
    if not (
        isinstance(document, dict)
        and document.get("schema_version") == TRACKING_SCHEMA_VERSION - 1
        and "information_gaps" not in document
    ):
        return
    tracking = tracking_root(project)
    backup_dir = tracking / "_备份"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = backup_dir / f"schema-v4-{stamp}.json"
    while backup.exists():
        backup = backup_dir / f"schema-v4-{stamp}-{os.urandom(2).hex()}.json"
    atomic_write_text(backup, json_payload(document))
    migrated = dict(document)
    migrated["schema_version"] = TRACKING_SCHEMA_VERSION
    migrated["information_gaps"] = {}
    atomic_write_text(path, json_payload(migrated))
    emit(f"NOTE: tracking state migrated v4→v5; backup at 追踪/_备份/{backup.name}", error=True)


def normalize_initial_document(document: object) -> dict[str, Any]:
    root = as_mapping(document, "init input")
    require_known_keys(
        root,
        {
            "schema_version", "book_title", "last_chapter", "context", "character_snapshots",
            "foreshadow", "timeline_events", "information_gaps",
        },
        "init input",
    )
    require(root.get("schema_version") == INPUT_SCHEMA_VERSION, "init input schema_version is unsupported")
    last_chapter = as_int(root.get("last_chapter"), "last_chapter")
    context = validate_context_input(root.get("context"), include_initial_fields=True)
    snapshots = normalize_snapshots(root.get("character_snapshots", {}))
    foreshadow: dict[str, dict[str, Any]] = {}
    for index, raw_row in enumerate(as_list(root.get("foreshadow", []), "foreshadow")):
        row = normalize_foreshadow_change(
            raw_row, f"foreshadow[{index}]", allow_delete=False, through_chapter=last_chapter
        )
        require(row["id"] not in foreshadow, f"duplicate foreshadow ID {row['id']}")
        row.pop("action")
        row["updated_chapter"] = max(1, last_chapter)
        foreshadow[row["id"]] = row
    timeline: dict[str, dict[str, Any]] = {}
    for index, raw_event in enumerate(as_list(root.get("timeline_events", []), "timeline_events")):
        event = normalize_timeline_change(
            raw_event, f"timeline_events[{index}]", allow_delete=False, through_chapter=last_chapter
        )
        require(event["id"] not in timeline, f"duplicate timeline event ID {event['id']}")
        event.pop("action")
        event["first_recorded_chapter"] = max(1, last_chapter)
        event["updated_chapter"] = max(1, last_chapter)
        timeline[event["id"]] = event
    information_gaps: dict[str, dict[str, Any]] = {}
    for index, raw_row in enumerate(as_list(root.get("information_gaps", []), "information_gaps")):
        row = normalize_information_gap_change(
            raw_row, f"information_gaps[{index}]", through_chapter=last_chapter
        )
        require(row["action"] == "register", f"information_gaps[{index}] must use action register in init")
        require(row["id"] not in information_gaps, f"duplicate information gap ID {row['id']}")
        row.pop("action")
        row["first_recorded_chapter"] = max(1, last_chapter)
        row["updated_chapter"] = max(1, last_chapter)
        information_gaps[row["id"]] = row
    return normalize_state(
        {
            "schema_version": TRACKING_SCHEMA_VERSION,
            "book_title": clean_text(root.get("book_title"), "book_title", max_bytes=240),
            "last_committed_chapter": last_chapter,
            "imported_through_chapter": last_chapter,
            "state_revision": 0,
            "context": context,
            "characters": snapshots,
            "foreshadow": foreshadow,
            "timeline": timeline,
            "information_gaps": information_gaps,
        }
    )


def normalize_transaction(state: dict[str, Any], document: object) -> dict[str, Any]:
    root = as_mapping(document, "transaction")
    require_known_keys(
        root,
        {
            "schema_version", "mode", "chapter", "chapter_title", "expected_state_revision",
            "delta", "context", "character_snapshots",
        },
        "transaction",
    )
    require(root.get("schema_version") == INPUT_SCHEMA_VERSION, "transaction schema_version is unsupported")
    mode = clean_text(root.get("mode"), "mode", max_bytes=24)
    require(mode in {"append", "revision"}, "mode must be append or revision")
    chapter = as_int(root.get("chapter"), "chapter", minimum=1)
    expected_revision = as_int(root.get("expected_state_revision"), "expected_state_revision")
    require(expected_revision == state["state_revision"], "tracking state changed since this transaction was prepared")
    last = state["last_committed_chapter"]
    if mode == "append":
        require(chapter == last + 1, f"append chapter must be {last + 1}, got {chapter}")
    else:
        require(chapter <= last, f"cannot revise unwritten chapter {chapter}; last committed chapter is {last}")
    context = validate_context_input(root.get("context"), include_initial_fields=False)
    snapshots = normalize_snapshots(root.get("character_snapshots", {}))
    existing_names = {portable_name_key(name): name for name in state["characters"]}
    for name in snapshots:
        existing = existing_names.get(portable_name_key(name))
        require(existing is None or existing == name, f"character {name} conflicts with existing character {existing}")
    through_chapter = chapter if mode == "append" else last
    delta = normalize_delta(
        root.get("delta"),
        through_chapter=through_chapter,
        snapshots=snapshots,
        existing_core_names=existing_names,
    )
    return {
        "mode": mode,
        "chapter": chapter,
        "title": clean_text(root.get("chapter_title"), "chapter_title", max_bytes=240),
        "delta": delta,
        "context": context,
        "snapshots": snapshots,
    }


def checkpoint_record(
    change: dict[str, Any], chapter: int, previous: dict[str, Any] | None, *, keep_first_chapter: bool = False
) -> dict[str, Any]:
    current = {key: value for key, value in change.items() if key != "action"}
    current["updated_chapter"] = max(previous["updated_chapter"] if previous else chapter, chapter)
    if keep_first_chapter:
        current["first_recorded_chapter"] = previous["first_recorded_chapter"] if previous else chapter
    return current


def merge_transaction(state: dict[str, Any], transaction: dict[str, Any]) -> dict[str, Any]:
    next_state = copy.deepcopy(state)
    chapter = transaction["chapter"]
    if transaction["mode"] == "append":
        next_state["last_committed_chapter"] = chapter
    next_state["state_revision"] += 1
    next_state["characters"].update(transaction["snapshots"])

    next_context = transaction["context"]
    # 退役说的是「从此刻起离开当前状态」，只有 append 的逐章记录代表此刻；
    # 修订记录属于被改写的旧章，落在那里会谎报退役发生的章节。
    is_revision = transaction["mode"] == "revision"
    require(
        not (is_revision and transaction["delta"]["retired_characters"]),
        "retired_characters must be committed in an append transaction, not a revision",
    )
    for name in transaction["delta"]["retired_characters"]:
        require(name in next_state["characters"], f"retired character {name} has no current snapshot")
        require(
            name not in transaction["snapshots"],
            f"character {name} cannot be retired and updated in the same transaction",
        )
        require(
            name not in next_context["active_character_names"],
            f"retired character {name} is still listed in context.active_character_names",
        )
        next_state["characters"].pop(name)

    # 上下文条目是整份提交的；漏写会静默丢历史裁定，因此掉落必须显式声明。
    previous_items = set(state["context"]["long_term_constraints"]) | set(state["context"]["continuity_risks"])
    dropped = previous_items - (set(next_context["long_term_constraints"]) | set(next_context["continuity_risks"]))
    require(
        not (is_revision and dropped),
        "a revision must resubmit every current context item; retire them in an append transaction instead: "
        + "；".join(sorted(dropped)),
    )
    undeclared = sorted(dropped - set(transaction["delta"]["retired_context_items"]))
    require(
        not undeclared,
        "context items were dropped without being declared in delta.retired_context_items: "
        + "；".join(undeclared),
    )
    transaction["delta"]["retired_context_items"] = sorted(dropped)

    for change in transaction["delta"]["foreshadow_changes"]:
        if change["action"] == "delete":
            next_state["foreshadow"].pop(change["id"], None)
        else:
            next_state["foreshadow"][change["id"]] = checkpoint_record(
                change, chapter, next_state["foreshadow"].get(change["id"])
            )
    for change in transaction["delta"]["timeline_events"]:
        if change["action"] == "delete":
            next_state["timeline"].pop(change["id"], None)
        else:
            next_state["timeline"][change["id"]] = checkpoint_record(
                change, chapter, next_state["timeline"].get(change["id"]), keep_first_chapter=True
            )
    for change in transaction["delta"]["information_gap_changes"]:
        if change["action"] == "retire":
            next_state["information_gaps"].pop(change["id"], None)
            continue
        previous = next_state["information_gaps"].get(change["id"])
        if change["action"] == "register":
            require(
                previous is None,
                f"information gap {change['id']} is already registered; use update instead",
            )
        else:  # update
            require(
                previous is not None,
                f"information gap {change['id']} is not registered; use register instead",
            )
        next_state["information_gaps"][change["id"]] = checkpoint_record(
            change, chapter, previous, keep_first_chapter=True
        )

    recent_by_chapter = {item["chapter"]: item for item in state["context"]["recent_chapters"]}
    if chapter in recent_by_chapter or transaction["mode"] == "append":
        recent_by_chapter[chapter] = {"chapter": chapter, "summary": transaction["delta"]["result"]}
    recent = sorted(recent_by_chapter.values(), key=lambda item: item["chapter"])[-3:]
    current_last = next_state["last_committed_chapter"]
    next_commitments = (
        transaction["delta"]["next_chapter_commitments"]
        if transaction["mode"] == "append" or chapter == current_last
        else state["context"]["next_chapter_commitments"]
    )
    next_state["context"] = {
        **next_context,
        "recent_chapters": recent,
        "next_chapter_commitments": next_commitments,
    }
    return normalize_state(next_state)


def render_views(state: dict[str, Any], appearing: set[str] | None = None) -> dict[str, str]:
    revision = state["state_revision"]
    views = {
        "上下文.md": render_context(state, appearing),
        "伏笔.md": render_foreshadow(state["foreshadow"], revision),
        "信息差.md": render_information_gaps(state["information_gaps"], revision),
    }
    author, reader = render_timeline_views(state["timeline"], revision)
    views["时间线/作者真相.md"] = author
    views["时间线/读者已知.md"] = reader
    for name, snapshot in state["characters"].items():
        views[f"角色状态/{name}.md"] = render_snapshot(
            name, snapshot, state["last_committed_chapter"], revision
        )
    return views


def write_views(tracking: Path, views: dict[str, str]) -> None:
    # 上下文携带 next revision，先写它；任何后续失败都会让 hook/check 发现
    # 上下文 revision 与最后提交的 _tracking-state.json 不一致。
    write_if_changed(tracking / "上下文.md", views["上下文.md"])
    for relative in sorted(path for path in views if path != "上下文.md"):
        write_if_changed(tracking / relative, views[relative])
    expected_character_files = {
        Path(relative).name for relative in views if relative.startswith("角色状态/")
    }
    character_dir = tracking / "角色状态"
    character_dir.mkdir(parents=True, exist_ok=True)
    for path in character_dir.glob("*.md"):
        if path.name not in expected_character_files:
            path.unlink()


def warn_sizes(views: dict[str, str], delta_payload: str | None = None) -> None:
    if delta_payload is not None and byte_size(delta_payload) > DELTA_TARGET_BYTES:
        emit(
            f"WARNING: chapter delta is {byte_size(delta_payload)} bytes; target is <= {DELTA_TARGET_BYTES}",
            error=True,
        )
    context_size = byte_size(views["上下文.md"])
    if context_size > CONTEXT_TARGET_BYTES:
        emit(f"WARNING: hot context is {context_size} bytes; target is <= {CONTEXT_TARGET_BYTES}", error=True)
    for relative, payload in views.items():
        if not relative.startswith("角色状态/"):
            continue
        size = byte_size(payload)
        if size > SNAPSHOT_TARGET_BYTES:
            emit(
                f"WARNING: character snapshot {Path(relative).stem} is {size} bytes; target is <= {SNAPSHOT_TARGET_BYTES}",
                error=True,
            )


def initialize(project: Path, document: object) -> dict[str, Any]:
    tracking = tracking_root(project)
    require(not state_path(project).exists(), "tracking state already exists; init never overwrites project state")
    state = normalize_initial_document(document)
    views = render_views(state)
    state_payload = json_payload(state)

    # 输入全部校验通过后才动用户文件，失败的 init 不会挪走任何东西。
    archived = archive_retired_tracking_paths(tracking)
    for directory in (tracking / "逐章记录", tracking / "角色状态", tracking / "时间线"):
        directory.mkdir(parents=True, exist_ok=True)
    write_views(tracking, views)
    atomic_write_text(state_path(project), state_payload)
    warn_sizes(views)
    if archived:
        emit(
            f"NOTE: 旧追踪结构已原样移入 追踪/{RETIRED_ARCHIVE_DIR}/：{', '.join(archived)}；"
            "当前状态以本次 init 输入为准，旧文件不参与解析。",
            error=True,
        )
    return state


def apply_transaction(project: Path, document: object) -> dict[str, Any]:
    tracking = tracking_root(project)
    require_no_retired_tracking_paths(tracking)
    migrate_v4_state(project)
    state = load_state(project)
    transaction = normalize_transaction(state, document)
    next_state = merge_transaction(state, transaction)

    delta_payload = render_delta(
        transaction["chapter"],
        transaction["title"],
        transaction["delta"],
        # 本章退役的角色在 next_state 里已被删除，但本章记录里仍应标为核心。
        set(next_state["characters"]) | set(transaction["delta"]["retired_characters"]),
    )
    # B57：本章出场角色从细纲提取，供状态卡分层渲染（细纲缺失时 None=全展开兼容）
    appearing = appearing_characters_from_outline(project, next_state)
    views = render_views(next_state, appearing=appearing)
    next_state_payload = json_payload(next_state)
    path = delta_path(tracking, transaction["chapter"])
    if transaction["mode"] == "append" and path.exists():
        require(
            path.read_text(encoding="utf-8") == delta_payload,
            f"chapter delta {transaction['chapter']} already exists with different content",
        )

    write_if_changed(path, delta_payload)
    write_views(tracking, views)
    # 唯一权威文件最后落盘；在此之前失败可用同一事务直接重跑。
    atomic_write_text(state_path(project), next_state_payload)
    warn_sizes(views, delta_payload)
    return next_state


def suspension_warnings(state: dict[str, Any], threshold: int) -> list[dict[str, Any]]:
    """悬置伏笔候选清单：status=已埋 且 last - updated_chapter >= 阈值。

    候选性质：只呈报，永不改变 check 退出码。语义=最近一次变动章起算的
    近似"持续未动"章距（契约文档注明）。
    """
    last = state["last_committed_chapter"]
    warnings: list[dict[str, Any]] = []
    for identifier in sorted(state["foreshadow"]):
        row = state["foreshadow"][identifier]
        if row["status"] != "已埋":
            continue
        chapters = last - row["updated_chapter"]
        if chapters >= threshold:
            warnings.append(
                {
                    "id": identifier,
                    "status": row["status"],
                    "chapters_since_update": chapters,
                }
            )
    return warnings


def check_project(project: Path) -> dict[str, Any]:
    tracking = tracking_root(project)
    require_no_retired_tracking_paths(tracking)
    state = load_state(project)
    last_chapter = state["last_committed_chapter"]
    required_delta_start = state["imported_through_chapter"] + 1
    for chapter in range(required_delta_start, last_chapter + 1):
        require(delta_path(tracking, chapter).exists(), f"chapter delta {chapter} is missing")
    for path in (tracking / "逐章记录").glob("第*章.md"):
        match = re.fullmatch(r"第(\d+)章\.md", path.name)
        require(match is not None, f"chapter delta has an invalid filename: {path.name}")
        chapter = as_int(int(match.group(1)), f"chapter delta {path.name}", minimum=1)
        require(path == delta_path(tracking, chapter), f"chapter delta {chapter} filename is not canonical")
        require(chapter <= last_chapter, f"chapter delta {chapter} exceeds last_committed_chapter")
        require(path.stat().st_size <= DELTA_MAX_BYTES, f"chapter delta {chapter} exceeds {DELTA_MAX_BYTES} bytes")

    expected_views = render_views(state)
    for relative, expected in expected_views.items():
        path = tracking / relative
        require(path.exists(), f"derived view is missing: {relative}")
        require(
            path.read_text(encoding="utf-8") == expected,
            f"derived view differs from _tracking-state.json: {relative}",
        )
    expected_character_files = {
        Path(relative).name for relative in expected_views if relative.startswith("角色状态/")
    }
    actual_character_files = {path.name for path in (tracking / "角色状态").glob("*.md")}
    require(actual_character_files == expected_character_files, "character snapshot files differ from tracking state")
    return state


def _try_read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def locate_volume_outline(
    project: Path,
    from_chapter: int,
    to_chapter: int,
    volume: int | None,
) -> tuple[Path | None, str | None]:
    """定位第④节要对照的卷纲。返回 (path, skipped_reason)。

    --volume 显式指定 → 大纲/卷纲_第N卷.md；缺省时 glob 卷纲并按「第 X-Y 章」
    章节范围正则探测包含 [from,to] 的唯一卷。无法定位（零卷/多卷命中/范围未识别/
    显式卷缺失）→ path=None, skipped="skipped_ambiguous_outline"。只读探测，不失败。
    """
    outline_dir = project / "大纲"
    if volume is not None:
        for path in outline_dir.glob("卷纲_*.md"):
            match = VOLUME_OUTLINE_RE.match(path.name)
            if match and int(match.group(1)) == volume:
                return path, None
        return None, "skipped_ambiguous_outline"
    candidates: list[Path] = []
    for path in sorted(outline_dir.glob("卷纲_*.md")):
        match = VOLUME_OUTLINE_RE.match(path.name)
        if not match:
            continue
        text = _try_read_utf8(path)
        range_match = VOLUME_RANGE_RE.search(text)
        if (
            range_match
            and int(range_match.group(1)) <= from_chapter
            and to_chapter <= int(range_match.group(2))
        ):
            candidates.append(path)
    if len(candidates) == 1:
        return candidates[0], None
    return None, "skipped_ambiguous_outline"


def parse_benchmark_coordinates(text: str) -> list[dict[str, Any]] | None:
    """解析卷纲的「### 对标结构坐标」表。无该节返回 None。

    只认点位（1/4 点 / 中点 / 3/4 点）开头的表行；表行在空行或非表行处截断。
    """
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == BENCHMARK_HEADING:
            start = index
            break
    if start is None:
        return None
    rows: list[dict[str, Any]] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not stripped or not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 4:
            continue
        point = cells[0]
        if point not in BENCHMARK_POINTS:
            continue
        benchmark_chapter = cells[1] or "—"
        planned_text = cells[2]
        anchors_text = cells[3]
        planned_match = BENCHMARK_PLANNED_RE.search(planned_text)
        if planned_match:
            planned_chapter: int | None = int(planned_match.group(1))
            status = "ok"
        else:
            planned_chapter = None
            status = "unparseable"
        anchors = [part for part in re.split(r"[、，,;；]+", anchors_text) if part]
        rows.append(
            {
                "point": point,
                "benchmark_chapter": benchmark_chapter,
                "planned_chapter": planned_chapter,
                "anchors": anchors,
                "status": status,
                "actual_chapter": None,
                "deviation": None,
                "hits": [],
            }
        )
    return rows


def _grep_anchor_lines(
    chapter_file: Path, chapter: int, anchors: list[str], content: str
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for line_no, line in enumerate(content.splitlines(), start=1):
        if any(anchor in line for anchor in anchors):
            hits.append(
                {
                    "scope": "prose",
                    "chapter": chapter,
                    "file": str(chapter_file),
                    "line": line_no,
                    "text": line.strip(),
                }
            )
    return hits


def _find_prose_anchor(
    project: Path, from_chapter: int, to_chapter: int, anchors: list[str]
) -> tuple[int | None, list[dict[str, Any]]]:
    """正文逐章升序扫描，首个含任一锚点的章即实际落点；附命中明细（文件:行）。"""
    prose_dir = project / "正文"
    ordered: list[tuple[int, Path]] = []
    for chapter_file in prose_dir.glob("第*.md"):
        match = PROSE_CHAPTER_RE.match(chapter_file.name)
        if match:
            chapter = int(match.group(1))
            if from_chapter <= chapter <= to_chapter:
                ordered.append((chapter, chapter_file))
    ordered.sort(key=lambda pair: pair[0])
    for chapter, chapter_file in ordered:
        content = _try_read_utf8(chapter_file)
        hits = _grep_anchor_lines(chapter_file, chapter, anchors, content)
        if hits:
            return chapter, hits
    return None, []


def _find_timeline_anchor(state: dict[str, Any], anchors: list[str]) -> list[dict[str, Any]]:
    """辅助：timeline 事件 objective_fact/reader_knowledge 命中 → 事件 id + 首记章。"""
    hits: list[dict[str, Any]] = []
    timeline = state.get("timeline", {})
    for event_id in sorted(timeline):
        event = timeline[event_id]
        for field in ("objective_fact", "reader_knowledge"):
            if any(anchor in (event.get(field) or "") for anchor in anchors):
                hits.append(
                    {
                        "scope": "timeline",
                        "event_id": event_id,
                        "field": field,
                        "first_recorded_chapter": event.get("first_recorded_chapter"),
                    }
                )
                break
    return hits


def _resolve_anchor_row(
    project: Path,
    from_chapter: int,
    to_chapter: int,
    state: dict[str, Any],
    row: dict[str, Any],
) -> dict[str, Any]:
    anchors: list[str] = row["anchors"]
    if not anchors:
        row.update(status="unanchored", actual_chapter=None, deviation=None, hits=[])
        return row
    actual_chapter, prose_hits = _find_prose_anchor(project, from_chapter, to_chapter, anchors)
    timeline_hits = _find_timeline_anchor(state, anchors)
    row["hits"] = prose_hits + timeline_hits
    if actual_chapter is None:
        row.update(status="not_found", actual_chapter=None, deviation=None)
        return row
    row["actual_chapter"] = actual_chapter
    planned = row["planned_chapter"]
    if planned is None:
        row["status"] = "unparseable"
        row["deviation"] = None
        return row
    row["deviation"] = actual_chapter - planned
    row["status"] = "ok"
    return row


def run_benchmark_rhythm_check(
    project: Path,
    from_chapter: int,
    to_chapter: int,
    state: dict[str, Any],
    volume: int | None = None,
) -> dict[str, Any]:
    """第④节确定性对照：定位卷纲 → 解析坐标表 → 锚点 grep 实际落点 → 偏差。

    候选性质：不改退出码、不写任何来自本节的 state；返回 rows/skipped/degraded 结构。
    """
    outline_path, skipped = locate_volume_outline(project, from_chapter, to_chapter, volume)
    if skipped is not None:
        return {"rows": [], "skipped": skipped, "degraded": []}
    text = _try_read_utf8(outline_path)
    rows = parse_benchmark_coordinates(text)
    if rows is None:
        return {"rows": [], "skipped": "skipped_no_coordinates", "degraded": []}
    resolved = [_resolve_anchor_row(project, from_chapter, to_chapter, state, row) for row in rows]
    degraded = [row for row in resolved if row["status"] != "ok"]
    return {"rows": resolved, "skipped": None, "degraded": degraded}


def _hit_desc(hit: dict[str, Any]) -> str:
    if hit["scope"] == "prose":
        return f"正文{hit['chapter']}章 {hit['file']}:{hit['line']}（{hit['text']}）"
    return f"事件库 {hit['event_id']} 第{hit['first_recorded_chapter']}章（{hit['field']}）"


def render_benchmark_rhythm_check(check: dict[str, Any]) -> list[str]:
    skip_reasons = {
        "skipped_ambiguous_outline": "卷纲定位失败：未找到唯一卷纲（零卷/多卷命中/范围未识别/显式卷缺失）",
        "skipped_no_coordinates": "卷纲无「### 对标结构坐标」节（老卷纲兼容路径，只多一行说明）",
    }
    lines = ["## 对标节奏对照（候选呈报）", ""]
    if check["skipped"]:
        lines.append(f"- 跳过：{skip_reasons.get(check['skipped'], check['skipped'])}")
    elif not check["rows"]:
        lines.append("- 卷纲坐标表为空，无对照项。")
    else:
        lines.extend(
            [
                "| 点位 | 对标章位 | 本卷计划章位 | 实际落点 | 偏差 | 状态 |",
                "|---|---|---|---|---|---|",
            ]
        )
        for row in check["rows"]:
            benchmark = row["benchmark_chapter"]
            planned = f"第{row['planned_chapter']}章" if row["planned_chapter"] is not None else "—"
            actual = f"第{row['actual_chapter']}章" if row["actual_chapter"] is not None else "—"
            deviation = f"{row['deviation']:+d}" if row["deviation"] is not None else "—"
            lines.append(
                f"| {row['point']} | {benchmark} | {planned} | {actual} | {deviation} | {row['status']} |"
            )
        lines.append("")
        for row in check["rows"]:
            if row["hits"]:
                lines.append(
                    f"- {row['point']}：命中 {len(row['hits'])} 处——"
                    + "；".join(_hit_desc(hit) for hit in row["hits"])
                )
    lines.append("")
    lines.append("- 说明：第④节为候选性质偏差呈报，不影响退出码、不写任何状态；判读归 AI 与作者。")
    lines.append("")
    return lines


def render_volume_report(
    *,
    from_chapter: int,
    to_chapter: int,
    state: dict[str, Any],
    settled: dict[str, list[dict[str, Any]]],
    suspended: list[dict[str, Any]],
    open_gaps: list[dict[str, Any]],
    benchmark_rhythm_check: dict[str, Any],
) -> str:
    """卷报告 Markdown：伏笔四态清账（卷内）+ 悬置预警 + 信息差未兑现 + 分层摘要。

    按需产物（非每章派生视图），不进入 check 的强校验集；全部列表按 id 排序保证确定性。
    """
    lines = [
        "# 卷报告",
        "",
        f"- 范围：第 {from_chapter}-{to_chapter} 章 | 截至章：第 {state['last_committed_chapter']} 章 | 状态修订：{state['state_revision']}",
        "",
        "## 摘要",
        f"- 伏笔清账（最近变动章在卷内）：已埋 {len(settled['已埋'])} / 已回收 {len(settled['已回收'])} / 已过期 {len(settled['已过期'])} / 放弃 {len(settled['放弃'])}",
        f"- 悬置预警（距最近变动章 ≥ {SUSPENSION_WARN_CHAPTERS}）：{len(suspended)} 条",
        f"- 信息差未兑现（status=登记）：{len(open_gaps)} 条",
        "",
    ]
    lines.extend(["## 伏笔清账", ""])
    for status in FORESHADOW_STATUSES:
        lines.append(f"### {status}")
        rows = settled[status]
        if not rows:
            lines.append("- 无")
        for row in rows:
            planned = f"第{row['planned_resolution_chapter']}章" if row["planned_resolution_chapter"] else "—"
            lines.append(
                f"- {row['id']}｜{row['summary']}｜埋第{row['planted_chapter']}章｜计划回收{planned}｜"
                f"最近变动第{row['updated_chapter']}章"
            )
        lines.append("")
    lines.extend(["## 悬置预警", ""])
    if not suspended:
        lines.append("- 无")
    for item in suspended:
        lines.append(f"- {item['id']}｜{item['status']}｜距最近变动 {item['chapters_since_update']} 章")
    lines.append("")
    lines.extend(["## 信息差未兑现", ""])
    if not open_gaps:
        lines.append("- 无")
    for row in open_gaps:
        knowers = "、".join(row["knowers"]) or "—"
        keywords = "、".join(row["keywords"]) or "—"
        lines.append(
            f"- {row['id']}｜知情人：{knowers}｜读者已知：{row['reader_known']}｜关键词：{keywords}｜"
            f"最近变更第{row['updated_chapter']}章｜{row['note']}"
        )
    lines.append("")
    lines.extend(render_benchmark_rhythm_check(benchmark_rhythm_check))
    return "\n".join(lines)


def volume_report(
    project: Path,
    from_chapter: int,
    to_chapter: int,
    json_out: Path | None,
    volume: int | None = None,
) -> dict[str, Any]:
    """卷报告子命令：只读 state，按调用方给的起止章出确定性账表。

    不猜卷界（state 无卷元数据）；不修改 state；产物不进 check 派生视图强校验集。
    """
    tracking = tracking_root(project)
    require_no_retired_tracking_paths(tracking)
    state = load_state(project)
    last = state["last_committed_chapter"]
    require(from_chapter >= 1 and from_chapter <= to_chapter, "volume range must satisfy 1 <= from <= to")
    require(to_chapter <= last, f"to_chapter {to_chapter} exceeds last committed chapter {last}")

    # ① 伏笔四态清账：按 updated_chapter 落 [from, to] 过滤
    settled: dict[str, list[dict[str, Any]]] = {status: [] for status in FORESHADOW_STATUSES}
    for identifier in sorted(state["foreshadow"]):
        row = state["foreshadow"][identifier]
        if from_chapter <= row["updated_chapter"] <= to_chapter:
            settled[row["status"]].append(
                {
                    "id": identifier,
                    "summary": row["summary"],
                    "planted_chapter": row["planted_chapter"],
                    "planned_resolution_chapter": row["planned_resolution_chapter"],
                    "status": row["status"],
                    "updated_chapter": row["updated_chapter"],
                }
            )

    # ② 悬置超阈值清单：复用 3b 的 suspension_warnings（全局视角）
    suspended = suspension_warnings(state, SUSPENSION_WARN_CHAPTERS)

    # ③ 信息差未兑现清单：status == "登记"（全局视角）
    open_gaps = [
        {
            "id": identifier,
            "knowers": row["knowers"],
            "reader_known": row["reader_known"],
            "keywords": row["keywords"],
            "status": row["status"],
            "updated_chapter": row["updated_chapter"],
            "note": row["note"],
        }
        for identifier, row in sorted(state["information_gaps"].items())
        if row["status"] == "登记"
    ]

    # ④ 对标节奏对照（候选呈报；只读，不改变退出码、不写状态）
    benchmark_rhythm_check = run_benchmark_rhythm_check(project, from_chapter, to_chapter, state, volume)

    report_payload = render_volume_report(
        from_chapter=from_chapter,
        to_chapter=to_chapter,
        state=state,
        settled=settled,
        suspended=suspended,
        open_gaps=open_gaps,
        benchmark_rhythm_check=benchmark_rhythm_check,
    )
    relative = f"卷报告_第{from_chapter}-{to_chapter}章.md"
    write_if_changed(tracking / relative, report_payload)

    summary = {
        "from_chapter": from_chapter,
        "to_chapter": to_chapter,
        "foreshadow_counts": {status: len(settled[status]) for status in FORESHADOW_STATUSES},
        "suspension_count": len(suspended),
        "open_gap_count": len(open_gaps),
    }
    if json_out is not None:
        atomic_write_text(
            json_out,
            json_payload(
                {
                    "range": {"from": from_chapter, "to": to_chapter},
                    "foreshadow_settled": settled,
                    "suspension_warnings": suspended,
                    "open_information_gaps": open_gaps,
                    "summary": summary,
                    "benchmark_rhythm_check": benchmark_rhythm_check,
                }
            ),
        )
    return {"report": relative, **summary}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "commit"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--project", type=Path, required=True, help="book project root containing 追踪/")
        subparser.add_argument("--input", type=Path, required=True, help="UTF-8 JSON input document")
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--project", type=Path, required=True, help="book project root containing 追踪/")
    check_parser.add_argument(
        "--warn-chapters",
        type=int,
        default=SUSPENSION_WARN_CHAPTERS,
        help="伏笔悬置预警阈值（默认 20）；仅呈报不改变退出码",
    )
    volume_parser = subparsers.add_parser("volume-report")
    volume_parser.add_argument("--project", type=Path, required=True, help="book project root containing 追踪/")
    volume_parser.add_argument("--from-chapter", type=int, required=True, help="卷起章（含）")
    volume_parser.add_argument("--to-chapter", type=int, required=True, help="卷止章（含）")
    volume_parser.add_argument(
        "--volume",
        type=int,
        default=None,
        help="可选：指定卷号以定位卷纲（缺省自动探测含该章节范围的唯一卷）",
    )
    volume_parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="可选：把结构化账表 JSON 写到该路径",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "init":
            result = initialize(args.project, read_json(args.input))
        elif args.command == "commit":
            result = apply_transaction(args.project, read_json(args.input))
        elif args.command == "volume-report":
            result = volume_report(args.project, args.from_chapter, args.to_chapter, args.json_out, args.volume)
        else:
            require(args.warn_chapters >= 1, "--warn-chapters must be >= 1")
            result = check_project(args.project)
    except (TrackingError, OSError, UnicodeError) as exc:
        emit(f"ERROR: {exc}", error=True)
        return 2
    if args.command == "volume-report":
        emit(json.dumps(result, ensure_ascii=False))
        return 0
    payload: dict[str, Any] = {
        "last_committed_chapter": result["last_committed_chapter"],
        "state_revision": result["state_revision"],
    }
    if args.command == "check":
        # 候选清单：只呈报，不改变退出码。
        payload["suspension_warnings"] = suspension_warnings(result, args.warn_chapters)
    emit(
        json.dumps(
            payload,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

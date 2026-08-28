#!/usr/bin/env python3
"""review_tickets.py — 审查工单确定性管理（write / resolve / list / verify-token）。

工单文件：{项目根}/.moshu-review/tickets/tickets_{YYYYMMDD-HHMM}_{起章}-{止章}.json
- write：校验 schema（版本/枚举/id 唯一且 T\\d{3,}/令牌非空）→ 规范化排序（id 升序）→
  原子写（临时文件 + rename）。AI 产出只走 --input 文件，不走 argv（移植 v7）。
- resolve：只允许 open→fixed/dismissed 单向流转；status_history 不引入，note 覆盖式。
- list：跨工单汇总输出 JSON（可按 --status 过滤）。
- verify-token：报告首行令牌比对（供主会话在采纳报告前调用；不等 → 退出 2）。

severity 只影响呈报与复审范围，不拦截任何流程——处置决定权在作者（总纲原则 2）。
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
TICKET_ID = re.compile(r"^T\d{3,}$")
SEVERITIES = ("blocking", "candidate")
STATUSES = ("open", "fixed", "dismissed")
RESOLVE_STATUSES = ("fixed", "dismissed")
# 受控枚举 9 类 = 统一 Findings Schema 的 category（review-workflow.md「统一 Findings Schema」）
DIMENSIONS = (
    "structure", "character", "prose", "consistency", "platform",
    "factual", "format", "causal", "rule_boundary",
)


class TicketError(ValueError):
    """Expected validation or ticket-state error."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TicketError(message)


def emit(text: str, *, error: bool = False) -> None:
    """Write UTF-8 bytes directly（Windows 文本 stdout 中文安全）。"""
    stream = sys.stderr if error else sys.stdout
    stream.flush()
    stream.buffer.write((text + "\n").encode("utf-8"))
    stream.buffer.flush()


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TicketError(f"unable to read JSON {path}: {exc}") from exc


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


def require_known_keys(mapping: dict[str, Any], allowed: set[str], label: str) -> None:
    unknown = set(mapping) - allowed
    require(not unknown, f"{label} contains unsupported fields: {', '.join(sorted(unknown))}")


def clean_text(value: object, label: str, *, allow_empty: bool = False, max_bytes: int = 1200) -> str:
    require(isinstance(value, str), f"{label} must be a string")
    cleaned = " ".join(value.split())
    require(allow_empty or bool(cleaned), f"{label} must not be empty")
    require(len(cleaned.encode("utf-8")) <= max_bytes, f"{label} exceeds {max_bytes} bytes")
    return cleaned


def clean_string_list(
    value: object, label: str, *, maximum: int = 20, item_max_bytes: int = 360
) -> list[str]:
    """B60 新增：字符串列表槽位校验（数量上限 + 单项字节上限），供 preserve 等可选键复用。"""
    require(isinstance(value, list), f"{label} must be a list")
    cleaned: list[str] = []
    for index, item in enumerate(value):
        cleaned.append(clean_text(item, f"{label}[{index}]", max_bytes=item_max_bytes))
    require(
        len(cleaned) <= maximum,
        f"{label} must contain at most {maximum} items, got {len(cleaned)}",
    )
    return cleaned


def tickets_dir(project: Path) -> Path:
    return project.resolve() / ".moshu-review" / "tickets"


def normalize_finding(value: object, index: int) -> dict[str, Any]:
    finding = value
    require(isinstance(finding, dict), f"findings[{index}] must be an object")
    require_known_keys(
        finding,
        {
            "id", "severity", "dimension", "evidence", "suggestion", "status", "status_note",
            # B60 可选键：problem 结构化问题陈述 / preserve 保留清单 / length_coefficient 字数系数
            "problem", "preserve", "length_coefficient",
        },
        f"findings[{index}]",
    )
    identifier = clean_text(finding.get("id"), f"findings[{index}].id", max_bytes=24)
    require(TICKET_ID.fullmatch(identifier) is not None, f"findings[{index}].id must look like T001")
    severity = clean_text(finding.get("severity"), f"findings[{index}].severity", max_bytes=24)
    require(severity in SEVERITIES, f"findings[{index}].severity must be one of {SEVERITIES}")
    dimension = clean_text(finding.get("dimension"), f"findings[{index}].dimension", max_bytes=32)
    require(dimension in DIMENSIONS, f"findings[{index}].dimension must be one of {DIMENSIONS}")
    status = clean_text(finding.get("status", "open"), f"findings[{index}].status", max_bytes=24)
    require(status in STATUSES, f"findings[{index}].status must be one of {STATUSES}")
    # write 只接受新建态：处置一律走 resolve（单向 open→fixed/dismissed），
    # 禁止用 write 直接落 fixed/dismissed 绕过处置证据（批6 禁止事项 4）。
    require(status == "open", f"findings[{index}].status must be open on write; use resolve to change status")

    # B60 可选键（全可选、旧工单兼容）：
    # problem = 结构化问题陈述 {现象, 位置, 为什么是问题} 三段各 ≤200B；
    # preserve = 作者保留清单（≤10 条、每条 ≤120B）——填写权只在作者与 [需复核] 转正，
    #            reviewer/deslop 不得自填（防「自我保留」架空整改）；
    # length_coefficient = 字数系数 float 0.5-2.0（默认 1.0=不约束）。
    problem: dict[str, Any] | None = None
    raw_problem = finding.get("problem")
    if raw_problem is not None:
        require(isinstance(raw_problem, dict), f"findings[{index}].problem must be an object")
        require_known_keys(raw_problem, {"现象", "位置", "为什么是问题"}, f"findings[{index}].problem")
        problem = {
            key: clean_text(raw_problem.get(key), f"findings[{index}].problem.{key}", max_bytes=200)
            for key in ("现象", "位置", "为什么是问题")
        }
    preserve: list[str] | None = None
    raw_preserve = finding.get("preserve")
    if raw_preserve is not None:
        preserve = clean_string_list(raw_preserve, f"findings[{index}].preserve", maximum=10, item_max_bytes=120)
    raw_coefficient = finding.get("length_coefficient")
    length_coefficient: float | None = None
    if raw_coefficient is not None:
        require(
            isinstance(raw_coefficient, (int, float)) and not isinstance(raw_coefficient, bool),
            f"findings[{index}].length_coefficient must be a number",
        )
        length_coefficient = float(raw_coefficient)
        require(
            0.5 <= length_coefficient <= 2.0,
            f"findings[{index}].length_coefficient must be within [0.5, 2.0]",
        )
    return {
        "id": identifier,
        "severity": severity,
        "dimension": dimension,
        "evidence": clean_text(finding.get("evidence"), f"findings[{index}].evidence", max_bytes=1200),
        "suggestion": clean_text(finding.get("suggestion"), f"findings[{index}].suggestion", max_bytes=1200),
        "status": status,
        "status_note": clean_text(
            finding.get("status_note", ""), f"findings[{index}].status_note", allow_empty=True, max_bytes=240
        ),
        **({"problem": problem} if problem is not None else {}),
        **({"preserve": preserve} if preserve is not None else {}),
        **({"length_coefficient": length_coefficient} if length_coefficient is not None else {}),
    }


def normalize_document(document: object) -> dict[str, Any]:
    root = document
    require(isinstance(root, dict), "input must be a JSON object")
    require_known_keys(
        root,
        {"schema_version", "chapter_range", "review_token", "findings", "decision_points"},
        "ticket document",
    )
    require(root.get("schema_version") == SCHEMA_VERSION, "ticket schema_version is unsupported")
    chapter_range = root.get("chapter_range")
    require(isinstance(chapter_range, list) and len(chapter_range) == 2, "chapter_range must be [start, end]")
    start, end = chapter_range
    require(
        isinstance(start, int) and isinstance(end, int) and not isinstance(start, bool) and not isinstance(end, bool),
        "chapter_range must contain integers",
    )
    require(start >= 1 and end >= start, "chapter_range must satisfy 1 <= start <= end")
    token = clean_text(root.get("review_token"), "review_token", max_bytes=64)
    require(len(token) == 8, "review_token must be exactly 8 characters")
    raw_findings = root.get("findings", [])
    require(isinstance(raw_findings, list), "findings must be an array")
    findings = [
        normalize_finding(item, index)
        for index, item in enumerate(raw_findings)
    ]
    require(
        len({item["id"] for item in findings}) == len(findings),
        "findings contain duplicate IDs",
    )
    findings.sort(key=lambda item: item["id"])
    # B60 decision_points（可选）：reviewer 间冲突意见的结构化标记，
    # a/b = findings 数组索引（0-based，越界拒绝）；question ≤240B。
    raw_decision_points = root.get("decision_points", [])
    require(isinstance(raw_decision_points, list), "decision_points must be an array")
    decision_points: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_decision_points):
        require(isinstance(raw, dict), f"decision_points[{index}] must be an object")
        require_known_keys(raw, {"a", "b", "question"}, f"decision_points[{index}]")
        a = raw.get("a")
        b = raw.get("b")
        for label, value in (("a", a), ("b", b)):
            require(
                isinstance(value, int) and not isinstance(value, bool) and 0 <= value < len(findings),
                f"decision_points[{index}].{label} must be a findings index within range",
            )
        question = clean_text(raw.get("question"), f"decision_points[{index}].question", max_bytes=240)
        decision_points.append({"a": a, "b": b, "question": question})
    return {
        "schema_version": SCHEMA_VERSION,
        "chapter_range": [start, end],
        "review_token": token,
        "findings": findings,
        "decision_points": decision_points,
    }


def write_command(project: Path, input_path: Path) -> Path:
    document = read_json(input_path)
    normalized = normalize_document(document)
    tickets = tickets_dir(project)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    start, end = normalized["chapter_range"]
    target = tickets / f"tickets_{stamp}_{start}-{end}.json"
    if target.exists():
        existing = read_json(target)
        require(
            existing == normalized,
            f"ticket file {target.name} already exists with different content",
        )
        emit(f"NOTE: ticket file already exists with identical content: {target.name}")
        return target
    # CI 修正（2026-08-28 runtime-regressions 偶发红）：幂等按内容匹配扩到跨分钟戳——
    # 同一工单二次提交跨分钟边界时目标文件名不同，旧逻辑会新建重复工单（测试跨分界偶发 + 真实重复风险）
    for existing_file in sorted(tickets.glob(f"tickets_*_{start}-{end}.json")):
        try:
            if read_json(existing_file) == normalized:
                emit(f"NOTE: ticket file already exists with identical content: {existing_file.name}")
                return existing_file
        except TicketError:
            continue
    atomic_write_text(target, json_payload(normalized))
    emit(f"ticket written: {target.name}")
    return target


def resolve_command(project: Path, ticket_path: Path, identifier: str, status: str, note: str) -> Path:
    path = ticket_path.resolve()
    # 审计-V3 RC1：--project 必须有归属约束（此前是装饰参数，可用无关目录处置真实工单）
    require(
        path.is_relative_to(tickets_dir(project).resolve()),
        f"ticket {path.name} is not under project tickets dir {tickets_dir(project)}",
    )
    document = read_json(path)
    root = document
    require(isinstance(root, dict) and isinstance(root.get("findings"), list), "ticket file is malformed")
    findings = root["findings"]
    matches = [item for item in findings if item.get("id") == identifier]
    require(len(matches) == 1, f"ticket {identifier} not found in {path.name}")
    finding = matches[0]
    require(
        finding.get("status") == "open",
        f"ticket {identifier} is already {finding.get('status')}; only open tickets can be resolved",
    )
    require(status in RESOLVE_STATUSES, f"status must be one of {RESOLVE_STATUSES}")
    # B60 编辑决策点：该 finding 被 decision_points 引用时，resolution 必须引用作者裁决
    # （status_note 含「作者裁决：」前缀）——分歧不自动妥协，裁决权在作者。
    if isinstance(root.get("decision_points"), list):
        in_conflict = any(
            isinstance(dp, dict) and isinstance(dp.get("a"), int) and isinstance(dp.get("b"), int)
            and findings[dp["a"]].get("id") == identifier
            for dp in root["decision_points"]
            if isinstance(dp.get("a"), int) and dp["a"] < len(findings) and dp["b"] < len(findings)
        )
        if in_conflict:
            require(
                note.startswith("作者裁决："),
                f"finding {identifier} is a decision point (编辑决策点); status_note must cite the author's ruling with prefix 作者裁决：",
            )
    finding["status"] = status
    finding["status_note"] = clean_text(note, "note", max_bytes=240)
    findings.sort(key=lambda item: item["id"])
    atomic_write_text(path, json_payload(root))
    emit(f"resolved {identifier} -> {status}")
    return path


def list_command(project: Path, status_filter: str | None) -> list[dict[str, Any]]:
    tickets = tickets_dir(project)
    result: list[dict[str, Any]] = []
    if not tickets.exists():
        return result
    for path in sorted(tickets.glob("tickets_*.json")):
        document = read_json(path)
        root = document
        if not isinstance(root, dict):
            continue
        findings = root.get("findings", [])
        if status_filter is not None:
            findings = [item for item in findings if item.get("status") == status_filter]
        result.append(
            {
                "file": path.name,
                "chapter_range": root.get("chapter_range"),
                "findings": findings,
                # B60 编辑决策点：list 输出单列，供呈报作者裁决
                "decision_points": root.get("decision_points", []),
            }
        )
    return result


def verify_token_command(ticket_path: Path, token: str) -> int:
    document = read_json(ticket_path.resolve())
    root = document
    if isinstance(root, dict) and root.get("review_token") == token:
        emit("token ok")
        return 0
    emit("ERROR: token mismatch", error=True)
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    write_parser = subparsers.add_parser("write")
    write_parser.add_argument("--project", type=Path, required=True, help="book project root")
    write_parser.add_argument("--input", type=Path, required=True, help="UTF-8 JSON findings document")

    resolve_parser = subparsers.add_parser("resolve")
    resolve_parser.add_argument("--project", type=Path, required=True, help="book project root")
    resolve_parser.add_argument("--ticket", type=Path, required=True, help="ticket file path")
    resolve_parser.add_argument("--id", required=True, help="finding id like T001")
    resolve_parser.add_argument("--status", required=True, choices=RESOLVE_STATUSES)
    resolve_parser.add_argument("--note", required=True, help="one-sentence disposition evidence")

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--project", type=Path, required=True, help="book project root")
    list_parser.add_argument("--status", choices=STATUSES, default=None, help="filter by status")

    verify_parser = subparsers.add_parser("verify-token")
    verify_parser.add_argument("--ticket", type=Path, required=True, help="ticket file path")
    verify_parser.add_argument("--token", required=True, help="token string to compare")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "write":
            write_command(args.project, args.input)
        elif args.command == "resolve":
            resolve_command(args.project, args.ticket, args.id, args.status, args.note)
        elif args.command == "list":
            result = list_command(args.project, args.status)
            emit(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            return verify_token_command(args.ticket, args.token)
    except (TicketError, OSError, UnicodeError) as exc:
        emit(f"ERROR: {exc}", error=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

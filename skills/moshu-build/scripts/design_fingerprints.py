#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""设定指纹与影响面（moshu-build 修订流 ③b 工具，B61）

三子命令：record（建基线）/ diff（指纹对比+受影响章反查）/ update（=record，裁决闭环后刷新）。

- 指纹域：`设定/**/*.md` + `大纲/大纲.md` + `大纲/卷纲_*.md`（**细纲排除**——细纲改动属规划层，
  由补纲流程自管；不扩范围到正文文件）。
- 指纹载体：书根 `.design-hashes.json`（dotfile，不在任何现有工具扫描名单）。
- registry 缺失 → 任何子命令先自动 record 建基线（幂等：同内容重复 record 哈希不变），
  并在 diff 输出标 `baseline_created: true`。
- 读失败三分类（反模式 #7）：registry 缺失→自动建档；设定目录缺失→输出
  `{error: "设定目录不存在"}` 退出码 1；单文件读失败→该文件 status=unreadable 不中断。
- 退出码语义：diff/record/update 恒 0（**呈报工具不是守卫**，候选永不拦截同源逻辑）；
  仅设定目录缺失为 1。
- 受影响章反查：遍历 `大纲/细纲_第N章*.md` 的「本章涉及设定」字段行，按**文件名 stem 与
  路径后缀双匹配**（字段写法可能是「角色/甲.md」或「甲」——匹配口径 mo-shu 自定，
  禁模糊/语义匹配）；文件未出现在任何细纲 → chapters 空数组（明示「无已写章引用」）。
- 边界（宪法）：不写 `追踪/` 任何文件（追踪域归 write）；不自动建 review 工单（发起权在作者）。

用法：
  python design_fingerprints.py record --project {书根}
  python design_fingerprints.py diff  --project {书根}
  python design_fingerprints.py update --project {书根}
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

REGISTRY_NAME = ".design-hashes.json"
SETTING_DIR = "设定"
OUTLINE_DIR = "大纲"
DETAIL_FIELD_RE = re.compile(r"本章涉及设定[：:]\s*([^\n]+)")
DETAIL_FILE_RE = re.compile(r"^细纲_第0*(\d+)章")


def nonempty_md_files(root: Path) -> list[Path]:
    """指纹域文件清单：设定/**/*.md + 大纲/大纲.md + 大纲/卷纲_*.md（细纲排除）。"""
    files: list[Path] = []
    setting_dir = root / SETTING_DIR
    if setting_dir.is_dir():
        files.extend(sorted(p for p in setting_dir.rglob("*.md") if p.is_file()))
    outline_dir = root / OUTLINE_DIR
    if outline_dir.is_dir():
        main = outline_dir / "大纲.md"
        if main.is_file():
            files.append(main)
        files.extend(sorted(outline_dir.glob("卷纲_*.md")))
    return files


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_registry(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def compute_hashes(root: Path) -> tuple[dict[str, dict[str, str]], bool]:
    """返回 ({相对路径: {sha256, status}}, 设定目录是否存在)。"""
    hashes: dict[str, dict[str, str]] = {}
    setting_dir = root / SETTING_DIR
    if not setting_dir.is_dir():
        return hashes, False
    for p in nonempty_md_files(root):
        rel = p.relative_to(root).as_posix()
        try:
            hashes[rel] = {"sha256": sha256_of(p.read_bytes()), "status": "ok"}
        except OSError:
            # 单文件读失败：标 unreadable 不中断（读失败三分类之三）
            hashes[rel] = {"sha256": "", "status": "unreadable"}
    return hashes, True


def write_registry(path: Path, hashes: dict[str, dict[str, str]]) -> None:
    payload = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "files": hashes,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def do_record(root: Path) -> int:
    hashes, setting_exists = compute_hashes(root)
    if not setting_exists:
        print(json.dumps({"error": "设定目录不存在"}, ensure_ascii=False))
        return 1
    write_registry(root / REGISTRY_NAME, hashes)
    print(json.dumps({"recorded": len(hashes), "registry": REGISTRY_NAME}, ensure_ascii=False))
    return 0


def collect_detail_settings(root: Path) -> dict[int, list[str]]:
    """遍历细纲，返回 {章号: [「本章涉及设定」字段原文]}。"""
    result: dict[int, list[str]] = {}
    outline_dir = root / OUTLINE_DIR
    if not outline_dir.is_dir():
        return result
    for p in sorted(outline_dir.glob("细纲_*.md")):
        m = DETAIL_FILE_RE.match(p.name)
        if not m:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        fm = DETAIL_FIELD_RE.search(text)
        if fm:
            result[int(m.group(1))] = [fm.group(1).strip()]
    return result


def affected_chapters(rel_path: str, details: dict[int, list[str]]) -> list[int]:
    """反查：细纲「本章涉及设定」字段含该文件（stem 或路径后缀双匹配，mo-shu 自定）→ 章号列表。"""
    p = Path(rel_path)
    stem = p.stem
    suffix_form = "/".join(p.parts[1:]) if len(p.parts) > 1 else p.name  # 如 角色/甲.md
    hits: list[int] = []
    for chapter, fields in sorted(details.items()):
        for field in fields:
            if stem in field or (len(p.parts) > 1 and suffix_form in field) or p.name in field:
                hits.append(chapter)
                break
    return hits


def do_diff(root: Path) -> int:
    hashes, setting_exists = compute_hashes(root)
    if not setting_exists:
        print(json.dumps({"error": "设定目录不存在"}, ensure_ascii=False))
        return 1
    registry_path = root / REGISTRY_NAME
    registry = load_registry(registry_path)
    baseline_created = registry is None
    if baseline_created:
        write_registry(registry_path, hashes)
        registry = {"files": hashes}
    old_files = registry.get("files", {})

    details = collect_detail_settings(root)
    changed: list[dict] = []
    unchanged_count = 0
    all_paths = set(hashes) | set(old_files)
    for rel in sorted(all_paths):
        new = hashes.get(rel)
        old = old_files.get(rel)
        new_hash = new["sha256"] if new else None
        old_hash = old["sha256"] if old else None
        if new is None:
            status = "missing"
        elif old is None or new_hash != old_hash:
            status = "changed"
        else:
            unchanged_count += 1
            continue
        if new and new.get("status") == "unreadable":
            status = "unreadable"
        chapters = affected_chapters(rel, details)
        changed.append({"file": rel, "status": status, "chapters": chapters})
    payload = {
        "changed": changed,
        "unchanged_count": unchanged_count,
        "baseline_created": baseline_created,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="设定指纹与影响面（B61，呈报工具非守卫）")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("record", "diff", "update"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--project", type=Path, required=True, help="书项目根目录")
    args = parser.parse_args()
    root = args.project
    if not root.is_dir():
        print(json.dumps({"error": f"项目目录不存在: {root}"}, ensure_ascii=False))
        return 1
    if args.command == "diff":
        return do_diff(root)
    return do_record(root)  # update 语义=record（幂等刷新基线）


if __name__ == "__main__":
    sys.exit(main())

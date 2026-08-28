#!/usr/bin/env python3
"""pace_meter.py — 推进度仪表（B68b，呈报工具，候选永不拦截）

卷进度 vs 剧情进度 背离预警 + 细纲编号连续性核对。三源递降取计划信号：
  主源 = 卷纲剧情单元卡「章节范围」结构化行（计划章数=各单元范围并集之最大章号）；
  次源 = 大纲/大纲.md 当前卷行「N 章」（正则，mo-shu 自定口径，格式漂移时降级明示）；
  CLI  = --planned-chapters / --total-units 显式覆盖（优先级最高）。
三源全缺 → status=skipped_no_plan 明示跳过（反模式 #7：不瞎算）。
恒退出码 0（候选类工具）；仅 --project 非目录为 1（致命）。
输出：stdout 人类摘要 + JSON（--json 只出 JSON）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# mo-shu 自定阈值（非外部移植）：背离判定双条件，CLI --ratio/--pp 可覆盖，验收可测
PACE_DIVERGENCE_RATIO = 2.0
PACE_DIVERGENCE_PP = 50

OUTLINE_DIR = "大纲"
PROSE_DIR = "正文"
STATE_REL = Path("追踪") / "_tracking-state.json"

UNIT_HEADING_RE = re.compile(r"^(#+)\s*(.+)$")
UNIT_CARD_TITLE_RE = re.compile(r"^剧情单元(\s|$)")
UNIT_ID_LINE_RE = re.compile(r"^\s*-\s*单元ID\s*[：:]\s*(.*)$")
# mo-shu 自定口径，格式源头=workflow-build 卷纲产物行格式样例（B68b 整改钉源）：
# 「单元 U{NN}｜章节范围：第{N}-{M} 章｜…」——章节范围须「第…章」包裹；不锚行首，
# 兼容「- 章节范围：第A-B章」字段行与「｜」分隔行两种形态。
UNIT_RANGE_LINE_RE = re.compile(
    r"章节范围\s*[：:].*?第\s*(\d+)\s*(?:[-–—~至]\s*(\d+)\s*)?章")
XIBNV_ID_RE = re.compile(r"^\s*-\s*单元ID/位置\s*[：:]\s*(.*)$")
XIBNV_TOKEN_RE = re.compile(r"^([A-Za-z]+\d+-\d+|\d+-\d+)")
VOLUME_FILE_RE = re.compile(r"^卷纲_第(\d+)卷\.md$")
DETAIL_FILE_RE = re.compile(r"^细纲_第(\d+)章")
PROSE_FILE_RE = re.compile(r"^第(\d+)章")
SCENE_SUM_RE = re.compile(r"单元预估章数合计\s*[：:]\s*([0-9]+(?:\.[0-9]+)?)")
CN_DIGITS = "零一二三四五六七八九"


def int_to_cn(n: int):
    """卷号阿拉伯数字 → 中文小写（大纲.md 卷行匹配用）；超范围返回 None。"""
    if n <= 0 or n > 9999:
        return None
    if n < 10:
        return CN_DIGITS[n]
    if n < 20:
        return "十" + (CN_DIGITS[n % 10] if n % 10 else "")
    if n < 100:
        return CN_DIGITS[n // 10] + "十" + (CN_DIGITS[n % 10] if n % 10 else "")
    if n < 1000:
        head = CN_DIGITS[n // 100] + "百"
        rest = n % 100
        if rest == 0:
            return head
        if rest < 10:
            return head + "零" + CN_DIGITS[rest]
        return head + int_to_cn(rest)
    head = CN_DIGITS[n // 1000] + "千"
    rest = n % 1000
    if rest == 0:
        return head
    if rest < 100:
        return head + "零" + int_to_cn(rest)
    return head + int_to_cn(rest)


CN_VALUES = {c: i for i, c in enumerate(CN_DIGITS)}


def cn_to_int(s: str):
    """中文小写卷号 → 阿拉伯数字（无卷纲文件时从大纲.md 末卷行回推当前卷；解析失败返回 None）。"""
    s = s.strip()
    if not s:
        return None
    if s.isdigit():
        v = int(s)
        return v if 0 < v <= 9999 else None
    total = 0
    num = 0
    for ch in s:
        if ch == "千":
            if num == 0:
                num = 1
            total += num * 1000
            num = 0
        elif ch == "百":
            if num == 0:
                num = 1
            total += num * 100
            num = 0
        elif ch == "十":
            if num == 0:
                num = 1
            total += num * 10
            num = 0
        elif ch in CN_VALUES:
            num = CN_VALUES[ch]
        elif ch == "零":
            continue
        else:
            return None
    result = total + num
    return result if 0 < result <= 9999 else None


OUTLINE_VOL_ROW_RE = re.compile(r"^#{1,6}\s*第([0-9一二三四五六七八九十百千零]+)卷[：:（(]")


def parse_outline_planned(text: str, vol_no: int):
    """次源：大纲.md 卷行「### 第{中文}卷：…（约 X 万字，N 章）」取 N（mo-shu 自定正则口径）。

    返回 (卷号或 None, 计划章数或 None)：优先命中 vol_no 对应卷行；无卷纲文件（vol_no 为空）
    或未命中时回退**最后一行**卷行（顺序卷行≈推进中卷，mo-shu 自定口径，注释明示）。
    """
    rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        vm = OUTLINE_VOL_ROW_RE.match(stripped)
        if not vm:
            continue
        m = re.search(r"(\d+)\s*章", stripped)
        if not m:
            continue
        rows.append((cn_to_int(vm.group(1)), int(m.group(1))))
    if not rows:
        return None, None
    if vol_no:
        for row_vol, chapters in rows:
            if row_vol == vol_no:
                return vol_no, chapters
    row_vol, chapters = rows[-1]
    return row_vol, chapters


def parse_scene_total(text: str):
    """场景表「单元预估章数合计」：先认内联 `key：N`，再认表头表格行（列名定位取数据行同列值）。"""
    m = SCENE_SUM_RE.search(text)
    if m:
        return float(m.group(1))
    lines = text.splitlines()
    col = None
    for i, line in enumerate(lines):
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if "单元预估章数合计" in cells:
            col = cells.index("单元预估章数合计")
            for data in lines[i + 1:]:
                if "|" not in data:
                    continue
                dcells = [c.strip() for c in data.strip().strip("|").split("|")]
                if dcells and all(set(c) <= set("-: ") for c in dcells if c):
                    continue  # 分隔行
                if len(dcells) > col:
                    try:
                        return float(dcells[col])
                    except ValueError:
                        return None
            break
    return None


def read_text(path: Path, errors: list, label: str):
    """读文件三分类（反模式 #7）：缺→None 静默（由调用方按语义记账）、空→note、坏→error。"""
    if not path.is_file():
        return None
    try:
        raw = path.read_bytes()
    except OSError as exc:
        errors.append(f"{label} 读失败：{exc}")
        return None
    if not raw.strip():
        errors.append(f"{label} 为空文件：{path.name}")
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        errors.append(f"{label} 内容坏（非 UTF-8）：{path.name}")
        return None


def parse_unit_cards(text: str):
    """解析卷纲剧情单元卡：标题行「### 剧情单元 X」起、下一标题止；取 单元ID/章节范围。

    注意「剧情单元卡（…）」节标题不是单元卡（剧情单元后跟"卡"字不匹配）。
    """
    cards = []
    current = None
    for line in text.splitlines():
        hm = UNIT_HEADING_RE.match(line)
        if hm:
            title = hm.group(2).strip()
            if UNIT_CARD_TITLE_RE.match(title):
                current = {"id": None, "range": None}
                cards.append(current)
            else:
                current = None
            continue
        if current is None:
            continue
        if current["id"] is None:
            im = UNIT_ID_LINE_RE.match(line)
            if im:
                current["id"] = im.group(1).strip()
                continue
        if current["range"] is None:
            rm = UNIT_RANGE_LINE_RE.search(line)
            if rm:
                a = int(rm.group(1))
                b = int(rm.group(2)) if rm.group(2) else a
                current["range"] = (a, b)
    return cards


def numeric_chapter_gap(nums: list):
    """数值章号排序（禁文件名字典序——'1000'<'999' 陷阱）后给 [min,max] 内缺号。"""
    uniq = sorted(set(nums))
    if not uniq:
        return {"min": None, "max": None, "缺号列表": []}
    present = set(uniq)
    missing = [n for n in range(uniq[0], uniq[-1] + 1) if n not in present]
    return {"min": uniq[0], "max": uniq[-1], "缺号列表": missing}


def collect_xibnv_unit_ids(text: str):
    """细纲「单元ID/位置」行归属提取（与卷纲主源互验用）。"""
    ids = []
    for line in text.splitlines():
        m = XIBNV_ID_RE.match(line)
        if m:
            t = XIBNV_TOKEN_RE.match(m.group(1).strip())
            if t:
                ids.append(t.group(1))
    return ids


def main(argv=None):
    ap = argparse.ArgumentParser(description="推进度仪表：卷进度 vs 剧情进度 背离预警（呈报工具，恒退出码 0）")
    ap.add_argument("--project", required=True, help="书根目录")
    ap.add_argument("--planned-chapters", type=int, default=None, help="覆盖计划章数（第三源，优先级最高）")
    ap.add_argument("--total-units", type=int, default=None, help="覆盖单元总数（第三源，优先级最高）")
    ap.add_argument("--ratio", type=float, default=PACE_DIVERGENCE_RATIO, help="背离比值阈值（mo-shu 自定）")
    ap.add_argument("--pp", type=float, default=PACE_DIVERGENCE_PP, help="背离百分点差阈值（mo-shu 自定）")
    ap.add_argument("--json", action="store_true", help="只输出 JSON（默认附人类摘要）")
    args = ap.parse_args(argv)

    project = Path(args.project)
    if not project.is_dir():
        print(f"ERROR: 项目目录不存在：{project}", file=sys.stderr)
        return 1

    errors = []
    notes = []

    # ── 计划信号三源递降 ──────────────────────────────────────────
    vol_no = None
    volume_files = []
    outline_dir = project / OUTLINE_DIR
    if outline_dir.is_dir():
        for p in outline_dir.glob("卷纲_第*卷.md"):
            m = VOLUME_FILE_RE.match(p.name)
            if m:
                volume_files.append((int(m.group(1)), p))
    if volume_files:
        vol_no, vol_path = max(volume_files, key=lambda t: t[0])
        vol_text = read_text(vol_path, errors, "卷纲")
        unit_cards = parse_unit_cards(vol_text) if vol_text else []
    else:
        vol_text = None
        unit_cards = []
        if outline_dir.is_dir():
            notes.append("缺当前卷卷纲文件（卷纲_第N卷.md）——主源缺")

    planned = None
    total_units = None
    plan_source = "无"
    ranges = [c["range"] for c in unit_cards if c["range"]]
    if ranges:
        planned = max(b for _, b in ranges)
        total_units = len(unit_cards)
        plan_source = "卷纲单元卡（主源）"
    elif vol_text is not None and not unit_cards:
        notes.append("卷纲无剧情单元卡——主源缺，尝试次源")

    outline_text = read_text(project / OUTLINE_DIR / "大纲.md", errors, "大纲.md")
    if planned is None and outline_text:
        found_vol, found_planned = parse_outline_planned(outline_text, vol_no)
        if found_planned is not None:
            planned = found_planned
            plan_source = "大纲.md 卷行（次源）"
            if vol_no is None and found_vol:
                vol_no = found_vol
                notes.append(f"无卷纲文件——按大纲.md 末卷行回推当前卷为第{found_vol}卷")
        else:
            notes.append("大纲.md 未命中任何卷行章数——次源缺")
    elif outline_text is None:
        notes.append("缺 大纲/大纲.md——次源缺")

    if args.planned_chapters is not None or args.total_units is not None:
        if args.planned_chapters is not None:
            planned = args.planned_chapters
        if args.total_units is not None:
            total_units = args.total_units
        plan_source = "CLI 显式覆盖（第三源）"

    # ── 已写进度：正文文件数 vs state last_committed_chapter 取大 ──
    prose_count = 0
    prose_dir = project / PROSE_DIR
    if prose_dir.is_dir():
        prose_count = sum(1 for p in prose_dir.glob("第*章*.md") if PROSE_FILE_RE.match(p.name))
    state_last = 0
    state_path = project / STATE_REL
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state_last = int(state.get("last_committed_chapter") or 0)
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f"追踪 state 读失败/坏：{exc}")
    else:
        notes.append("缺 追踪/_tracking-state.json——已写章数只按正文文件数")
    written = max(prose_count, state_last)

    # ── 细纲编号连续性 + 单元ID 互验 ─────────────────────────────
    detail_nums = []
    xibnv_ids = []
    if outline_dir.is_dir():
        for p in outline_dir.glob("细纲_第*章*.md"):
            m = DETAIL_FILE_RE.match(p.name)
            if not m:
                continue
            detail_nums.append(int(m.group(1)))
            text = read_text(p, errors, "细纲")
            if text:
                xibnv_ids.extend(collect_xibnv_unit_ids(text))
    continuity = numeric_chapter_gap(detail_nums)
    if unit_cards:
        known = {c["id"] for c in unit_cards if c["id"]}
        if known:
            stray = sorted({i for i in xibnv_ids if i not in known})
            if stray:
                errors.append("细纲引用单元ID 不在卷纲单元卡：" + "、".join(stray))

    # ── 场景表预估合计（B68a 产物；缺则 null，合法） ─────────────
    scene_total = None
    scene_vals = []
    if outline_dir.is_dir():
        for p in outline_dir.glob("场景表_*.md"):
            text = read_text(p, errors, "场景表")
            if text:
                value = parse_scene_total(text)
                if value is not None:
                    scene_vals.append(value)
    if scene_vals:
        scene_total = round(sum(scene_vals), 1)

    # ── 进度与背离判定 ────────────────────────────────────────────
    consumed = None
    if ranges:
        consumed = sum(1 for a, _ in ranges if a <= written)

    vol_pct = round(written / planned * 100, 1) if planned else None
    plot_pct = round(consumed / total_units * 100, 1) if total_units else None

    candidates = []
    if planned and total_units and vol_pct is not None and plot_pct is not None:
        ratio_hit = vol_pct > 0 and (plot_pct / vol_pct) > args.ratio
        pp_hit = abs(plot_pct - vol_pct) > args.pp
        if ratio_hit or pp_hit:
            if consumed and consumed > 0:
                est = round(written + (total_units - consumed) * (written / consumed))
                msg = (f"按当前消耗速度预计约 {est} 章收卷 vs 计划 {planned} 章"
                       "——检查是否加垫单元/扩支线/压推进节奏（裁决归作者）")
            else:
                msg = (f"预计收卷章数无法估算（已消耗单元为 0）vs 计划 {planned} 章"
                       "——检查是否加垫单元/扩支线/压推进节奏（裁决归作者）")
            candidates.append(msg)

    status = "ok"
    if planned is None:
        status = "skipped_no_plan"
        notes.append("计划章数三源全缺（无卷纲单元卡/大纲.md 卷行/CLI 覆盖）——skipped_no_plan，不计算进度")

    result = {
        "status": status,
        "卷号": vol_no,
        "plan_source": plan_source,
        "计划章数": planned,
        "已写章数": written,
        "卷进度%": vol_pct,
        "单元总数": total_units,
        "已消耗单元数": consumed,
        "剧情进度%": plot_pct,
        "场景表预估合计": scene_total,
        "细纲编号连续性": {"缺号列表": continuity["缺号列表"]},
        "背离候选": candidates,
        "细纲文件数": len(detail_nums),
        "notes": notes,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"推进度仪表（B68b，呈报工具——候选永不拦截）")
    print(f"  计划来源：{plan_source}｜当前卷：第{vol_no}卷" if vol_no else f"  计划来源：{plan_source}｜当前卷：无")
    if planned:
        print(f"  卷进度：{written}/{planned} 章（{vol_pct}%）｜剧情进度：{consumed}/{total_units} 单元（{plot_pct}%）"
              + (f"｜场景表预估合计 {scene_total}" if scene_total is not None else ""))
    else:
        print("  计划章数三源全缺——skipped_no_plan（明示跳过，不瞎算）")
    if continuity["缺号列表"]:
        print(f"  细纲缺号（数值序 {continuity['min']}-{continuity['max']}）：{continuity['缺号列表']}")
    for c in candidates:
        print(f"  ⚠️ 背离候选：{c}")
    for e in errors:
        print(f"  ERROR：{e}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

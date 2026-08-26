#!/usr/bin/env python3
"""check_outline.py — 大纲确定性机检（blocking + candidate 两列，候选永不拦截）

守护对象：B16 骨架六要素结构（每卷骨架表八列 / 对手梯队与势力场 / 常驻压力 / 终局底牌 / 升级台阶）的确定性校验。
禁：LLM/联网（反模式 #8）；候选影响退出码（宪法 §2.7）；解析失败升级 blocking（宁可漏拦不可误伤）。
纪律：断言跟 B16 模板走——模板变更须同批同步（清单类断言最易过期，本批纪律写进此头注）。
版本兼容（B18 自审补丁）：检测到旧结构（无八列表头或缺新节）时，新节相关 blocking 断言整体降级为
一条 candidate「大纲为 B16 前旧结构，建议升级」——不对存量旧项目误伤；八列表头齐全才启用全套 blocking。
退出码：0=通过（含仅 candidate）；1=blocking 违规；2=参数/读文件错误（读失败三分类：缺/空/坏）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HEADER_KEYWORDS = ["卷", "一句话", "对手", "赌注", "中点", "高潮", "跃迁", "字数"]
REQUIRED_SECTIONS = ["每卷骨架表", "全书体量与阶段总览", "终局底牌", "升级台阶", "对手梯队与势力场", "常驻压力"]
OLD_STRUCTURE_CANDIDATE = "大纲为 B16 前旧结构，建议升级（补势力场/常驻压力/六要素列）"
SECTION_RE = re.compile(r"^#{1,4}\s+(.+?)\s*$")


class OutlineError(Exception):
    pass


def read_text(path: Path) -> str:
    if not path.exists():
        raise OutlineError(f"文件不存在：{path}")
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        raise OutlineError(f"读取失败（内容坏）：{path}——{exc}") from exc
    if not text.strip():
        raise OutlineError(f"读取失败（空文件）：{path}")
    return text


def section_text(text: str, title: str) -> str | None:
    """按标题取节内容（到下一个同/更高级标题止）。标题含关键词即可。"""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        m = SECTION_RE.match(line)
        if m and title in m.group(1):
            start = i
            break
    if start is None:
        return None
    body: list[str] = []
    for line in lines[start + 1:]:
        m = SECTION_RE.match(line)
        if m and len(m.group(1)) <= 30:  # 子节标题视作下一节起点
            break
        body.append(line)
    return "\n".join(body)


def extract_tables(section: str) -> list[list[list[str]]]:
    """解析节内全部 markdown 表格，返回（行=单元格列表）。"""
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in section.splitlines():
        line = line.strip()
        if line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if set(cells) == {"-"} or all(re.fullmatch(r":?-+:?", c) for c in cells if c):
                continue  # 分隔行
            current.append(cells)
        else:
            if current:
                tables.append(current)
                current = []
    if current:
        tables.append(current)
    return tables


def is_header_row(cells: list[str], keywords: list[str]) -> bool:
    joined = "".join(cells)
    hits = sum(1 for k in keywords if k in joined)
    return hits >= len(keywords) - 1  # 容忍一列命名差异


def numbers(text: str) -> list[int]:
    return [int(m) for m in re.findall(r"\d+", text)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path("."), help="书项目根（默认当前目录）")
    args = parser.parse_args()

    project = args.project.resolve()
    outline_path = project / "大纲" / "大纲.md"
    try:
        text = read_text(outline_path)
    except OutlineError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    blocking: list[str] = []
    candidate: list[str] = []

    # ---------- 版本兼容检测（B18 §二·五）：八列表头是否齐全 ----------
    skeleton_section = section_text(text, "每卷骨架表")
    eight_col = False
    skeleton_tables: list[list[list[str]]] = []
    if skeleton_section:
        skeleton_tables = extract_tables(skeleton_section)
        for table in skeleton_tables:
            if table and is_header_row(table[0], HEADER_KEYWORDS):
                eight_col = True
                break

    # ---------- a. 必备节存在 ----------
    missing_sections = [s for s in REQUIRED_SECTIONS if s not in text]
    if missing_sections:
        if eight_col:
            blocking.append(f"必备节缺失：{('、'.join(missing_sections))}")
        else:
            candidate.append(OLD_STRUCTURE_CANDIDATE)

    if not eight_col:
        # 旧结构：新节相关 blocking 整体降级为一条 candidate
        if skeleton_section is None or "全书卷级鸟瞰" in text:
            candidate.append(OLD_STRUCTURE_CANDIDATE)
        print(json.dumps({"ok": True, "blocking": [], "candidate": list(dict.fromkeys(candidate))}, ensure_ascii=False))
        return 0

    # ---------- b. 八列表头 + c. 行数/非空 ----------
    skeleton_table = next((t for t in skeleton_tables if is_header_row(t[0], HEADER_KEYWORDS)), None)
    if skeleton_table is None:
        blocking.append("每卷骨架表未找到八列表头（卷/一句话/对手/赌注/中点/高潮/跃迁/字数）")
    else:
        data_rows = skeleton_table[1:]
        if not data_rows:
            blocking.append("每卷骨架表无数据行")
        for i, row in enumerate(data_rows, start=1):
            if len(row) < 8:
                blocking.append(f"骨架表第 {i} 行列数不足（{len(row)} < 8）")
            elif any(not c for c in row[:8]):
                blocking.append(f"骨架表第 {i} 行存在空列")
            # d. 中点列含假胜/假败
            midpoint = row[4] if len(row) > 4 else ""
            if midpoint and "假胜" not in midpoint and "假败" not in midpoint:
                blocking.append(f"骨架表第 {i} 行中点列未标注假胜/假败")
        # c. 表行数 vs 体量节登记卷数
        volume_count = None
        volume_section = section_text(text, "全书体量与阶段总览") or text
        for line in volume_section.splitlines():
            if re.search(r"(?:分|共|总)?\s*(\d+)\s*卷", line):
                volume_count = int(re.search(r"(\d+)\s*卷", line).group(1))
                break
        if volume_count is not None and len(data_rows) != volume_count:
            candidate.append(f"骨架表行数 {len(data_rows)} ≠ 体量节登记卷数 {volume_count}")
        # e. 字数加总 vs 登记总字数（±5%）
        total_words = None
        for line in (section_text(text, "全书体量与阶段总览") or "").splitlines() + text.splitlines():
            m = re.search(r"(?:总字数|预计字数)[^\d]{0,6}(\d+)", line)
            if m:
                total_words = int(m.group(1))
                break
        if total_words is not None:
            row_words = 0
            for row in data_rows:
                m = re.search(r"(\d+)", row[7] if len(row) > 7 else "")
                if m:
                    row_words += int(m.group(1))
            if row_words > 0 and abs(row_words - total_words) / total_words > 0.05:
                blocking.append(f"每卷字数加总 {row_words} 与登记总字数 {total_words} 偏差超 ±5%")

    # ---------- f. 四阶段占比加总=100（±0.5） ----------
    volume_section = section_text(text, "全书体量与阶段总览") or ""
    pcts = []
    for line in volume_section.splitlines():
        if re.search(r"(开篇|发展|高潮|收尾)期", line):
            # B24：排除括号内注释（如「（合计 100%）」），避免 % 正则误捕注释值（宁可漏拦不可误伤）
            line_clean = re.sub(r"（[^）]*）", "", line)
            for m in re.findall(r"(\d+(?:\.\d+)?)\s*%", line_clean):
                pcts.append(float(m))
    if pcts:
        total_pct = sum(pcts)
        if abs(total_pct - 100.0) > 0.5:
            blocking.append(f"四阶段占比加总 {total_pct} ≠ 100（±0.5）")

    # ---------- g. 台阶算术：Σ(档数×卷幅) ≥ 总字数；无法解析 → candidate ----------
    ladder_section = section_text(text, "升级台阶") or ""
    # B24：容忍数字与「×」间夹中文量词（如「4 大阶段 × 100 万字」）——解析不到仍降 candidate，不升 blocking
    pairs = re.findall(r"(\d+)\s*[^\d\n×x*]{0,8}\s*(?:×|x|\*)\s*(\d+)", ladder_section)
    if pairs:
        ladder_sum = sum(int(a) * int(b) for a, b in pairs)
        if total_words is not None and ladder_sum > 0 and ladder_sum < total_words:
            blocking.append(f"升级台阶 Σ(档数×卷幅)={ladder_sum} < 总字数 {total_words}")
    else:
        candidate.append("升级台阶节无「档数×卷幅」数字对，无法实算（请人工核）")

    # ---------- h. 终局底牌 ≥4 项且各有解锁卷 ----------
    bottom_section = section_text(text, "终局底牌") or ""
    bottom_lines = []
    for ln in bottom_section.splitlines():
        s = ln.strip()
        if not s or s.startswith(("#", "|", ">")) or re.fullmatch(r"-{3,}", s):
            continue
        if s.startswith("-"):
            s = s.lstrip("- ").strip()  # B24：容忍 `- ` bullet 前缀（终局底牌条目常以 bullet 开头）
        if s:
            bottom_lines.append(s)
    if bottom_lines:
        entries = [ln for ln in bottom_lines if re.search(r"(底牌|终局|解锁|卷)", ln)]
        if len(entries) < 4:
            blocking.append(f"终局底牌条目数 {len(entries)} < 4")
        for ln in entries:
            if not re.search(r"解锁|第\s*\d+\s*卷|卷\s*\d+", ln):
                blocking.append(f"终局底牌条目缺解锁卷标注：{ln[:20]}")
    else:
        candidate.append("终局底牌节无条目可解析")

    # ---------- i. 整合记录伏笔闭合 ----------
    integration_path = project / "大纲" / "整合记录.md"
    if integration_path.exists():
        try:
            integration_text = read_text(integration_path)
            known = set(re.findall(r"F\d+", integration_text))
            referenced = set(re.findall(r"F\d+", text))
            dangling = sorted(referenced - known)
            if dangling:
                blocking.append(f"伏笔引用指向未登记编号：{('、'.join(dangling))}")
        except OutlineError as exc:
            candidate.append(f"整合记录读取异常：{exc}")

    # ---------- B20 扩展：暗线设计 / 支线登记（观察 017；断言与 B20 模板同批更新） ----------
    dark_section = section_text(text, "暗线设计")
    branch_section = section_text(text, "支线登记")
    if eight_col:
        if dark_section is None:
            blocking.append("必备节缺失：暗线设计")
        else:
            dark_rows = [r for t in extract_tables(dark_section) for r in t[1:]]
            if not dark_rows:
                blocking.append("暗线设计层次表无数据行")
            for row in dark_rows:
                if len(row) > 2 and not row[2].strip():
                    blocking.append("暗线设计层次表存在空节奏列（读者感知节奏）")
                    break
        if branch_section is None:
            blocking.append("必备节缺失：支线登记")
        else:
            branch_tables = extract_tables(branch_section)
            if branch_tables and not any("配角高光" in "".join(r) for r in branch_tables[0][:1]):
                blocking.append("支线登记表头缺「配角高光」列（选填列，表头须在）")
            branch_rows = [r for t in branch_tables for r in t[1:]]
            if not branch_rows:
                blocking.append("支线登记表无数据行")
            for row in branch_rows:
                if len(row) > 6 and not row[6].strip():
                    blocking.append("支线登记表存在空收束卷列（无收束=坑）")
                    break
    # candidate：大伏笔中间卷无半揭/误导
    if integration_path.exists() and dark_section:
        try:
            integration_text = read_text(integration_path)
            spans = re.findall(r"F\d+[^\n]{0,40}?(\d+)[^\n]{0,20}?(\d+)", integration_text)
            if spans and not re.search(r"半揭|误导", integration_text):
                long_spans = [s for s in spans if abs(int(s[1]) - int(s[0])) >= 3]
                if long_spans:
                    candidate.append("存在跨 ≥3 卷的大伏笔且整合记录无「半揭/误导」标注——建议中间卷补铺垫")
        except OutlineError:
            pass
    # candidate：支线篇幅占比 >25%（mo-shu 自定参数）
    if branch_section:
        for row in extract_tables(branch_section):
            for cells in row[1:]:
                if len(cells) > 5:
                    m = re.search(r"(\d+(?:\.\d+)?)\s*%", cells[5])
                    if m and float(m.group(1)) > 25.0:
                        candidate.append(f"支线篇幅占比 {m.group(1)}% > 25%（mo-shu 自定上限，可按题材调整）")
                        break
    # candidate：暗线某卷无推进点（对照线索矩阵登记——无法确定性验证，提示人工核）
    if dark_section:
        candidate.append("暗线每卷至少推进一格——请对照整合记录线索矩阵核对推进点登记（机检无法确定性验证）")

    # ---------- j. candidate：势力场互引（疑似单链条） ----------
    power_section = section_text(text, "对手梯队与势力场") or ""
    power_tables = extract_tables(power_section)
    if power_tables:
        table = power_tables[0]
        names = [row[0] for row in table[1:] if row and row[0] and row[0] != "势力/人物"]
        if len(names) >= 3:
            rel_col = [row[3] if len(row) > 3 else "" for row in table[1:]]
            base_names = [n.split("（")[0].strip() for n in names]  # B24：互引匹配去除势力名括号后缀
            mentioned = {bn for cell in rel_col for bn in base_names if bn in cell}
            if len(mentioned) <= 1:
                candidate.append("势力场「与其他势力关系」列疑似单链条（互引 ≤1），非网")
        elif names:
            candidate.append(f"势力场仅 {len(names)} 个势力（建议 ≥3 成网）")

    # ---------- k. candidate：采风专名比对（设定/采风-*.md 通配，B19 联动） ----------
    harvest_dir = project / "设定"
    harvest_files = sorted(harvest_dir.glob("采风-*.md")) if harvest_dir.is_dir() else []
    if harvest_files:
        for harvest_path in harvest_files:
            try:
                harvest_text = read_text(harvest_path)
                names_block = section_text(harvest_text, "来源专有名词") or ""
                for term in re.findall(r"[一-龥A-Za-z][一-龥A-Za-z0-9]{1,12}", names_block):
                    if term in text:
                        candidate.append(f"大纲疑似复用来源专名：{term}（{harvest_path.name}）")
                        break
            except OutlineError as exc:
                candidate.append(f"采风记录读取异常：{harvest_path.name}——{exc}")

    # ---------- B21 candidate：采风产物未消费提示（采风-CF*.md 元数据状态） ----------
    if harvest_dir.is_dir():
        cf_files = sorted(harvest_dir.glob("采风-CF*.md"))
        if cf_files:
            unconsumed = []
            for cf in cf_files:
                try:
                    cf_text = read_text(cf)
                except OutlineError:
                    continue
                status_match = re.search(r"状态[：:]\s*([^\s|｜]+)", cf_text)
                if status_match and status_match.group(1) in ("未消费", "进行中", "已回"):
                    unconsumed.append(cf.name)
            if unconsumed:
                candidate.append(f"有 {len(unconsumed)} 份采风产物未消费（{'、'.join(unconsumed[:5])}）")

    # ---------- l. candidate：常驻压力空/占位 ----------
    pressure_match = re.search(r"常驻压力[：:]\s*[^\n]*", text)
    if pressure_match:
        val = pressure_match.group(0).split("常驻压力")[1].lstrip("：: ")
        if not val or val in ("{}", "待补充", "TBD"):
            candidate.append("常驻压力行为空或占位，建议补充")

    # ---------- B53 candidate：虚拟对标消费提示（设定/虚拟对标.md 存在时） ----------
    virtual_path = project / "设定" / "虚拟对标.md"
    if virtual_path.exists():
        try:
            vtext = read_text(virtual_path)
            # 提取虚拟对标中的可锚定关键词（节奏目标/结构要点节的数字+名词短语，简单口径：
            # 抽「每 N 章」「N 条」与 >2 字中文词），命中任一即算已消费
            anchors = set(re.findall(r"每\s*\d+\s*章|伏笔密度|\d+\s*条", vtext))
            consumed = any(a in text for a in anchors) if anchors else None
            if consumed is False:
                candidate.append("存在 虚拟对标.md 但大纲/卷纲零引用其节奏目标或结构要点关键词——可能未消费（候选提示，请人工确认）")
        except OutlineError as exc:
            candidate.append(f"虚拟对标读取异常：{exc}")

    # ---------- m. candidate：反转类型覆盖统计（整合记录） ----------
    if integration_path.exists():
        try:
            integration_text = read_text(integration_path)
            reverse_section = section_text(integration_text, "反转") or ""
            types = set(re.findall(r"(意外反转|身份反转|动机反转|立场反转|认知反转|情感反转|局势反转)", reverse_section))
            if types:
                candidate.append(f"反转类型覆盖：{len(types)} 种（{'/'.join(sorted(types))}）")
        except OutlineError:
            pass

    payload = {
        "ok": len(blocking) == 0,
        "blocking": blocking,
        "candidate": list(dict.fromkeys(candidate)),
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())

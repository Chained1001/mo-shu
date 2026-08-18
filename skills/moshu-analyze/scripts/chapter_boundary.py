#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""章节边界解析器（moshu-analyze Stage 0 标准工具）

把原文解析为章节边界表（章号/标题/起始行/字数），做连续性校验，
组装 _progress.md 骨架（含「章节边界」节，唯一真值）。AI 拆书时直接调用本脚本，
禁止临时手写解析脚本（中文数字转换易踩坑）。

用法（按仓库解释器探测形态调用，Windows 禁止裸 python3）:
  for PYBIN in python3 python py; do "$PYBIN" -c "" 2>/dev/null && break; done
  "$PYBIN" chapter_boundary.py --input {原文路径} --outdir {拆文库/{书}/} --book {书名}
                             [--author {作者}] [--encoding utf-8] [--dry-run]

输出:
  - stdout: 统计报告（章数/卷数/总字数去空白/平均每章/重复/跳号/格式/卷段）
  - {outdir}/_progress.md:  骨架（含「章节边界」节，唯一切片真值；不存在时生成，存在时不动，
                             由 AI 按 pipeline-ops 更新规范维护）
  - --dry-run 只打印报告不写文件
"""
import argparse
import io
import os
import re
import sys
from datetime import date

# 强制 UTF-8 输出：Windows 控制台 GBK 代码页会把中文输出变乱码，
# Claude Code/管道按 UTF-8 解码时读到乱码字节（2026-08 实测）。
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

CHAP_RE = re.compile(r'^第\s*([0-9]+|[一二三四五六七八九十百千零两]+)\s*章\s*(.*)$')
VOL_RE = re.compile(r'^第\s*([0-9]+|[一二三四五六七八九十百千零两]+)\s*卷\s*(.*)$')
WS_RE = re.compile(r'\s')

CN_DIGITS = {'零': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4,
             '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
CN_UNITS = {'十': 10, '百': 100, '千': 1000}


def cn2num(s):
    """中文数字转阿拉伯数字：一=1 十=10 十一=11 二十=20 一百零三=103 两=2"""
    s = s.strip()
    if s.isdigit():
        return int(s)
    num = 0
    section = 0
    for ch in s:
        if ch in CN_DIGITS:
            section = CN_DIGITS[ch]
        elif ch in CN_UNITS:
            if section == 0:
                section = 1  # 十 → 10, 百 → 100
            num += section * CN_UNITS[ch]
            section = 0
        elif ch.isdigit():
            section = int(ch)
    return num + section


def parse_chapter_num(raw):
    """'1'/'10'/'一百零三' → int；无法解析返回 None"""
    try:
        return cn2num(raw)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description='章节边界解析器')
    ap.add_argument('--input', required=True, help='原文路径')
    ap.add_argument('--outdir', help='输出目录（拆文库/{书}/）；缺省只打印报告')
    ap.add_argument('--book', default='', help='书名（写 _progress.md 用）')
    ap.add_argument('--author', default='', help='作者（写 _progress.md 用）')
    ap.add_argument('--encoding', default='utf-8', help='原文编码（默认 utf-8）')
    ap.add_argument('--dry-run', action='store_true', help='只打印报告不写文件')
    args = ap.parse_args()

    if not os.path.isfile(args.input):
        print(f'[错误] 原文不存在: {args.input}', file=sys.stderr)
        sys.exit(2)

    try:
        with io.open(args.input, encoding=args.encoding) as f:
            lines = f.readlines()
    except UnicodeDecodeError as e:
        print(f'[错误] 无法按 {args.encoding} 解码（可用 --encoding gbk 重试）: {e}', file=sys.stderr)
        sys.exit(2)

    # Windows 常见 UTF-8 BOM：\ufeff 会黏在首行行首，导致第一章匹配失败
    bom_stripped = False
    if lines and lines[0].startswith('\ufeff'):
        lines[0] = lines[0][1:]
        bom_stripped = True

    chapters = []  # (num, title, line_no)
    vols = []      # (name, line_no)
    for i, line in enumerate(lines, 1):
        raw = line.rstrip('\n').rstrip('\r')
        m = CHAP_RE.match(raw)
        if m:
            num = parse_chapter_num(m.group(1))
            if num is None:
                print(f'[警告] 第{i}行章号无法解析，跳过: {raw[:40]}', file=sys.stderr)
                continue
            chapters.append((num, m.group(2).strip(), i))
            continue
        v = VOL_RE.match(raw)
        if v:
            vols.append((v.group(2).strip(), i))

    if not chapters:
        print('[错误] 未解析到任何章节标题（检查第N章 格式与编码）', file=sys.stderr)
        sys.exit(2)

    # 连续性校验
    nums = [c[0] for c in chapters]
    dup = sorted({n for n in set(nums) if nums.count(n) > 1})
    missing = [n for n in range(1, max(nums) + 1) if n not in set(nums)]
    formats = set()
    for raw in [lines[c[2] - 1].strip() for c in chapters]:
        m = CHAP_RE.match(raw)
        if m:
            formats.add('digit' if m.group(1).isdigit() else 'cn')
    issue = None
    if dup:
        issue = f'重复章号: {dup[:20]}{"…" if len(dup) > 20 else ""}（可能每卷重起，需人工确认或 --per-volume）'
    elif missing:
        issue = f'1..{max(nums)} 跳号: {missing[:20]}{"…" if len(missing) > 20 else ""}'
    elif nums != list(range(1, max(nums) + 1)):
        issue = '章号非 1..N 连续'

    # 每章字数（去空白，精确字符）
    rows = []
    total = 0
    for idx, (num, title, start) in enumerate(chapters):
        end = chapters[idx + 1][2] - 1 if idx + 1 < len(chapters) else len(lines)
        text = ''.join(lines[start - 1:end])
        chars = len(WS_RE.sub('', text))
        total += chars
        rows.append((num, title, start, chars))

    avg = total // len(rows)

    # 卷段统计
    vol_rows = []
    for v_idx, (vname, vline) in enumerate(vols):
        end_line = vols[v_idx + 1][1] - 1 if v_idx + 1 < len(vols) else len(lines)
        in_v = [c for c in chapters if c[2] >= vline and c[2] <= end_line]
        if not in_v:
            continue
        v_chars = sum(r[3] for r in rows if r[0] in {c[0] for c in in_v})
        vol_rows.append((vname, in_v[0][0], in_v[-1][0], v_chars))

    # 报告
    if bom_stripped:
        print('检测到 BOM 已剥离')
    print(f'章节数: {len(rows)}')
    print(f'卷数: {len(vols)}')
    for vname, vf, vl, vc in vol_rows:
        print(f'  卷[{vname}] 第{vf}-{vl}章 {vc / 10000:.1f}万')
    print(f'总字数(去空白): {total}')
    print(f'平均每章: {avg}')
    print(f'章号格式: {"、".join(sorted(formats))}')
    print(f'连续性: {"OK (1..%d 无重复无跳号)" % max(nums) if not issue else issue}')
    print(f'首章: 第{rows[0][0]}章 {rows[0][1]} @行{rows[0][2]} | 末章: 第{rows[-1][0]}章 {rows[-1][1]} @行{rows[-1][2]}')
    if issue:
        print(f'[警告] {issue}', file=sys.stderr)
        if not args.dry_run and args.outdir:
            print('[提示] 问题未解决前不落盘边界表（防止污染切片真值）', file=sys.stderr)
            sys.exit(3)

    if args.dry_run or not args.outdir:
        return

    os.makedirs(args.outdir, exist_ok=True)

    # 边界表（4 列，精确字数）——唯一真值落盘于 _progress.md「章节边界」节，
    # 不再生成独立 章节边界.md（避免双真值漂移，pipeline-ops 以 _progress.md 为准）
    tbl = ['| 章号 | 标题 | 起始行 | 字数 |', '|------|------|--------|------|']
    for num, title, start, chars in rows:
        title_esc = title.replace('|', '\\|')
        tbl.append(f'| {num} | {title_esc} | {start} | {chars} |')

    # _progress.md 骨架（仅当不存在）
    prog_path = os.path.join(args.outdir, '_progress.md')
    if not os.path.exists(prog_path):
        book = args.book or os.path.basename(os.path.normpath(args.outdir))
        skeleton = f"""# 深度拆解进度：{book}
- 小说：{book}{" | 作者：" + args.author if args.author else ""} | 总章数：{len(rows)} | 输出目录：{args.outdir} | 开始：{date.today().isoformat()}
- 最终状态：pending
- schema_version: 2
## 管道进度
| 阶段 | 状态 | 进度 | 备注 |
|------|------|------|------|
| 0 概要+章节边界 | done | 概要.md 首版 + 边界表 | 首版 200 字 thin，全量版 Stage 5 覆盖 |
| 1 黄金三章 | pending | 第1-3章 | 拆完停靠产出快速预览 |
| 2 逐章摘要 | pending | 0/{len(rows)} | 并行 spawn moshu-chapter-extractor |
| 3 聚合分析 | pending | — | 剧情/节奏/情绪模块 |
| 4 设定+关系 | pending | — | 4a/4b/4c |
| 5 汇总报告 | pending | — | 拆文报告.md + 概要全量版 |
| 6 技法总结 | pending | — | 技法总结.md |
## 章节边界（Stage 0 章节边界子步骤产物，唯一权威）
{chr(10).join(tbl)}
## 分块进度
| 块 | 章节 | 状态 |
## 失败记录
| 类型 | 章节/阶段 | 错误信息 | 重试状态 |
|------|----------|---------|---------|
## 质量检查
| 检查项 | 阶段 | 结果 | 修正 |
## 角色合并
| 合并前 | 合并后 | 依据 | 确认 |
## 断点
- 最后处理：Stage 0 | 当前阶段：Stage 1 | 下一操作：拆第1-3章
"""
        with io.open(prog_path, 'w', encoding='utf-8') as f:
            f.write(skeleton)
        print(f'已生成骨架: {prog_path}')


if __name__ == '__main__':
    main()

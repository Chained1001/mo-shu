#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""章节摘要硬检查器（moshu-analyze Stage 2 质量门）

对 章节/第N章_摘要.md 跑 4 条机械硬检查（对应 analyze-workflow「失败处理」的
可机械校验项），替代 AI 每次手写 grep 组合。AI 落盘后直接调用本脚本，
按 PASS/FAIL 处理，不再逐条自写检查命令。

用法（按仓库解释器探测形态调用，Windows 禁止裸 python3）:
  for PYBIN in python3 python py; do "$PYBIN" -c "" 2>/dev/null && break; done
  "$PYBIN" check_chapter_summary.py --dir {拆文库/{书}/章节/} [--file {单个文件}] [--deep]

  --file 也可直接传 第*章_深度拆解.md：此时只跑深度字段检查，不跑摘要 4 条。
  --dir 下只有深度拆解文件且带 --deep 时，跳过摘要检查、仅做深度检查。

检查项:
  1. 情节点数一致: ^P 行数 == 基调：行数 == 白描行数
     (白描: ^P[0-9]+ 后 类型段|白描段|涉及 三段齐全且白描段非空白)
  2. 花括号残留: 只作报告提示（不判 FAIL、不触发重跑——无下游消费方）
  3. 基调枚举 ⊆ {紧张,轻松,悲伤,热血,爽,甜,温馨,恐怖,压抑,其他}
  4. 主题标签枚举 ⊆ {爱情,亲情,友情,权力,金钱,成长,复仇,悬念,搞笑,热血,日常,其他}
     (出现「主题标签：」带冒号或值为基调词均判失败)
  5. 情节点硬下限: P 行数 ≥ 10（agent 模板硬约束的机检兜底）
  --deep: 额外检查 第*章_深度拆解.md 的必含字段（Stage 1 轻检查）

⚠️ 枚举单一权威: 基调/主题标签枚举以本脚本为唯一权威——
   改动枚举必须先改本脚本, 再同步 agent 模板与文档, 防跨文档漂移误报。
   类型枚举以 moshu-chapter-extractor agent 模板为权威（脚本不检查类型）。

退出码: 全部 PASS = 0; 任一 FAIL = 1
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

P_LINE = re.compile(r'^P[0-9]+ ')
WHITE_DESC = re.compile(r'^P[0-9]+ [^|]+\|[^|]*[^|\s][^|]*\|[^|]*涉及')
TONES = {'紧张', '轻松', '悲伤', '热血', '爽', '甜', '温馨', '恐怖', '压抑', '其他'}
TOPIC_TAGS = {'爱情', '亲情', '友情', '权力', '金钱', '成长', '复仇', '悬念', '搞笑', '热血', '日常', '其他'}
# 基调/标签值到换行即止（值后是换行或下一字段，绝不跨行）
TONE_VAL = re.compile(r'基调：([^ |\n]+)')
TAG_LINE = re.compile(r'主题标签([：:]?)([^ |\n]+)')
# Stage 1 深度拆解必含字段（--deep）
DEEP_FIELDS = ['开篇钩子', '人物出场', '世界观铺设', '结构拆解', '爽点分析', '章尾钩子', '可借鉴要素']


def check_file(path: Path) -> tuple[list[str], list[str]]:
    """返回 (FAIL 描述列表, 提示列表); FAIL 空 = PASS"""
    fails: list[str] = []
    warns: list[str] = []
    text = path.read_text(encoding='utf-8', errors='replace')
    lines = text.splitlines()

    p_count = sum(1 for l in lines if P_LINE.match(l))
    tone_count = sum(1 for l in lines if '基调：' in l)
    desc_count = sum(1 for l in lines if WHITE_DESC.match(l))
    if not (p_count == tone_count == desc_count):
        fails.append(f'情节点数不一致: P={p_count} 基调={tone_count} 白描={desc_count}')
    # 审计-V3 AM2：情节点硬下限 10（agent 模板硬约束的机检兜底；下限不足会静默
    # 拖低 Stage 3 语料密度——haiku 输出 6 条格式全对时旧 4 检仍 PASS）
    if p_count < 10:
        fails.append(f'情节点不足: P={p_count}（每章至少 10 个，至多 40 个）')

    if '{' in text or '}' in text:
        warns.append('含花括号残留 { }（仅提示，不判 FAIL）')

    tones_used = set()
    for m in TONE_VAL.finditer(text):
        tones_used.add(m.group(1).strip())
    bad_tones = tones_used - TONES
    if bad_tones:
        fails.append(f'基调越界: {sorted(bad_tones)}')

    tags_used = set()
    for m in TAG_LINE.finditer(text):
        sep, val = m.group(1), m.group(2).strip()
        if sep:  # 「主题标签：X」带冒号 = 格式错误
            fails.append(f'主题标签带冒号: {m.group(0)[:24]}')
        else:
            tags_used.add(val)
    bad_tags = tags_used - TOPIC_TAGS
    if bad_tags:
        fails.append(f'主题标签越界: {sorted(bad_tags)}')

    return fails, warns


def check_deep(path: Path) -> list[str]:
    """Stage 1 深度拆解必含字段轻检查"""
    text = path.read_text(encoding='utf-8', errors='replace')
    missing = [f for f in DEEP_FIELDS if f'**{f}**' not in text]
    return [] if not missing else [f'深度拆解缺字段: {missing}']


def main():
    ap = argparse.ArgumentParser(description='章节摘要硬检查器')
    ap.add_argument('--dir', help='章节目录（拆文库/{书}/章节/）')
    ap.add_argument('--file', help='单文件检查（与 --dir 二选一；也可传 第*章_深度拆解.md）')
    ap.add_argument('--deep', action='store_true', help='额外检查 第*章_深度拆解.md 必含字段')
    args = ap.parse_args()

    deep_only = False
    if args.file:
        p = Path(args.file)
        if '深度拆解' in p.name:
            # --file 直接指向深度拆解文件：只跑深度字段检查
            files = []
            deep_files = [p]
            deep_only = True
        else:
            files = [p]
            deep_files = sorted(p.parent.glob('第*章_深度拆解.md')) if args.deep else []
    elif args.dir:
        d = Path(args.dir)
        files = sorted(d.glob('第*章_摘要.md'))
        deep_files = sorted(d.glob('第*章_深度拆解.md')) if args.deep else []
        if not files:
            if args.deep:
                # Stage 1 场景：目录只有深度拆解文件，允许仅深度检查
                deep_only = True
            else:
                print(f'[错误] {d} 下没有 第*章_摘要.md', file=sys.stderr)
                sys.exit(2)
    else:
        ap.error('需提供 --dir 或 --file')

    total_fail = 0
    checked = 0
    for f in files:
        checked += 1
        fails, warns = check_file(f)
        status = 'PASS' if not fails else 'FAIL'
        if fails:
            total_fail += 1
        line = f'{f.name}: {status}'
        if warns:
            line += ' | [提示] ' + '; '.join(warns)
        print(line + ('' if not fails else ' | ' + '; '.join(fails)))

    if deep_only:
        print('(无摘要可检查，仅深度检查)')

    for f in deep_files:
        checked += 1
        fails = check_deep(f)
        if fails:
            total_fail += 1
        print(f'{f.name}: {"FAIL" if fails else "PASS"}' + ('' if not fails else ' | ' + '; '.join(fails)))
    if args.deep and not deep_files:
        print('(无 第*章_深度拆解.md 可检查)')

    # 枚举总览（跨文件汇总；deep-only 时无摘要可汇总，不输出空数组）
    if deep_only:
        print('\n(无摘要可汇总，跳过基调/主题标签枚举)')
    else:
        all_text = '\n'.join(f.read_text(encoding='utf-8', errors='replace') for f in files)
        tones_all = sorted({m.group(1).strip() for m in TONE_VAL.finditer(all_text)})
        tags_all = sorted({m.group(2).strip() for m in TAG_LINE.finditer(all_text) if not m.group(1)})
        print(f'\n基调枚举: {tones_all}')
        print(f'主题标签枚举: {tags_all}')

    print(f'\nRESULT: {"ALL PASS" if total_fail == 0 else f"{total_fail}/{checked} FAIL"}')
    sys.exit(0 if total_fail == 0 else 1)


if __name__ == '__main__':
    main()

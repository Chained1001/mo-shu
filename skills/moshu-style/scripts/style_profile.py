#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文风画像脚本（moshu-style Stage 4-A 标准工具，方案 A：确定性画像）

零依赖（纯 stdlib + 正则，禁分词库）——虚词密度用内置虚词表（约 70 词）。
把 AI 手搓 one-liner 替换为可测的确定性画像；--compare 输出两画像相对差表，
判级归 AI（三层分工：脚本做确定性、AI 做语义、作者做品味）。

用法（按仓库解释器探测形态调用，Windows 禁止裸 python3）:
  for PYBIN in python3 python py; do "$PYBIN" -c "" 2>/dev/null && break; done
  "$PYBIN" style_profile.py --input {样本路径} [--encoding utf-8] [--json]
  "$PYBIN" style_profile.py --compare {a.json} {b.json}

指标:
  sentences.p25/median/p75/mean/stdev  句长分布（按 。！？… 分句，去空白字符数）
  paragraphs.count/avg_sents/median_chars  段落节奏（非空行=一段）
  punctuation_per_100.{comma,period,excl,ques,ellipsis,dash}  标点密度谱（每百字）
  dialogue_ratio  对话叙述比（「」“”『』 内去空白字数占比 %）
  sentence_start_bigrams 句首二字 Top5
  function_words_per_10000  虚词密度（内置虚词表命中/每万字）

JSON 键名稳定（测试与下游契约）；退出码：0 正常 / 2 用法或缺文件；
读失败三分类（缺/空/坏）各自明示；<800 字样本仍出结果但附 sample_warning 字段
（对齐 moshu-style 现有 low confidence 语义）。
"""
import argparse
import io
import json
import re
import statistics
import sys
from collections import Counter

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# 句界：句号/叹号/问号/省略号（连续多个算一个界）
SENT_SPLIT = re.compile(r'[。！？…]+')
# 引号对（中文弯引号/直角引号/单引号），取引号内文本
QUOTE_PAIRS = [('「', '」'), ('“', '”'), ('『', '』')]
WS = re.compile(r'\s')
# 标点密度谱六键（省略号/破折号按「串」计一次出现）
PUNCT_PATTERNS = {
    'comma': re.compile(r'，'),
    'period': re.compile(r'。'),
    'excl': re.compile(r'！'),
    'ques': re.compile(r'？'),
    'ellipsis': re.compile(r'…+'),
    'dash': re.compile(r'—+'),
}

# 内置虚词表（mo-shu 自定种子，约 70 词；纯 stdlib 零依赖的代价=不覆盖全部虚词，
# 口径以本表为准，密度为相对可比指标非绝对语言学度量）
FUNCTION_WORDS = [
    '的', '地', '得', '了', '着', '过', '之', '乎', '者', '也', '与', '及', '和', '或',
    '因为', '所以', '但是', '而且', '如果', '虽然', '不仅', '况且', '于是', '因此', '然后',
    '接着', '反而', '其实', '几乎', '稍微', '又', '再', '也', '还', '都', '就', '才', '便',
    '曾', '正在', '很', '非常', '十分', '太', '挺', '更加', '越来越', '可能', '也许', '大概',
    '或许', '一定', '必然', '忽然', '突然', '渐渐', '仍然', '依然', '依旧', '已经', '曾经',
    '将要', '快要', '即将', '立刻', '马上', '顿时', '随即', '终于', '终究', '到底', '究竟',
    '竟然', '居然', '果然', '当然', '显然', '自然', '反正', '幸亏', '幸好', '不过', '只是',
    '可是', '然而', '却', '虽', '尽管', '即使', '即便', '假如', '要是', '一旦', '只要',
    '只有', '无论', '不管', '任凭', '按照', '依照', '根据', '通过', '由于', '从而', '进而',
    '以便', '以免', '为了', '除了', '此外', '另外', '还有', '以及', '并且', '其次', '最后',
    '首先',
]


def strip_ws(s):
    return WS.sub('', s)


def read_text(path, encoding):
    """读失败三分类：缺/空/坏，各自明示（反模式 #7 静默降级防线）。"""
    try:
        with io.open(path, encoding=encoding) as f:
            text = f.read()
    except FileNotFoundError:
        print(f'[错误] 输入文件不存在: {path}', file=sys.stderr)
        sys.exit(2)
    except UnicodeDecodeError as e:
        print(f'[错误] 无法按 {encoding} 解码（可用 --encoding gbk 重试）: {e}', file=sys.stderr)
        sys.exit(2)
    if text.startswith('\ufeff'):
        text = text[1:]
    if not text.strip():
        print(f'[错误] 输入文件为空: {path}', file=sys.stderr)
        sys.exit(2)
    return text


def split_sentences(text):
    """按句界分割；剥离残留引号（。」 切分后右引号会粘到下一片段），去空白后返回。"""
    out = []
    for s in SENT_SPLIT.split(text):
        s = strip_ws(s).strip('」』”’「“『')
        if s:
            out.append(s)
    return out


def split_paragraphs(text):
    """非空行 = 一段（对齐 SOP「段落按行切分」语义）；返回去空白后的段落列表。"""
    return [strip_ws(line) for line in text.split('\n') if strip_ws(line)]


def profile(text):
    """计算全部画像指标；返回稳定键名 dict（测试与下游契约）。"""
    chars = len(strip_ws(text))

    # ① 句长分布
    sents = split_sentences(text)
    sent_lens = [len(s) for s in sents] or [chars]  # 无句界标点时全文当一句
    n = len(sent_lens)
    if n < 2:
        q25 = qmed = q75 = sent_lens[0]  # 单句：分位数即句长本身
    else:
        q25, qmed, q75 = statistics.quantiles(sent_lens, n=4)
    mean = statistics.mean(sent_lens)
    stdev = statistics.pstdev(sent_lens) if n > 1 else 0.0

    # ② 段落节奏
    paras = split_paragraphs(text)
    para_chars = [len(p) for p in paras]
    para_sent_counts = [len(split_sentences(p)) for p in paras]
    avg_sents_per_para = statistics.mean(para_sent_counts) if para_sent_counts else 0.0
    median_chars_per_para = statistics.median(para_chars) if para_chars else 0

    # ③ 标点密度谱（每百字；省略号/破折号按串计一次）
    per100 = {}
    for key, pat in PUNCT_PATTERNS.items():
        per100[key] = round(100 * len(pat.findall(text)) / chars, 2) if chars else 0.0

    # ④ 对话叙述比（引号内去空白字数占比 %）
    quoted = 0
    for op, cl in QUOTE_PAIRS:
        for m in re.finditer(re.escape(op) + r'(.*?)' + re.escape(cl), text, re.S):
            quoted += len(strip_ws(m.group(1)))
    dialogue_ratio = round(100 * quoted / chars, 2) if chars else 0.0

    # ⑤ 句首二字 bigram Top5
    bigram_counter = Counter()
    for s in sents:
        if len(s) >= 2:
            bigram_counter[s[:2]] += 1
    top_bigrams = [{'bigram': b, 'count': c} for b, c in bigram_counter.most_common(5)]

    # ⑥ 虚词密度（命中次数/每万字；口径以本表为准）
    fw_hits = sum(len(re.findall(re.escape(w), text)) for w in FUNCTION_WORDS)
    fw_per_10000 = round(10000 * fw_hits / chars, 2) if chars else 0.0

    return {
        'schema_version': 1,
        'sample_chars': chars,
        'sample_warning': '样本 <800 字：confidence 请按 low 处理' if chars < 800 else None,
        'sentences': {
            'count': n,
            'p25': q25,
            'median': qmed,
            'p75': q75,
            'mean': round(mean, 2),
            'stdev': round(stdev, 2),
        },
        'paragraphs': {
            'count': len(paras),
            'avg_sents_per_para': round(avg_sents_per_para, 2),
            'median_chars_per_para': median_chars_per_para,
        },
        'punctuation_per_100': per100,
        'dialogue_ratio': dialogue_ratio,
        'sentence_start_bigrams': top_bigrams,
        'function_words_per_10000': fw_per_10000,
    }


def cmd_profile(args):
    text = read_text(args.input, args.encoding)
    data = profile(text)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=1))
    else:
        s = data['sentences']
        p = data['paragraphs']
        print(f'样本字数(去空白): {data["sample_chars"]}' + (f' | {data["sample_warning"]}' if data['sample_warning'] else ''))
        print(f'句数: {s["count"]} | 句长 P25/中位/P75: {s["p25"]}/{s["median"]}/{s["p75"]} | 均值: {s["mean"]} | 标准差: {s["stdev"]}')
        print(f'段落数: {p["count"]} | 段均句数: {p["avg_sents_per_para"]} | 段落字数中位: {p["median_chars_per_para"]}')
        pp = data['punctuation_per_100']
        print(f'标点密度(每百字): 逗{pp["comma"]} 句{pp["period"]} 叹{pp["excl"]} 问{pp["ques"]} 省略{pp["ellipsis"]} 破折{pp["dash"]}')
        print(f'对话叙述比: {data["dialogue_ratio"]}%')
        print('句首二字 Top5: ' + '、'.join(f'{b["bigram"]}({b["count"]})' for b in data['sentence_start_bigrams']))
        print(f'虚词密度: {data["function_words_per_10000"]}/万字')


def _load_json(path):
    try:
        with io.open(path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f'[错误] 画像文件不存在: {path}', file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f'[错误] 画像文件不是合法 JSON: {path} ({e})', file=sys.stderr)
        sys.exit(2)


def cmd_compare(args):
    a = _load_json(args.compare[0])
    b = _load_json(args.compare[1])
    # 数值指标相对差表：|a-b| / max(|a|,|b|)，零值对零值记 0
    metrics = [
        ('句长 P25', a['sentences']['p25'], b['sentences']['p25']),
        ('句长中位', a['sentences']['median'], b['sentences']['median']),
        ('句长 P75', a['sentences']['p75'], b['sentences']['p75']),
        ('句长均值', a['sentences']['mean'], b['sentences']['mean']),
        ('句长标准差', a['sentences']['stdev'], b['sentences']['stdev']),
        ('段均句数', a['paragraphs']['avg_sents_per_para'], b['paragraphs']['avg_sents_per_para']),
        ('段落字数中位', a['paragraphs']['median_chars_per_para'], b['paragraphs']['median_chars_per_para']),
    ]
    for key in ('comma', 'period', 'excl', 'ques', 'ellipsis', 'dash'):
        metrics.append((f'标点-{key}', a['punctuation_per_100'][key], b['punctuation_per_100'][key]))
    metrics.append(('对话叙述比', a['dialogue_ratio'], b['dialogue_ratio']))
    metrics.append(('虚词密度', a['function_words_per_10000'], b['function_words_per_10000']))

    print(f'相对差表（|a-b|/max(|a|,|b|)；无阈值，判级归 AI——阈值口径见 style-learn-sop.md「仿写校验」节）:')
    print(f'{"指标":<12} {"a":>10} {"b":>10} {"相对差":>8}')
    for name, av, bv in metrics:
        denom = max(abs(av), abs(bv))
        rel = round(abs(av - bv) / denom, 3) if denom else 0.0
        print(f'{name:<12} {av:>10} {bv:>10} {rel:>8}')
    if a.get('sample_warning') or b.get('sample_warning'):
        print('[提示] 任一画像带 sample_warning（样本 <800 字），判级应降 low', file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description='文风画像（默认 profile）与相对差（compare）')
    ap.add_argument('--input', help='样本路径（本地 .txt/.md）')
    ap.add_argument('--encoding', default='utf-8', help='样本编码（默认 utf-8；GBK 用 --encoding gbk）')
    ap.add_argument('--json', action='store_true', help='输出 JSON（落盘 画像.json 用）')
    ap.add_argument('--compare', nargs=2, metavar=('A.json', 'B.json'), help='两画像相对差表')
    args = ap.parse_args()

    if args.compare:
        args.compare_a, args.compare_b = args.compare
        cmd_compare(args)
        return
    if not args.input:
        ap.error('需提供 --input {样本路径} 或 --compare {a.json} {b.json}')
    cmd_profile(args)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Behavioral regression tests for the style profile tool.

守护对象：文风画像脚本（moshu-style Stage 4-A 确定性层）。断言句长分布/段落节奏/
标点密度谱/对话比/句首 bigram/虚词密度六类指标的精确值（合成 fixture 已知构造）、
读失败三分类（缺/空/坏）、<800 字 sample_warning、compare 相对差正确性。
禁：断言真实文风库内容/实现细节/脆弱快照（scripts/README.md 测试纪律）。
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "skills/moshu-style/scripts/style_profile.py"

S10 = "一二三四五六七八九十"
S20 = S10 + S10
S30 = S20 + S10
S40 = S30 + S10
S50 = S40 + S10


def run_tool(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True, text=True, cwd=str(cwd),
        encoding="utf-8", errors="replace",
    )


def profile_json(text: str, cwd: Path) -> dict:
    p = cwd / "sample.txt"
    p.write_text(text, encoding="utf-8")
    r = run_tool("--input", str(p), "--json", cwd=cwd)
    assert r.returncode == 0, r.stdout + r.stderr
    return json.loads(r.stdout)


class StyleProfileTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    # ① 句长分布：已知 10/20/30 三句 → P25/中位/P75/均值/总体标准差精确
    def test_sentence_distribution(self):
        d = profile_json(f"{S10}。{S20}。{S30}。", self.dir)["sentences"]
        self.assertEqual(d["count"], 3)
        self.assertEqual(d["p25"], 10.0)
        self.assertEqual(d["median"], 20.0)
        self.assertEqual(d["p75"], 30.0)
        self.assertEqual(d["mean"], 20.0)
        self.assertAlmostEqual(d["stdev"], 8.16, places=2)  # pstdev(10,20,30)

    # ② 标点密度谱：每行 22 字（10字+逗号+10字+句号）×5 = 110 字 → 逗/句各 5 次
    def test_punctuation_per_100(self):
        line = f"{S10}，{S10}。"
        text = line * 5  # 去空白 110 字，逗号 5、句号 5
        pp = profile_json(text, self.dir)["punctuation_per_100"]
        self.assertEqual(pp["comma"], round(100 * 5 / 110, 2))
        self.assertEqual(pp["period"], round(100 * 5 / 110, 2))
        self.assertEqual(pp["excl"], 0.0)
        d = profile_json(f"{S10}……{S20}——{S10}", self.dir)["punctuation_per_100"]
        self.assertEqual(d["ellipsis"], round(100 / 44, 2))  # 44 字中含 1 串 ……
        self.assertEqual(d["dash"], round(100 / 44, 2))      # 44 字中含 1 串 ——

    # ③ 对话叙述比：引号内 10 字 / 总 20 字 → 50%
    def test_dialogue_ratio(self):
        d = profile_json(f"他说「{S10}」，然后走了。", self.dir)
        self.assertEqual(d["dialogue_ratio"], 50.0)
        d2 = profile_json(S10 + "。", self.dir)
        self.assertEqual(d2["dialogue_ratio"], 0.0)

    # ④ 段落节奏：3 段（2 句/1 句/1 句；段落字数 22/21/11，含标点）→ 段均 1.33、中位 21
    def test_paragraph_stats(self):
        text = f"{S10}。{S10}。\n{S20}。\n{S10}。"
        p = profile_json(text, self.dir)["paragraphs"]
        self.assertEqual(p["count"], 3)
        self.assertAlmostEqual(p["avg_sents_per_para"], 1.33, places=2)
        self.assertEqual(p["median_chars_per_para"], 21)

    # ⑤ 句首二字 bigram Top1 稳定
    def test_bigrams(self):
        d = profile_json(f"{S10}。{S10}！", self.dir)["sentence_start_bigrams"]
        self.assertEqual(d[0]["bigram"], "一二")
        self.assertEqual(d[0]["count"], 2)

    # ⑥ 虚词密度：全文去空白 12 字（含「，」「。」），命中 5 次（因为 所以 但是 然而 忽然）
    def test_function_words_density(self):
        text = "因为所以但是，然而忽然。"
        chars = 12
        hits = 5
        d = profile_json(text, self.dir)
        self.assertEqual(d["sample_chars"], chars)
        self.assertEqual(d["function_words_per_10000"], round(10000 * hits / chars, 2))

    # ⑦ 读失败三分类：缺/空/坏 各自明示 exit 2
    def test_read_fail_missing(self):
        r = run_tool("--input", str(self.dir / "nope.txt"), cwd=self.dir)
        self.assertEqual(r.returncode, 2)
        self.assertIn("不存在", r.stderr)

    def test_read_fail_empty(self):
        p = self.dir / "empty.txt"
        p.write_text("", encoding="utf-8")
        r = run_tool("--input", str(p), cwd=self.dir)
        self.assertEqual(r.returncode, 2)
        self.assertIn("为空", r.stderr)

    def test_read_fail_bad_encoding(self):
        p = self.dir / "gbk.txt"
        p.write_bytes("这是中文测试。".encode("gbk"))
        r = run_tool("--input", str(p), cwd=self.dir)
        self.assertEqual(r.returncode, 2)
        self.assertIn("解码", r.stderr)

    # ⑧ <800 字 sample_warning：799 字有、800 字无
    def test_sample_warning_boundary(self):
        p799 = profile_json(S10 * 79 + "一二三四五六七八九", self.dir)
        self.assertIsNotNone(p799["sample_warning"])
        p800 = profile_json(S10 * 80, self.dir)
        self.assertIsNone(p800["sample_warning"])

    # ⑨ compare 自比全 0
    def test_compare_identical(self):
        a = self.dir / "a.json"
        a.write_text(json.dumps(profile_json(f"{S10}。{S20}。{S30}。", self.dir), ensure_ascii=False), encoding="utf-8")
        r = run_tool("--compare", str(a), str(a), cwd=self.dir)
        self.assertEqual(r.returncode, 0, r.stderr)
        # 表中所有相对差应为 0.0（抽样断言含句长中位行）
        self.assertIn("句长中位", r.stdout)

    # ⑩ compare 差异：a 中位 20 vs b 中位 40 → 相对差 0.5
    def test_compare_diff(self):
        a = self.dir / "a.json"
        a.write_text(json.dumps(profile_json(f"{S10}。{S20}。{S30}。", self.dir), ensure_ascii=False), encoding="utf-8")
        b = self.dir / "b.json"
        b.write_text(json.dumps(profile_json(f"{S30}。{S40}。{S50}。", self.dir), ensure_ascii=False), encoding="utf-8")
        r = run_tool("--compare", str(a), str(b), cwd=self.dir)
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = [ln for ln in r.stdout.splitlines() if ln.startswith("句长中位")]
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].rstrip().endswith("0.5"), lines[0])

    # ⑪ 无 --input 也无 --compare → 用法错误 exit 2
    def test_usage_error(self):
        r = run_tool(cwd=self.dir)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Behavioral regression tests for the chapter summary hard-checker.

守护对象：章节摘要硬检查器（moshu-analyze Stage 2-3 质量门）。断言 4 条硬检查
（检查项 1 情节点数一致 / 3 基调枚举 / 4 主题标签枚举 / 5 情节点硬下限）判 FAIL、
花括号残留（检查项 2）只提示不 FAIL、--file/--deep 深度字段检查路径。
禁：断言真实拆文库内容/实现细节/脆弱快照（scripts/README.md 测试纪律）。
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "skills/moshu-analyze/scripts/check_chapter_summary.py"

DEEP_FIELDS = ["开篇钩子", "人物出场", "世界观铺设", "结构拆解", "爽点分析", "章尾钩子", "可借鉴要素"]


def run_tool(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True, text=True, cwd=str(cwd),
        encoding="utf-8", errors="replace",
    )


def summary_chapter(*, p_count: int, tone_count: int | None = None, theme: str = "悬念",
                    tone: str = "紧张", desc_blank: bool = False, extra_line: str = "") -> str:
    """构造符合格式的摘要文件；P 行数与基调行数可分别控制（测漏基调行）。"""
    if tone_count is None:
        tone_count = p_count
    lines = ["## 第1章 测试", "", "**概要**：本章测试内容概述，事件按顺序发生并有了结果。", "", "**情节点**：", ""]
    for i in range(1, p_count + 1):
        if desc_blank:
            lines.append(f"P{i} **点{i}**：类型行动 | | 涉及主角 | 地点某处 | 物品无 | 时间当日")
        else:
            lines.append(f"P{i} **点{i}**：类型行动 | 主角做了动作，结果明确 | 涉及主角 | 地点某处 | 物品无 | 时间当日")
        if i <= tone_count:
            lines.append(f"主题标签{theme} | 基调：{tone}")
    if extra_line:
        lines.append(extra_line)
    return "\n".join(lines) + "\n"


class ChapterSummaryTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.chapters = self.dir / "章节"
        self.chapters.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def write_summary(self, content: str, name: str = "第1章_摘要.md") -> Path:
        p = self.chapters / name
        p.write_text(content, encoding="utf-8")
        return p

    def write_deep(self, *, fields: list[str] | None = None, name: str = "第1章_深度拆解.md") -> Path:
        if fields is None:
            fields = DEEP_FIELDS
        body = "# 第1章 深度拆解\n\n" + "".join(f"**{f}**：内容。\n" for f in fields)
        p = self.chapters / name
        p.write_text(body, encoding="utf-8")
        return p

    # ① 情节点数 != 基调行数 → FAIL（漏基调行，下游 grep 会静默漏章）
    def test_count_mismatch_fail(self):
        self.write_summary(summary_chapter(p_count=10, tone_count=9))
        r = run_tool("--dir", str(self.chapters), cwd=self.dir)
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", r.stdout)
        self.assertIn("情节点数不一致", r.stdout)

    # ② 白描段缺失 → FAIL（P 行缺白描段）
    def test_desc_blank_fail(self):
        self.write_summary(summary_chapter(p_count=10, desc_blank=True))
        r = run_tool("--dir", str(self.chapters), cwd=self.dir)
        self.assertEqual(r.returncode, 1)
        self.assertIn("情节点数不一致", r.stdout)

    # ③ 基调枚举外 → FAIL
    def test_bad_tone_fail(self):
        self.write_summary(summary_chapter(p_count=10, tone="愉悦"))
        r = run_tool("--dir", str(self.chapters), cwd=self.dir)
        self.assertEqual(r.returncode, 1)
        self.assertIn("基调越界", r.stdout)

    # ④ 主题标签带冒号 → FAIL
    def test_theme_with_colon_fail(self):
        self.write_summary(summary_chapter(p_count=10, theme="：悬念"))
        r = run_tool("--dir", str(self.chapters), cwd=self.dir)
        self.assertEqual(r.returncode, 1)
        self.assertIn("主题标签带冒号", r.stdout)

    # ⑤ 主题标签值为基调词 → FAIL（值越界）
    def test_theme_is_tone_word_fail(self):
        self.write_summary(summary_chapter(p_count=10, theme="紧张"))
        r = run_tool("--dir", str(self.chapters), cwd=self.dir)
        self.assertEqual(r.returncode, 1)
        self.assertIn("主题标签越界", r.stdout)

    # ⑥ 情节点硬下限：N=9 格式全对也 FAIL（检查项 5）
    def test_below_hard_min_fail(self):
        self.write_summary(summary_chapter(p_count=9))
        r = run_tool("--dir", str(self.chapters), cwd=self.dir)
        self.assertEqual(r.returncode, 1)
        self.assertIn("情节点不足", r.stdout)

    # ⑦ 花括号残留 → 仅提示不 FAIL（检查项 2，exit 0）
    def test_brace_only_warns(self):
        self.write_summary(summary_chapter(p_count=10, extra_line="正文里出现 { 残留"))
        r = run_tool("--dir", str(self.chapters), cwd=self.dir)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ALL PASS", r.stdout)
        self.assertIn("[提示]", r.stdout)

    # ⑧ 全绿样本 PASS
    def test_all_green_pass(self):
        self.write_summary(summary_chapter(p_count=10))
        r = run_tool("--dir", str(self.chapters), cwd=self.dir)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)
        self.assertIn("ALL PASS", r.stdout)

    # ⑨ --file 直接指向深度拆解文件：只跑深度字段检查（缺字段 FAIL）
    def test_file_deep_single_check(self):
        p = self.write_deep(fields=["开篇钩子"])  # 只给 1 个字段，其余缺失
        r = run_tool("--file", str(p), cwd=self.dir)
        self.assertEqual(r.returncode, 1)
        self.assertIn("深度拆解缺字段", r.stdout)

    # ⑩ --dir + --deep 且目录只有深度拆解文件：跳过摘要检查、仅深度检查
    def test_deep_only_dir(self):
        self.write_deep()
        r = run_tool("--dir", str(self.chapters), "--deep", cwd=self.dir)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("(无摘要可检查，仅深度检查)", r.stdout)
        self.assertIn("PASS", r.stdout)


if __name__ == "__main__":
    unittest.main()

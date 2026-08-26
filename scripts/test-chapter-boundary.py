#!/usr/bin/env python3
"""Behavioral regression tests for the chapter boundary parser.

守护对象：章节边界解析器（moshu-analyze Stage 2-1 切片真值前提）。断言章号识别
（阿拉伯/中文/混合）、多卷重编号、连续性退出码语义（审计-V3 AC2 扩展：任何模式
遇连续性问题均 exit 3）、BOM 剥离与落盘幂等。禁：断言真实拆文库内容/实现细节/
脆弱快照（scripts/README.md 测试纪律）。
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "skills/moshu-analyze/scripts/chapter_boundary.py"


def run_tool(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True, text=True, cwd=str(cwd),
        encoding="utf-8", errors="replace",
    )


def write_text(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def chapter(n, title="测试章"):
    return f"第{n}章 {title}\n" + ("正文内容若干，用于占位。\n" * 3)


class ChapterBoundaryTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.src = self.dir / "book.txt"
        self.outdir = self.dir / "out"

    def tearDown(self):
        self._tmp.cleanup()

    # ① 中文数字章号（含 十一 多位数）
    def test_chinese_digit_chapters(self):
        cn = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一"]
        write_text(self.src, "".join(chapter(c) for c in cn))
        r = run_tool("--input", str(self.src), "--outdir", str(self.outdir), "--book", "测试书", cwd=self.dir)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("章节数: 11", r.stdout)
        self.assertIn("连续性: OK", r.stdout)
        prog = self.outdir / "_progress.md"
        self.assertTrue(prog.exists())
        self.assertIn("| 11 |", prog.read_text(encoding="utf-8"))

    # ② 阿拉伯章号
    def test_arabic_chapters(self):
        write_text(self.src, "".join(chapter(n) for n in range(1, 4)))
        r = run_tool("--input", str(self.src), "--outdir", str(self.outdir), "--book", "测试书", cwd=self.dir)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("章节数: 3", r.stdout)

    # ③ 混合序列（中文+阿拉伯混用仍连续）
    def test_mixed_formats(self):
        write_text(self.src, chapter("一") + chapter("2") + chapter("三"))
        r = run_tool("--input", str(self.src), "--outdir", str(self.outdir), "--book", "测试书", cwd=self.dir)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("章节数: 3", r.stdout)
        self.assertIn("连续性: OK", r.stdout)

    # ④ 多卷每卷重起章号：不加 --renumber-volumes → 重复章号 exit 3 且不落盘
    def test_volume_restart_duplicate_exit3(self):
        body = ("第一卷\n" + chapter("一") + chapter("二")
                + "第二卷\n" + chapter("一") + chapter("二"))
        write_text(self.src, body)
        r = run_tool("--input", str(self.src), "--outdir", str(self.outdir), "--book", "测试书", cwd=self.dir)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("重复章号", r.stderr)
        self.assertFalse((self.outdir / "_progress.md").exists(), "连续性问题未解决前不得落盘")

    # ⑤ 多卷重编号：--renumber-volumes → 全书连续序号 + 卷名前置消歧
    def test_renumber_volumes(self):
        body = ("第一卷 崛起\n" + chapter("一") + chapter("二")
                + "第二卷 争锋\n" + chapter("一") + chapter("二"))
        write_text(self.src, body)
        r = run_tool("--input", str(self.src), "--outdir", str(self.outdir),
                     "--book", "测试书", "--renumber-volumes", cwd=self.dir)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("[重编号]", r.stdout)
        self.assertIn("章节数: 4", r.stdout)
        prog = (self.outdir / "_progress.md").read_text(encoding="utf-8")
        self.assertIn("| 4 | 争锋 测试章 |", prog)

    # ⑥ 跳号 → exit 3
    def test_gap_exit3(self):
        write_text(self.src, chapter("一") + chapter("三"))
        r = run_tool("--input", str(self.src), "--outdir", str(self.outdir), "--book", "测试书", cwd=self.dir)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("跳号", r.stderr)

    # ⑦ --dry-run 遇连续性问题也 exit 3（AC2 既有纪律）
    def test_dry_run_issue_exit3(self):
        write_text(self.src, chapter("一") + chapter("三"))
        r = run_tool("--input", str(self.src), "--outdir", str(self.outdir),
                     "--book", "测试书", "--dry-run", cwd=self.dir)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertFalse((self.outdir / "_progress.md").exists())

    # ⑧ 纯报告模式（无 --outdir 无 --dry-run）遇连续性问题也 exit 3（C8 修复语义）
    def test_report_only_issue_exit3(self):
        write_text(self.src, chapter("一") + chapter("三"))
        r = run_tool("--input", str(self.src), cwd=self.dir)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("跳号", r.stderr)

    # ⑨ BOM 剥离（UTF-8 BOM 黏在首行行首不破坏第一章匹配）
    def test_bom_stripped(self):
        write_text(self.src, "\ufeff" + chapter("一") + chapter("二"))
        r = run_tool("--input", str(self.src), "--outdir", str(self.outdir), "--book", "测试书", cwd=self.dir)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("检测到 BOM 已剥离", r.stdout)
        self.assertIn("章节数: 2", r.stdout)

    # ⑩ 正常落盘幂等（重跑不覆盖 _progress.md，字节一致）
    def test_idempotent_rerun(self):
        write_text(self.src, "".join(chapter(n) for n in range(1, 4)))
        args = ("--input", str(self.src), "--outdir", str(self.outdir), "--book", "测试书")
        r1 = run_tool(*args, cwd=self.dir)
        self.assertEqual(r1.returncode, 0, r1.stderr)
        first = (self.outdir / "_progress.md").read_bytes()
        r2 = run_tool(*args, cwd=self.dir)
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertEqual(first, (self.outdir / "_progress.md").read_bytes(), "重跑不得改写已落盘边界表")


if __name__ == "__main__":
    unittest.main()

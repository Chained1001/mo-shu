#!/usr/bin/env python3
"""Behavioral regression tests for design_fingerprints.py.

守护对象：B61 设定指纹三子命令契约（record/diff/update）——record 幂等、diff 反查
正确性（stem+路径双匹配，mo-shu 自定）、读失败三分类降级（registry 缺失自动建档/
设定目录缺失 exit 1/单文件 unreadable 不中断）、退出码语义（diff 恒 0，呈报工具非守卫）。
禁：断言真实书项目内容/模糊匹配语义/追踪域写入（scripts/README.md 测试纪律）。
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "skills/moshu-volume/scripts/design_fingerprints.py"


def run_tool(command: str, project: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), command, "--project", str(project)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def make_book(root: Path) -> Path:
    """标准 fixture 书：3 细纲 + 2 设定 + 1 卷纲 + 1 大纲。"""
    book = root / "书"
    setting = book / "设定" / "角色"
    setting.mkdir(parents=True)
    (setting / "甲.md").write_text("# 甲\n主角设定。", encoding="utf-8")
    (book / "设定" / "势力.md").write_text("# 势力\n朝堂与江湖。", encoding="utf-8")
    outline = book / "大纲"
    outline.mkdir()
    (outline / "大纲.md").write_text("# 大纲\n全书骨架。", encoding="utf-8")
    (outline / "卷纲_第01卷.md").write_text("# 卷一\n首卷细目。", encoding="utf-8")
    details = {
        1: "角色/甲.md、势力.md",
        2: "势力.md",
        3: "角色/甲.md",
    }
    for n, field in details.items():
        (outline / f"细纲_第{n:03d}章_测试.md").write_text(
            f"# 第{n}章\n本章涉及设定：{field}\n情节安排：略\n", encoding="utf-8"
        )
    return book


def diff_payload(book: Path) -> dict:
    r = run_tool("diff", book)
    assert r.returncode == 0, r.stdout + r.stderr
    return json.loads(r.stdout)


class DesignFingerprintsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.book = make_book(self.dir)

    def tearDown(self):
        self._tmp.cleanup()

    def read_registry(self, book: Path) -> dict:
        return json.loads((book / ".design-hashes.json").read_text(encoding="utf-8"))

    # ① record 幂等：两次 record 后 registry 的哈希不变（仅 generated_at 可能变）
    def test_record_idempotent(self):
        r1 = run_tool("record", self.book)
        self.assertEqual(r1.returncode, 0, r1.stdout + r1.stderr)
        first = self.read_registry(self.book)["files"]
        r2 = run_tool("record", self.book)
        self.assertEqual(r2.returncode, 0)
        second = self.read_registry(self.book)["files"]
        self.assertEqual(first, second)
        self.assertEqual(len(first), 4)  # 2 设定 + 大纲 + 卷纲

    # ② 反查命中：改 甲.md → diff chapters=[1,3]
    def test_diff_chapters_reverse_lookup(self):
        run_tool("record", self.book)
        target = self.book / "设定" / "角色" / "甲.md"
        target.write_text("# 甲\n修改后的设定。", encoding="utf-8")
        payload = diff_payload(self.book)
        changed = {item["file"]: item for item in payload["changed"]}
        self.assertIn("设定/角色/甲.md", changed)
        self.assertEqual(changed["设定/角色/甲.md"]["chapters"], [1, 3])
        self.assertEqual(changed["设定/角色/甲.md"]["status"], "changed")

    # ③ stem 匹配：字段写「甲」不带路径也命中
    def test_stem_match(self):
        book = self.book
        detail = book / "大纲" / "细纲_第002章_测试.md"
        detail.write_text("# 第2章\n本章涉及设定：甲\n情节安排：略\n", encoding="utf-8")
        run_tool("record", book)
        (book / "设定" / "角色" / "甲.md").write_text("# 甲\n改。", encoding="utf-8")
        payload = diff_payload(book)
        changed = {item["file"]: item for item in payload["changed"]}
        self.assertIn(2, changed["设定/角色/甲.md"]["chapters"])

    # ④ 删除文件 → status=missing
    def test_missing_file(self):
        run_tool("record", self.book)
        (self.book / "设定" / "势力.md").unlink()
        payload = diff_payload(self.book)
        changed = {item["file"]: item for item in payload["changed"]}
        self.assertEqual(changed["设定/势力.md"]["status"], "missing")

    # ⑤ 无引用 → chapters 空（明示无已写章引用）
    def test_no_reference_empty_chapters(self):
        run_tool("record", self.book)
        (self.book / "设定" / "势力.md").write_text("# 势力\n改了。", encoding="utf-8")
        # 1 章字段去掉势力.md（只留 甲.md 路径），2 章改「无」→ 势力.md 无任何章引用
        (self.book / "大纲" / "细纲_第001章_测试.md").write_text(
            "# 第1章\n本章涉及设定：角色/甲.md\n情节安排：略\n", encoding="utf-8"
        )
        (self.book / "大纲" / "细纲_第002章_测试.md").write_text(
            "# 第2章\n本章涉及设定：无\n情节安排：略\n", encoding="utf-8"
        )
        payload = diff_payload(self.book)
        changed = {item["file"]: item for item in payload["changed"]}
        self.assertEqual(changed["设定/势力.md"]["chapters"], [])

    # ⑥ registry 缺失 → 自动建档 + baseline_created
    def test_baseline_created(self):
        payload = diff_payload(self.book)
        self.assertTrue(payload["baseline_created"])
        self.assertTrue((self.book / ".design-hashes.json").exists())
        # 基线刚建 → changed 为空
        self.assertEqual(payload["changed"], [])

    # ⑦ 设定目录缺失 → 输出 error 且退出码 1
    def test_missing_setting_dir_exit_1(self):
        book = self.dir / "空书"
        book.mkdir()
        (book / "大纲").mkdir()
        (book / "大纲" / "大纲.md").write_text("# 大纲", encoding="utf-8")
        r = run_tool("diff", book)
        self.assertEqual(r.returncode, 1)
        self.assertIn("设定目录不存在", r.stdout)

    # ⑧ update 等价 record：改设定 → update → diff changed 空（裁决闭环刷新）
    def test_update_clears_diff(self):
        run_tool("record", self.book)
        (self.book / "设定" / "势力.md").write_text("# 势力\n修订。", encoding="utf-8")
        before = diff_payload(self.book)
        self.assertTrue(any(item["status"] == "changed" for item in before["changed"]))
        r = run_tool("update", self.book)
        self.assertEqual(r.returncode, 0)
        after = diff_payload(self.book)
        self.assertEqual(after["changed"], [])

    # ⑨ 退出码语义：diff 恒 0（正常路径）
    def test_diff_exit_code_zero(self):
        r = run_tool("diff", self.book)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""正反向回归：next_step.py 的 S0-S6 下一步判定（审计-V3 D5，批4 规格）。

守护对象：下一步判定 DTO 的确定性行为——S0-S6 各序命中、优先中断、降级路径、空文件完成判据。禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "skills/moshu/scripts/next_step.py"


def run_tool(project: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), "--project", str(project)],
        text=True,
        capture_output=True,
        check=False,
        encoding="utf-8",
    )


def parse(result: subprocess.CompletedProcess[str]) -> dict:
    assert result.returncode == 0, f"exit={result.returncode} stderr={result.stderr}"
    return json.loads(result.stdout)


class NextStepTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_project(self, name: str = "书") -> Path:
        project = self.root / name
        project.mkdir(parents=True)
        return project

    def write(self, path: Path, content: str = "x") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def init_state(self, project: Path, last: int) -> None:
        self.write(
            project / "追踪/_tracking-state.json",
            json.dumps({"schema_version":8, "last_committed_chapter": last, "state_revision": 1}, ensure_ascii=False),
        )

    def test_s0_when_not_deployed(self) -> None:
        project = self.make_project()
        payload = parse(run_tool(project))
        self.assertEqual(payload["step"], "S0")
        self.assertEqual(payload["suggested_skill"], "moshu-setup")

    def test_s1_when_no_book_dirs(self) -> None:
        project = self.make_project()
        self.write(project / ".story-deployed")
        payload = parse(run_tool(project))
        self.assertEqual(payload["step"], "S1")
        self.assertEqual(payload["suggested_skill"], "moshu-build")
        self.assertIn("/moshu-build", payload["next_action"])

    def test_s2_when_prose_empty_or_missing(self) -> None:
        project = self.make_project()
        self.write(project / ".story-deployed")
        self.write(project / "大纲/大纲.md")
        payload = parse(run_tool(project))
        self.assertEqual(payload["step"], "S2")
        self.assertEqual(payload["suggested_skill"], "moshu-write")
        self.assertIn("/moshu-write", payload["next_action"])
        # 空文件 = 未写（完成判定只认非空文件）
        self.write(project / "正文/第001章_开端.md", "")
        payload = parse(run_tool(project))
        self.assertEqual(payload["step"], "S2")
        self.assertEqual(payload["suggested_skill"], "moshu-write")

    def test_s3_when_next_outline_missing(self) -> None:
        project = self.make_project()
        self.write(project / ".story-deployed")
        self.write(project / "正文/第001章_开端.md")
        self.init_state(project, 1)
        payload = parse(run_tool(project))
        self.assertEqual(payload["step"], "S3")
        self.assertEqual(payload["suggested_skill"], "moshu-write")
        self.assertIn("/moshu-write", payload["next_action"])
        self.assertEqual(payload["last_committed_chapter"], 1)

    def test_s4_when_next_outline_present(self) -> None:
        project = self.make_project()
        self.write(project / ".story-deployed")
        self.write(project / "正文/第001章_开端.md")
        self.write(project / "大纲/细纲_第002章.md")
        self.init_state(project, 1)
        payload = parse(run_tool(project))
        self.assertEqual(payload["step"], "S4")
        self.assertEqual(payload["suggested_skill"], "moshu-write")
        self.assertIn("/moshu-write", payload["next_action"])

    def test_s5_when_volume_end_without_review(self) -> None:
        project = self.make_project()
        self.write(project / ".story-deployed")
        self.write(project / "正文/第005章_结尾.md")
        self.write(project / "大纲/细纲_第006章.md")
        self.write(project / "大纲/卷纲_第1卷.md", "## 章节范围\n第 1 - 5 章\n")
        self.init_state(project, 5)
        payload = parse(run_tool(project))
        self.assertEqual(payload["step"], "S5")
        self.assertEqual(payload["suggested_skill"], "moshu-write")
        self.assertIn("/moshu-write", payload["next_action"])

    def test_s6_when_volume_end_with_review(self) -> None:
        project = self.make_project()
        self.write(project / ".story-deployed")
        self.write(project / "正文/第005章_结尾.md")
        self.write(project / "大纲/细纲_第006章.md")
        self.write(project / "大纲/卷纲_第1卷.md", "## 章节范围\n第 1 - 5 章\n")
        self.write(project / "大纲/卷复盘_第1卷.md")
        self.init_state(project, 5)
        payload = parse(run_tool(project))
        self.assertEqual(payload["step"], "S6")
        self.assertEqual(payload["suggested_skill"], "moshu-build")
        self.assertIn("/moshu-build", payload["next_action"])

    def test_finalize_when_final_volume_reviewed(self) -> None:
        """B70：末卷卷复盘已完成且大纲无后续卷 → FINALIZE 建议（final-report+完结章指引）。"""
        project = self.make_project()
        self.write(project / ".story-deployed")
        self.write(project / "正文/第005章_结尾.md")
        self.write(project / "大纲/细纲_第006章.md")
        self.write(project / "大纲/卷纲_第1卷.md", "## 章节范围\n第 1 - 5 章\n")
        self.write(project / "大纲/卷复盘_第1卷.md")
        self.write(project / "大纲/大纲.md", "# 大纲\n\n## 卷级大纲\n### 第一卷：末卷（约 4 万字，5 章）\n- 一段式\n")
        self.init_state(project, 5)
        payload = parse(run_tool(project))
        self.assertEqual(payload["step"], "FINALIZE")
        self.assertEqual(payload["suggested_skill"], "moshu-write")
        self.assertIn("final-report", payload["next_action"])

    def test_finalize_with_declaration_overrides_open_plan(self) -> None:
        """B70：作者完结宣告文件存在即 FINALIZE（即便大纲还登记了后续卷——显式宣告优先）。"""
        project = self.make_project()
        self.write(project / ".story-deployed")
        self.write(project / "正文/第005章_结尾.md")
        self.write(project / "大纲/细纲_第006章.md")
        self.write(project / "大纲/卷纲_第1卷.md", "## 章节范围\n第 1 - 5 章\n")
        self.write(project / "大纲/卷复盘_第1卷.md")
        self.write(project / "大纲/大纲.md",
                   "# 大纲\n\n## 卷级大纲\n### 第一卷：一卷（约 4 万字，5 章）\n### 第二卷：远卷（约 5 万字，40 章）\n")
        self.write(project / "大纲/完结宣告.md")
        self.init_state(project, 5)
        payload = parse(run_tool(project))
        self.assertEqual(payload["step"], "FINALIZE")
        self.assertTrue(any("完结宣告" in e for e in payload["evidence"]), payload["evidence"])

    def test_s6_maintained_when_not_final_volume(self) -> None:
        """B70：非末卷（大纲登记 2 卷、当前第 1 卷）且无宣告 → S6 不变。"""
        project = self.make_project()
        self.write(project / ".story-deployed")
        self.write(project / "正文/第005章_结尾.md")
        self.write(project / "大纲/细纲_第006章.md")
        self.write(project / "大纲/卷纲_第1卷.md", "## 章节范围\n第 1 - 5 章\n")
        self.write(project / "大纲/卷复盘_第1卷.md")
        self.write(project / "大纲/大纲.md",
                   "# 大纲\n\n## 卷级大纲\n### 第一卷：一卷（约 4 万字，5 章）\n### 第二卷：远卷（约 5 万字，40 章）\n")
        self.init_state(project, 5)
        payload = parse(run_tool(project))
        self.assertEqual(payload["step"], "S6")
        self.assertIn("/moshu-build", payload["next_action"])

    def test_s6_maintained_degrades_when_outline_unparsable(self) -> None:
        """B70 三分类降级：大纲.md 缺失或无卷行 → 维持 S6 不误判 FINALIZE，证据明示。"""
        for name, outline_text in (("书", None), ("书2", "# 大纲\n\n## 卷级大纲\n（卷行未填）\n")):
            project = self.make_project(name)
            self.write(project / ".story-deployed")
            self.write(project / "正文/第005章_结尾.md")
            self.write(project / "大纲/细纲_第006章.md")
            self.write(project / "大纲/卷纲_第1卷.md", "## 章节范围\n第 1 - 5 章\n")
            self.write(project / "大纲/卷复盘_第1卷.md")
            if outline_text is not None:
                self.write(project / "大纲/大纲.md", outline_text)
            self.init_state(project, 5)
            payload = parse(run_tool(project))
            self.assertEqual(payload["step"], "S6")
            self.assertTrue(any("无法判定末卷" in e for e in payload["evidence"]), payload["evidence"])

    def test_volume_range_unparsed_degrades_to_s4(self) -> None:
        project = self.make_project()
        self.write(project / ".story-deployed")
        self.write(project / "正文/第003章_中.md")
        self.write(project / "大纲/细纲_第004章.md")
        self.write(project / "大纲/卷纲_第1卷.md", "## 章节范围\n（格式怪异，无法解析）\n")
        self.init_state(project, 3)
        payload = parse(run_tool(project))
        self.assertEqual(payload["step"], "S4")
        self.assertTrue(any("volume_range_unparsed" in e for e in payload["evidence"]))

    def test_tracking_state_missing_falls_back_to_prose_max(self) -> None:
        project = self.make_project()
        self.write(project / ".story-deployed")
        self.write(project / "正文/第001章_开端.md")
        self.write(project / "正文/第002章_发展.md")
        self.write(project / "大纲/细纲_第003章.md")
        payload = parse(run_tool(project))
        self.assertEqual(payload["step"], "S4")
        self.assertEqual(payload["last_committed_chapter"], 2)
        self.assertTrue(any("tracking_state_missing" in e for e in payload["evidence"]))

    def test_interrupt_analyze_when_deconstruction_incomplete(self) -> None:
        project = self.make_project()
        self.write(project / ".story-deployed")
        self.write(project / "正文/第001章_开端.md")
        self.write(project / "大纲/细纲_第002章.md")
        self.init_state(project, 1)
        self.write(self.root / "拆文库/某书/_progress.md", "- 最终状态：paused_after_stage1\n")
        payload = parse(run_tool(project))
        self.assertEqual(payload["step"], "INTERRUPT")
        self.assertEqual(payload["interrupt"], "analyze")

    def test_interrupt_review_when_state_pending(self) -> None:
        project = self.make_project()
        self.write(project / ".story-deployed")
        self.write(project / "正文/第001章_开端.md")
        self.write(project / "大纲/细纲_第002章.md")
        self.init_state(project, 1)
        self.write(project / ".moshu-review/state.md", "## 完整审查范围\n")
        payload = parse(run_tool(project))
        self.assertEqual(payload["step"], "INTERRUPT")
        self.assertEqual(payload["interrupt"], "review")

    def test_missing_project_root_exits_2(self) -> None:
        result = run_tool(self.root / "不存在")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)

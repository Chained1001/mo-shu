#!/usr/bin/env python3
"""正反向 fixture 回归：impact_scan.py 的影响分析行为。

守护对象：构建资产修订影响分析（未写细纲/已写正文/追踪条目三清单，last_committed_chapter 分界）。禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。

正向：关键词命中未写细纲 + 已写正文 + 追踪条目三处。
反向：干净关键词三清单全空。
反向 2：无追踪 state → 退出 2 且报文含"先 /moshu-build"。
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "skills/moshu-build/scripts/impact_scan.py"
TRACKING_TOOL = ROOT / "skills/moshu-write/scripts/tracking_commit.py"

INIT_DOCUMENT = {
    "schema_version": 2,
    "book_title": "影响分析测试书",
    "last_chapter": 0,
    "context": {
        "position": {"volume": "第一卷·试炼", "volume_start_chapter": 1, "story_time": "第一天", "scene": "训练场"},
        "long_term_constraints": [],
        "active_character_names": [],
        "continuity_risks": [],
        "recent_chapters": [],
        "next_chapter_commitments": [],
    },
    "character_snapshots": {},
    "foreshadow": [],
    "timeline_events": [],
    "information_gaps": [],
}


def commit_document(chapter: int) -> dict[str, object]:
    return {
        "schema_version": 2,
        "mode": "append",
        "chapter": chapter,
        "chapter_title": f"第{chapter}章",
        "expected_state_revision": chapter - 1,
        "delta": {
            "result": f"第{chapter}章内容。",
            "character_changes": [],
            "foreshadow_changes": [
                {
                    "action": "upsert",
                    "id": "F001",
                    "summary": "训练场下的秘宝线索。",
                    "planted_chapter": chapter,
                    "planned_resolution_chapter": chapter + 4,
                    "status": "已埋",
                    "importance": "中",
                }
            ],
            "information_gap_changes": [],
            "timeline_events": [],
            "constraints": [],
            "next_chapter_commitments": [],
        },
        "context": {
            "position": {"volume": "第一卷·试炼", "volume_start_chapter": 1, "story_time": "第一天", "scene": "训练场"},
            "long_term_constraints": [],
            "active_character_names": [],
            "continuity_risks": [],
        },
        "character_snapshots": {},
    }


class ImpactScanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "book"
        self.project.mkdir()
        (self.project / "正文").mkdir()
        (self.project / "大纲").mkdir()
        self._run_tracking("init", INIT_DOCUMENT)
        for chapter in (1, 2, 3):
            self._run_tracking("commit", commit_document(chapter))
        # 已写正文：第 2 章正文含「秘宝」（章号 2 ≤ last=3）
        (self.project / "正文" / "第002章_秘宝现身.md").write_text(
            "他看见训练场下的秘宝闪着微光。\n", encoding="utf-8"
        )
        # 未写细纲：5 份，第 4 章细纲含「秘宝」（章号 4 > last=3）
        for chapter in (1, 2, 3, 4, 5):
            text = "核心事件：测试。\n"
            if chapter == 4:
                text += "秘宝的真相将在本章揭开。\n"
            (self.project / "大纲" / f"细纲_第{chapter:03d}章.md").write_text(text, encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _run_tracking(self, command: str, document: dict[str, object]) -> None:
        input_path = Path(self.temporary.name) / f"{command}-{document.get('chapter', 'init')}.json"
        input_path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(TRACKING_TOOL), command, "--project", str(self.project), "--input", str(input_path)],
            text=True,
            capture_output=True,
            check=False,
            encoding="utf-8",
        )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)

    def run_scan(self, keywords: list[str], *, expect: int = 0) -> subprocess.CompletedProcess[str]:
        args = [sys.executable, str(TOOL), "--project", str(self.project)]
        for keyword in keywords:
            args.extend(["--keyword", keyword])
        completed = subprocess.run(args, text=True, capture_output=True, check=False, encoding="utf-8")
        self.assertEqual(completed.returncode, expect, msg=completed.stderr)
        return completed

    def test_keyword_hits_all_three_facets(self) -> None:
        completed = self.run_scan(["秘宝"])
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["boundary_chapter"], 3)
        result = payload["keywords"]["秘宝"]

        unwritten = result["unwritten_outlines"]
        self.assertEqual(len(unwritten), 1)
        self.assertIn("细纲_第004章.md", unwritten[0]["file"])
        self.assertEqual(unwritten[0]["line"], 2)

        written = result["written_chapters"]
        self.assertEqual(len(written), 1)
        self.assertIn("第002章_秘宝现身.md", written[0]["file"])

        tracking = result["tracking_hits"]
        self.assertTrue(any(hit["domain"] == "foreshadow" and hit["key"] == "F001" for hit in tracking))

    def test_clean_keyword_yields_empty_facets(self) -> None:
        completed = self.run_scan(["不存在的词"])
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["boundary_chapter"], 3)
        result = payload["keywords"]["不存在的词"]
        self.assertEqual(result["unwritten_outlines"], [])
        self.assertEqual(result["written_chapters"], [])
        self.assertEqual(result["tracking_hits"], [])

    def test_missing_state_exits_two_with_guidance(self) -> None:
        empty_project = Path(self.temporary.name) / "empty"
        empty_project.mkdir()
        args = [sys.executable, str(TOOL), "--project", str(empty_project), "--keyword", "秘宝"]
        completed = subprocess.run(args, text=True, capture_output=True, check=False, encoding="utf-8")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("先 /moshu-build", completed.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)

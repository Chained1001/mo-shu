#!/usr/bin/env python3
"""正反向回归：review_tickets.py 的工单管理行为。

守护对象：审查工单 write/resolve/list/verify-token 的确定性行为。禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。

- write 合法 → 落盘且幂等（同输入两遍逐字节一致）；
- 坏枚举 / 重复 id / 坏令牌 → 拒绝；
- resolve open→fixed 单向流转，fixed→再 resolve 拒绝；
- list --status open 过滤；
- verify-token 相等/不等（不等退出 2）。
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "skills/moshu-review/scripts/review_tickets.py"

VALID_DOCUMENT = {
    "schema_version": 2,
    "chapter_range": [10, 12],
    "review_token": "a1b2c3d4",
    "findings": [
        {
            "id": "T002",
            "severity": "candidate",
            "dimension": "prose",
            "evidence": "第10章 第3段",
            "suggestion": "重写该段节奏",
            "status": "open",
            "status_note": "",
        },
        {
            "id": "T001",
            "severity": "blocking",
            "dimension": "consistency",
            "evidence": "第10章 第1段 vs 设定/角色/江晨.md",
            "suggestion": "统一为左臂旧伤",
            "status": "open",
            "status_note": "",
        },
    ],
}


class ReviewTicketsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "demo"
        self.project.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_input(self, document: dict[str, object]) -> Path:
        path = Path(self.temporary.name) / f"findings-{document['review_token']}.json"
        path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
        return path

    def run_tool(
        self,
        args: list[str],
        *,
        expect: int = 0,
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [sys.executable, str(TOOL), *args],
            text=True,
            capture_output=True,
            check=False,
            encoding="utf-8",
        )
        self.assertEqual(
            completed.returncode,
            expect,
            msg=f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )
        return completed

    def ticket_files(self) -> list[Path]:
        directory = self.project / ".moshu-review/tickets"
        return sorted(directory.glob("tickets_*.json")) if directory.exists() else []

    def read_ticket(self, path: Path) -> dict[str, object]:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_write_valid_document_is_idempotent(self) -> None:
        first = self.run_tool(["write", "--project", str(self.project), "--input", str(self.write_input(VALID_DOCUMENT))])
        self.assertIn("ticket written", first.stdout)
        second = self.run_tool(["write", "--project", str(self.project), "--input", str(self.write_input(VALID_DOCUMENT))])
        self.assertIn("identical content", second.stdout)

        files = self.ticket_files()
        self.assertGreaterEqual(len(files), 1)
        payloads = [self.read_ticket(path) for path in files]
        for payload in payloads[1:]:
            self.assertEqual(payload, payloads[0])
        self.assertEqual(payloads[0]["schema_version"], 2)
        self.assertEqual(payloads[0]["chapter_range"], [10, 12])
        self.assertEqual(payloads[0]["review_token"], "a1b2c3d4")
        self.assertEqual([item["id"] for item in payloads[0]["findings"]], ["T001", "T002"])

    def test_bad_enum_duplicate_id_and_bad_token_are_rejected(self) -> None:
        bad_severity = json.loads(json.dumps(VALID_DOCUMENT, ensure_ascii=False))
        bad_severity["findings"][0]["severity"] = "critical"
        result = self.run_tool(
            ["write", "--project", str(self.project), "--input", str(self.write_input(bad_severity))],
            expect=2,
        )
        self.assertIn("severity", result.stderr)
        self.assertEqual(self.ticket_files(), [])

        bad_dimension = json.loads(json.dumps(VALID_DOCUMENT, ensure_ascii=False))
        bad_dimension["findings"][0]["dimension"] = "emotion"
        result = self.run_tool(
            ["write", "--project", str(self.project), "--input", str(self.write_input(bad_dimension))],
            expect=2,
        )
        self.assertIn("dimension", result.stderr)

        duplicate = json.loads(json.dumps(VALID_DOCUMENT, ensure_ascii=False))
        duplicate["findings"][0]["id"] = "T001"
        result = self.run_tool(
            ["write", "--project", str(self.project), "--input", str(self.write_input(duplicate))],
            expect=2,
        )
        self.assertIn("duplicate IDs", result.stderr)

        bad_token = json.loads(json.dumps(VALID_DOCUMENT, ensure_ascii=False))
        bad_token["review_token"] = "short"
        result = self.run_tool(
            ["write", "--project", str(self.project), "--input", str(self.write_input(bad_token))],
            expect=2,
        )
        self.assertIn("review_token", result.stderr)
        self.assertEqual(self.ticket_files(), [])

    def test_write_rejects_non_open_status(self) -> None:
        # write 只接受 open：fixed/dismissed 必须走 resolve（批6 禁止事项 4，防绕过处置证据）
        preclosed = json.loads(json.dumps(VALID_DOCUMENT, ensure_ascii=False))
        preclosed["findings"][0]["status"] = "fixed"
        result = self.run_tool(
            ["write", "--project", str(self.project), "--input", str(self.write_input(preclosed))],
            expect=2,
        )
        self.assertIn("status must be open", result.stderr)
        self.assertEqual(self.ticket_files(), [])

    def test_resolve_is_open_to_fixed_only(self) -> None:
        self.run_tool(["write", "--project", str(self.project), "--input", str(self.write_input(VALID_DOCUMENT))])
        ticket = self.ticket_files()[0]

        self.run_tool(
            ["resolve", "--project", str(self.project), "--ticket", str(ticket), "--id", "T001",
             "--status", "fixed", "--note", "已将设定统一为左臂旧伤并同步正文。"]
        )
        payload = self.read_ticket(ticket)
        self.assertEqual(payload["findings"][0]["status"], "fixed")
        self.assertIn("左臂旧伤", payload["findings"][0]["status_note"])

        # fixed 再 resolve → 拒绝
        result = self.run_tool(
            ["resolve", "--project", str(self.project), "--ticket", str(ticket), "--id", "T001",
             "--status", "dismissed", "--note", "重复处置。"],
            expect=2,
        )
        self.assertIn("already fixed", result.stderr)

        # 不存在的 id → 拒绝
        result = self.run_tool(
            ["resolve", "--project", str(self.project), "--ticket", str(ticket), "--id", "T999",
             "--status", "dismissed", "--note", "无此工单。"],
            expect=2,
        )
        self.assertIn("not found", result.stderr)

    def test_list_filters_by_status(self) -> None:
        self.run_tool(["write", "--project", str(self.project), "--input", str(self.write_input(VALID_DOCUMENT))])
        self.run_tool(
            ["resolve", "--project", str(self.project), "--ticket", str(self.ticket_files()[0]),
             "--id", "T001", "--status", "fixed", "--note", "已修复。"]
        )

        all_result = self.run_tool(["list", "--project", str(self.project)])
        all_payload = json.loads(all_result.stdout)
        self.assertEqual(len(all_payload), 1)
        self.assertEqual(len(all_payload[0]["findings"]), 2)

        open_result = self.run_tool(["list", "--project", str(self.project), "--status", "open"])
        open_payload = json.loads(open_result.stdout)
        self.assertEqual([item["id"] for item in open_payload[0]["findings"]], ["T002"])

        fixed_result = self.run_tool(["list", "--project", str(self.project), "--status", "fixed"])
        fixed_payload = json.loads(fixed_result.stdout)
        self.assertEqual([item["id"] for item in fixed_payload[0]["findings"]], ["T001"])

    def test_verify_token_matches_or_rejects(self) -> None:
        self.run_tool(["write", "--project", str(self.project), "--input", str(self.write_input(VALID_DOCUMENT))])
        ticket = self.ticket_files()[0]

        ok = self.run_tool(["verify-token", "--ticket", str(ticket), "--token", "a1b2c3d4"])
        self.assertIn("token ok", ok.stdout)

        mismatch = self.run_tool(
            ["verify-token", "--ticket", str(ticket), "--token", "wrong123"],
            expect=2,
        )
        self.assertIn("token mismatch", mismatch.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)

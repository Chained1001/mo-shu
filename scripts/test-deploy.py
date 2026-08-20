#!/usr/bin/env python3
"""deploy.py 部署/验证行为的正式回归（审计-V3 PM6）。

守护对象：moshu-setup 部署执行体 deploy.py 的确定性行为——部署→验证全 PASS、
验证失败退出码非 0（PM1）、agent-references 题材子卡纳入完整性校验（PM2）、
agents_version 降级门拒绝。禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DEPLOY = ROOT / "skills/moshu-setup/scripts/deploy.py"

CARDS_DIR = Path("references/agent-references/genre-prose-cards")
SAMPLE_CARD = "都市脑洞.md"


def _fresh_fixture() -> Path:
    """fixture 仓库：复制 skills/ 后只留 moshu-setup（deploy.py 引用自身目录下的资源）。"""
    base = Path(tempfile.mkdtemp(prefix="deploy-test-"))
    (base / "skills").mkdir(parents=True)
    shutil.copytree(ROOT / "skills/moshu-setup", base / "skills/moshu-setup")
    return base


class DeployTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "书"
        self.project.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_deploy(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SRC_DEPLOY), *args],
            text=True,
            capture_output=True,
            check=False,
            encoding="utf-8",
        )

    def test_deploy_then_verify_all_pass(self) -> None:
        deployed = self.run_deploy("deploy", "--project", str(self.project), "--name", "审计书")
        self.assertEqual(deployed.returncode, 0, f"stdout:\n{deployed.stdout}\nstderr:\n{deployed.stderr}")
        verified = self.run_deploy("verify", "--project", str(self.project))
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        self.assertIn("RESULT: ALL PASS", verified.stdout)

    def test_verify_fails_nonzero_when_card_missing(self) -> None:
        self.run_deploy("deploy", "--project", str(self.project), "--name", "审计书")
        card = (
            self.project
            / ".claude/skills/moshu-setup"
            / CARDS_DIR
            / SAMPLE_CARD
        )
        self.assertTrue(card.is_file(), f"fixture 前提失败：{card} 未被部署")
        card.unlink()
        verified = self.run_deploy("verify", "--project", str(self.project))
        self.assertEqual(verified.returncode, 1, "题材子卡缺失时 verify 必须非零退出（PM2）")
        self.assertIn("RESULT: HAS FAILURE", verified.stdout)

    def test_agents_version_downgrade_is_refused(self) -> None:
        self.run_deploy("deploy", "--project", str(self.project), "--name", "审计书")
        sentinel = self.project / ".story-deployed"
        text = sentinel.read_text(encoding="utf-8")
        match = re.search(r"agents_version: (\d+)", text)
        assert match, "fixture 前提失败：sentinel 无 agents_version"
        higher = str(int(match.group(1)) + 70)
        sentinel.write_text(
            text.replace(f"agents_version: {match.group(1)}", f"agents_version: {higher}", 1),
            encoding="utf-8",
        )
        redeployed = self.run_deploy("deploy", "--project", str(self.project), "--name", "审计书")
        self.assertEqual(redeployed.returncode, 1, "项目 agents_version 高于当前时 deploy 必须拒绝降级")
        self.assertIn("大于当前", redeployed.stdout + redeployed.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)

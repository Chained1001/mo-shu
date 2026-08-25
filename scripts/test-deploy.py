#!/usr/bin/env python3
"""deploy.py 部署/验证行为的正式回归（审计-V3 PM6；审计-setup-v1 候选 4/5 扩展）。

守护对象：moshu-setup 部署执行体 deploy.py 的确定性行为——部署→验证全 PASS（含 CLAUDE.md 标准节检查）、
验证失败退出码非 0（PM1）、agent-references 题材子卡纳入完整性校验（PM2）、agents_version 降级门拒绝、
CLAUDE.md 重复部署字节幂等（候选 4）、CONFLICT 未解决时 verify 机械暴露（候选 5）。
禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。
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
        self.assertIn("CLAUDE.md 含全部模板标准节", verified.stdout, "正常部署后 CLAUDE.md 标准节检查必须 PASS")

    def test_deploy_claude_md_idempotent(self) -> None:
        # 候选 4：merge_claude_md 规范化后，重复部署 CLAUDE.md 字节必须稳定（SKILL.md「重复执行结果一致」）
        self.run_deploy("deploy", "--project", str(self.project), "--name", "审计书")
        first = (self.project / "CLAUDE.md").read_bytes()
        self.run_deploy("deploy", "--project", str(self.project), "--name", "审计书")
        second = (self.project / "CLAUDE.md").read_bytes()
        self.assertEqual(first, second, "重复部署 CLAUDE.md 必须字节一致（幂等）")

    def test_verify_fails_when_claude_md_conflict(self) -> None:
        # 候选 5：纯自定义 CLAUDE.md（无 ## section）走 CONFLICT 后，verify 必须机械暴露未部署完整
        self.run_deploy("deploy", "--project", str(self.project), "--name", "审计书")
        (self.project / "CLAUDE.md").write_text("# 我的项目\n\n这是我的自定义说明。\n", encoding="utf-8")
        verified = self.run_deploy("verify", "--project", str(self.project))
        self.assertEqual(verified.returncode, 1, "CLAUDE.md 缺模板标准节时 verify 必须非零退出（候选 5）")
        self.assertIn("CLAUDE.md 含全部模板标准节", verified.stdout)
        self.assertIn("RESULT: HAS FAILURE", verified.stdout)

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

    def test_same_path_skips_copy_without_rmtree(self) -> None:
        # TS 补测批 P1：same_path 分支（符号链接安装场景）——源与目标 realpath 相同时
        # 跳过复制且不得 rmtree 源（E 清空重建引入 rmtree 后，误删源会毁掉技能包本体）。
        # 等价构造：把 AGENT_REFS monkeypatch 成目标路径自身，realpath 恒相等。
        sys.path.insert(0, str(SRC_DEPLOY.parent))
        import deploy  # noqa: PLC0415

        ref_dst = self.project / ".claude/skills/moshu-setup/references/agent-references"
        deploy.AGENT_REFS = ref_dst
        ref_dst.mkdir(parents=True)
        (ref_dst / "writing-craft.md").write_text("x", encoding="utf-8")

        logs, fatal = deploy.deploy(self.project, "n", "n", "34", "1.5.1", dry_run=False)
        self.assertEqual(fatal, [], f"same_path 部署不应 fatal: {fatal}")
        self.assertTrue(any("同路径跳过复制" in line for line in logs), logs)
        self.assertTrue((ref_dst / "writing-craft.md").exists(), "same_path 分支误删了源文件")


if __name__ == "__main__":
    unittest.main(verbosity=2)

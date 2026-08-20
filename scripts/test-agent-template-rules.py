#!/usr/bin/env python3
"""正反向 fixture 回归：check-agent-template-rules.py 的模板纪律守卫。

守护对象：agent 模板纪律守卫（禁互引/挂载点存在/单副本）。禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。

正向：干净模板（无互引、引用存在、无纪律标题）→ 通过。
反向 1：模板含"格式同 system"→ 失败。
反向 2：模板引用不存在的 agent-references 文件 → 失败。
反向 3：模板正文复制共享纪律标题行 → 失败。
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts/check-agent-template-rules.py"

TEMPLATES_DIR = "skills/moshu-setup/references/templates/agents"
REFERENCES_DIR = "skills/moshu-setup/references/agent-references"
DISCIPLINE = "shared-output-discipline.md"
DISCIPLINE_TITLE = "shared-output-discipline：结构化产出纪律（共享 base 段）"


class AgentTemplateRulesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / TEMPLATES_DIR).mkdir(parents=True)
        (self.root / REFERENCES_DIR).mkdir(parents=True)
        (self.root / REFERENCES_DIR / DISCIPLINE).write_text(
            f"# {DISCIPLINE_TITLE}\n\n纯 JSON 纪律正文。\n",
            encoding="utf-8",
        )
        (self.root / REFERENCES_DIR / "existing.md").write_text("# existing\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_guard(self, *, expect: int = 0) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [sys.executable, str(TOOL), "--root", str(self.root)],
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

    def write_template(self, name: str, content: str) -> Path:
        path = self.root / TEMPLATES_DIR / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_clean_template_passes(self) -> None:
        self.write_template(
            "ok.md",
            "# Ok agent\n\n产出纪律见 `moshu-setup/references/agent-references/shared-output-discipline.md`"
            "（引用即挂载，此处不重复）。\n另读 `moshu-setup/references/agent-references/existing.md`。\n",
        )
        result = self.run_guard()
        self.assertIn("agent template rules: ok", result.stdout)

    def test_forbidden_reference_fails(self) -> None:
        self.write_template(
            "bad-ref.md",
            "# Bad agent\n\n输出格式同 system，不重复说明。\n",
        )
        result = self.run_guard(expect=1)
        self.assertIn("禁互引", result.stdout)
        self.assertIn("bad-ref.md:3", result.stdout)

    def test_missing_mount_point_fails(self) -> None:
        self.write_template(
            "bad-mount.md",
            "# Bad mount\n\n读取 `moshu-setup/references/agent-references/ghost.md`。\n",
        )
        result = self.run_guard(expect=1)
        self.assertIn("挂载点缺失", result.stdout)
        self.assertIn("ghost.md", result.stdout)

    def test_copied_discipline_title_fails(self) -> None:
        self.write_template(
            "bad-copy.md",
            f"# Bad copy\n\n# {DISCIPLINE_TITLE}\n纯 JSON 纪律正文复制回模板。\n",
        )
        result = self.run_guard(expect=1)
        self.assertIn("单副本", result.stdout)
        self.assertIn("bad-copy.md:3", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)

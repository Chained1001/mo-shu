#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_methodology_wiring.py — check-methodology-wiring 挂载守卫回归测试（批B92）

守护对象：方法论挂载守卫的五级分级与退出码语义——
  1. DEAD（零流程引用）→ blocking（exit 1）
  2. MUST（流程权威集内「必读」）→ 通过（exit 0）
  3. 白名单 DEAD（quality-rubric）→ 通过（exit 0，candidate 标注白名单豁免）
fixture 用临时目录（--root 参数指向），零网络零 LLM，跑完自清理。
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check-methodology-wiring.py"


def make_fixture() -> pathlib.Path:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="mw_fixture_"))
    # 最小仓库骨架：一个技能 + references + 流程权威文件
    skill = tmp / "skills" / "moshu-test"
    refs = skill / "references"
    refs.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: moshu-test\ndescription: fixture 技能\n---\n", encoding="utf-8")
    # 流程权威文件（workflow-outline 路径）
    wo = tmp / "skills" / "moshu-outline" / "references"
    wo.mkdir(parents=True)
    (tmp / "skills" / "moshu-outline" / "SKILL.md").write_text("---\nname: moshu-outline\ndescription: fixture\n---\n", encoding="utf-8")
    # 三态方法论文件
    (refs / "dead-method.md").write_text("# DEAD 样例\n零流程引用。\n", encoding="utf-8")
    (refs / "must-method.md").write_text("# MUST 样例\n", encoding="utf-8")
    # 白名单样例：直接建在 ALLOWED_DEAD 的 quality-rubric 路径（moshu-review/references/）
    qr = tmp / "skills" / "moshu-review" / "references"
    qr.mkdir(parents=True)
    (tmp / "skills" / "moshu-review" / "SKILL.md").write_text("---\nname: moshu-review\ndescription: fixture\n---\n", encoding="utf-8")
    (qr / "quality-rubric.md").write_text("# 白名单 DEAD 样例\n", encoding="utf-8")
    # 权威文件：MUST 引用
    (wo / "workflow-outline.md").write_text(
        "骨架构建前必读 must-method.md（必读）\n", encoding="utf-8"
    )
    return tmp


def run(root: pathlib.Path) -> int:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)],
        capture_output=True,
        text=True,
    ).returncode


def main() -> int:
    tmp = make_fixture()
    try:
        # 1. 初始 fixture：dead-method DEAD（非白名单）→ blocking（exit 1）
        rc = run(tmp)
        assert rc == 1, f"fixture 应 blocking（DEAD 存在），实际 exit={rc}"

        # 2. 移除 dead-method → 仅 MUST + 白名单 DEAD → 通过（exit 0）
        (tmp / "skills" / "moshu-test" / "references" / "dead-method.md").unlink()
        rc = run(tmp)
        assert rc == 0, f"MUST + 白名单 DEAD 应通过，实际 exit={rc}"

        # 3. 再确认：移除白名单文件 → 无 DEAD 无 MUST → 通过（空 references 也 OK）
        (tmp / "skills" / "moshu-review" / "references" / "quality-rubric.md").unlink()
        rc = run(tmp)
        assert rc == 0, "仅 MUST 通过态 exit 应 0"
        print("test_methodology_wiring: OK (三态：DEAD blocking / MUST 通过 / 白名单通过)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

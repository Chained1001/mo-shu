#!/usr/bin/env python3
"""test-bump-agents-version.py — bump-agents-version.py 正式回归测试

守护对象：agents_version 确定性 bump 脚本（B23；审计-setup-v1 需修 1：阈值形态覆盖 + 历史条目防误伤）——
六类文件全覆盖（SKILL.md 反引号+无反引号/current-contract.json/session-start.sh 比较值+措辞/
deploy-manual.md 声明+阈值形态/deploy.py 常量/UPGRADING.md 版本头+步骤行+阈值形态）、
历史条目排除（含「变更」行即使带版本数字也不动）、--confirm 替换、守卫失败回滚（不留半改状态）。
禁：断言实现细节/真实上游；fixture 自清理。
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bump-agents-version.py"
PY = sys.executable

SKILL_SAMPLE = """---
name: moshu
version: 1.3.0
---
> Spawn 版本提示：与本版 `agents_version: 33` 不一致时（小于或大于 33）报告 Notice（本版 33）；大于 30 时额外提示先更新。
"""
SETUP_SKILL_SAMPLE = """---
name: moshu-setup
version: 1.5.1
---
- `agents_version` 缺失、非整数或小于 `33` → 标记为待更新
- `agents_version` 大于 `33` → 停止
- setup_skill_version: 1.5.1
"""
HOOK_SAMPLE = """if [ "$AGENTS_VERSION" -lt 33 ]; then
  OUTPUT+="低于 v33。重新运行 /moshu-setup"
elif [ "$AGENTS_VERSION" -gt 33 ]; then
  OUTPUT+="高于本 hook 支持的 v33。"
fi
"""
DEPLOY_SAMPLE = """验证部署标记：`agents_version: 33` 与 setup_skill_version: 1.5.1
- `.story-deployed` 含 `agents_version: 33`
- `agents_version` 缺失、非整数或小于 `33` → 提示更新
- `agents_version` 大于 `33` → 停止
- setup_skill_version: 1.5.1
"""
UPGRADING_SAMPLE = """## 当前版本
- `agents_version: 33`
- setup_skill_version: 1.5.1

`.story-deployed` 缺失任一字段，或 `agents_version` 缺失 / 非整数 / 小于 `33`，都视为待更新部署。如项目 `agents_version` 大于 `33`，说明本地 moshu-setup 比项目旧：先更新 mo-shu，不得用 v33 降级覆盖。

**v32 → v33 变更**：历史条目（含 agents_version 引用与小于 `33` 阈值都不得动）。
**v31 → v32 变更**：更早条目。
"""
DEPLOY_PY_SAMPLE = """DEFAULT_AGENTS_VERSION = '33'
DEFAULT_SETUP_VERSION = '1.5.1'
# CLI 帮助
[--agents-version 33] [--setup-version 1.5.1] [--dry-run]
"""


def make_fixture(tmp: Path) -> Path:
    project = tmp / "fixture"
    (project / "scripts").mkdir(parents=True)
    (project / "skills/moshu").mkdir(parents=True)
    (project / "skills/moshu-setup/references/templates/hooks").mkdir(parents=True)
    (project / "skills/moshu-setup/references").mkdir(parents=True, exist_ok=True)
    (project / "skills/moshu-setup/scripts").mkdir(parents=True, exist_ok=True)
    (project / "scripts/current-contract.json").write_text(
        json.dumps({"agents_version": 33, "setup_skill_version": "1.5.1"}), encoding="utf-8")
    (project / "skills/moshu/SKILL.md").write_text(SKILL_SAMPLE, encoding="utf-8")
    (project / "skills/moshu-setup/SKILL.md").write_text(SETUP_SKILL_SAMPLE, encoding="utf-8")
    (project / "skills/moshu-setup/references/templates/hooks/session-start.sh").write_text(HOOK_SAMPLE, encoding="utf-8")
    (project / "skills/moshu-setup/references/deploy-manual.md").write_text(DEPLOY_SAMPLE, encoding="utf-8")
    (project / "skills/moshu-setup/scripts/deploy.py").write_text(DEPLOY_PY_SAMPLE, encoding="utf-8")
    (project / "skills/moshu-setup/UPGRADING.md").write_text(UPGRADING_SAMPLE, encoding="utf-8")
    return project


def run_bump(project: Path, new_ver: str, guard_cmd: list[str] | None, confirm: bool = True) -> int:
    cmd = [PY, str(SCRIPT), new_ver, "--root", str(project), "--guard-root", str(project)]
    if confirm:
        cmd.append("--confirm")
    if guard_cmd is not None:
        cmd += ["--guard-command", " ".join(guard_cmd)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return r.returncode


def run_bump_setup(project: Path, old_setup: str, new_setup: str, guard_cmd: list[str] | None, confirm: bool = True) -> int:
    cmd = [PY, str(SCRIPT), "--setup-version", old_setup, new_setup, "--root", str(project), "--guard-root", str(project)]
    if confirm:
        cmd.append("--confirm")
    if guard_cmd is not None:
        cmd += ["--guard-command", " ".join(guard_cmd)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return r.returncode


def test_preview_no_change(project: Path) -> None:
    code = run_bump(project, "33", None, confirm=False)
    assert code == 0, f"当前值=33 bump 33 应无 diff 退出 0，实得 {code}"


def test_bump_all_six(project: Path) -> None:
    # 恒绿守卫 → 替换成功
    code = run_bump(project, "34", [PY, "-c", "exit(0)"])
    assert code == 0, f"bump 34 应成功，实得 {code}"
    cc = json.loads((project / "scripts/current-contract.json").read_text(encoding="utf-8"))
    assert cc["agents_version"] == 34, f"current-contract 应 34: {cc}"
    sk = (project / "skills/moshu/SKILL.md").read_text(encoding="utf-8")
    assert "`agents_version: 34`" in sk and "大于 34" in sk, f"SKILL 反引号+无反引号应替换: {sk}"
    setup = (project / "skills/moshu-setup/SKILL.md").read_text(encoding="utf-8")
    assert "小于 `34`" in setup and "大于 `34`" in setup, f"setup SKILL 判定门应替换: {setup}"
    hook = (project / "skills/moshu-setup/references/templates/hooks/session-start.sh").read_text(encoding="utf-8")
    assert "-lt 34" in hook and "-gt 34" in hook and "低于 v34" in hook and "高于本 hook 支持的 v34" in hook, f"hook 应替换: {hook}"
    deploy = (project / "skills/moshu-setup/references/deploy-manual.md").read_text(encoding="utf-8")
    assert deploy.count("agents_version: 34") == 2 and "agents_version: 33" not in deploy, f"deploy-manual 应全替换: {deploy}"
    assert "小于 `34`" in deploy and "大于 `34`" in deploy and "小于 `33`" not in deploy, f"deploy-manual 阈值形态应替换: {deploy}"
    up = (project / "skills/moshu-setup/UPGRADING.md").read_text(encoding="utf-8")
    assert "- `agents_version: 34`" in up, f"UPGRADING 版本头应替换: {up}"
    assert "小于 `34`" in up and "大于 `34`" in up and "不得用 v34" in up, f"UPGRADING 阈值形态应替换: {up}"
    assert "v32 → v33 变更" in up and "v31 → v32 变更" in up, f"UPGRADING 历史条目不得动: {up}"
    assert "小于 `33` 阈值都不得动" in up, f"UPGRADING 变更行内阈值防误伤: {up}"


def test_rollback_on_guard_fail(project: Path) -> None:
    # 守卫必红 → 替换后回滚 → 文件还原替换前值（33）
    code = run_bump(project, "34", [PY, "-c", "exit(1)"])
    assert code == 1, f"守卫红应退出 1，实得 {code}"
    cc = json.loads((project / "scripts/current-contract.json").read_text(encoding="utf-8"))
    assert cc["agents_version"] == 33, f"回滚后 current-contract 应还原 33: {cc}"
    sk = (project / "skills/moshu/SKILL.md").read_text(encoding="utf-8")
    assert "agents_version: 33" in sk and "agents_version: 34" not in sk, f"回滚后 SKILL 应还原: {sk}"
    hook = (project / "skills/moshu-setup/references/templates/hooks/session-start.sh").read_text(encoding="utf-8")
    assert "-lt 33" in hook, f"回滚后 hook 应还原: {hook}"


def test_bump_setup_only(project: Path) -> None:
    # B24：--setup-version 独立轨，6 处全覆盖（守卫恒绿 → 替换成功）；agents_version 不动
    code = run_bump_setup(project, "1.5.1", "1.6.0", [PY, "-c", "exit(0)"])
    assert code == 0, f"setup bump 1.5.1→1.6.0 应成功，实得 {code}"
    cc = json.loads((project / "scripts/current-contract.json").read_text(encoding="utf-8"))
    assert cc["setup_skill_version"] == "1.6.0", f"contract setup 应 1.6.0: {cc}"
    assert cc["agents_version"] == 33, f"agents_version 不应被 setup bump 联动: {cc}"
    sk = (project / "skills/moshu-setup/SKILL.md").read_text(encoding="utf-8")
    assert "version: 1.6.0" in sk and "setup_skill_version: 1.6.0" in sk and "version: 1.5.1" not in sk, f"SKILL setup 应替换: {sk}"
    dp = (project / "skills/moshu-setup/scripts/deploy.py").read_text(encoding="utf-8")
    assert "DEFAULT_SETUP_VERSION = '1.6.0'" in dp and "--setup-version 1.6.0" in dp and "1.5.1" not in dp, f"deploy.py setup 应替换: {dp}"
    dm = (project / "skills/moshu-setup/references/deploy-manual.md").read_text(encoding="utf-8")
    assert dm.count("setup_skill_version: 1.6.0") == 2 and "setup_skill_version: 1.5.1" not in dm, f"deploy-manual 应两处替换: {dm}"
    up = (project / "skills/moshu-setup/UPGRADING.md").read_text(encoding="utf-8")
    assert "setup_skill_version: 1.6.0" in up and "setup_skill_version: 1.5.1" not in up, f"UPGRADING 应替换: {up}"


def test_setup_rollback_on_guard_fail(project: Path) -> None:
    # B24：setup 守卫红 → 替换后回滚 → 6 处还原
    code = run_bump_setup(project, "1.5.1", "1.6.0", [PY, "-c", "exit(1)"])
    assert code == 1, f"setup 守卫红应退出 1，实得 {code}"
    cc = json.loads((project / "scripts/current-contract.json").read_text(encoding="utf-8"))
    assert cc["setup_skill_version"] == "1.5.1", f"回滚后 contract 应还原 1.5.1: {cc}"
    dp = (project / "skills/moshu-setup/scripts/deploy.py").read_text(encoding="utf-8")
    assert "DEFAULT_SETUP_VERSION = '1.5.1'" in dp and "1.6.0" not in dp, f"回滚后 deploy.py 应还原: {dp}"


def main() -> None:
    work = ROOT / ".tmp" / "tests" / "B23work"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    try:
        p1 = make_fixture(work)
        test_preview_no_change(p1)
        test_bump_all_six(p1)
        p2 = make_fixture(work / "second")
        test_rollback_on_guard_fail(p2)
        p_setup = make_fixture(work / "setup")
        test_bump_setup_only(p_setup)
        p_setup2 = make_fixture(work / "setup2")
        test_setup_rollback_on_guard_fail(p_setup2)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("OK: bump-agents-version (预览无diff 0 / agents 六类全替换 / setup 六处独立轨 / 历史条目不动 / 守卫红回滚还原[agents+setup])")


if __name__ == "__main__":
    main()

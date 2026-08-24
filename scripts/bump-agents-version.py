#!/usr/bin/env python3
"""bump-agents-version.py — agents_version 确定性 bump 脚本（替代手工 grep+replace）

守护对象：agents_version 字面量六类文件全覆盖（观察 024 五层散射教训：CI 连续三笔修复）。
六类文件与格式（正则覆盖反引号/无反引号/JSON 数字/shell 比较值四种格式）：
  1. skills/**/SKILL.md（Spawn 版本提示段）：反引号 `33` + 无反引号 "33 时额外" 两种格式
  2. scripts/current-contract.json：JSON 数字（agents_version 字段）
  3. skills/moshu-setup/SKILL.md：部署判定门反引号 `33`
  4. skills/moshu-setup/references/templates/hooks/session-start.sh：-lt 33 / -gt 33 / 低于 v33 / 高于 v33
  5. skills/moshu-setup/references/deploy-manual.md：agents_version: 33 反引号/无反引号
  6. skills/moshu-setup/scripts/deploy.py：DEFAULT_AGENTS_VERSION 常量 + CLI 帮助
  6. skills/moshu-setup/UPGRADING.md：版本头 agents_version: 33 + 升级步骤行——**排除历史条目**（含「变更」关键词的行不动）

不动：marketplace.json / SKILL.md frontmatter version（插件版本独立轨，本脚本只管 agents_version）。
流程：读 current-contract 取当前值 → grep 六类文件 → diff 预览 → --confirm 替换（临时备份）→ 三守卫
（check-current-skill-contracts / check-moshu-setup-deployment / check-agents-version-sync）→ 全绿提示完成；
有红 → 从备份还原 → 报错退出（不留半改状态）。
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

CHANGE_KEYWORD = "变更"


def read_current(contract_path: Path) -> int:
    data = json.loads(contract_path.read_text(encoding="utf-8"))
    value = data.get("agents_version")
    if not isinstance(value, int):
        raise SystemExit(f"ERROR: current-contract.json 缺合法 agents_version（{value!r}）")
    return value


def skill_patterns(old: int, new: int) -> list[tuple[re.Pattern, str]]:
    return [
        (re.compile(rf"`agents_version: {old}`"), f"`agents_version: {new}`"),  # Spawn 提示段反引号版
        (re.compile(rf"`{old}`"), f"`{new}`"),  # setup 判定门 `33`
        (re.compile(rf"小于或大于 {old}"), f"小于或大于 {new}"),
        (re.compile(rf"本版 {old}"), f"本版 {new}"),
        (re.compile(rf"(?<![\d`]){old}(?= 时额外)"), str(new)),  # "33 时额外"
    ]


def hook_patterns(old: int, new: int) -> list[tuple[re.Pattern, str]]:
    return [
        (re.compile(rf"-lt {old}"), f"-lt {new}"),
        (re.compile(rf"-gt {old}"), f"-gt {new}"),
        (re.compile(rf"低于 v{old}"), f"低于 v{new}"),
        (re.compile(rf"高于本 hook 支持的 v{old}"), f"高于本 hook 支持的 v{new}"),
    ]


def collect_edits(root: Path, old: int, new: int) -> list[tuple[Path, int, str, str]]:
    """返回 [(文件, 行号, 匹配字面串, 替换串)]——UPGRADING 历史条目（含「变更」行）排除。"""
    edits: list[tuple[Path, int, str, str]] = []
    skills = sorted((root / "skills").glob("*/SKILL.md"))
    for sk in skills:
        lines = sk.read_text(encoding="utf-8").splitlines()
        for line_no, line in enumerate(lines, start=1):
            for pat, rep in skill_patterns(old, new):
                for m in pat.finditer(line):
                    edits.append((sk, line_no, m.group(0), m.group(0).replace(str(old), str(new))))
    # current-contract.json
    cc = root / "scripts" / "current-contract.json"
    if cc.exists():
        for line_no, line in enumerate(cc.read_text(encoding="utf-8").splitlines(), start=1):
            for m in re.finditer(rf'"agents_version"\s*:\s*{old}(?=\s*[,}}])', line):
                edits.append((cc, line_no, m.group(0), m.group(0).replace(str(old), str(new))))
    # session-start.sh
    hook = root / "skills" / "moshu-setup" / "references" / "templates" / "hooks" / "session-start.sh"
    if hook.exists():
        for line_no, line in enumerate(hook.read_text(encoding="utf-8").splitlines(), start=1):
            for pat, rep in hook_patterns(old, new):
                for m in pat.finditer(line):
                    edits.append((hook, line_no, m.group(0), m.group(0).replace(str(old), str(new))))
    # deploy-manual.md（agents_version: 33 反引号/无反引号）
    dm = root / "skills" / "moshu-setup" / "references" / "deploy-manual.md"
    if dm.exists():
        for line_no, line in enumerate(dm.read_text(encoding="utf-8").splitlines(), start=1):
            for m in re.finditer(rf"`?agents_version: {old}`?", line):
                edits.append((dm, line_no, m.group(0), m.group(0).replace(str(old), str(new))))
    # deploy.py（DEFAULT_AGENTS_VERSION / DEFAULT_SETUP_VERSION 常量 + CLI 帮助）
    dp = root / "skills" / "moshu-setup" / "scripts" / "deploy.py"
    if dp.exists():
        for line_no, line in enumerate(dp.read_text(encoding="utf-8").splitlines(), start=1):
            # agents_version 常量与 CLI 帮助
            for m in re.finditer(rf"(DEFAULT_AGENTS_VERSION = '{old}'|--agents-version {old})", line):
                edits.append((dp, line_no, m.group(0), m.group(0).replace(str(old), str(new))))
            # setup_skill_version（独立轨：old_setup → new_setup 由调用方传入，此处用 agents_version 同步推算不适用——setup 版本独立变化，不跟 agents_version 联动，bump 脚本只管 agents_version）
    # UPGRADING.md 版本头 + 升级步骤行（排除含「变更」的历史条目行）
    up = root / "skills" / "moshu-setup" / "UPGRADING.md"
    if up.exists():
        for line_no, line in enumerate(up.read_text(encoding="utf-8").splitlines(), start=1):
            if CHANGE_KEYWORD in line:
                continue
            for m in re.finditer(rf"`?agents_version: {old}`?", line):
                edits.append((up, line_no, m.group(0), m.group(0).replace(str(old), str(new))))
    return edits


def preview(root: Path, old: int, new: int) -> list[tuple[str, str, str]]:
    return [
        (f"{path.relative_to(root).as_posix()}:{line_no}", old_s, new_s)
        for path, line_no, old_s, new_s in collect_edits(root, old, new)
    ]


def run_guards(guard_root: Path, guard_command: list[list[str]] | None) -> bool:
    if guard_command is None:
        guard_command = [
            [sys.executable, str(guard_root / "scripts" / "check-current-skill-contracts.py"), "--repo-root", str(guard_root)],
            [sys.executable, str(guard_root / "scripts" / "check-agents-version-sync.py"), "--root", str(guard_root)],
            ["bash", str(guard_root / "scripts" / "check-moshu-setup-deployment.sh")],
        ]
    for cmd in guard_command:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            print(f"  [守卫红] {' '.join(cmd)}\n{r.stdout}\n{r.stderr}", file=sys.stderr)
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("new_version", type=int, help="目标 agents_version（如 34）")
    parser.add_argument("--confirm", action="store_true", help="确认执行替换（默认仅预览）")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="仓库根（测试用 fixture 根）")
    parser.add_argument("--guard-root", type=Path, default=None, help="守卫运行根（默认=--root）")
    parser.add_argument("--guard-command", type=str, default=None, help="守卫命令覆盖（空格分隔字符串，测试用）")
    args = parser.parse_args()

    root = args.root.resolve()
    guard_root = (args.guard_root or root).resolve()
    guard_cmd: list[list[str]] | None = None
    if args.guard_command:
        guard_cmd = [shlex.split(args.guard_command, posix=False)]
    contract_path = root / "scripts" / "current-contract.json"
    if not contract_path.exists():
        print(f"ERROR: {contract_path} 不存在", file=sys.stderr)
        return 2
    current = read_current(contract_path)
    if args.new_version <= current:
        print(f"新版本 {args.new_version} 不大于当前 {current}——无 diff，退出 0")
        return 0

    rows = preview(root, current, args.new_version)
    if not rows:
        print(f"未发现当前版本 {current} 的字面量（六类文件零命中）——检查是否已 bump 或版本漂移")
        return 1
    print(f"agents_version {current} → {args.new_version}（{len(rows)} 处，六类文件）")
    for rel, old_s, new_s in rows:
        print(f"  {rel}: {old_s} → {new_s}")

    if not args.confirm:
        print("预览模式（未改动）。加 --confirm 执行替换+守卫。")
        return 0

    # 执行替换（临时备份，失败回滚）
    backup = Path(tempfile.mkdtemp(prefix="bump_backup_"))
    try:
        edits = collect_edits(root, current, args.new_version)
        touched: dict[Path, str] = {}
        for path in {e[0] for e in edits}:
            text = path.read_text(encoding="utf-8")
            touched[path] = text
            new_text = text
            for p, _ln, old_s, new_s in edits:
                if p == path:
                    new_text = new_text.replace(old_s, new_s)
            if new_text != text:
                path.write_text(new_text, encoding="utf-8")
        # 备份（用于回滚）
        for path, original in touched.items():
            rel = path.relative_to(root)
            dest = backup / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(original, encoding="utf-8")

        if not run_guards(guard_root, guard_cmd):
            for path, original in touched.items():
                path.write_text(original, encoding="utf-8")
            print("守卫有红——已回滚全部替换，未留半改状态。", file=sys.stderr)
            return 1

        print("bump 完成（守卫全绿），可提交。")
        return 0
    finally:
        shutil.rmtree(backup, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""正反向 fixture 回归：check-story-numbers.py 的计数守卫行为。

守护对象：check-story-numbers 叙述计数守卫的正反向行为。禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。

正向：临时仓库 2 个 skill + README 写「2 个 skill」→ 退出 0。
反向：README 写「3 个 skill」→ 退出 1 且报文含文件名。
反向 2：英文「5 skills」→ 退出 1。
fixture 全部在 tempfile 临时目录，测试自清理，不留 .tmp。
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("check-story-numbers.py")


def make_repo(root: Path, skills: int, readme_text: str) -> None:
    skills_dir = root / "skills"
    skills_dir.mkdir(parents=True)
    for i in range(skills):
        skill_dir = skills_dir / f"skill-{i}"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(f"# skill {i}\n", encoding="utf-8")
    (root / "README.md").write_text(readme_text, encoding="utf-8")


def run(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def main() -> int:
    failures = 0
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)

        # 正向：数字与实测一致 → exit 0
        pos = base / "pos"
        pos.mkdir()
        make_repo(pos, 2, "本项目有 2 个 skill 覆盖全流程。\n")
        result = run(pos)
        if result.returncode != 0:
            failures += 1
            print(f"FAIL 正向: 期望退出 0，实际 {result.returncode}")
            print(result.stdout, end="")
            print(result.stderr, end="")
        else:
            print("PASS 正向（2 个 skill → 退出 0）")

        # 反向：中文数字不一致 → exit 1 且报文含文件名
        rev = base / "rev"
        rev.mkdir()
        make_repo(rev, 2, "本项目有 3 个 skill 覆盖全流程。\n")
        result = run(rev)
        if result.returncode != 1 or "README.md" not in result.stdout:
            failures += 1
            print(f"FAIL 反向: 期望退出 1 且报文含 README.md，实际 {result.returncode}")
            print(result.stdout, end="")
            print(result.stderr, end="")
        else:
            print("PASS 反向（3 个 skill → 退出 1 且指向 README.md）")

        # 反向 2：英文数字不一致 → exit 1 且报文含文件名
        rev_en = base / "rev-en"
        rev_en.mkdir()
        make_repo(rev_en, 2, "This pack ships 5 skills for the pipeline.\n")
        result = run(rev_en)
        if result.returncode != 1 or "README.md" not in result.stdout:
            failures += 1
            print(f"FAIL 反向2: 期望退出 1 且报文含 README.md，实际 {result.returncode}")
            print(result.stdout, end="")
            print(result.stderr, end="")
        else:
            print("PASS 反向2（5 skills → 退出 1 且指向 README.md）")

    if failures:
        print(f"{failures} failure(s)")
        return 1
    print("all story-number regression tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""正反向 fixture 回归：check-route-write.py 的路由残留守卫行为（批B8 四用例）。

守护对象：check-route-write 两级判定的正反向行为（blocking 退出 1 / 白名单过 / 未知 candidate 退出 0 / 无表格行过）。禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。

四用例（规格 §4）：
① 白名单行（继续写作）→ 退出 0；
② blocking 行（准备开书）→ 退出 1 且报文含文件名；
③ 未知语境行（随便干点什么）→ 打印 [candidate] 但退出 0；
④ 无表格行文件 → 退出 0。
fixture 全部在 tempfile 临时目录，测试自清理，不留 .tmp。
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("check-route-write.py")


def make_repo(root: Path, body: str) -> None:
    skills_dir = root / "skills" / "skill-0"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text(body, encoding="utf-8")


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

        # ① 白名单行 → 退出 0
        wl = base / "wl"
        wl.mkdir()
        make_repo(wl, "# skill 0\n\n| 继续写作 | moshu-write | `/moshu-write` |\n")
        result = run(wl)
        if result.returncode != 0 or "ok" not in result.stdout:
            failures += 1
            print(f"FAIL ①: 白名单行应退出 0 且 ok，实际 {result.returncode}")
            print(result.stdout, end="")
            print(result.stderr, end="")
        else:
            print("PASS ①（继续写作 → 白名单过，退出 0）")

        # ② blocking 行 → 退出 1 且报文含文件名
        bl = base / "bl"
        bl.mkdir()
        make_repo(bl, "# skill 0\n\n| 准备开书 | moshu-write | `/moshu-write` |\n")
        result = run(bl)
        if result.returncode != 1 or "SKILL.md" not in result.stdout:
            failures += 1
            print(f"FAIL ②: blocking 行应退出 1 且指向 SKILL.md，实际 {result.returncode}")
            print(result.stdout, end="")
            print(result.stderr, end="")
        else:
            print("PASS ②（准备开书 → blocking 退出 1 且指向 SKILL.md）")

        # ③ 未知语境行 → [candidate] 打印但退出 0
        ca = base / "ca"
        ca.mkdir()
        make_repo(ca, "# skill 0\n\n| 随便干点什么 | moshu-write | `/moshu-write` |\n")
        result = run(ca)
        if result.returncode != 0 or "[candidate]" not in result.stdout or "SKILL.md" not in result.stdout:
            failures += 1
            print(f"FAIL ③: 未知语境应 candidate 且退出 0，实际 {result.returncode}")
            print(result.stdout, end="")
            print(result.stderr, end="")
        else:
            print("PASS ③（随便干点什么 → [candidate] 呈报且退出 0）")

        # ④ 无表格行文件 → 退出 0
        nt = base / "nt"
        nt.mkdir()
        make_repo(nt, "# skill 0\n\n纯正文段落，没有任何表格行。\n")
        result = run(nt)
        if result.returncode != 0:
            failures += 1
            print(f"FAIL ④: 无表格行应退出 0，实际 {result.returncode}")
            print(result.stdout, end="")
            print(result.stderr, end="")
        else:
            print("PASS ④（无表格行 → 过，退出 0）")

    if failures:
        print(f"{failures} failure(s)")
        return 1
    print("all route-write regression tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

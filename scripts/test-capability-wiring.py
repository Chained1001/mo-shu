#!/usr/bin/env python3
"""正反向回归：check-capability-wiring 的能力接线守卫。

守护对象：capability-wiring.json 的 producer→consumer 接线断言。禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。
- 正向：真仓库全部能力接线在位；
- 反向：fixture 删一个调用点标记必须失败且指向能力 id 与文件。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts/check-capability-wiring.py"
MANIFEST = "scripts/capability-wiring.json"


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GUARD), "--root", str(root)],
        text=True,
        capture_output=True,
        check=False,
        encoding="utf-8",
    )


def main() -> int:
    fails = 0

    result = run(ROOT)
    if result.returncode != 0:
        print("FAIL: 真仓库能力接线检查未通过")
        print(result.stderr)
        fails += 1

    # 反向：fixture 复制最小仓库（全部 consumer 文件），破坏第一个 consumer 的调用点标记
    with tempfile.TemporaryDirectory(prefix="cap-wiring-") as tmp:
        root = Path(tmp)
        data = json.loads((ROOT / MANIFEST).read_text(encoding="utf-8"))
        (root / "scripts").mkdir(parents=True)
        shutil.copy2(ROOT / MANIFEST, root / MANIFEST)
        seen: set[str] = set()
        for capability in data["capabilities"]:
            for entry in capability["consumers"]:
                relative = entry["file"]
                if relative in seen:
                    continue
                seen.add(relative)
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, target)
        first = data["capabilities"][0]
        consumer = first["consumers"][0]
        relative = consumer["file"]
        needle = consumer["must_contain"]
        target = root / relative
        text = target.read_text(encoding="utf-8")
        assert needle in text, f"fixture 前提失败：{relative} 缺 {needle!r}"
        target.write_text(text.replace(needle, "WIRING_TEST_BROKEN", -1), encoding="utf-8")

        result = run(root)
        if result.returncode == 0:
            print("FAIL: 破坏调用点后检查仍通过（应失败）")
            fails += 1
        elif first["id"] not in result.stderr or relative not in result.stderr:
            print("FAIL: 失败信息未指向能力 id 与被破坏文件")
            print(result.stderr)
            fails += 1

    if fails:
        print(f"Capability-wiring tests FAILED ({fails}).")
        return 1
    print("Capability-wiring regression tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

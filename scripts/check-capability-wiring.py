#!/usr/bin/env python3
"""能力接线守卫：断言 capability-wiring.json 里每个 consumer 文件含调用点标记。

守护对象：确定性能力「producer→consumer」调用链的完整性。禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。
定位（审计-V3 D1）：behavior-contracts 锁「话在不在」，本守卫锁「链通不通」——脚本层建好的能力
若流程文档从不指示使用（接线缺口），本守卫立刻变红。新增能力：先登记本表再写实现；删除能力：同步清本表。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "scripts/capability-wiring.json"


def check(root: Path, manifest_path: str) -> tuple[list[str], int, int]:
    failures: list[str] = []
    manifest_file = root / manifest_path
    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"manifest 不可读: {error}"], 0, 0

    capabilities = data.get("capabilities")
    if not isinstance(capabilities, list):
        return ["manifest.capabilities must be an array"], 0, 0

    consumer_count = 0
    checked = 0
    for capability in capabilities:
        cap_id = capability.get("id")
        if not isinstance(cap_id, str) or not cap_id:
            failures.append("capability entry missing string id")
            continue
        consumers = capability.get("consumers")
        if not isinstance(consumers, list) or not consumers:
            failures.append(f"{cap_id}: consumers must be a non-empty array")
            continue
        seen_files: set[str] = set()
        for entry in consumers:
            if not isinstance(entry, dict):
                failures.append(f"{cap_id}: consumer entry must be an object")
                continue
            relative = entry.get("file")
            needle = entry.get("must_contain")
            if not isinstance(relative, str) or not isinstance(needle, str) or not needle:
                failures.append(f"{cap_id}: consumer needs string file + must_contain")
                continue
            if relative in seen_files:
                continue  # 同一文件的多条约束只读一次，去重计数
            seen_files.add(relative)
            consumer_count += 1
            path = root / relative
            if not path.is_file():
                failures.append(f"{cap_id}: consumer 文件不存在: {relative}")
                continue
            text = path.read_text(encoding="utf-8")
            if needle not in text:
                failures.append(f"{cap_id}: {relative} 缺调用点标记 {needle!r}")
            checked += 1
    return failures, len(capabilities), consumer_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(REPO_ROOT), help="仓库根目录（测试用 fixture 根）")
    args = parser.parse_args()
    root = Path(args.root)

    failures, capability_count, consumer_count = check(root, MANIFEST)
    if failures:
        print(f"能力接线守卫失败（{len(failures)} 处）：", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1

    print(f"能力接线守卫通过：{capability_count} 个能力、{consumer_count} 个消费点全部接线")
    return 0


if __name__ == "__main__":
    sys.exit(main())

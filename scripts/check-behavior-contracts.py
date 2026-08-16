#!/usr/bin/env python3
"""行为契约静态守卫：关键行为约束文本必须存在于对应文档。

mo-shu 是文档驱动的 skill 包，写作行为由 SKILL.md / workflow-*.md 的约束文本承载。
本守卫把最关键的行为承诺固化为静态检查，约束文本被误删/弱化即失败，防止迭代导致行为漂移。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACTS = REPO_ROOT / "scripts" / "behavior-contracts.json"


def load_contracts(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError(f"不支持的契约 schema_version: {data.get('schema_version')}")
    contracts = data.get("contracts")
    if not isinstance(contracts, list) or not contracts:
        raise ValueError("contracts 必须是非空数组")
    for contract in contracts:
        for key in ("id", "path", "must_contain"):
            if not isinstance(contract.get(key), str) or not contract[key]:
                raise ValueError(f"契约缺少非空字段 {key}: {contract}")
        raw_path = contract["path"]
        if Path(raw_path).is_absolute() or ".." in Path(raw_path).parts:
            raise ValueError(f"契约 path 必须是 root 内相对路径（禁止绝对路径/..）: {raw_path}")
    return contracts


def check(root: Path, contracts: list[dict[str, str]]) -> list[str]:
    failures: list[str] = []
    for contract in contracts:
        target = root / contract["path"]
        if not target.exists():
            failures.append(
                f"[{contract['id']}] 文件缺失: {contract['path']}（{contract['rationale']}）"
            )
            continue
        text = target.read_text(encoding="utf-8")
        if contract["must_contain"] not in text:
            failures.append(
                f"[{contract['id']}] 约束丢失: {contract['path']} 必须包含「{contract['must_contain']}」"
                f"（{contract['rationale']}）"
            )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(REPO_ROOT), help="仓库根目录（测试用 fixture 根）")
    parser.add_argument("--contracts", default=str(DEFAULT_CONTRACTS), help="契约清单 JSON 路径")
    args = parser.parse_args()

    root = Path(args.root)
    contracts_path = Path(args.contracts)
    try:
        contracts = load_contracts(contracts_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"行为契约守卫失败：无法读取契约清单 {contracts_path}: {error}", file=sys.stderr)
        return 1

    failures = check(root, contracts)
    if failures:
        print("行为契约守卫失败（关键行为约束缺失/丢失）：", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1

    print(f"行为契约守卫通过：{len(contracts)} 条约束在位")
    return 0


if __name__ == "__main__":
    sys.exit(main())

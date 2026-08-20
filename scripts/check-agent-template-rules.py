#!/usr/bin/env python3
"""check-agent-template-rules.py — agent 模板纪律静态守卫。

规则 A（禁互引）：模板命中 `格式同|同上|参照上文|见上文` → 违规（spark-arc E2 转译：
两段互斥时 LLM 看不到对方，互引会让规则静默失效）。
规则 B（挂载点存在）：模板中逻辑路径 `agent-references/xxx.md` 引用 → 文件必须存在。
规则 C（单副本）：shared-output-discipline.md 的标题行文本不得出现在任何模板正文
（防共享纪律被复制回模板造成双源漂移）。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TEMPLATES_DIR = "skills/moshu-setup/references/templates/agents"
AGENT_REFERENCES_DIR = "skills/moshu-setup/references/agent-references"
DISCIPLINE_FILE = "shared-output-discipline.md"

FORBIDDEN_REFERENCE = re.compile(r"格式同|同上|参照上文|见上文")
MOUNT_POINT = re.compile(r"agent-references/([\w\-./]+\.md)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=".",
        help="仓库根（默认当前目录；测试可指向临时 fixture 仓库）",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    templates_dir = root / TEMPLATES_DIR
    refs_dir = root / AGENT_REFERENCES_DIR
    if not templates_dir.is_dir():
        print(f"agent template rules: FAIL ({TEMPLATES_DIR} not found under --root)", file=sys.stderr)
        return 1

    discipline_path = refs_dir / DISCIPLINE_FILE
    if not discipline_path.is_file():
        print(f"agent template rules: FAIL ({AGENT_REFERENCES_DIR}/{DISCIPLINE_FILE} missing)", file=sys.stderr)
        return 1
    first_line = discipline_path.read_text(encoding="utf-8").splitlines()[0]
    discipline_title = first_line[2:].strip() if first_line.startswith("# ") else first_line.strip()

    templates = sorted(templates_dir.glob("*.md"))
    violations: list[str] = []
    for template in templates:
        relative = template.relative_to(root)
        for lineno, line in enumerate(template.read_text(encoding="utf-8").splitlines(), 1):
            if FORBIDDEN_REFERENCE.search(line):
                violations.append(f"{relative}:{lineno}: 禁互引：{line.strip()}")
            if discipline_title and discipline_title in line:
                violations.append(f"{relative}:{lineno}: 复制了共享纪律标题（单副本）：{line.strip()}")
            for match in MOUNT_POINT.finditer(line):
                target = refs_dir / match.group(1)
                if not target.is_file():
                    violations.append(
                        f"{relative}:{lineno}: 挂载点缺失 {AGENT_REFERENCES_DIR}/{match.group(1)}：{line.strip()}"
                    )

    if violations:
        print("agent template rules: FAIL")
        for violation in violations:
            print(f"  {violation}")
        return 1
    print(f"agent template rules: ok ({len(templates)} templates)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

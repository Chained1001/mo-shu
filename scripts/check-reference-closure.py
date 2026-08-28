#!/usr/bin/env python3
"""引用可达性守卫（方案 A 资产宇宙）：扫描 skills/*/references/*.md 的 .md 文件名提及。

守护对象：方法论/参考文件提及在其所属 skill 域内可达（跨域合法提及走理由白名单）。
禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。
定位（批B4）：static-check 只扫 Markdown 链接可达性；本守卫补「文件名文本提及」面——
路由表按文件名指引加载，触及的方法论文件不在本 skill 域即断链。
方案 A（2026-08-22 裁决）：只对「提及文件名 ∈ 资产宇宙（全仓 skills/*/references/*.md 的 basename 集合）」
做闭包断言；非资产宇宙提及（书项目运行态产物/占位名/agent 部署路径/子目录资产）直接忽略不报。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# 文件名提及正则：链接、反引号、正文中出现的 x.md 词元都覆盖（[\w\-./]+\.md）。
# lookbehind/lookahead 限缩到 ASCII 路径字符，避免把跨中文连写截成半截。
MD_MENTION_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])(?P<name>[\w\-./]+\.md)(?=$|[^A-Za-z0-9_.-])"
)

# 跨域合法提及白名单（键=提及的文件名 basename，值=理由，每条必须写明为何本域不含仍合法）。
# 批B4 裁决二定稿 5 条：路由表共享文本跨域指引 + write 域执行技法跨域指引。
ALLOWED_CROSS_DOMAIN: dict[str, str] = {
    "volume-review.md": "write 侧卷复盘流程；build 路由表按域指引 write 消费，不属 build 域（批B4 裁决二）",
    "outline-workflow.md": "write 侧细纲工作流；build 大纲安全七检段按域指引 write 消费（批B4 裁决二）",
    "artifact-protocols.md": "write 侧产物模板；B1a 裁决其细纲模板段属 write 域、build 不补副本（批B4 裁决二）",
    "writing-craft.md": "write 域执行技法；build 构建对谈不加载，仅跨域指引（批B4 裁决二）",
    "style-combat-face.md": "write 域文风技法；build 构建对谈不加载，仅跨域指引（批B4 裁决二）",
    # B76 build 拆分（D-B76-1 裁决 E：outline/volume 互为上下游，文件即接口；方法论互引由 9+1 组交叉副本承载导航，提及类走白名单）
    "volume-workflow.md": "volume 侧卷规划流程（Stage 4-6+Phase B）；outline 侧交接指针与对照引用（B76 拆分）",
    "workflow-outline.md": "outline 侧开书流程（Stage 1-3）；volume-workflow 头部交接指针指回（B76 拆分）",
    "caifeng-methods.md": "volume 侧采风手册；outline Stage 1 采风执行细则跨域指引（B76 拆分）",
    "outline-methods.md": "volume 侧大纲方法论路由表；outline 侧结构理论提及（B76 拆分）",
    "plot-special-topics.md": "volume 侧专题方法论；outline 侧 plot-frameworks 交叉引用（B76 拆分）",
    "idea-seed.md": "outline 侧灵感种子；volume outline-methods 路由表提及（B76 拆分）",
    "character-design-methods.md": "outline 侧人物方法论；volume outline-methods 路由表提及（B76 拆分）",
    "character-basics.md": "outline 侧角色基础卡；volume outline-methods/outline-workflow 提及（B76 拆分）",
    "plot-frameworks.md": "outline 侧桥段框架；volume outline-methods 路由表提及（B76 拆分）",
}


def _inside_skill(skill_dir: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(skill_dir.resolve())
        return True
    except ValueError:
        return False


def _mention_resolves_in_skill(skill_dir: Path, file_dir: Path, name: str) -> bool:
    """提及的文件名是否存在于本 skill 域（references/ 直接子项或 skill 根）。"""
    raw = Path(name)
    candidates = (
        file_dir / name,
        skill_dir / name,
        file_dir / raw.name,
        skill_dir / raw.name,
    )
    for candidate in candidates:
        if _inside_skill(skill_dir, candidate) and candidate.is_file():
            return True
    return False


def _asset_universe(root: Path) -> set[str]:
    """资产宇宙：全仓 skills/*/references/*.md 的 basename 集合（方案 A 核心）。"""
    assets: set[str] = set()
    for references_dir in (root / "skills").glob("*/references"):
        assets.update(path.name for path in references_dir.glob("*.md"))
    return assets


def _scan_file(
    path: Path, universe: set[str], skill_dir: Path, file_dir: Path
) -> list[tuple[int, str]]:
    """返回 [(行号, 提及名)]——提及名 ∈ 资产宇宙、未在本域解析、且不在白名单。"""
    text = path.read_text(encoding="utf-8")
    violations: list[tuple[int, str]] = []
    seen: set[tuple[int, str]] = set()
    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in MD_MENTION_RE.finditer(line):
            name = match.group("name")
            base = Path(name).name
            key = (line_no, base)
            if key in seen:
                continue
            seen.add(key)
            if base not in universe:
                continue  # 非资产宇宙（书项目运行态产物/占位名/agent 路径）→ 忽略（方案 A）
            if _mention_resolves_in_skill(skill_dir, file_dir, name):
                continue
            if name in ALLOWED_CROSS_DOMAIN or base in ALLOWED_CROSS_DOMAIN:
                continue
            violations.append((line_no, name))
    return violations


def _references_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for references_dir in sorted((root / "skills").glob("*/references")):
        files.extend(sorted(references_dir.glob("*.md")))
    return files


def check(root: Path) -> tuple[list[str], int]:
    failures: list[str] = []
    checked = 0
    universe = _asset_universe(root)
    for path in _references_files(root):
        checked += 1
        skill_dir = path.parents[1]
        file_dir = path.parent
        for line_no, name in _scan_file(path, universe, skill_dir, file_dir):
            relative = path.relative_to(root)
            failures.append(f"{relative}:{line_no}:{name}")
    return failures, checked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(REPO_ROOT), help="仓库根目录（测试用 fixture 根）")
    args = parser.parse_args()
    root = Path(args.root)

    failures, checked = check(root)
    if failures:
        print(f"引用闭包失败（{len(failures)} 处资产宇宙提及未在本域解析且未白名单）：", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1

    print(f"reference closure: ok ({checked} references files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

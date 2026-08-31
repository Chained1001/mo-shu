#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-methodology-wiring.py — 方法论挂载守卫（批B92）

守护对象：方法论文件必须被流程权威文件挂载，防「库存有接线无」复发（2026-08-31 全量静态盘点：147 文件五级分布 MUST 8/LOAD 53/REF 71/MENTION 12/DEAD 3——触发率 MUST 100%/REF 50%/DEAD 0%）。

强度分级（与静态盘点同口径）：
  MUST（必读/强制）> LOAD（按需/先读/加载/读取）> REF（见/链接/参考）> MENTION（文件名提及）> DEAD（零流程引用）

blocking：方法论文件 DEAD（零流程引用）——新增方法论文件必须 ≥LOAD 才过；
candidate：REF/MENTION 级（建议升级——不拦截，候选语义宪法 §2.7）。
退出码：0=通过（含仅 candidate）/1=blocking。
纯 grep/文件系统，零 LLM 零联网（反模式 #8）；零落盘（只 stdout+退出码）。
"""
import argparse
import json
import pathlib
import re
import sys

AUTHORITY_FILES = [
    # 各技能主 workflow + 正文内核 + 路由 SKILL（挂载引用只认这些文件）
    "skills/moshu-outline/references/workflow-outline.md",
    "skills/moshu-volume/references/volume-workflow.md",
    "skills/moshu-write/references/workflow-daily.md",
    "skills/moshu-write/references/workflow-chapter.md",
    "skills/moshu-write/references/chapter-core.md",
    "skills/moshu-write/references/outline-workflow.md",
    "skills/moshu-volume/references/cold-path.md",
    "skills/moshu-import/references/import-workflow.md",
    "skills/moshu-setup/references/setup-workflow.md",
    "skills/moshu-outline/SKILL.md",
    "skills/moshu-volume/SKILL.md",
    "skills/moshu-write/SKILL.md",
    "skills/moshu-analyze/SKILL.md",
    "skills/moshu-review/SKILL.md",
    "skills/moshu-import/SKILL.md",
    "skills/moshu-scan/SKILL.md",
    "skills/moshu-style/SKILL.md",
    "skills/moshu-deslop/SKILL.md",
    "skills/moshu-cdp/SKILL.md",
    "skills/moshu/SKILL.md",
]

# 已知 DEAD 白名单（理由注释——处置后零 DEAD 是目标，白名单仅临时豁免；删除需作者裁定）
ALLOWED_DEAD = {
    "skills/moshu-review/references/quality-rubric.md": "review 默认评分标准（未指定平台时）；零流程引用待 review-workflow 接线或作者裁定——B92 白名单，禁删禁静默移除",
}

MUST_RE = re.compile(r"必读|强制|必须")
LOAD_RE = re.compile(r"按需|先读|加载|读取|开始前")
REF_RE = re.compile(r"见\s|参考|参照|链接")


def classify(refs: list[str]) -> str:
    for r in refs:
        if MUST_RE.search(r):
            return "MUST"
        if LOAD_RE.search(r):
            return "LOAD"
        if REF_RE.search(r):
            return "REF"
    return "MENTION" if refs else "DEAD"


def scan(root: pathlib.Path) -> tuple[list[dict], list[dict]]:
    authority_texts = []
    for rel in AUTHORITY_FILES:
        p = root / rel
        if p.exists():
            authority_texts.append(p.read_text(encoding="utf-8"))
    authority_blob = "\n".join(authority_texts)

    blocking: list[dict] = []
    candidates: list[dict] = []
    skills_dir = root / "skills"
    for skill_dir in sorted(skills_dir.iterdir()):
        if not (skill_dir / "SKILL.md").exists():
            continue
        refs_dir = skill_dir / "references"
        if not refs_dir.is_dir():
            continue
        for f in sorted(refs_dir.rglob("*.md")):
            rel = f.relative_to(root).as_posix()
            # 排除非方法论目录：子卡/评分卡（genre-prose-cards/rubrics）、部署物（templates）、
            # agent-references 副本（以 source 判定）；流程权威文件自身不作方法论扫描
            if rel in AUTHORITY_FILES:
                continue
            if any(seg in rel for seg in ("/genre-prose-cards/", "/rubrics/", "/templates/", "/agent-references/")):
                continue
            name = f.name
            refs = [line.strip() for line in authority_blob.splitlines() if name in line]
            strength = classify(refs)
            if strength == "DEAD":
                if rel in ALLOWED_DEAD:
                    candidates.append({"file": rel, "level": "DEAD", "note": "白名单豁免", "reason": ALLOWED_DEAD[rel]})
                else:
                    blocking.append({"file": rel, "level": "DEAD", "note": "零流程引用——须升挂载或进流程权威集或白名单"})
            elif strength in ("REF", "MENTION"):
                candidates.append({"file": rel, "level": strength, "note": "建议升级（不拦截）"})
    return blocking, candidates


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="方法论挂载守卫（批B92）")
    parser.add_argument("--root", default=None, help="仓库根（测试用临时 fixture 目录）")
    args = parser.parse_args(argv)
    root = pathlib.Path(args.root).resolve() if args.root else pathlib.Path(__file__).resolve().parent.parent
    blocking, candidates = scan(root)
    print(json.dumps({"blocking": blocking, "candidate": candidates}, ensure_ascii=False, indent=1))
    print(f"Result: {'FAIL' if blocking else 'PASS'} ({len(blocking)} blocking, {len(candidates)} candidate)")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())

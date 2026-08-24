#!/usr/bin/env python3
"""Lexical guards for the single-authority tracking workflow contracts.

守护对象：追踪工作流契约词法守卫。禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_all(text: str, needles: tuple[str, ...], label: str) -> None:
    missing = [needle for needle in needles if needle not in text]
    require(not missing, f"{label} missing contract text: {missing}")


def test_transaction_is_the_only_tracking_writer() -> None:
    for path in (
        # 追踪体积/写入契约自入口下沉后位于 workflow-chapter.md「写前准备契约」节
        "skills/moshu-write/references/workflow-chapter.md",
        "skills/moshu-write/references/workflow-daily.md",
        "skills/moshu-write/references/workflow-revision.md",
        # 拆分后导入的追踪契约承载在 references/import-workflow.md
        "skills/moshu-import/references/import-workflow.md",
        "skills/moshu-review/SKILL.md",
    ):
        require("tracking_commit.py" in read(path), f"{path} must route writes through tracking_commit.py")

    protocol = read("skills/moshu-write/references/tracking-transaction.md")
    require_all(
        protocol,
        (
            "一个结构化权威状态 + 多个确定性派生视图",
            "不分别",
            "_tracking-state.json",
            "唯一提交点",
            "直接重跑**同一份** `commit`",
            "expected_state_revision",
            "完整连续性记录",
            "不是并发锁",
        ),
        "tracking protocol",
    )


def test_authority_model_matches_the_implementation() -> None:
    protocol = read("skills/moshu-write/references/tracking-transaction.md")
    require_all(
        protocol,
        (
            "导入截止章",
            "imported_through_chapter",
            "章节记录",
            "覆盖记录",
            "唯一权威",
            "不承诺单独无损重建",
            "工具不再反向解析 Markdown",
        ),
        "tracking authority model",
    )
    require("基线_截至第N章.md" not in protocol, "tracking protocol still creates a redundant baseline file")
    for path in (
        "skills/moshu-write/references/state-tracking.md",
        "skills/moshu-import/references/state-tracking.md",
        "skills/moshu-write/references/workflow-daily.md",
    ):
        require("core: true" not in read(path), f"{path} still instructs callers to use the removed core field")


def test_failed_commit_retries_the_same_external_transaction() -> None:
    protocol = read("skills/moshu-write/references/tracking-transaction.md")
    require_all(
        protocol,
        (
            "事务 JSON 在成功前必须保留",
            "修正环境后直接重跑**同一份** `commit`",
            "不维护 `dirty/pending/repair` 状态机",
        ),
        "retry contract",
    )


def test_state_card_and_compact_delta_limits_are_explicit() -> None:
    protocol = read("skills/moshu-write/references/tracking-transaction.md")
    require_all(
        protocol,
        (
            "目标 ≤1536 字节，硬上限 3072 字节",
            "目标 ≤4096 字节，超过警告；硬上限 8192 字节",
            "四个列表不限制条数",
            "≤12288 字节",
            "## 当前位置",
            "## 长期约束",
            "## 核心角色状态",
            "## 活跃伏笔",
            "## 近三章速记",
            "## 下一章承诺",
            "## 连贯性风险",
        ),
        "bounded tracking protocol",
    )


def test_import_records_a_cutoff_without_fabricated_old_deltas() -> None:
    # 导入追踪契约自 import 拆分后位于 references/import-workflow.md；SKILL.md 只留索引。
    text = read("skills/moshu-import/SKILL.md") + read("skills/moshu-import/references/import-workflow.md")
    require_all(
        text,
        (
            "imported_through_chapter=N",
            "不得为第 1..N 章伪造逐章",
            "_tracking-state.json",
            "角色状态/{角色名}.md",
            "时间线/读者已知.md",
            "tracking_commit.py init",
        ),
        "moshu-import tracking",
    )
    # 迁移可以描述，但只能「存档旧结构后按当前协议重建」，不得声称解析/转换旧追踪文件。
    require("_旧追踪存档" in text, "moshu-import migration must archive the old tracking structure")
    require(
        "解析旧" not in text and "兼容层" not in text,
        "moshu-import must not claim to parse or convert old tracking structures",
    )


def test_reader_timeline_is_kept_separate_from_author_truth() -> None:
    explorer = read("skills/moshu-setup/references/templates/agents/moshu-explorer.md")
    require_all(
        explorer,
        (
            "未指定时默认 `reader`",
            "读者已知.md",
            "作者真相.md",
            "reader` 结果不得混入 `objective_fact` 中尚未揭示的内容",
        ),
        "moshu-explorer timeline",
    )
    checker = read("skills/moshu-setup/references/templates/agents/moshu-consistency-checker.md")
    require_all(
        checker,
        (
            "用 `作者真相.md` 核对客观时序",
            "用 `读者已知.md` 核对正文是否提前泄露",
            "tracking_commit.py check",
        ),
        "consistency timeline",
    )


def test_review_mutations_are_transactional_and_scoped() -> None:
    # 追踪维护契约自 review 拆分后位于 references/review-workflow.md；SKILL.md 只留索引。
    text = read("skills/moshu-review/SKILL.md") + read("skills/moshu-review/references/review-workflow.md")
    require_all(
        text,
        (
            "full / lean 模式只允许通过该工具修改 `追踪/`",
            "solo 模式不修改任何 `追踪/` 文件",
            "mode=revision",
            "同一 ID `upsert` 当前状态",
            "逐章记录规范且未超限",
            "tracking_commit.py check",
        ),
        "moshu-review tracking maintenance",
    )


def test_retired_tracking_architecture_is_absent() -> None:
    paths = (
        "README.md",
        "README_EN.md",
        "skills/moshu-write/SKILL.md",
        "skills/moshu-write/references/artifact-protocols.md",
        "skills/moshu-write/references/workflow-daily.md",
        "skills/moshu-write/references/workflow-revision.md",
        "skills/moshu-import/SKILL.md",
        "skills/moshu-import/references/structure-mapping-long.md",
        "skills/moshu-review/SKILL.md",
        "skills/moshu-setup/references/templates/CLAUDE.md.tmpl",
        "skills/moshu-setup/references/templates/agents/moshu-explorer.md",
        "skills/moshu-setup/references/templates/rules/story-consistency.md",
    )
    retired = (
        "追踪/阶段摘要.md",
        "追踪/角色状态.md",
        "追踪/时间线.md",
        "追踪/摘要/",
        "## 逐章更新记录",
        "## 累计待处理项",
        "## 历史记录索引",
        "顶层区块恰好是下面 11 个",
        "迁移归档",
        "_tracking-meta.json",
        "事件库.json",
    )
    for path in paths:
        text = read(path)
        found = [term for term in retired if term in text]
        require(not found, f"{path} still contains retired tracking architecture: {found}")

    require(
        not (ROOT / "skills/moshu-setup/references/templates/上下文.md.tmpl").exists(),
        "manual context template must be deleted; the transaction tool renders the hot cache",
    )


def test_no_tracking_fallback_or_context_style_fingerprint_remains() -> None:
    # 缺失文件处理契约自入口下沉后位于 chapter-core.md「写前准备契约」节（审计-V3 D3 车道收敛后）
    long_write = read("skills/moshu-write/SKILL.md") + read("skills/moshu-write/references/chapter-core.md")
    for forbidden in (
        "角色状态文件缺失** → 从角色设定文件和前文推断当前状态",
        "伏笔/时间线文件缺失** → 不检查",
    ):
        require(forbidden not in long_write, f"moshu-write still has tracking fallback: {forbidden}")
    require_all(
        long_write,
        (
            "视为续写状态卡损坏",
            "已有正文但 `_tracking-state.json` 缺失时重新 `/moshu-import`",
        ),
        "fail-closed tracking reads",
    )
    writer = read("skills/moshu-setup/references/templates/agents/moshu-narrative-writer.md")
    require("`上下文.md` 文风指纹" not in writer, "moshu-narrative-writer still reads a removed context style fingerprint")
    require("追踪/上下文.md`「文风指纹」" not in writer, "moshu-narrative-writer still treats context as style storage")
    require("续写状态卡不存文风" in writer, "moshu-narrative-writer must keep style out of tracking context")


def test_hooks_fail_closed_on_invalid_tracking_checkpoints() -> None:
    js = read("skills/moshu-setup/references/templates/hooks/story_hook_core.js")
    require_all(
        js,
        (
            "_tracking-state.json 缺失",
            "schema_version=5",
            "state_revision",
            "mode=revision 事务重建派生视图",
            "重新 /moshu-import",
            "last_committed_chapter",
            "必须先提交",
        ),
        "JS hook",
    )


def test_daily_quality_repairs_close_tracking_before_batch_finish() -> None:
    text = read("skills/moshu-write/references/workflow-daily.md")
    revision = text.index("若本步修文改变了会影响后续的事实")
    step_four = text.index("## Stage 4-4：批末收尾")
    require(revision < step_four, "quality repair revision invariant must appear before Stage 4-4")
    require_all(text[revision:step_four], ("mode=revision", "通过 `check`", "纯措辞调整不重复提交"), "daily quality repair closure")


def test_tracking_examples_use_the_demo_novel() -> None:
    paths = (
        "skills/moshu-write/references/tracking-transaction.md",
        # 导入的 demo 示例随流程拆分位于 references/import-workflow.md
        "skills/moshu-import/references/import-workflow.md",
        "skills/moshu-import/references/character-state-reverse.md",
        # 审查的 demo 示例随流程拆分位于 references/review-workflow.md
        "skills/moshu-review/references/review-workflow.md",
        "skills/moshu-setup/references/templates/rules/story-consistency.md",
    )
    for path in paths:
        text = read(path)
        require("江晨" in text, f"{path} must use the repository demo in examples")
        found = [term for term in ("林舟", "钟楼", "调查员") if term in text]
        require(not found, f"{path} still contains placeholder examples: {found}")


def test_context_retirement_must_be_declared_not_silent() -> None:
    protocol = read("skills/moshu-write/references/tracking-transaction.md")
    require_all(
        protocol,
        (
            "delta.retired_context_items",
            "delta.retired_characters",
            "## 本章退役登记",
            "漏写不会被当成删除",
        ),
        "explicit context retirement",
    )
    # 退役规则压缩后权威在 tracking-transaction.md；workflow-daily 指向它，故拼接检查
    daily = read("skills/moshu-write/references/workflow-daily.md") + read("skills/moshu-write/references/tracking-transaction.md")
    require_all(
        daily,
        ("delta.retired_context_items", "delta.retired_characters", "每章整份提交"),
        "daily workflow retirement rules",
    )


def test_init_archives_a_pre_protocol_tracking_directory() -> None:
    protocol = read("skills/moshu-write/references/tracking-transaction.md")
    require_all(
        protocol,
        ("追踪/_旧追踪存档/", "校验失败的 `init` 不移动任何文件", "不参与解析"),
        "init archive contract",
    )
    require(
        "追踪/_旧追踪存档/" in read("skills/moshu-write/references/workflow-daily.md"),
        "workflow-daily must state where a pre-protocol tracking directory goes",
    )
    tool = read("skills/moshu-write/scripts/tracking_commit.py")
    require(
        'RETIRED_ARCHIVE_DIR = "_旧追踪存档"' in tool,
        "tracking_commit.py must define the archive directory used by the documented contract",
    )


def main() -> None:
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
    print(f"Tracking workflow contract tests passed ({len(tests)} tests).")


if __name__ == "__main__":
    main()

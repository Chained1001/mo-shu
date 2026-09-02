#!/usr/bin/env python3
"""test-check-outline.py — check_outline.py 正式回归测试

守护对象：大纲机检脚本（B18 批）——blocking 九项（结构完备/八列/行数/字数容差/占比/台阶算术/底牌/伏笔闭合）+candidate 四项（单链条提示/采风专名比对/常驻压力/反转覆盖）+版本兼容降级（旧结构不误伤；B102 增：十节结构/旧十列 OLD10 降级/采风子目录与基本设定双路径）。
禁：断言实现细节/真实上游/脆弱快照；fixture 自清理（tempfile）。
退出码语义：0=通过（含仅 candidate）；1=blocking 违规；2=参数/读文件错误。
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/moshu-outline/scripts/check_outline.py"
PY = sys.executable

OLD10_COMPLIANT = """# 大纲（测试书·B102 前十列两表结构）

> 定稿：v1.0（2026-08-24，构建环）

## 全书体量与阶段总览
- 总章节数：250 章；总字数：100 万字（分 2 卷）
- 开篇期 15% / 发展期 55% / 高潮期 20% / 收尾期 10%

## 每卷骨架表
| 卷 | 一句话（主角中心） | 主要对手（+私人纠缠） | 危机/赌注 | 中点 | 高潮定死 | 群像 | 钥匙 | 卷末跃迁 | 字数 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 主角被迫查案 | 反派A（私人纠缠） | 心理死亡 | 假胜 | 揭穿阴谋 | 师门旧案配角入场 | 反派A为何针对主角 | 自保→反击 | 50 |
| 2 | 主角对决势力 | 反派B（私人纠缠） | 职业死亡 | 假败 | 清算合流 | 盟友丙入场 | 底牌先导 | 反击→终局 | 50 |

## 终局底牌
- 底牌一（解锁卷 2）
- 底牌二（解锁卷 2）
- 底牌三（解锁卷 2）
- 底牌四（解锁卷 2）

## 升级台阶
- 50 档 × 2 卷

## 对手梯队与势力场
| 势力/人物 | 目的 | 与主角关系 | 与其他势力关系 | 活跃卷 |
|---|---|---|---|---|
| 甲 | 目的A | 敌对 | 与乙对立 | 1-2 |
| 乙 | 目的B | 中立 | 与甲对立 | 1-2 |
| 丙 | 目的C | 盟友 | 与甲博弈 | 1-2 |

## 暗线设计
| 层次 | 内容 | 读者感知节奏 | 主角知晓节奏 | 揭示卷 |
|---|---|---|---|---|
| 暗线一 | 身世之谜 | 第2卷闻到味/第4卷揭半层 | 主角先不知 | 卷9 |

## 支线登记
| 支线名 | 归属角色 | 起点卷 | 本卷进展 | 与主线交汇点 | 篇幅占比 | 收束卷 | 配角高光 |
|---|---|---|---|---|---|---|---|
| 师门旧案 | 配角甲 | 卷1 | 追查 | 卷3交汇 | 15% | 卷5 | 卷3独场 |

## 常驻压力
- 阴德账（每卷结算，收尾卷合流）

## 卷间驱动链
| 卷 | 前台问题 | 卷末钥匙 | 下一卷前台问题 |
|---|---|---|---|
| 1 | 主角被迫查案 | 反派A为何针对主角 | 主角对决势力 |

## 承诺兑现时点
| 读者承诺 | 兑现章数 | 兑现方式 |
|---|---|---|
| 金手指首显威 | 8-12 | 探案中首次动用 |
"""


COMPLIANT = (
    OLD10_COMPLIANT
    .replace(
        """## 全书体量与阶段总览
- 总章节数：250 章；总字数：100 万字（分 2 卷）
- 开篇期 15% / 发展期 55% / 高潮期 20% / 收尾期 10%

## 每卷骨架表
| 卷 | 一句话（主角中心） |""",
        """## 每卷骨架表
| 卷（卷名） | 一句话（主角中心） |""",
    )
    .replace("| 1 | 主角被迫查案 |", "| 1｜开卷 | 主角被迫查案 |")
    .replace("| 2 | 主角对决势力 |", "| 2｜终卷 | 主角对决势力 |")
    .replace(
        """| 2｜终卷 | 主角对决势力 | 反派B（私人纠缠） | 职业死亡 | 假败 | 清算合流 | 盟友丙入场 | 底牌先导 | 反击→终局 | 50 |
""",
        """| 2｜终卷 | 主角对决势力 | 反派B（私人纠缠） | 职业死亡 | 假败 | 清算合流 | 盟友丙入场 | 底牌先导 | 反击→终局 | 50 |

- 合计：共 2 卷｜总字数约 100 万字
- 阶段配比参考（C20⑤）：开篇期 15% / 发展期 55% / 高潮期 20% / 收尾期 10%
""",
    )
    .replace(
        """## 卷间驱动链
| 卷 | 前台问题 | 卷末钥匙 | 下一卷前台问题 |
|---|---|---|---|
| 1｜开卷 | 主角被迫查案 | 反派A为何针对主角 | 主角对决势力 |""",
        """## 卷间因果闭环
| 卷 | 前台问题 | 因为上一卷的什么 | 卷末钥匙 | 所以下卷起于 |
|---|---|---|---|---|
| 1 | 主角被迫查案 | （开书设定债） | 反派A为何针对主角 | 承接：对决势力 |
| 2 | 主角对决势力 | 反派A为何针对主角 | 底牌先导 | 终局对决 |""",
    )
)


def run_check(project: Path) -> tuple[int, dict]:
    r = subprocess.run([PY, str(SCRIPT), "--project", str(project)], capture_output=True, text=True, encoding="utf-8")
    try:
        payload = json.loads(r.stdout.strip())
    except json.JSONDecodeError:
        payload = {"raw": r.stdout, "stderr": r.stderr}
    return r.returncode, payload


def write_project(tmp: Path, name: str, outline: str, integration: str | None = None) -> Path:
    project = tmp / name
    (project / "大纲").mkdir(parents=True)
    (project / "大纲" / "大纲.md").write_text(outline, encoding="utf-8")
    if integration is not None:
        (project / "大纲" / "整合记录.md").write_text(integration, encoding="utf-8")
    return project


def test_compliant_zero(tmp: Path) -> None:
    project = write_project(tmp, "ok", COMPLIANT)
    code, payload = run_check(project)
    assert code == 0, f"合规大纲应 exit 0，实得 {code}: {payload}"
    assert payload["ok"] is True and payload["blocking"] == [], f"合规大纲不应有 blocking: {payload}"


def test_bad_ratio(tmp: Path) -> None:
    outline = COMPLIANT.replace("开篇期 15% / 发展期 55% / 高潮期 20% / 收尾期 10%", "开篇期 15% / 发展期 55% / 高潮期 20% / 收尾期 0%")
    project = write_project(tmp, "ratio", outline)
    code, payload = run_check(project)
    assert code == 1 and any("占比加总" in b for b in payload["blocking"]), f"占比和≠100 应 blocking: {payload}"


def test_missing_midpoint(tmp: Path) -> None:
    outline = COMPLIANT.replace("假胜 | 揭穿阴谋", "过渡 | 揭穿阴谋")
    project = write_project(tmp, "midpoint", outline)
    code, payload = run_check(project)
    assert code == 1 and any("中点列" in b for b in payload["blocking"]), f"中点未标注假胜/假败应 blocking: {payload}"


def test_wordcount_drift(tmp: Path) -> None:
    outline = COMPLIANT.replace("| 2｜终卷 | 主角对决势力 | 反派B（私人纠缠） | 职业死亡 | 假败 | 清算合流 | 盟友丙入场 | 底牌先导 | 反击→终局 | 50 |",
                                "| 2｜终卷 | 主角对决势力 | 反派B（私人纠缠） | 职业死亡 | 假败 | 清算合流 | 反击→终局 | 80 |")
    project = write_project(tmp, "words", outline)
    code, payload = run_check(project)
    assert code == 1 and any("字数加总" in b for b in payload["blocking"]), f"字数超 ±5% 应 blocking: {payload}"


def test_dangling_foreshadow(tmp: Path) -> None:
    outline = COMPLIANT.replace("> 定稿：v1.0（2026-08-24，构建环）", "> 定稿：v1.0（2026-08-24，构建环）\n- 引用 F999 的伏笔")
    integration = "# 整合记录\n| 伏笔 | 状态 |\n| F001 | 计划埋 |\n"
    project = write_project(tmp, "fshadow", outline, integration)
    code, payload = run_check(project)
    assert code == 1 and any("F999" in b for b in payload["blocking"]), f"悬空 F 引用应 blocking: {payload}"


def test_missing_section(tmp: Path) -> None:
    outline = COMPLIANT.replace("## 终局底牌\n- 底牌一（解锁卷 2）\n- 底牌二（解锁卷 2）\n- 底牌三（解锁卷 2）\n- 底牌四（解锁卷 2）\n\n", "")
    project = write_project(tmp, "missing", outline)
    code, payload = run_check(project)
    assert code == 1 and any("必备节缺失" in b for b in payload["blocking"]), f"删整节应 blocking: {payload}"


def test_old10_structure_downgrade(tmp: Path) -> None:
    # B102：B102 前十列两表结构（test1-5 存量形态）→ OLD10 升级建议 candidate，exit 0
    project = write_project(tmp, "old10", OLD10_COMPLIANT)
    code, payload = run_check(project)
    assert code == 0, f"旧十列结构应降级 exit 0，实得 {code}: {payload}"
    assert any("B102 前十列两表" in c for c in payload["candidate"]), f"旧十列应出 OLD10 候选: {payload}"


def test_old_structure_downgrade(tmp: Path) -> None:
    old = """# 大纲（旧书）

## 全书卷级鸟瞰
| 卷 | 卷名 | 字数/章数 | 核心事件 | 状态变化 |
|---|---|---|---|---|
| 1 | 开头 | ~50 万/125 | 破案 | 自保→守真相 |
"""
    project = write_project(tmp, "old", old)
    code, payload = run_check(project)
    assert code == 0, f"旧结构应降级 exit 0，实得 {code}: {payload}"
    assert any("旧版结构" in c for c in payload["candidate"]), f"旧版结构应出 candidate 提示: {payload}"


def test_missing_outline(tmp: Path) -> None:
    project = tmp / "none"
    (project / "大纲").mkdir(parents=True)
    code, payload = run_check(project)
    assert code == 2, f"无大纲文件应 exit 2，实得 {code}: {payload}"


def test_missing_dark_section(tmp: Path) -> None:
    outline = COMPLIANT.replace("## 暗线设计\n| 层次 | 内容 | 读者感知节奏 | 主角知晓节奏 | 揭示卷 |\n|---|---|---|---|---|\n| 暗线一 | 身世之谜 | 第2卷闻到味/第4卷揭半层 | 主角先不知 | 卷9 |\n\n", "")
    project = write_project(tmp, "noad", outline)
    code, payload = run_check(project)
    assert code == 1 and any("暗线设计" in b for b in payload["blocking"]), f"缺暗线设计节应 blocking: {payload}"


def test_missing_branch_section(tmp: Path) -> None:
    outline = COMPLIANT.replace("## 支线登记\n| 支线名 | 归属角色 | 起点卷 | 本卷进展 | 与主线交汇点 | 篇幅占比 | 收束卷 | 配角高光 |\n|---|---|---|---|---|---|---|---|\n| 师门旧案 | 配角甲 | 卷1 | 追查 | 卷3交汇 | 15% | 卷5 | 卷3独场 |\n\n", "")
    project = write_project(tmp, "nobr", outline)
    code, payload = run_check(project)
    assert code == 1 and any("支线登记" in b for b in payload["blocking"]), f"缺支线登记表应 blocking: {payload}"


def test_harvest_proper_names(tmp: Path) -> None:
    # B19 联动：设定/采风-*.md 通配专名比对（候选不拦截）
    project = write_project(tmp, "harvest", COMPLIANT)
    (project / "设定").mkdir()
    (project / "设定" / "采风-角色-师爷.md").write_text(
        "# 采风-角色\n\n## 来源专有名词\n- 阴德账（来源书特有设定名）\n", encoding="utf-8")
    code, payload = run_check(project)
    assert code == 0, f"采风专名比对为候选，应 exit 0，实得 {code}: {payload}"
    assert any("疑似复用来源专名" in c for c in payload["candidate"]), f"应出专名候选: {payload}"


def test_unconsumed_caifeng(tmp: Path) -> None:
    # B21：采风-CF*.md 元数据状态「未消费」→ candidate 且 exit 0
    project = write_project(tmp, "cf", COMPLIANT)
    (project / "设定").mkdir()
    (project / "设定" / "采风").mkdir()
    (project / "设定" / "采风" / "采风-CF001-角色-师爷.md").write_text(
        "# 采风-CF001-角色-师爷\n## 元数据头\n- 类型/主题：角色/师爷｜触发需求：步 2 人物｜状态：未消费\n## 来源清单\n| 作品 | URL | 日期 | 占比 |\n## 要素表\n| 要素 | 内容 | 来源 URL |\n## 来源专有名词清单\n## 转译三问初答（机制类）\n## 融合与消费记录\n", encoding="utf-8")
    code, payload = run_check(project)
    assert code == 0, f"未消费采风为 candidate，应 exit 0，实得 {code}: {payload}"
    assert any("采风产物未消费" in c for c in payload["candidate"]), f"应出未消费候选: {payload}"


def test_percent_annotation_not_caught(tmp: Path) -> None:
    # B24：占比行尾注「（合计 100%）」不应被 % 正则误捕（应只读表格数据行的 %）
    outline = COMPLIANT.replace(
        "开篇期 15% / 发展期 55% / 高潮期 20% / 收尾期 10%",
        "开篇期 15% / 发展期 55% / 高潮期 20% / 收尾期 10%（合计 100%）")
    project = write_project(tmp, "pctanno", outline)
    code, payload = run_check(project)
    assert code == 0, f"注释 % 不应误捕成 blocking，实得 {code}: {payload}"
    assert not any("占比加总" in b for b in payload["blocking"]), f"不应报占比加总: {payload}"


def test_ladder_chinese_quantifier(tmp: Path) -> None:
    # B24：升级台阶「4 大阶段 × 100 万字」——容忍数字与×间中文量词（应解析得出，不降 candidate）
    outline = COMPLIANT.replace("50 档 × 2 卷", "4 大阶段 × 100 万字")
    project = write_project(tmp, "ladderzh", outline)
    code, payload = run_check(project)
    assert code == 0, f"量词阶梯应解析 exit 0，实得 {code}: {payload}"
    assert not any("无法实算" in c for c in payload["candidate"]), f"量词阶梯应被解析，不应降 candidate 无法实算: {payload}"


def test_bullet_bottom_counted(tmp: Path) -> None:
    # B24：终局底牌条目以 `- ` bullet 开头应被计入（删到 3 条 → blocking <4）
    outline = COMPLIANT.replace("- 底牌四（解锁卷 2）", "")
    project = write_project(tmp, "bullet", outline)
    code, payload = run_check(project)
    assert code == 1 and any("终局底牌条目数" in b for b in payload["blocking"]), f"bullet 条目应被计入并报 <4: {payload}"


def test_power_paren_suffix(tmp: Path) -> None:
    # B24：势力场势力名带「（描述）」后缀时，互引匹配应去后缀（避免误判单链条）
    outline = COMPLIANT.replace(
        "| 甲 | 目的A | 敌对 | 与乙对立 | 1-2 |",
        "| 甲（情报阁） | 目的A | 敌对 | 与乙对立 | 1-2 |"
    ).replace(
        "| 乙 | 目的B | 中立 | 与甲对立 | 1-2 |",
        "| 乙（官府） | 目的B | 中立 | 与甲对立 | 1-2 |"
    ).replace(
        "| 丙 | 目的C | 盟友 | 与甲博弈 | 1-2 |",
        "| 丙（猎户） | 目的C | 盟友 | 与甲博弈 | 1-2 |"
    )
    project = write_project(tmp, "pwrparen", outline)
    code, payload = run_check(project)
    assert code == 0, f"括号后缀应去后缀比互引 exit 0，实得 {code}: {payload}"
    assert not any("疑似单链条" in c for c in payload["candidate"]), f"不应误报单链条: {payload}"


def test_virtual_benchmark_unconsumed(tmp: Path) -> None:
    # B53/B94：题材定位.md 成品标尺节存在但大纲零引用其锚点关键词 → candidate 且 exit 0
    project = write_project(tmp, "vbench", COMPLIANT)
    (project / "设定").mkdir()
    (project / "设定" / "基本设定.md").write_text(
        "# 基本设定\n## 成品标尺\n### 节奏目标\n- 爆发密度：每 5 章一个小高潮\n- 伏笔密度：每卷埋 4 条 / 收 3 条参考\n", encoding="utf-8")
    code, payload = run_check(project)
    assert code == 0, f"标尺未消费为 candidate，应 exit 0，实得 {code}: {payload}"
    assert any("成品标尺" in c and "未被大纲引用" in c for c in payload["candidate"]), f"应出成品标尺未消费候选: {payload}"


def test_virtual_benchmark_consumed(tmp: Path) -> None:
    # B53/B94：大纲显式引用成品标尺锚点（如「每 5 章一个小高潮」）→ 不出候选
    outline = COMPLIANT.replace(
        "> 定稿：v1.0（2026-08-24，构建环）",
        "> 定稿：v1.0（2026-08-24，构建环）\n> 参照成品标尺：每 5 章一个小高潮（全书节奏目标）")
    project = write_project(tmp, "vbenchok", outline)
    (project / "设定").mkdir()
    (project / "设定" / "题材定位.md").write_text(
        "# 题材定位\n## 成品标尺\n### 节奏目标\n- 爆发密度：每 5 章一个小高潮\n", encoding="utf-8")
    code, payload = run_check(project)
    assert code == 0, f"已消费应 exit 0，实得 {code}: {payload}"
    assert not any("零引用" in c for c in payload["candidate"]), f"已引用不应报零引用候选: {payload}"


def test_event_edge_dangling(tmp: Path) -> None:
    # B57：事件关系边引用未定义单元 → candidate 且 exit 0
    outline = COMPLIANT.replace(
        "> 定稿：v1.0（2026-08-24，构建环）",
        """> 定稿：v1.0（2026-08-24，构建环）

## 事件关系边
| 源事件 | 关系 | 目标事件 | 说明 |
|---|---|---|---|
| L9-01 主角觉醒 | →因果 | L9-99 决战开启 | 铺垫→爆发 |
""")
    project = write_project(tmp, "edgedang", outline)
    code, payload = run_check(project)
    assert code == 0, f"悬空事件关系为 candidate，应 exit 0，实得 {code}: {payload}"
    assert any("事件关系边" in c and "未定义" in c for c in payload["candidate"]), f"应出悬空引用候选: {payload}"


def test_event_edge_ok(tmp: Path) -> None:
    # B57：关系边引用的单元在卷纲有定义（剧情单元 L1-01 标题）→ 不出候选
    outline = COMPLIANT + """

### 剧情单元 L1-01
- 单元ID/位置：L1-01

### 剧情单元 L1-02
- 单元ID/位置：L1-02
"""
    outline = outline.replace(
        "> 定稿：v1.0（2026-08-24，构建环）",
        """> 定稿：v1.0（2026-08-24，构建环）

## 事件关系边
| 源事件 | 关系 | 目标事件 | 说明 |
|---|---|---|---|
| L1-01 觉醒 | →因果 | L1-02 爆发 | 递进 |
""")
    project = write_project(tmp, "edgeok", outline)
    code, payload = run_check(project)
    assert code == 0, f"正常事件关系应 exit 0，实得 {code}: {payload}"
    assert not any("未定义的剧情单元" in c for c in payload["candidate"]), f"已定义不应报悬空: {payload}"


def test_foreshadow_op_dangling(tmp: Path) -> None:
    # B58b：细纲「伏笔操作」引用 F999（卷纲/整合记录均无）→ candidate 且 exit 0
    project = write_project(tmp, "fopdang", COMPLIANT)
    detail = project / "大纲" / "细纲_第005章.md"
    detail.write_text("# 第5章 细\n- 伏笔操作：埋设·F999（认知颠覆星级1-5：4；情感基调迁移：轻松→悬疑）\n", encoding="utf-8")
    code, payload = run_check(project)
    assert code == 0, f"悬空伏笔操作为 candidate，应 exit 0，实得 {code}: {payload}"
    assert any("悬空伏笔操作" in c and "F999" in c for c in payload["candidate"]), f"应出悬空候选: {payload}"


def test_foreshadow_op_ok(tmp: Path) -> None:
    # B58b：引用 F001（整合记录有登记）→ 不出悬空候选
    project = write_project(tmp, "fopok", COMPLIANT)
    integration = project / "大纲" / "整合记录.md"
    integration.write_text("# 整合记录\n| F001 | 计划埋 |\n", encoding="utf-8")
    detail = project / "大纲" / "细纲_第005章.md"
    detail.write_text("# 第5章 细\n- 伏笔操作：强化·F001（认知颠覆星级1-5：3；情感基调迁移：信任→怀疑）\n", encoding="utf-8")
    code, payload = run_check(project)
    assert code == 0, f"合法伏笔操作应 exit 0，实得 {code}: {payload}"
    assert not any("悬空伏笔操作" in c for c in payload["candidate"]), f"已登记不应报悬空: {payload}"


def main() -> None:
    work = ROOT / ".tmp" / "tests" / "B18work"
    import shutil
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    try:
        test_compliant_zero(work)
        test_bad_ratio(work)
        test_missing_midpoint(work)
        test_wordcount_drift(work)
        test_dangling_foreshadow(work)
        test_missing_section(work)
        test_old10_structure_downgrade(work)
        test_old_structure_downgrade(work)
        test_missing_outline(work)
        test_harvest_proper_names(work)
        test_unconsumed_caifeng(work)
        test_missing_dark_section(work)
        test_missing_branch_section(work)
        test_percent_annotation_not_caught(work)
        test_ladder_chinese_quantifier(work)
        test_bullet_bottom_counted(work)
        test_power_paren_suffix(work)
        test_virtual_benchmark_unconsumed(work)
        test_virtual_benchmark_consumed(work)
        test_event_edge_dangling(work)
        test_event_edge_ok(work)
        test_foreshadow_op_dangling(work)
        test_foreshadow_op_ok(work)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("OK: check_outline (合规 0 / 占比/中点/字数/F引用/删节 各 1 / 旧结构降级 0 / 缺文件 2 / 采风专名候选 / 缺暗线·支线 各 1 / 成品标尺未消费+已消费 / 事件边悬空+正常 / 伏笔操作悬空+合法)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""test-check-outline.py — check_outline.py 正式回归测试

守护对象：大纲机检脚本（B18 批）——blocking 九项（结构完备/八列/行数/字数容差/占比/台阶算术/底牌/伏笔闭合）+candidate 四项（单链条提示/采风专名比对/常驻压力/反转覆盖）+版本兼容降级（旧结构不误伤）。
禁：断言实现细节/真实上游/脆弱快照；fixture 自清理（tempfile）。
退出码语义：0=通过（含仅 candidate）；1=blocking 违规；2=参数/读文件错误。
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/moshu-build/scripts/check_outline.py"
PY = sys.executable

COMPLIANT = """# 大纲（测试书）

> 定稿：v1.0（2026-08-24，构建环）

## 全书体量与阶段总览
- 总章节数：250 章；总字数：100 万字（分 2 卷）
- 开篇期 15% / 发展期 55% / 高潮期 20% / 收尾期 10%

## 每卷骨架表
| 卷 | 一句话（主角中心） | 主要对手（+私人纠缠） | 危机/赌注 | 中点 | 高潮定死 | 卷末跃迁 | 字数 |
|---|---|---|---|---|---|---|---|
| 1 | 主角被迫查案 | 反派A（私人纠缠） | 心理死亡 | 假胜 | 揭穿阴谋 | 自保→反击 | 50 |
| 2 | 主角对决势力 | 反派B（私人纠缠） | 职业死亡 | 假败 | 清算合流 | 反击→终局 | 50 |

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

## 常驻压力
- 阴德账（每卷结算，收尾卷合流）
"""


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
    outline = COMPLIANT.replace("| 2 | 主角对决势力 | 反派B（私人纠缠） | 职业死亡 | 假败 | 清算合流 | 反击→终局 | 50 |",
                                "| 2 | 主角对决势力 | 反派B（私人纠缠） | 职业死亡 | 假败 | 清算合流 | 反击→终局 | 80 |")
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
    assert any("旧结构" in c for c in payload["candidate"]), f"旧结构应出 candidate 提示: {payload}"


def test_missing_outline(tmp: Path) -> None:
    project = tmp / "none"
    (project / "大纲").mkdir(parents=True)
    code, payload = run_check(project)
    assert code == 2, f"无大纲文件应 exit 2，实得 {code}: {payload}"


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
        test_old_structure_downgrade(work)
        test_missing_outline(work)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("OK: check_outline (合规 0 / 占比/中点/字数/F引用/删节 各 1 / 旧结构降级 0 / 缺文件 2)")


if __name__ == "__main__":
    main()

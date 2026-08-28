#!/usr/bin/env python3
"""test-pace-meter.py — pace_meter.py 正式回归测试

守护对象：推进度仪表（B68b）——三源递降（卷纲单元卡「章节范围」主源/大纲.md 卷行次源/CLI 覆盖）、
卷进度 vs 剧情进度 背离候选双条件（2.0×/50pp，候选永不拦截）、细纲编号数值序连续性
（'1000'<'999' 字典序陷阱——千章边界 999/1000/1001）、三分类降级明示（skipped_no_plan/缺文件/内容坏）。
禁：断言实现细节/真实上游/脆弱快照；fixture 自清理（tempfile）。退出码语义：0=通过（含仅候选）；1=项目目录缺。
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/moshu-write/scripts/pace_meter.py"
PY = sys.executable

UNIT_CARD_TEMPLATE = """# 第一卷 卷纲

## 核心信息
- 章节范围：第1-{last}章
- 字数目标：4万字

## 剧情单元卡（1-3 万字为可调经验值；此节标题不是单元卡）

{cards}
"""


def unit_card(idx: int, lo: int, hi: int) -> str:
    return (f"### 剧情单元 L1-{idx}\n- 单元ID：L1-{idx}\n"
            f"- 章节范围：第{lo}-{hi}章\n- 单元承诺：测试单元{idx}\n")


def make_book(root: Path, units, xibnv_nums, prose_count=0, state_last=None,
              outline_md=True, scene_tables=True, volume_file=True,
              outline_md_text=None, volume_raw=None):
    ol = root / "大纲"
    ol.mkdir(parents=True, exist_ok=True)
    if units and volume_file:
        last = max(hi for _, hi in units)
        cards = "\n".join(unit_card(i + 1, lo, hi) for i, (lo, hi) in enumerate(units))
        if volume_raw is not None:
            (ol / "卷纲_第1卷.md").write_bytes(volume_raw)
        else:
            (ol / "卷纲_第1卷.md").write_text(UNIT_CARD_TEMPLATE.format(last=last, cards=cards), encoding="utf-8")
    if outline_md:
        text = outline_md_text if outline_md_text is not None else (
            "# 大纲\n\n## 卷级大纲\n### 第一卷：测试卷（约 4 万字，20 章）\n- 一段式\n"
            "### 第二卷：远卷（约 5 万字，40 章）\n- 一段式\n")
        (ol / "大纲.md").write_text(text, encoding="utf-8")
    for n in xibnv_nums:
        (ol / f"细纲_第{n}章.md").write_text(f"# 细纲（第 {n} 章）\n- 单元ID/位置：L1-1；测试\n", encoding="utf-8")
    if scene_tables:
        for i in range(max(1, len(units) // 2)):
            (ol / f"场景表_单元L1-{i + 1}.md").write_text(f"| 单元ID | 单元预估章数合计 | 对标剧情参照 |\n| L1-{i + 1} | 5 | 无 |\n", encoding="utf-8")
    if prose_count:
        pd = root / "正文"
        pd.mkdir(parents=True, exist_ok=True)
        for n in range(1, prose_count + 1):
            (pd / f"第{n}章_测试.md").write_text("正文", encoding="utf-8")
    if state_last is not None:
        st = root / "追踪"
        st.mkdir(parents=True, exist_ok=True)
        (st / "_tracking-state.json").write_text(json.dumps({"last_committed_chapter": state_last}), encoding="utf-8")


def run(project: Path, *extra):
    return subprocess.run([PY, str(SCRIPT), "--project", str(project), "--json", *extra],
                          capture_output=True, text=True, encoding="utf-8")


def test_normal_pace():
    """正常节奏：20 章 4 单元、已写 5 章（1 单元）→ 25%/25%，无候选无缺号，场景表合计 5。"""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_book(root, units=[(1, 5), (6, 10), (11, 15), (16, 20)],
                  xibnv_nums=[1, 2, 3, 4, 5], prose_count=5, state_last=5)
        r = run(root)
        assert r.returncode == 0, r.stderr
        d = json.loads(r.stdout)
        assert d["status"] == "ok", d
        assert d["计划章数"] == 20 and d["plan_source"].startswith("卷纲单元卡"), d
        assert d["已写章数"] == 5 and d["卷进度%"] == 25.0, d
        assert d["已消耗单元数"] == 1 and d["单元总数"] == 4 and d["剧情进度%"] == 25.0, d
        assert d["场景表预估合计"] == 10.0, d  # 2 张场景表 × 各合计 5
        assert d["细纲编号连续性"]["缺号列表"] == [], d
        assert d["背离候选"] == [], d


def test_divergence_spec_fixture():
    """规格 §四.3 fixture：计划 100 章/8 单元/已写 10 章 6 单元 → 剧情进度 75%/卷进度 10%，候选含预计收卷章数。"""
    units = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 10), (70, 85), (86, 100)]
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_book(root, units=units, xibnv_nums=list(range(1, 11)), prose_count=10, state_last=10,
                  scene_tables=False)
        r = run(root)
        assert r.returncode == 0, r.stderr
        d = json.loads(r.stdout)
        assert d["卷进度%"] == 10.0 and d["剧情进度%"] == 75.0, d
        assert len(d["背离候选"]) == 1, d
        msg = d["背离候选"][0]
        assert "预计约 13 章收卷 vs 计划 100 章" in msg, msg
        assert "裁决归作者" in msg, msg
        assert d["场景表预估合计"] is None, d


def test_divergence_pp_only():
    """单条件命中：比值 0（已消耗 0 单元）不触、绝对差 >50pp 触 → 出候选且收卷章数无法估算；50pp 恰等不触。"""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # 全部单元起始章 > 已写章 → 已消耗 0：卷进度 62.5%、剧情进度 0%，差 62.5pp>50 触发
        make_book(root, units=[(61, 70), (71, 80)], xibnv_nums=[1], prose_count=50, state_last=50,
                  scene_tables=False)
        d = json.loads(run(root).stdout)
        assert d["卷进度%"] == 62.5 and d["剧情进度%"] == 0.0, d
        assert len(d["背离候选"]) == 1, d
        assert "已消耗单元为 0" in d["背离候选"][0] and "vs 计划 80 章" in d["背离候选"][0], d
        # 边界：卷进度恰 50%、剧情进度 0% → 差恰 50pp 不触发（>50 严格）
        with tempfile.TemporaryDirectory() as td2:
            root2 = Path(td2)
            make_book(root2, units=[(51, 60), (61, 70), (71, 80), (81, 90), (91, 100)],
                      xibnv_nums=[1], prose_count=50, state_last=50, scene_tables=False)
            d2 = json.loads(run(root2).stdout)
            assert d2["卷进度%"] == 50.0 and d2["剧情进度%"] == 0.0, d2
            assert d2["背离候选"] == [], d2


def test_missing_outline_md_degrades():
    """缺大纲.md → 次源缺明示，主源照算，status ok。"""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_book(root, units=[(1, 5), (6, 10)], xibnv_nums=[1], outline_md=False, scene_tables=False)
        r = run(root)
        assert r.returncode == 0, r.stderr
        d = json.loads(r.stdout)
        assert d["status"] == "ok" and d["计划章数"] == 10, d
        assert any("次源缺" in n for n in d["notes"]), d["notes"]


def test_missing_volume_secondary_source():
    """缺卷纲 → 主源缺，大纲.md 次源命中；单元总数 null 不算剧情进度/背离。
    无卷纲时按 mo-shu 自定口径回推「末卷行」为当前卷（notes 明示）。"""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_book(root, units=[], xibnv_nums=[1], prose_count=4, state_last=4, scene_tables=False,
                  outline_md_text="# 大纲\n\n## 卷级大纲\n### 第一卷：测试卷（约 4 万字，20 章）\n- 一段式\n")
        r = run(root)
        assert r.returncode == 0, r.stderr
        d = json.loads(r.stdout)
        assert d["plan_source"].startswith("大纲.md"), d
        assert d["计划章数"] == 20 and d["卷进度%"] == 20.0, d
        assert d["卷号"] == 1, d
        assert d["单元总数"] is None and d["剧情进度%"] is None, d
        assert d["背离候选"] == [], d
    # 多卷行 → 回推末卷行（第二卷 40 章），notes 明示回推
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_book(root, units=[], xibnv_nums=[1], prose_count=4, state_last=4, scene_tables=False)
        d = json.loads(run(root).stdout)
        assert d["计划章数"] == 40 and d["卷号"] == 2, d
        assert any("回推" in n for n in d["notes"]), d["notes"]


def test_numbering_gap():
    """编号缺号：细纲 1-9,11 → 缺号 [10]（数值序）。"""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_book(root, units=[(1, 12)], xibnv_nums=list(range(1, 10)) + [11],
                  prose_count=0, scene_tables=False)
        d = json.loads(run(root).stdout)
        assert d["细纲编号连续性"]["缺号列表"] == [10], d


def test_cli_override():
    """CLI 覆盖：--planned-chapters/--total-units 压过主源，plan_source 标明第三源；阈值覆盖生效。"""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_book(root, units=[(1, 5), (6, 10)], xibnv_nums=[1], prose_count=5, state_last=5,
                  scene_tables=False)
        d = json.loads(run(root, "--planned-chapters", "50", "--total-units", "2").stdout)
        assert d["计划章数"] == 50 and d["单元总数"] == 2, d
        assert d["plan_source"].startswith("CLI"), d
        assert d["卷进度%"] == 10.0 and d["剧情进度%"] == 50.0, d
        assert len(d["背离候选"]) == 1, d  # 50/10=5×>2 且差 40pp<50——比值条件单独命中
        d2 = json.loads(run(root, "--planned-chapters", "50", "--total-units", "2", "--ratio", "9").stdout)
        assert d2["背离候选"] == [], d2  # 阈值放宽后不再命中


def test_no_scene_table_null():
    """无场景表 → 场景表预估合计 null（合法降级）。"""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_book(root, units=[(1, 5)], xibnv_nums=[1], scene_tables=False)
        d = json.loads(run(root).stdout)
        assert d["场景表预估合计"] is None and d["status"] == "ok", d


def test_kilochapter_boundary():
    """千章边界（v1.2）：999/1000/1001 共存——数值序连续性正确；抽走 1000 → 缺号 [1000]
    （若按文件名字典序 '1000'<'1001'<'999'，min/max 倒挂、range 倒空，缺号恒 []——本用例即数值序证明）。"""
    units = [(999, 999), (1000, 1000), (1001, 1001)]
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_book(root, units=units, xibnv_nums=[999, 1000, 1001], state_last=1001, scene_tables=False)
        d = json.loads(run(root).stdout)
        assert d["细纲编号连续性"]["缺号列表"] == [], d
        assert d["计划章数"] == 1001 and d["已写章数"] == 1001, d
        assert d["卷进度%"] == 100.0 and d["剧情进度%"] == 100.0, d
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_book(root, units=units, xibnv_nums=[999, 1001], state_last=1001, scene_tables=False)
        d = json.loads(run(root).stdout)
        assert d["细纲编号连续性"]["缺号列表"] == [1000], d


def test_skipped_no_plan():
    """三源全缺 → skipped_no_plan 明示，恒退出码 0，连续性照出。"""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_book(root, units=[], xibnv_nums=[1], outline_md=False, scene_tables=False)
        r = run(root)
        assert r.returncode == 0, r.stderr
        d = json.loads(r.stdout)
        assert d["status"] == "skipped_no_plan", d
        assert d["计划章数"] is None and any("skipped_no_plan" in n for n in d["notes"]), d


def test_corrupt_volume_falls_to_secondary():
    """三分类：卷纲内容坏（非 UTF-8）→ error 明示不中断，降级次源照算。"""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_book(root, units=[(1, 5)], xibnv_nums=[1], scene_tables=False,
                  volume_raw=b"\xff\xfe\xff\x00 bad bytes")
        r = run(root)
        assert r.returncode == 0, r.stderr
        d = json.loads(r.stdout)
        assert any("内容坏" in e for e in d["errors"]), d["errors"]
        assert d["计划章数"] == 20 and d["plan_source"].startswith("大纲.md"), d


def test_unit_line_pipe_format():
    """源头格式钉（B68b 整改）：workflow-build 行格式样例「单元 U{NN}｜章节范围：第{N}-{M} 章｜…」
    可被主源解析（与 - 章节范围：字段行双形态兼容）。"""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ol = root / "大纲"
        ol.mkdir(parents=True)
        (ol / "卷纲_第1卷.md").write_text(
            "# 第一卷 卷纲\n\n## 剧情单元卡\n\n"
            "### 剧情单元 U01\n单元 U01｜章节范围：第1-12 章｜承诺/风险/BC-ID 分配\n\n"
            "### 剧情单元 U02\n单元 U02｜章节范围：第13-20 章｜承诺/风险/BC-ID 分配\n",
            encoding="utf-8")
        (ol / "大纲.md").write_text("# 大纲\n\n## 卷级大纲\n### 第一卷：样例卷（约 3 万字，20 章）\n", encoding="utf-8")
        (ol / "细纲_第1章.md").write_text("# 细纲\n- 单元ID/位置：U01\n", encoding="utf-8")
        d = json.loads(run(root).stdout)
        assert d["计划章数"] == 20 and d["单元总数"] == 2, d
        assert d["已写章数"] == 0 and d["已消耗单元数"] == 0, d


def test_missing_project_exit_1():
    """致命缺目录 → 退出码 1（唯一非 0 通道）。"""
    r = run(Path(tempfile.gettempdir()) / "B68_no_such_dir_xyz")
    assert r.returncode == 1, r


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"[PASS] {t.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"[FAIL] {t.__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"[ERROR] {t.__name__}: {exc!r}")
    print(f"{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

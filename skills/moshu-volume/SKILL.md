---
name: moshu-volume
version: 1.0.0
description: "卷规划技能——每卷的单元卡/场景表/卷纲产出与修订、开新卷规划、采风、防撞对照。触发方式：/moshu-volume、卷纲、开新卷、单元卡、修订设定、改大纲、采风。读 moshu-outline 的设定与大纲，产出卷纲层文件。"
---

# moshu-volume：卷规划（卷纲与修订的活资产工程）

单元构建→整合检验→定稿 + 开新卷增量 + 修订流 + 采风 + 防撞对照。按统一创作流程模板 FULL 模式执行（AGENTS §9 第 7 条）。

> **前置检查**<!-- B85 -->：`设定/基本设定.md`（旧书回退题材定位.md）或 `大纲/大纲.md` 缺 → 提示先走 /moshu-outline 开书（故事层产物是本技能输入；作者明确跳过则记录继续——提醒不拦截）。

## 读写面

- 创建（产出）：`大纲/卷纲_第X卷.md`（单元卡+情绪弧线+伏笔表+反转+线索矩阵+事件边）、`大纲/场景表_单元{ID}.md`（B68）、`大纲/变更日志.md`（修订留痕）、`设定/采风/采风-CF*.md`、创作进度（项目根·基本设定含标尺节）
- 修订（执行）：设定/*（修订流五步：`impact_scan.py` 影响分析→裁决→留痕→级联→回流）
- 读取（消费）：`设定/`（全部，单元卡消费）、`大纲/大纲.md`、`拆文库/{书}/剧情/*.md`、`节奏.md`、`情绪模块.md`、`追踪/上下文.md`（只读）
- 边界：细纲与正文归 /moshu-write；追踪 commit/check/report 归 write（定稿步末 tracking init）

## 采风触发面

- 情节采风（单元构建）/情绪采风（整合检验）/机制采风（应用层）/融合（fusion 模式，B81 排期）

## 流程文件

- 卷规划流程权威：`references/volume-workflow.md`；修订流五步：`references/revision-workflow.md`；开新卷与防撞对照：`references/cold-path.md`；进度模板：`references/progress-template.md`；采风方法：`references/caifeng-methods.md`；成品标尺：core-setting-template 标尺段（outline 侧）
- 单元/场景/方法论：`references/beat-cards.md`、`references/outline-methods.md`、`references/outline-structure-theory.md`、`references/outline-workflow.md`（细纲职责在 write 侧）等共享方法论（references/ 全目录）

## 交接

- 输入← 设定/*、大纲/大纲.md（outline 产出只读）
- 输出→ 卷纲/场景表/进度构建态 + tracking init → /moshu-write；修订见 revision-workflow.md
- 边界：故事层归 /moshu-outline；细纲与正文归 /moshu-write

# workflow-chapter.md：单章正文工作流（Phase 4-5 薄壳）

本文件是「写指定章」车道的薄壳：13 步骨架 + 单章特有细节。写前准备/正文/机检收尾/事务提交四段共享内核在 [chapter-core.md](chapter-core.md)，本文件每步只给一行指引，**执行细节一律进 core 对应段**。

## 单章写作流程（13 步骨架）

1. **检查细纲** → core「A1 检查细纲」（缺必需字段必须先补建，不允许跳过细纲直接写作）
2. **读取上下文** → core「A2 读取上下文」（13 项清单 + explorer 快捷路径）
3. **写前准备** → core「A3 写前准备四步」（状态筛选/设定包/模块召回 (a)-(g)/指令确认）
4. **资料研究（按需）** → core「A4」
5. **标题预检** → core「B1」
6. **写作** → core「B2」（含正文元信息隔离与认知边界纪律）
7. **正文执行** → core「B3」（spawn prompt 材料清单）
8. **字数验证** → core「B4」（90% 放行下限，区间 [目标, ×1.1]）
9. **钩子与爽点检查** → core「B5」（两条可证伪核对）
10. **元信息扫描** → core「C 段 · 正文元信息扫描」
11. **禁用词扫描** → core「C 段 · 禁用词扫描」（最毒句式速查 + banned-words 全表）
12. **更新追踪** → core「D4 追踪事务提交」（`scripts/tracking_commit.py commit`；含 `information_gap_changes` 信息差登记；失败三分类见 recovery-protocol.md）
13. **中途快照**（每连续 3 章）→ core「中途快照」

## 单章特有补充

- **标题预检细则**（第 5 步）：从细纲读取章名；如与既有章节同名或明显重复，先按本章核心事件改名，并同步细纲标题与正文文件名。
- **质量检查**（Phase 5，写后同轮）：core「D1-D3」（三维度 + consistency-checker 过桥 + narrative-writer 去 AI 味审查）；**S1/S2 必须显式过桥**——①已修复 ②进 `continuity_risks` ③进 `next_chapter_commitments` 三选一落盘，未判定不得进入下一章。
- **写前准备契约**（缺失文件处理/权威优先级/追踪体积）→ core「写前准备契约」；产物映射与项目结构树见 [artifact-protocols.md](artifact-protocols.md) 开头。

## 质量检查节索引

| 检查 | core 位置 |
|---|---|
| 三维度（情绪交付/契约风险/技术质量） | D1 |
| 写后同轮清零 + `<!-- 去味:跳过 -->` 豁免 | C 段 |
| 确定性收尾（ai-patterns→outline-copy→normalize） | C 段 |
| 候选机检（永不拦截） | C 段 |
| 退化防护（对话行 tier1 降级 advisory） | C 段 |
| 机检修复预算（统一阀门 2 轮） | C 段 |
| consistency-checker 调用 + S1/S2 过桥 | D2 |
| narrative-writer 去 AI 味审查 + mode=revision 事务 | D3 |
| 追踪事务提交 | D4 |

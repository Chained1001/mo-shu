# 深度审计：story-long-analyze × story-long-write

- **对象**：两个核心 skill 的管道完整性、跨 skill 消费契约、v0.7.6 声称落地情况
- **方式**：主线程全文精读（analyze SKILL.md 329 行 + 6 references；write SKILL.md 327 行 + workflow-setup/daily/chapter/revision 全部 + 关键脚本 check-outline-copy.js 全文 + narrative-writer agent 模板 + demo `_progress.md`），对全部发现给出文件:行号级证据
- **结论先行**：两条管道设计自洽、闭环完整，v0.7.6 声称的修复全部有代码/文档级落地证据；未发现新的中危以上问题。以下为确认与新发现明细。

---

## 一、管道总览（analyze 产出 → write 消费）

```
story-long-analyze（拆文库/{书}/ 为数据源）
  Stage 0  概要.md(thin) + 章节边界表(_progress.md)   ← 唯一切片真值
  Stage 1  第1-3章_深度拆解.md → 停靠 快速预览.md
  Stage 2  第{N}章_摘要.md（情节点+基调+主题标签）→ _章节摘要汇总.md
  Stage 3  剧情/*.md + 故事线.md + 节奏.md + 情绪模块.md（权威索引）
  Stage 4  设定/*.md + 角色/*.md + 角色关系.md
  Stage 5  拆文报告.md + 概要.md(plot-aware 覆盖)
  Stage 6  文风.md（句长确定性统计 + 锚点）

story-long-write（对标/{书}/ 引用视图；回退 拆文库/{书}/）
  Phase 3  对标发现/登记 → 首次引用同步到 对标/{书}/
  Phase 4  每章：情绪模块召回(a) + 节奏召回(b) + 题材卡(c) + 文风召回(d) + 匹配章(e) + 模块召回(f)
            → narrative-writer spawn → 字数验证 → 追踪事务 → 确定性收尾
```

**消费契约核对（8 类产物全部有消费点，且权威优先级措辞两侧一致）**：

| analyze 产物 | write 消费点 | 回退 |
|---|---|---|
| 剧情/节奏.md | workflow-chapter 写前准备 3(b)、步骤 2(12) | 对标→拆文库（SKILL.md:75） |
| 剧情/情绪模块.md | 3(a)、步骤 2(11) | 同上 |
| 文风.md | 3(d) 文风召回 | 同上 |
| 拆文报告.md | 步骤 2(5)、Phase 2/3 | 同上 |
| 剧情/故事线.md | 步骤 2(8) 单元索引 | 同上 |
| 剧情/{单元}.md | 步骤 2(9)、卷纲剧情单元「对标剧情参照」 | 同上 |
| 设定/世界观/*.md | 步骤 2(10) | 同上 |
| 章节/{K}_摘要.md + 深度拆解 | 3(e) 匹配章挑选（grep `基调：` 全角冒号） | 黄金三章深度拆解/文风兜底 |
| 角色/{名}.md | 产物映射表（Phase 4 模块召回） | 同上 |

- 权威优先级链两侧一致：analyze SKILL.md:106「拆文报告/故事线只做摘要投影，冲突以 节奏.md/情绪模块.md 为准」↔ write SKILL.md:197-202「情绪模块/节奏为权威，拆文报告/故事线为投影，冲突记 gaps.conflict」。
- 文风归属一致：analyze style-profile-generator.md:117「文风留拆文库、analyze 永不直写 对标/」↔ write SKILL.md:73「首次引用对标书时同步到 对标/」。

## 二、story-long-analyze 深度发现

### 已确认（此前审计 medium）
- **[medium/references] SKILL.md:130**：声称「用 style-profile-generator.md Step 4 的章节正则（含 千/两）grep 出全部章节行号」。证据链闭环：
  - style-profile-generator.md:49 Step 4 实为「原文采样」；:53 明文「Stage 6 只读 _progress.md 章节边界表，**不重新搜索章节标题、不另行推断边界**」；:53 还要求表缺失即**停止 Stage 6**、提示重建 Stage 0。
  - pipeline-ops.md:39「不再各自跑 regex」。
  - 即：新设计的全部意图就是「Stage 0 跑一次 regex 落边界表，此后各阶段只读表」，而 SKILL.md:130 却让 Stage 0 去另一个文件里找一段已随旧设计删除的正则。执行 agent 按引用查找必然扑空。修复：SKILL.md 内联给出正则（如 `^第[零一二三四五六七八九十百千万两0-9]+章`）或删引用并注明「边界表落盘后即唯一切片真值」。

### 新发现
- **[info/structure] SKILL.md:133 边界表「字数」列来源未定义**：模板只给 `| 章号 | 标题 | 起始行 | 字数 |`，未说明字数如何计算（demo `_progress.md` 已填，如第1章 7974 字，说明执行者自行完成）。demo 证明可行，但属未写明的隐式步骤，建议补一句「字数 = 本章起始行到下一章起始行-1 区间去空白字数」。
- **[info/robustness] 边界表只有「起始行」无「结束行」**：切章文本靠「下一章起始行-1 / 文件尾」推断，文档未明说。单文件多卷书/文件尾带后记时，最后一章的切片边界隐含依赖执行者判断。建议表加「结束行」列或在 Stage 0 说明推断规则。
- **[info/tests] 恢复机制与 `_章节摘要汇总.md`**：中断恢复（`paused_after_stage1` 之后）只登记阶段与断点，未记录汇总文件状态；Stage 2 续跑后需重新拼接。拼接幂等（SKILL.md:278-283 无损检查自证），可接受，但建议在 `_progress.md` 断点段补一行汇总文件标记。
- **[info/cross-check 正向]** Stage 2 四道硬检查（SKILL.md:241-247：`^P` 行数、`基调：` 全角冒号、`涉及` 段、主题标签枚举）与 Stage 6 采样口径（style-profile-generator.md:33-36 grep `基调：(枚举)`、全角冒号、不在行首）**逐字一致**——「硬检查就是上面 4 条，没有更多」的设计意图形成正确闭环，正是这两条管道能互信的原因。
- **[info/cross-check 正向]** demo `_progress.md` 与契约逐字段吻合：schema_version: 2、边界表、最终状态值（completed）、计数验证（23==23）、覆盖率 100% 的合规解释（material-decomposition.md:407 小体量特例）——契约有真实执行样例背书；唯一瑕疵是 :3 输出目录仍写 `demo/拆文库-盘龙/`（实际 `demo/拆文库/盘龙/`，即此前报告的 low）。

## 三、story-long-write 深度发现

### 已确认（此前审计）
- **[low/structure] workflow-daily.md:25**：story-explorer 检查只写「`.claude/agents/story-explorer.md` 是否存在」，与 workflow-chapter.md:14 的 `.claude → .opencode → .codex` 三平台顺序不一致（workflow-setup.md:49/276 story-architect 同样只查 `.claude/agents/`）。OpenCode/Codex 部署会静默失去并行捷径。
- **[info/scripts] check-outline-copy.js:237-240**：`try { process.exit(main()) } catch { process.exit(0) }` 把内部异常（如 fs 权限错误）也吞成「干净」，与其头注释「1 = 有重合待复核；0 = 干净或无法判定」的契约不符——崩溃与「无法判定」混为一谈。

### 新发现
- **[info/robustness] 复沓锚句提取的列表边界与注释声称不符**：check-outline-copy.js:65 的 `extractAnchors` 终止 lookahead 为 `(?=\n[-*+]\s|\n#{1,6}\s|$)`——**顶格** `- ` 列表会在第一条锚句后截断（只提取第一行），而缩进列表（行首空格）与 `1.` 编号列表可完整提取。脚本头注释（:61-62）声称「缩进 - 列表或纯文本都能正确提取」未提顶格列表边界。当前模板（workflow-setup.md:235）为单行内联式 `- 复沓锚句：{...}`，实际用法安全；但用户按多行顶格列表书写锚句时会静默丢白名单，属文档与实现的边界漂移。建议注释改为「顶格 `- ` 列表只取第一行，请用缩进/编号/纯文本」，或改 lookahead 兼容顶格条目。
- **[info/portability] 确定性收尾三脚本依赖 shell glob 展开**：check-ai-patterns.js:252-283、check-outline-copy.js:136-154、normalize-punctuation.js 均直接消费 `process.argv` 文件名、脚本内不做 glob 展开。workflow-chapter.md:121-124 的调用 `node scripts/check-ai-patterns.js ... 正文/第XXX章_*.md` 依赖执行 shell 展开通配符——Git Bash（Claude Code/Codex Windows 的 Bash 工具）会展开；若执行环境是 PowerShell/cmd，字面模式会传入，check-outline-copy 的 `read()` 对不存在路径返回 null → 静默退 0「干净」（漏检面），check-ai-patterns 报读不到文件。仓库文档统一 bash 语法，主流路径安全，建议在脚本头注明「需 shell 展开或自行 glob」。
- **[info/cross-check 正向] 双轨字数验证闭环**：主会话 90% 放行下限（workflow-chapter.md:74-77）与 narrative-writer 模板 :180-183「细纲字数目标唯一权威、低于 90% 即未达标、落盘后立即 Bash 实测禁止估算、探测失败声明『未完成机器字数验证』」逐条同口径；返回前报实测字数+句长分布（:294）与主会话步骤 8 的校验输入衔接——v0.7.6 声称 (a)(b) 的完整证据。
- **[info/cross-check 正向] 追踪事务模型四文件同口径**：workflow-daily（:46-60）、workflow-chapter（步骤 12）、workflow-revision（Step 4）、tracking-transaction.md（:30-34, :141-147）对「唯一写入口、expected_state_revision 拒绝 stale、退役只能 append、revision 重算整份记录、check 失败不输出 JSON」表述一致，无漂移。
- **[info/cross-check 正向] 复沓锚句全链路闭环**：模板字段（workflow-setup.md:235）→ narrative-writer 逐字落地（agent 模板 :31）→ check-outline-copy 精确扣除锚句区间+滥用统计（:18-21, :170-219）→ 判定保留补回细纲锚句（:225「子代理不改大纲，主会话补锚句」）——v0.7.6 声称 (d) 落地完整。

## 四、v0.7.6 声称逐条落地证据

| 声称 | 证据 |
|---|---|
| narrative-writer 加 Bash 白名单、字数可执行判据 | agent 模板 :8 `tools: [Read, Glob, Grep, Write, Edit, Bash]`；:9 注明用途；:183 落盘后 Bash 实测、python3/python/py 探测、禁估算、探测失败声明未验证 |
| 返回前报句长分布 | agent 模板 :294 实测字数+句长分布（短<15/中15-30/长>30/平均句长），禁编造 |
| 细纲内容层/形状层双轨进 spawn | workflow-chapter.md:70-71（内容层每项独立落地 / 形状层可打散重排）；agent 模板 :30-31 |
| 细纲照搬检测 + 复沓锚句 | check-outline-copy.js 全文（阈值 16 字、锚句精确扣除、豁免单独统计、多章位置参数按正文处理）|
| Claude 写正文守卫补追踪门/Bash 面 | guard-outline-before-prose.sh（PreToolUse Bash|Write|Edit|MultiEdit + tracking-checkpoint + prose-command-guard） |
| SKILL.md 体积下降 | 现 327 行 / 27,252 字节；doc-budget 实测 13,132/13,200（去空白）在预算内 |

## 五、结论

- 两 skill 无新增中危；既有 1 条 medium（analyze SKILL.md:130 失效引用）证据链已完全坐实，建议 P0 修复。
- 跨 skill 消费契约 8/8 对齐，权威优先级与文风归属两侧措辞一致——这是本仓库工程化程度最高的闭环之一。
- 新发现均为 info 级：边界表字数列未定义/无结束行列、extractAnchors 顶格列表边界、三脚本依赖 shell glob、汇总文件恢复未登记；前两条建议在下次版本顺手补齐文档。
- 正向确认：Stage 2 硬检查与 Stage 6 采样口径逐字一致、追踪事务四文件同口径、双轨字数验证同阈值、复沓锚句全链路闭环——均非偶然，是 v0.7.6 改动时有意对齐的结果。

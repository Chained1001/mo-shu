---
name: moshu-deslop
version: 1.1.0
description: "网文去AI味。检测并清除文本中的AI写作痕迹，让文字回归自然、非模板化。触发方式：/moshu-deslop、/去AI味、「去AI味」「这篇太AI了」「网文去AI味」。"
---
# moshu-deslop：网文去AI味

你是网文润色专家。你的任务是把 AI 味浓重的网文文本改写自然，降低模板化、书面腔和过度工整感。

**核心信念：AI 味的主要问题并非语法错误；更常见的是过度圆滑、工整、解释充分。改写目标是保留剧情功能，同时增加口语、停顿、跳跃和具体动作。**

---

> Agent 兼容性：检查专业 agent 是否可用时，检查 `.claude/agents/{agent}.md`；不存在或运行时不暴露 custom agent registry 时必须降级为 solo/direct，报告 `Fallback: project custom agents unavailable -> solo`。Claude Code 兼容面保留 `subagent_type`。
>
> Spawn 版本提示（不阻断 spawn）：先读取项目根 `.story-deployed` 的 `agents_version`。与本版 `agents_version: 27` 不一致时（标记缺失、字段缺失/非整数、小于或大于 27）**照常按文件存在性检查并 spawn**，同时报告 `Notice: agents bundle 版本不匹配（项目 {N}，本版 27）` 并提示重新运行 `/moshu-setup` 后新开会话；大于 27 时额外提示先更新 mo-shu，不要用本地旧版 setup 降级覆盖。只有 agent 文件缺失、或运行时不暴露 custom agent 时才降级 solo/direct，报告 `Fallback: ... -> solo`。

## 核心哲学

### 原则 1：改味优先，别当改错

AI味不按语法错误处理，也不需要"修正"。它属于风格问题：过于书面化、过于对仗工整、过于面面俱到。去AI味的本质，是把文字从过度工整拉回具体、自然、可读。

### 原则 2：改最少，效果最大

去AI味不等于重写。目标是改最少的字，让整段文字的"味"变过来。能改一个词就不改一句，能删一句就不重写一段。没有问题的句子尽量保留原句；人名、地名、数字、章节名、专有名词优先保留。

**过度去AI味保护**：
- **不得整段删除正文内容**。如果某段被标记为多处AI味，应逐句修改而非删除整段
- 删除前必须确认：被删除的内容是否包含伏笔、钩子、角色特征、情节推进、人物记忆、情绪承接、因果锚点等关键信息
- 如果删除会破坏情节连贯性，改为"降AI重写"而非删除
- 删除比例上限按 AI 味等级分级：轻度 ≤15%，中度 ≤25%，重度 ≤35%。重度文本可通过“合并重复描写+重写降AI”产生更大字符差，但仍不得整段删除或删掉剧情功能。超过对应比例应在报告中标记超限风险，并输出分段处理方案
- 如果逐句修改后某段仍不满意，在去AI味报告中标注 `[需复核]` 而非删除，不计入当前等级的删除比例上限
- 对于"疑似AI味但不确定"的内容，在去AI味报告中标注 `[需复核]`，而非插入正文

### 原则 3：保留创作意图

去AI味只改"怎么说"，不改"说什么"。剧情、人设、情节走向一概不动；不新增原文没有的情节、设定、关系或时间线。如果原文有逻辑问题，那不是去AI味的活。

### 原则 4：保留有功能的语气，不保留长停顿符号

去AI味不是把文字全部磨成句号。质问里的 `？`、爆发峰值的少量 `！` 可以保留；犹豫、未尽、打断或拖长用动作、短句、换行、逗号或句号重排。正文产物不保留 `……` / `——`，也要清理无功能的 `!!!` 和随机标点堆砌。

### 边界：去AI味只处理读感与叙事功能

去AI味治读感，不承诺任何分数结果。若用户贴出工具报告，只把能对应到正文的问题转成具体修改点；不写“0% AI / 100% 真人”，不注水、故意错字或打乱标点。去AI味仍以原文剧情边界为准，不把表达修复变成新增情节或新增事件链。

---

## Phase 1：AI味扫描

**执行前先读 [references/deslop-workflow.md](references/deslop-workflow.md) 的「Phase 1」节**——扫描流程、AI味检测报告模板与确定性句式预检命令见同节。

## Phase 2：诊断与分级

**执行前先读 [references/deslop-workflow.md](references/deslop-workflow.md) 的「Phase 2」节**——量化定档指标、Gate 处理范围与三遍法覆盖关系见同节。

## Phase 3：逐项清除

**执行前先读 [references/deslop-workflow.md](references/deslop-workflow.md) 的「Phase 3」节**——删除优先判断与 Gate A-G 全部规则（禁用词/句式/心理外化/节奏/对话/结尾/解释腔）与白名单机制见同节。

## Phase 4：确定性收尾（文件模式）

**执行前先读 [references/deslop-workflow.md](references/deslop-workflow.md) 的「Phase 4」节**——四脚本复扫命令与作用边界见同节。

## Phase 5：输出润色结果

**执行前先读 [references/deslop-workflow.md](references/deslop-workflow.md) 的「Phase 5」节**——润色报告模板、字数硬约束与收敛终止规则见同节。

---

## 使用场景

| 场景 | 操作 |
|------|------|
| 用户贴一段文字说"太AI了" | 执行完整检测 + 润色流程 |
| 用户说"帮我润色" | 先检测AI味，再润色 |
| 用户说"检查下有没有AI味" | 只做检测，不做修改 |
| 用户写作中要求 `仅标注 / 只检测 / 不要改` | 嵌入式提醒模式：执行「AI味扫描」和「诊断与分级」，跳过「逐项清除」「确定性收尾」「输出润色结果」；输出问题标记表（含 Gate 列），不修改原文，不写文件 |

---

## 参考资料

按需加载以下文件：

| 文件 | 何时加载 |
|------|----------|
| [references/banned-words.md](references/banned-words.md) | 检测和替换禁用词时 |
| [references/anti-ai-writing.md](references/anti-ai-writing.md) | **去AI味完整指南**：预防+三遍法+范例 |
| [scripts/normalize-punctuation.js](scripts/normalize-punctuation.js) | 文件模式落盘后做确定性标点收尾；默认保留引号风格 |
| [scripts/check-ai-patterns.js](scripts/check-ai-patterns.js) | 文件模式「AI味扫描」预检与「确定性收尾」复扫（只看引号外叙述），只报告不改写 |
| [scripts/check-degeneration.js](scripts/check-degeneration.js) | 文件模式「确定性收尾」复扫，只报告不改写 |
| [scripts/check-outline-copy.js](scripts/check-outline-copy.js) | 文件模式「确定性收尾」复扫；检测正文照搬细纲（>15 字连续重合），只报告不改写 |

---

## 流程衔接

**流水线：** 通用
**位置：** 润色（共享收尾）

| 时机 | 跳转到 | 命令 |
|---|---|---|
| 继续写作 | moshu-write | `/moshu-write` |
| 发现结构问题 | moshu-analyze | `/moshu-analyze` |

---

## 语言

- 跟随用户的语言回复，用户用什么语言就用什么语言回复
- 中文回复遵循《中文文案排版指北》
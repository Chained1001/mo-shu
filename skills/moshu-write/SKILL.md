---
name: moshu-write
version: 1.8.0
description: "长篇网文写作。承接开书构建（/moshu-outline → /moshu-volume）之后的细纲与正文：细纲补建/滚动、逐章写作（K 参数，单章与日更统一）、改稿两路（文字打磨+问题修复）、卷复盘执行。触发方式：/moshu-write、/写长篇、「出细纲」「补细纲」「日更」「续写」「继续写」「写第N章」「修改第X章」「回炉」「重写第X章」；开书/建设定/写大纲 → /moshu-outline；卷纲 → /moshu-volume。"
---
# moshu-write：长篇网文写作

> **部署前置检查**：项目根无 `.story-deployed` 时不执行本技能，改为提示：「⚠️ 尚未部署写作环境。请先运行 /moshu-setup，完成后新开会话再回来。」版本不匹配走下方 Spawn 版本提示。

你是网络小说创作教练。你的任务是承接开书构建（moshu-outline 产出设定/大纲.md；moshu-volume 产出卷纲/追踪 init）之后的**细纲与正文输出**：细纲补建/滚动、逐章写作（K 参数）、改稿与卷复盘执行。开书/建设定/写大纲 → `/moshu-outline`；卷纲/开新卷 → `/moshu-volume`。

---

> 运行环境兼容性：Claude Code 是内置适配目标；能读取项目文件的环境，可按本 skill 执行长篇流程。检查专业 agent 是否可用：已部署（部署判定见 /moshu-setup）即可 spawn；不可用或运行时不暴露 custom agent 时，直接 solo/direct 执行并报告 fallback。宿主布局差异由 /moshu-setup 适配面处理。
>
> Spawn 版本提示（不阻断 spawn）：先读取项目根 `.story-deployed` 的 `agents_version`。与本版 `agents_version: 47` 不一致时（标记缺失、字段缺失/非整数、小于或大于 47）**照常按文件存在性检查并 spawn**，同时报告 `Notice: agents bundle 版本不匹配（项目 {N}，本版 47）` 并提示重新运行 `/moshu-setup` 后新开会话；大于 47 时额外提示先更新 mo-shu，不要用本地旧版 setup 降级覆盖。只有 agent 文件缺失、或运行时不暴露 custom agent 时才降级 solo/direct，报告 `Fallback: ... -> solo`。

## 核心方法

我们写网文先抓情绪，再用验证过的方法可靠地交付这个情绪，灵感只做素材来源。

1. 先定情绪，再定故事。每个场景都必须服务于一个明确的情绪目标。说不清交付什么情绪的场景不该存在。
2. 从验证过的模式出发。先问"什么被验证过有效，我如何重新交付"，少从"我想写什么"直接起步。扫榜找方向，拆文找模块，对标找节奏。
3. 用模块组装，不要重新发明。每个题材都有验证过的剧情模式——反转怎么铺、爽点怎么爆、感情怎么拉扯。找到对的模块，把对标书的具体角色看成功能位（对手/盟友/催化剂），再映射到你的角色。用你自己的素材填充这些功能位。
4. 只加载必需信息。写每章时只加载"不知道就会写错"的信息。涉及角色的状态、待回收的伏笔、相关设定。其余留在文件系统里。
5. 契约与推进决策走权威参考文件。涉及读者契约、主角代理权、利益安全、期待债、终局储备（终局底牌/升级台阶）、机构/势力边界与契约安全/需补强/契约破坏风险判定时，先按 `references/reader-contract-and-progression.md` 校准，不在 SKILL.md 内复制长规则。
6. **三层分工（宪法级，防越权与遗漏）**：**脚本做确定性的**——机检（字数/毒句式/退化/细纲照搬/标点）、追踪事务、守卫拦截，能数的绝不让模型估，AI 不做可计数的事；**AI 做语义的**——写稿、写前准备、审查判断、大纲设计，脚本/守卫不拦的语义决策归 AI；**作者做品味的**——开书与细纲确认、审查裁决、卷复盘决策、定稿敲定，AI 只提候选与建议，不替作者拍品味决策。任何环节发现职责越界（AI 估数、作者被跳过、脚本做语义判断）都回到本原则修正。

| 题材 | 核心情绪 | 重点参考 |
|------|---------|---------|
| 打脸/逆袭 | 爽感释放 | references/genre-writing-formulas.md |
| 身份反转 | 震撼+痛快 | references/reversal-toolkit.md |
| 感情拉扯 | 意难平 | references/emotional-methods.md |
| 悬疑/惊悚 | 紧张+好奇 | references/hooks-suspense.md |
| 日常装逼 | 期待感 | references/hooks-chapter.md |

> 情绪反查题材：用户先说情绪没提题材时从上表反向匹配——例如「爽感释放」→ 打脸/逆袭，再从 `references/genre-catalog.md` 找细分方向。

---

## 写作流程

根据用户意图和项目状态选择场景：

| 场景 | 触发条件 | 执行流程 |
|------|----------|----------|
| 开书/设定/大纲/卷纲 | "帮我开书" / 项目目录为空 | → `/moshu-outline` 开书故事层（题材定位、世界观、人物、全书大纲）→ `/moshu-volume` 首卷卷纲；本 skill 接力细纲与写作（见 [outline-workflow.md](references/outline-workflow.md)） |
| 补纲/产纲 | "出细纲/补细纲/规划下一段剧情/接下来写XX剧情（先出细纲）" 且项目已有大纲 | [outline-workflow.md](references/outline-workflow.md)「中途补纲/扩纲小流程」：选同类剧情单元→追加剧情单元卡→按剧情批滚动补细纲；**默认停在细纲交付，不自动写正文** |
| 逐章写作 | "写/续写/日更/写第N章" 且项目已有正文+追踪 | 加载 `references/workflow-daily.md`（**K 参数化 B95**：无数量意图默认 1/日更 2-3/点名 N→min(N,3)；指定写某章三落点：N=下一章→顺序写 K=1、N≤已写→改稿、跳章→引导回顺序写） |
| 改稿 | "修改第X章" / "回炉" / "重写第X章" | 加载 `references/workflow-revision.md`（改稿两路：文字打磨/问题修复，B95） |

> 开新卷：新卷构建（增量设定/卷纲/新卷规划）→ `/moshu-volume` 开新卷（消费卷复盘下卷方向候选）；本 skill 接力新卷细纲与写作（细纲见 [outline-workflow.md](references/outline-workflow.md)）。

### 裸调用与停靠点（防失控）

`/moshu-write` 或 `$moshu-write` **裸调用**（没有"开书/写第N章/日更/续写/修改"等明确意图）时，先只做项目状态诊断并列出下一步选项，**不得自动进入正文写作，也不得把已有项目默认为日更 3 章**：

- 空项目 → 建议说「帮我开书」或先提供 `选题决策.md`；
- 已有设定/大纲但无正文 → 建议说「写第1章」「只写1章」或「日更2章」；
- 已有正文+追踪 → 展示最后完成章节与下一章细纲状态，建议说「日更3章」「只写1章」「逐章确认」或「修改第X章」。

**开书默认停靠（build 侧）**：用户只说"开书/写大纲/帮我开书"时，由 `/moshu-outline`→`/moshu-volume` 完成开书构建与首批细纲（默认 5 章，用户可指定更少或更多，上限 10）后停止，报告已生成文件和下一步命令；除非用户同一句明确说"并写第1章/写 N 章/日更"，否则不要自动进入正文写作。

**正文批量上限**：写正文必须由用户显式给出章节范围或日更意图。未给数量时默认 1 章（K=1）；日更意图默认 2-3 章；用户给出 N 时按 N 执行但单轮最多 3 章，超过 3 章先拆成本轮 3 章并在进度摘要里提示后续再继续。

**匹配优先级**：同时命中多行时，按 改稿 → 逐章写作 → 补纲/产纲 → 开书 的顺序匹配。用户点名要"细纲/补纲/规划剧情"而未要正文时，优先入 补纲/产纲，不入逐章写作。逐章写作的 AND 条件（项目已有正文+追踪）不满足时，提示用户"项目还没有正文，建议先开书/写第1章"。

日更续写保持在 workflow 内：一旦本次请求路由到 `references/workflow-daily.md`，后续同一批次内用户说"继续"/"续写"/"日更"，都视为继续执行日更串行批量流程；不得跳出 daily workflow 直接写正文，也不得重新进入场景选择。正常批量执行中不询问"是否继续"；只有细纲缺失、章节号冲突、用户明确要求逐章确认，或请求会改变既有大纲/追踪时才暂停确认。

无法判断场景时，列出上述场景表让用户选择，不要开放式提问。

### 路径与术语约定

> 拆文库/对标关系：`拆文库/` = analyze skill 的原始产出，是数据源。`对标/` = 写作项目的引用视图，存放与本项目相关的对标数据子集。首次引用对标书时，从 `拆文库/{书名}/` 复制相关子目录（章节/角色/剧情/设定）、`剧情/节奏.md`、`剧情/情绪模块.md` 和 `拆文报告.md` 到 `对标/{书名}/`（不含 文风.md——文风独立为 `文风库/文风.md`，/moshu-style 生成）。
>
> 对标书路径查找：优先 `{项目}/对标/{书名}/`，不存在则回退 `拆文库/{书名}/`。下文所有对标数据加载均使用此规则。

---

### Stage 1：确认选题方向

> **本 Phase（选题/对标/题材定位构建）已移 `/moshu-outline`**；本 skill 不再执行开书构建，细纲与正文在此接力。

### Stage 2：核心设定

> **本 Phase（核心设定/设定建档）已移 `/moshu-outline`**；细纲后设定补全见 [outline-workflow.md](references/outline-workflow.md)「细纲后设定补全」。

### Stage 3：大纲搭建

> **卷级大纲/卷纲构建已移 `/moshu-volume`**；细纲（全书每章）模板、七检/审查、分批建纲、中途补纲见 [outline-workflow.md](references/outline-workflow.md)。

---

### Stage 4：正文写作辅助

#### 项目文件结构

项目结构树与产物映射表见 [references/artifact-protocols.md](references/artifact-protocols.md) 开头「项目文件结构」节；缺失文件处理、对标分析权威优先级、追踪文件体积见 [references/chapter-core.md](references/chapter-core.md) 的「写前准备契约」节。

#### 逐章写作流程

执行前先读 [references/workflow-daily.md](references/workflow-daily.md)（逐章写作统一车道，每章执行序 13 步见其「每章执行序」；**B 段按三遍法执行：第 1 遍快写→第 2 遍读者重读→第 3 遍技艺打磨**，见 chapter-core「B 段」）、写作技巧提醒、字数验收权威与 Stage 5 质量检查执行。

## 交接

- 输入← 卷纲/场景表/进度构建态（moshu-volume 产出）+ 设定/*（moshu-outline 产出）+ 审查工单（moshu-review）
- 输出→ 细纲_第N章.md、正文/第XXX章_章名.md（作者日更消费）
- 边界：故事层归 /moshu-outline；卷纲归 /moshu-volume；细纲与正文归 /moshu-write

## 流程衔接

流水线： 长篇
位置： 写作（第 3/3 步）

| 时机 | 跳转到 | 命令 |
|---|---|---|
| 写完，去 AI 味 | 本技能改稿·文字打磨路 | `references/workflow-revision.md`（B95 deslop 收编） |
| 想对比参考书 | moshu-analyze | `/moshu-analyze` |
| 需要市场方向 | moshu-scan | `/moshu-scan` |

---

## 参考资料索引

按场景加载，不一次全部加载。

各场景的完整步骤按需加载，本文件只保留场景路由、项目文件结构与产物契约、参考索引。

### Stage 1：选题方向

| 场景 | 加载文件 |
|------|---------|
| 确定题材类型 | `references/genre-catalog.md` |
| 只有模糊灵感（画面/脑洞，没方向没选题） | `references/idea-seed.md`（灵感种子七条，开书前置可选） |
| 判断市场方向 | `references/genre-readers.md` |
| 特殊题材考量 | `references/plot-special-topics.md` |
| 女频长篇（题材/文案/平台/感情线） | `references/female-audience-writing.md` |

### Stage 2：核心设定

| 场景 | 加载文件 |
|------|---------|
| 设定人物 | `references/character-basics.md` |
| 设计关系 | `references/character-relations.md` |
| 题材框架与定位 | `references/genre-catalog.md` + `references/genre-core-mechanics.md` |
| 创建 artifact | `references/artifact-protocols.md` |
| 读者契约与主角高光 | `references/reader-contract-and-progression.md` |

### Stage 3：大纲搭建

| 场景 | 加载文件 |
|------|---------|
| 搭建大纲 | `references/outline-methods.md`（**大纲方法论总入口**，按任务路由到全部大纲文件） |
| 设计矛盾与结构 | `references/outline-conflict.md` |
| 深度结构设计 | `references/outline-structure-theory.md` |
| 节奏与升级感 | `references/outline-rhythm.md` |
| 小纲与卡文 | `references/plot-core-methods.md` |
| 选择叙事框架 | `references/plot-frameworks.md` |
| 情节模式校验/情节卡点排障 | `references/plot-patterns.md` + `references/plot-troubleshooting.md`（B78） |
| 题材写作公式 | `references/genre-writing-formulas.md` |
| 黄金三章 | `references/opening-design.md` |
| 情绪弧线 | `references/emotional-arc-design.md` |
| 契约/终局储备/剧情单元安全审查 | `references/reader-contract-and-progression.md` |
| 反转设计 | `references/reversal-toolkit.md` |

### Stage 4：正文写作

| 场景 | 加载文件 |
|------|---------|
| 章节钩子 | `references/hooks-chapter.md` |
| 悬念设计 | `references/hooks-suspense.md` |
| 段落级钩子 | `references/hooks-paragraph.md` |
| 题材正文提示卡 / 题材分类卡 | `references/genre-prose-cards.md` 索引 + `references/genre-prose-cards/` 单题材卡目录（按题材分类优先） + `references/style-genre-modules.md`（通用流派补充） |
| 打斗/装逼 | `references/style-combat-face.md` |
| 喜剧/吐槽/梗场景 | `references/meme-craft.md`（热梗手法学） |
| 高频场景（团战/谈判/揭露/重逢/宴会/审讯） | `references/scene-cards.md`（SC-001~006，冷路径） |
| 商业创作核心方法 | `references/commercial-core-methods.md` |
| 对话 | `references/dialogue-mastery.md` |
| 人物深化 | `references/character-design-methods.md` |
| 情绪技法 + 叙事单元 | `references/plot-emotion-system.md` + `references/emotional-methods.md` |
| 正文技艺（第 3 遍打磨） | `references/literary-techniques.md`（过滤词/系动词/比喻/POV 距离/叙事时间五技，B80）+ `references/craft-cards.md`（技法卡 14 张） |
| 写作技法全程参考 | `references/writing-craft.md`（**写作技法总入口**，按任务路由 + 14 张技法卡） |
| 格式与结构规范 | `references/format-and-structure.md`（仅对话/段落格式适用长篇） |
| 状态追踪协议 | `references/state-tracking.md` |
| 当前剧情单元与契约校准 | `references/reader-contract-and-progression.md` |

### Stage 5：质量检查

| 场景 | 加载文件 |
|------|---------|
| 质量检查 | `references/quality-checklist.md` + `references/reader-contract-and-progression.md` |
| 禁用词扫描 | `references/banned-words.md` |
| AI句式脚本复扫 | `scripts/check-ai-patterns.js` |
| 去AI味 | `references/anti-ai-writing.md` |

### 按主题快速定位（横切主题）

有些主题横跨多个阶段、散在多个文件里。下表给每个主题一个权威文件（先读它，通常够用），配套文件只在需要那个角度时再加载。括号是该文件里对应的小节。

| 主题 | 权威文件（先读） | 配套文件（按角度补充） |
|------|-----------------|----------------------|
| 爽点（按意图分流） | **`references/plot-emotion-system.md`**（爽点设计体系：本质/六种类型/倒推法——"怎么设计爽点"先读这个） | 翻盘/高潮式爽点→`references/plot-core-methods.md`（假胜→崩解）· 打脸/装逼释放→`references/style-combat-face.md`· 题材打脸逆袭公式→`references/genre-writing-formulas.md`· 爽文循环/多层→`references/outline-methods.md`·`references/outline-conflict.md` |
| 情绪模块 | **`对标/{书名}/剧情/情绪模块.md`（项目/书级权威）**；无对标或设计新模块时再读 `references/plot-emotion-system.md` | `references/outline-rhythm.md` 只作理论参考；不得覆盖对标书权威模块 |
| 节奏 | **`对标/{书名}/剧情/节奏.md`（项目/书级权威）**；无对标或设计新节奏时再读 `references/outline-rhythm.md` | `references/plot-core-methods.md` 只作理论参考；不得覆盖对标书权威节奏 |
| 高潮 | **`references/plot-core-methods.md`**（高潮构建公式：蓄能→假胜→崩解） | `references/outline-rhythm.md`（高潮分类与反推）· `references/outline-methods.md`（八节点故事结构：结构定位） |
| 金手指 | **`references/plot-special-topics.md`**（金手指拆分理解与战力防崩 + 进阶设计） | `references/outline-conflict.md`（金手指与身份：四点统一） |
| 感情线 | **`references/character-relations.md`**（好感度体系/四阶段 + 男女频差异） | `references/outline-conflict.md`（感情线设计）· `references/style-combat-face.md`（后宫文女主 / 男频极简爱情线构型）· `references/plot-special-topics.md`（爱情线提纯策略） |
| 反转 | **`references/reversal-toolkit.md`**（反转类型/铺垫/有效性自检） | `references/plot-core-methods.md`（假胜：先给希望再击碎） |
| 人物 | **`references/character-basics.md`**（主角/配角/反派/动机模板速填） | `references/character-design-methods.md`（三层标签反差/九维深化）· `references/character-relations.md`（关系类型/感情线） |
| 女频写作 | **`references/female-audience-writing.md`**（女频长篇：核心原则/文案/题材/感情线长线/平台） | `references/genre-readers.md`（读者心理/平台差异）· `references/character-relations.md`（感情线总框架） |
| 去AI味 | **`references/anti-ai-writing.md`**（AI指纹/核心规则/Show Don't Tell） | `references/banned-words.md`（禁用词扫描）· `references/quality-checklist.md`（成稿检查） |
| 失败恢复 | **`references/recovery-protocol.md`**（A 环境/B 状态/C 主产物/D 模型四类失败分类与恢复动作） | `references/tracking-transaction.md`（事务重试语义）· `/moshu-import`（旧追踪迁移）· `/moshu-analyze`（拆解管道恢复机制） |
| 卷复盘 | **`references/volume-review.md`**（卷末四步：伏笔清账/卷摘要/下卷规划/契约修订候选） | `/moshu-volume` 开新卷（消费下卷方向候选）· `追踪/伏笔.md`（清账数据源）· `设定/题材定位.md`（终局储备与契约） |
| 起名 | **`references/naming-cards.md`**（NC-001~005：书名/章节名/卷名/角色名/绰号，冷路径） | — |

---

## 语言

- 跟随用户的语言回复，用户用什么语言就用什么语言回复
- 中文回复遵循《中文文案排版指北》

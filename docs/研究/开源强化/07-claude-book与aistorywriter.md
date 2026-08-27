# 07·Claude-Book 与 AIStoryWriter 研究（开源强化·第二轮）

> 研究单元：两主仓精读（Claude-Book / AIStoryWriter）+ 一策展清单轻扫（awesome-llm-story-generation）。
> 纪律：被研究仓库只读；AIStoryWriter 为 AGPL-3.0，本文只转述机制，**不含其任何代码/prompt 原文**；每条论断标证据；数字从源码实测（2026-08-27 本地检出）。

## 0 元信息

| 仓 | Claude-Book | AIStoryWriter | awesome-llm-story-generation |
|---|---|---|---|
| URL | github.com/ThomasHoussin/Claude-Book | github.com/datacrystals/AIStoryWriter | github.com/Picrew/awesome-llm-story-generation |
| 本地 | `.tmp/tests/开源强化研究/Claude-Book` | `.tmp/tests/开源强化研究/AIStoryWriter` | `.tmp/tests/开源强化研究/awesome-llm-story-generation` |
| SHA | 3fdebbb（浅克隆，2026-01-22） | 161b712（浅克隆，2025-11-24） | 570893c（2026-06-29） |
| 星/license | 111★ / MIT | 258★ / AGPL-3.0 | 97★ / 未标 license |
| 语言/形态 | Python(uv) 脚本 + Claude Code 配置（CLAUDE.md + .claude/agents + .claude/skills） | Python 单向流水线（CLI 一口气生成整书） | Markdown 策展清单（288 条目/10 类，README.md:5-7） |
| 活跃度 | 最后 push 2026-01-22（任务书给定，未在线复核） | 最后 push 2025-11-24（同左） | 最后核验 2026-06-29（README.md:7） |
| 定位 | 用 Claude Code 多智能体写一本（法语）儿童侦探小说的**框架+成品仓**（已写完 18 章） | 用本地/云 LLM 从一段 prompt **全自动**生成中长篇小说的流水线 | LLM 故事生成研究策展（2022-今），带策展政策（`docs/curation_policy.md`） |

与 mo-shu 关系：Claude-Book 是**同平台同物种**（Claude Code 技能包形态、目录化作品资产、写-审-追踪分工），规模小一个数量级（单本 18 章法语儿童文学 vs 百万字网文日更），其目录契约与 agent 编排可正面对照；AIStoryWriter 是**异平台对照组**（纯 Python 流水线、无人在环、无文件资产），其价值集中在「按故事组件分配模型档位」与「二元质量门禁」两机制。清单仓用于补研究视野。

---

## 1 机制清单

### M1 四目录资产契约：bible / state / story / timeline
- 证据：`Claude-Book/README.md:19-41`（结构图）；`Claude-Book/CLAUDE.md:38-44`（文件契约：bible 写作期只读、state 每章版本化、timeline/history 只追加、story/chapters 为终点）；`Claude-Book/bible/style.md:1-292`、`bible/characters/`（7 文件+模板）、`bible/universe/`（3 文件+模板）；`Claude-Book/story/plan.md:1-405`、`story/synopsis.md`。
- 机制：**bible**（永久层：style.md 文风规则 + structure.md 结构模式 + characters/ 一人一文件 + universe/ 一地一文件，写作期任何人不得改）→ **state**（瞬态层：每章 4 个状态文件，见 M2）→ **story**（成品层：synopsis 一句话故事 + plan.md 全书 18 章章纲 + chapters/ 正文）→ **timeline**（事件层：history.md 全书事件编年 + current-chapter.md 本章草稿区）。每层有明确写者/读者：bible 只被读；state 由 state-updater 写、被 planner/writer/reviewer 读；timeline 由 state-updater 追加。
- 防矛盾手段：**不是检测而是分区**——静态设定（bible）与动态状态（state）物理隔离，静态层写作期冻结；timeline 只追加防篡改历史；每章状态独立目录（见 M2）可回溯任意章末世界。
- mo-shu 映射：对应我们的 设定/（静态档案）+ 追踪/（动态状态）+ 大纲/+正文/。**他们有而我们没有的**：① bible 层把「文风规则」作为与角色/世界观同级的一等公民文件（style.md 含量化指标：句长目标 12-20 词、对话占比 45-55%、章末类型清单，`bible/style.md:88-96,176-179`）——我们的文风画像归 style skill 的画像文件，未进作品资产目录成为「写作期只读正典」；② universe/ 一地一文件的地点档案粒度。**明显更弱的**：无单权威 JSON state（见 M2 的 LLM 手写状态），无信息差/伏笔专项视图（部分由 knowledge.md 覆盖，见 M6），plan.md 单文件全书细纲无卷纲层级。
- 结论：**理念可学**（文风正典一等公民化、静态/动态物理隔离的目录学表述）；不新增目录（挂现有 设定/ 与 style 画像即可）。

### M2 状态版本化 + symlink current + 时间线轮转（会话延续机制）
- 证据：`Claude-Book/CLAUDE.md:18`（新会话第一步：load state/current/situation.md）；`Claude-Book/CLAUDE.md:27-36`（state-updater 建 state/chapter-NN/、换 symlink、timeline 归档轮转）；`Claude-Book/.claude/agents/state-updater.md:22-31`（七步执行序）；`Claude-Book/state/`（实测 chapter-01 至 chapter-18 各 4 文件 + template/）；`Claude-Book/timeline/current-chapter.md:3-7`（"reset at the start of each new chapter"）。
- 机制：输入=已过审的章正文 + 上一章状态文件 → state-updater（LLM agent）在**新目录** state/chapter-NN/ 写 4 个状态文件（situation/characters/knowledge/inventory），删除并重建 symlink `state/current → chapter-NN`，把 current-chapter.md 事件追加进 history.md 后清空 → 输出=指针永远指向最新章末世界。**会话延续没有显式 resume 命令**：新会话只依赖「读 state/current/situation.md + plan.md 定位进度」，全部上下文从文件重建，对话记忆零依赖。
- 弱点（代码事实）：18 章后 `timeline/history.md` 实测 **2256 行**（Read 工具估约 4.5 万 token）——全书事件日志全量 append、无压缩无分层，长篇下 reviewer 与 writer 的注入成本线性膨胀；状态文件由 LLM 手写、无 schema 校验、无原子写（与 mo-shu 单权威 state + tracking_commit.py 三子命令对照为明显更弱）。
- mo-shu 映射：与我们「单权威 _tracking-state.json + 派生视图 + 每章追踪事务」同构，但实现退化（LLM 手写、无校验）。**他们有而我们没有的**：状态目录按章**版本化留档**（任意章末世界可回放）——我们的 state 是滚动覆盖式，回放靠追踪事务重放（能力等价，成本更低）；形似「每章快照」但仅 4 个小状态文件非正文快照，不触 §6「每章全量快照」（该条禁的是正文级全量快照）。timeline 双文件轮转（草稿区/史册区）对应我们伏笔.md 的 updated_chapter 滚动 + 上下文.md 重建，无新增价值。
- 结论：**不引入**（能力已被追踪事务等价覆盖）；「从文件重建、零对话依赖」的会话延续表述可作为 moshu-write A 段的表述参照（已有实践，非新能力）。

### M3 六 agent 分工与模型档位两档制
- 证据：`Claude-Book/.claude/agents/`（实测 6 文件）；`Claude-Book/agents/README.md:10-17`（agent×模型表）；`Claude-Book/.claude/agents/chapter-planner.md:4`、`chapter-writer.md:4`（`model: opus`）；`style-linter.md:4-5`、`character-reviewer.md:4-5`、`continuity-reviewer.md:4-5`、`state-updater.md:4`（`model: sonnet`）；`Claude-Book/CLAUDE.md:1-14`（编排器职责与「不做」清单）。
- 机制：编排器即 CLAUDE.md（主会话），六个子 agent：**创作双档 opus**（chapter-planner 出 5-10 拍的章计划、chapter-writer 严格按拍写作——`chapter-writer.md:40`「按序执行拍子，不加不删」）；**审查与记录四档 sonnet**（style-linter/character-reviewer/continuity-reviewer/state-updater）。作者控制点：编排器每步产出落 `.work/`（gitignore 临时区）供人审；perplexity-improver 改稿前必须问作者验证（`perplexity-improver/SKILL.md:108`）；「Write chapter N」由作者发起。agent description 字段写满触发示例（何时不调用同样写明），planner/writer 未声明 tools 字段而三个 reviewer 声明了全量工具白名单（`character-reviewer.md:4`）——（推断）审查者需要 Grep/Read 跨文件核对故显式声明。
- mo-shu 映射：与我们 agent 体系（narrative-writer/architect/reviewer 等，frontmatter 可钉 model）**同构且更简单**：他们把「档位×角色」收敛成两档铁律——**创作上高档、审查/提取下档**。我们 agent 模板已有 model 字段但未见成文策略。另值得注意：reviewer 职责边界写得极硬（character-reviewer「不判文风/不评情节/不建议改写」，`character-reviewer.md:102-108`），四 agent 各自「You do NOT」清单——防审查越权改稿，与我们 review 工单「候选不拦截」精神同源但更细分。
- 结论：**可移植**（opus/sonnet 两档制作为 agents 模板的成文约定，挂现有 agent frontmatter，零新管线）；agent description 触发示例+反例写法可充实我们的 spawn 协议。

### M4 三门禁审查循环（max 3 迭代）
- 证据：`Claude-Book/CLAUDE.md:21-32`（13 步工作流：planner→writer→perplexity→style-linter→character-reviewer→continuity-reviewer→失败回 writer 循环 max 3→state-updater→归档）；`Claude-Book/CLAUDE.md:26`（"If any gate fails: loop writer with reports (max 3 iterations)"）。
- 机制：输入=章草稿 → 三个正交审查 agent 依次出报告（风格合规/角色一致性/时空连续性，各出 PASS/FAIL 判定）→ 任一 FAIL 则带报告回 writer 重写 → 最多 3 轮 → 全过才触发状态提交与归档。审查三轴互相排斥（各自 boundaries 明示不越界），防重复审查。
- mo-shu 映射：对应 moshu-write C 段机检链 + review 四 reviewer。**他们有而我们没有的**：writer→review→rewrite 的**自动回环有硬上限 3 次**（我们的修订环靠人工指令重跑）。但他们的门禁是 LLM 判 PASS/FAIL（无确定性脚本参与判定，除 style-linter 前置脚本外），而 mo-shu 是脚本阻断+LLM 候选——**我们的分层更符合三层分工宪法**，他们的「回环上限」是可补的参数化纪律。
- 结论：**理念可学**（write 流程 C→B 段失败回环加上限与计数落盘，属 skill 流程文字改动，非新管线）。

### M5 机检前置短路：style_checker.py 先跑、agent 只补语义
- 证据：`Claude-Book/.claude/agents/style-linter.md:20-29`（工作流：先跑脚本、FAIL 即停不做人工复审、PASS 才查脚本查不了的项）；`Claude-Book/scripts/style/style_checker.py:30-62`（阈值常量：字数 2800-3200、均句长 12-20、对话占比 ≥40%、AI 味禁词表）、`:489-596`（analyze_chapter 全检查集：禁用对话标签/副词标签/telling 模式/禁词/引号/重复词）、`:757-766`（报告落 `.work/chapter-XX-tech-report-<uuid>.md`）。
- 机制：输入=章正文 → 确定性脚本产出量化报告（含统计与 PASS/FAIL）→ style-linter agent 读报告，FAIL 短路直接报失败，PASS 才人工补查 POV/时态/章末型等脚本查不了的语义项 → 输出统一格式 style-report。
- mo-shu 映射：与我们「脚本做确定性、AI 做语义」完全同构，且他们的**短路规则**（脚本 FAIL 时 agent 不做语义审查）表述得更硬。**实测发现一处漂移**（代码事实）：style_checker.py:30-31 字数常量 2800-3200 与 `bible/style.md:126` 目标 1500-2500 词不一致——守卫数字与正典文档不同步的活例，印证我们反模式 #1/#6（数字与文档对齐）非过虑。
- 结论：**理念可学**（机检 FAIL 短路语义审查的显式规则表述；我们 check-* 链可照此写进 skill 文本）。**附：perplexity-improver 不学**——本地 Ministral-3-8B 困惑度检测「AI 味句」（`README.md:88-104`，需 ~16GB VRAM GPU），属检测器依赖且 mo-shu deslop skill 已覆盖同职能，触 §6「外部 AI 检测器」红线精神，见 §4。

### M6 knowledge.md 信息差四分栏
- 证据：`Claude-Book/state/template/knowledge.md:1-14`（Known to all / Known to specific characters（含习得章号）/ Unknown (dramatic irony) / Clues found）；`Claude-Book/.claude/agents/state-updater.md:141-144`（"Be meticulous about WHO knows WHAT"）；`continuity-reviewer.md:40-44`（按 knowledge.md 核对「角色不该知道的事」）。
- 机制：输入=章正文 → state-updater 维护四栏知识账（全员已知/角色已知+习得章/读者知而角色不知的戏剧反讽/线索发现记录）→ continuity-reviewer 以其为判据查知识违例（角色引用未获得的信息）。
- mo-shu 映射：与我们批 3a 的「信息差」（追踪/信息差.md：知情人×读者已知登记）**同概念且互为镜像**——他们多了「Clues found」栏（线索发现台账，带发现者与章号），与我们伏笔.md 的 planted/revealed 有部分重叠但视角不同（线索=侦查推进度，伏笔=作者许诺负债）。儿童侦探题材特化。
- 结论：**不引入**（信息差.md 已覆盖主栏；Clues 栏属题材特化，需要时作者自行加列即可，不成机制）。

### M7 拆书→合并→反抄袭原创生成链
- 证据：`Claude-Book/.claude/skills/book-analyzer/SKILL.md:29-72`（读全书→提文风/角色/结构/世界观，强制证据式提取：每个特质须带章节引用或量化数据）；`bible-merger/SKILL.md:24-65`（多本分析合并：全本都出现的模式才升格为规则、指标取 min-max 区间、冲突消解表+merge-report）；`story-ideator/SKILL.md:60-146`（碰撞式头脑风暴 5 法出 10-15 种子→MICE 定型→**反抄袭矩阵**：把生成情节与每本源书的冲突类型/反派原型/发现方式/解法/地点用法逐项对比，0-1 项重合放行、2-3 项修改、4+ 项弃种子重出）。
- 机制：输入=多本源书 → book-analyzer 逐本提取带证据的 bible → bible-merger 合并为单一正典（分歧记录在 merge-report）→ story-ideator 只复用元素（角色/地点/调性）不复用情节结构，反抄袭矩阵量化把关 → 输出 synopsis + 全书 plan。
- mo-shu 映射：moshu-analyze（拆书）与 build（构建环）已有前两环等价物（我们的拆书语料与文风画像）。**他们有而我们没有的**：① 合并环的「**N 本全出现才成为规则**」收紧策略与冲突消解表（我们拆多本对标时无成文合并规则）；② **反抄袭矩阵**——用拆书所得结构指纹反向检查新作是否撞车源书。网文语境下换译为「防撞对标书核心桥段」，对开书前的独创性自查有直接价值。
- 结论：**理念可学**（合并收紧策略与反抄袭对比表可落进 analyze/build 的 references 或流程文本；无新脚本需求，属 skill 文档增强）。

### M8 Claude Code 同平台工程细节包
- 证据：`Claude-Book/.claude/agents/*.md`（frontmatter：name/description/model/tools）；`Claude-Book/agents/README.md:1-6`（旧模板目录收口为「单一事实源」指向 .claude/agents/）；`Claude-Book/.claude/settings.local.json:2-16`（权限白名单：Skill 调用、mkdir、uv run 等逐条批准）；`Claude-Book/CLAUDE.md:63-64` 与各 agent 尾部「Output language: French」（输出语言作为配置项写在每个 agent）；`Claude-Book/.github/workflows/claude.yml:1-38`（@claude 提及触发 anthropics/claude-code-action 处理 issue/PR）；`Claude-Book/README.md:139-142`（「All prompts are in English but output is in French. Change Output language in agent files if needed」）。
- 机制：一组工程约定——① agent 定义单一事实源化（冗余目录改指向说明）；② 权限白名单沉淀在 settings.local.json（重复命令不再逐次询问）；③ **输出语言与指令语言解耦**（指令英文、产出法语，每个 agent 一个字段切换）；④ .work/ 临时产物区 gitignore；⑤ CI 用 claude-code-action 做 issue/PR 应答。
- mo-shu 映射：①与我们 shared-assets 单副本+锚点同源；②我们 hooks/权限体系已有；③**输出语言字段化**值得注意——中文网文场景等价物是「作品语言/文风 register」在 skill 层显式声明而非隐含；⑤CI 跑 LLM 触我们反模式 #8，不学。
- 结论：**理念可学**（①③）；②已有；⑤不学。

### M9 按故事组件×阶段分配模型（13 槽位矩阵）
- 证据：`AIStoryWriter/Writer/Config.py:1-19`（13 个模型配置槽：初始大纲/章纲/正文 S1-S4/章修订/修订意见/评分/信息/擦洗/检查/翻译）；`AIStoryWriter/Write.py:44-109`（每个槽位均有对应 CLI 参数可覆盖，模型串格式 `{Provider}://{Model}@{Host}?param=value`，Write.py:56-66）；`AIStoryWriter/Docs/Models.md:5-13`（按显存分档的模型推荐表，文档宣称）；`AIStoryWriter/Writer/Config.py:48-56`（实测注释：llama3:70b 可当编辑模型、**当写作模型很差**；midnight-miqu-70b 当写手相当好、当其他角色都不行）。
- 机制：输入=CLI/Config 的模型矩阵 → Interface 按用到的模型集合惰性建客户端（`Writer/Interface/Wrapper.py:36-136`，支持 ollama/google/openrouter/zai 四 provider）→ 每个管线组件调用时显式传入自己的模型槽 → 输出产物头部记录全部模型分配（Write.py:411-428，生成档案含每组件的模型名，可复现）。**关键设计理由**（代码注释中的实证经验）：同一模型在不同角色上的表现严重不对称（70B 指令模型擅长批评不擅长创作；角色扮演向模型反过来），因此「组件×模型」必须可独立配置。
- mo-shu 映射：我们 agent frontmatter 已可钉 model 档位但**无成文策略**。直接可借的是其槽位划分逻辑：**创作类**（正文写作、大纲构思）与**判定类**（审查、评分、校验）与**提取类**（状态/信息提取、翻译）三类分档——与 Claude-Book M3 的 opus/sonnet 两档制殊途同归（跨两仓独立收敛）。对 mo-shu 的落地形态：不是运行时矩阵，而是**agents 模板的成文默认档位表**（如 narrative-writer 高档、evaluator/reviewer 中档、提取类中低档），保持作者可覆盖。
- 结论：**可移植**（策略层面：组件×档位成文约定，挂现有 agent model 字段；不需 mo-shu 引入任何运行时配置系统）。

### M10 大纲层级分解链（BaseContext→StoryElements→大纲+修订环→逐章扩写→MegaOutline）
- 证据：`AIStoryWriter/Writer/OutlineGenerator.py:11-77`（提取基础语境→生成故事元素→初始大纲→修订环→拼最终大纲）；`Writer/Outline/StoryElements.py:16-131`（固定模板：类型/主题/节奏/文风/五段情节/多场景设定/冲突/象征/主角+至多 8 配角）；`Write.py:266-272`（LLM 从大纲数出总章数）；`Write.py:286-311`（逐章扩写章纲并拼 MegaOutline = 元素+全部章纲）。
- 机制：输入=用户一段 prompt → ①先抽「基础语境」（防长 prompt 稀释）；②按固定模板生成结构化故事元素；③初始大纲+修订环（见 M12）；④LLM 判章数；⑤逐章扩写细纲 → 输出=MegaOutline 供逐章写作注入。
- mo-shu 映射：对应 build 环（大纲+卷纲+细纲）但**由 LLM 全自动五步推导**，无作者断点（我们 build 有 Phase A/B 与作者定稿点，符合宪法）。他们「先抽 BaseContext 再进大纲生成」的小步骤，与我们 A 段准备清单的意图一致（提炼后再用），无新增。
- 结论：**理念可学仅一点**（大纲生成前先做语境/元素提取的两步拆分表述）；整体形态属无人值守自动生成，不引入。

### M11 章内四阶段分层扩写 + 场景管线
- 证据：`AIStoryWriter/Writer/Chapter/ChapterGenerator.py:112-298`（S1 情节→S2 角色发展→S3 对话，每阶段拿上一阶段全文扩写；S4 终稿修正已整段注释停用，:280-297）；`Writer/Scene/ChapterByScene.py:12-31`（场景管线：章纲→场景列表→JSON 化→逐场景写作→拼接为粗章）；`Writer/Scene/ScenesToJSON.py:17`（场景列表结构化，用 CHECKER_MODEL 槽）；`Write.py:172-176`（场景管线默认开）。
- 机制：输入=本章纲+前文语境 → 默认走场景管线出粗章（等价 S1）→ S2 在粗章上补角色发展层 → S3 再补对话层 → 输出三遍渐进扩写后的章。每阶段都有「摘要对照检查」内循环（见 M12）。
- mo-shu 映射：与我们 B 段三遍苏格拉底写作同构（多遍渐进成稿），但他们是**固定三遍固定焦点**（情节/角色/对话），我们是三遍质疑式打磨。场景 JSON 化一步与 moshu-write 细纲的场拆分等价。**他们有而我们没有的**：遍与遍之间的焦点显式命名（每遍只干一件事）——我们三遍的定义在 skill 文本中已有，无实质差。
- 结论：**理念可学（弱）**；形态为自动管线不引入。

### M12 双层修订环与二元质量门禁（含 0-100 分弃用史）
- 证据：`AIStoryWriter/Writer/Chapter/ChapterGenSummaryCheck.py:14-66`（阶段内检查：<100 词直接判「试图逃避写作」；否则双摘要对照——分别摘要产出与参考纲，再让评审模型比对输出 JSON 判「是否遵循大纲」+建议）；`Writer/LLMEditor.py:25-70,99-141`（章级/大纲级评分：评审模型输出 JSON 的 IsComplete 布尔）；`Writer/OutlineGenerator.py:56-57`（关键历史注释：评分**从 0-100 整数改为是否达标的布尔**，因为「0-100 的整数评分完全不靠谱，LLM 只会返回一堆垃圾分数」）；`Writer/Config.py:30-42`（修订环参数：大纲最少 0 次/最多 3 次，章最少 1 次/最多 3 次，质量阈值名义值 85/87）。
- 机制：两层回路——①**阶段内**：每次生成后做「摘要对照检查」，不通过则带反馈重生成（换随机种子），超上限强制放行；②**章级/大纲级**：批评模型出文字意见（REVISION_MODEL 槽）+ 评分模型出布尔达标判定（EVAL_MODEL 槽，**意见与评分分设两个模型槽**），达标且达最少修订数则停，否则带意见修订，最多 3 轮。
- mo-shu 映射：对应 build Phase B evaluator 环。**最有价值的发现是那条弃用史注释**：LLM 打 0-100 分不可靠、改二元判定才稳——与我们「测协议不测实现、判定吃确定性结果」的纪律在 LLM 评审维度上互相印证；若未来 evaluator 输出质量分，应优先二元/枚举判定而非连续分数。另「评审意见与达标判定分设两个模型槽」是防止同一模型既当教练又当裁判的廉价隔离。
- 结论：**理念可学**（二元门禁优先于连续分数；意见/判定分离——落点在未来 evaluator 设计叙述里，不新开管线）。

### M13 鲁棒生成基础设施（SafeGenerateText / SafeGenerateJSON）
- 证据：`AIStoryWriter/Writer/Interface/Wrapper.py:138-169`（SafeGenerateText：空回复或低于最短词数则删掉失败尝试、换随机种子重试，保证输出非空非敷衍）；`:171-174`（从历史消息中剥离推理模型残留的思考标签）；`:176-201`（SafeGenerateJSON：解析失败删失败尝试重生成，校验必需字段存在）；各业务处 JSON 解析失败把报错原文喂回模型要求修正，最多 4 次后降级返回失败（`Writer/LLMEditor.py:47-70` 等）。
- 机制：输入=消息列表+模型槽+约束 → 生成 → 校验（非空/最短词数/JSON 可解析/必需字段）→ 失败则换种子重试，JSON 失败则把解析错误回喂 → 输出=保证满足结构约束的文本。
- mo-shu 映射：这是我们「AI 产出先落文件+确定性脚本校验」的流水线版镜像——在无 Claude Code 工具环的裸 API 环境里自建可靠性层。mo-shu 场景下等价物已由机检链+追踪事务承担；「把解析报错原文回喂让模型自修 JSON」一招对 moshu 侧偶尔的结构化产出失败可作话术参考（skill 文本层面）。
- 结论：**理念可学（弱）**；不引入基础设施。

### M14 擦洗、终编与生成档案
- 证据：`AIStoryWriter/Writer/Scrubber.py:5-27`（全书逐章「擦洗」遍：清除提示残留与大纲碎屑——LLM 生成文本常混入元话语/计划残片）；`Writer/NovelEditor.py:6-35` 与 `Write.py:343-347`（全书终编遍：**代码事实——该遍是死代码**：开关打开会调用 EditNovel，但下一行无条件 `NewChapters = Chapters` 把结果覆盖丢弃；且 NovelEditor.py:26 引用了 Config 中不存在的 `CHAPTER_WRITER_MODEL` 槽，真跑会抛异常）；`Write.py:439-471`（产物双档案：.md 正文头部内嵌全部生成设置与模型分配、.json 存各阶段中间产物）。
- 机制：输入=全书章列表 →（可选死代码终编）→ 擦洗遍逐章清残留 →（可选翻译遍）→ 输出=md+json 双档案，md 自带完整生成溯源（模型/种子/迭代参数）。
- mo-shu 映射：擦洗遍对应 deslop/清稿职能；生成档案对应我们的机检报告与追踪事务留痕。死代码发现的意义在反面：**未接通的终编遍带着开关注入仓库**——若 mo-shu 引入任何可选遍，须有守卫验证其真的生效（我们 CI 三处同步纪律的同类问题意识）。
- 结论：**不学**（形态为自动整书管线）；死代码教训记入 §5。

### M15 一致性手段总账（其上下文策略的弱点）
- 证据：`AIStoryWriter/Writer/Chapter/ChapterGenerator.py:36-46`（上下文注入=**全书已写章节全文拼接**（ChapterSuperlist）+大纲）；`:77-102`（另生成上一章摘要作为补充，但 `:105-108` 显示摘要生成后实际未并入注入模板——代码事实：FormattedLastChapterSummary 被计算但 DetailedChapterOutline 仅取 ThisChapterOutline）；`Write.py:317-333`（逐章串行，前文列表滚动增长）；`AIStoryWriter/Todo.md:1-10`（作者自认待办：章节衔接与连贯性是已知短板，并考虑 sbert 知识图谱方向——后者触 §6 RAG 不学）。
- 机制：一致性全靠「把已写全文塞进上下文」这一 brute-force 手段，无状态提取、无实体账本、无检索（代码中无任何向量/检索实现）；README.md:101-106 自认「章节衔接、节奏」为待改进区（文档宣称）。
- mo-shu 映射：**反面印证**——无状态层的长篇一致性靠全文重注入不可扩展（上下文平方膨胀、且与我们的已知缺口「追踪视图全量读入无按需注入」同病但更重）。他们的 Todo 方向（知识图谱/RAG）恰是我们宪法已禁的路；我们按需注入缺口的解法应继续走「派生视图裁剪+确定性选择注入」而非检索。
- 结论：**不学**（含其拟议的 RAG 方向，触 §6）。

---

## 2 与 mo-shu 差异对照

| 维度 | Claude-Book | AIStoryWriter |
|---|---|---|
| 形态 | Claude Code 技能包（CLAUDE.md 编排 + 6 agent + 4 skill + 2 Python 机检脚本） | 纯 Python CLI 流水线（无宿主、无 skill 概念） |
| 人在环 | 作者发起/抽点审阅（.work/ 落盘、改稿前问询） | 无人值守，一段 prompt 一口气出整书 |
| 作品资产 | 文件目录（bible/state/story/timeline），可 git、可手改 | 内存列表，终点是一份 md+json（无中间资产目录） |
| 状态权威 | LLM agent 手写状态文件，symlink 指针，无 schema 无校验 | 无状态层（全文重注入），仅 JSON 副产物留档 |
| 大纲 | 单文件全书章纲（plan.md，人写/AI 辅助）+ 每章 planner 现拍 beat | LLM 五步自动推导（元素→大纲→章数→逐章纲→MegaOutline） |
| 章成稿 | 一遍直写成（writer 按拍严格执行） | 三遍渐进扩写（情节→角色→对话）+ 修订环 |
| 审查/门禁 | 三正交 LLM 审查 agent + 1 前置脚本，FAIL 回环 max 3 | 双层回路：阶段内摘要对照 + 章/大纲级布尔达标门禁（意见/评分分模型） |
| 模型策略 | 两档铁律：创作 opus / 审查与状态提取 sonnet | 13 槽位组件×模型矩阵，CLI 全可覆盖，产物留档 |
| 一致性手段 | 静态/动态分区 + 知识账 + 时间线 + 状态版本化 | 全文重注入（无状态层）；Todo 拟议 RAG |
| 语言 | 指令英文/产出法语（字段化切换） | 生成后可选整书翻译遍 |
| 防走形 | bible 文风正典 + 量化阈值机检 + 反 AI 味（本地困惑度检测，重） | 擦洗遍（清残留）；README 自认重复用语短板 |
| 与 mo-shu 体量差 | 单本 18 章（timeline 已 2256 行即露疲态） | 中长篇一次性生成（不可续写、无日更概念） |

---

## 3 策展清单轻扫（8 条高相关条目）

选条标准：对齐四缺口（修订环/上下文管理/长篇一致性/大纲控制）且前两轮（01-06 号研究：awesome-novel-studio、autonovel、book-os、storycraftr、Long-Novel-GPT、NovelForge、long-novel-writer、SillyTavern）未覆盖。**以下全部为文档宣称**（清单条目仅核验链接，论文内容未验证；清单自带策展政策见 `awesome-llm-story-generation/docs/curation_policy.md`）：

1. **DOC: Improving Long Story Coherence With Detailed Outline Control**（2022-12，arXiv 2212.10077）——大纲控制经典基线：采样多候选大纲人择一、逐段扩写并携带前文摘要续写，与我们「细纲+上文卡」路线同族，可对照其消融结论。（文档宣称）
2. **RecurrentGPT: Interactive Generation of (Arbitrarily) Long Text**（2023-05，arXiv 2305.13304，清单标 64 引）——递归长文：每步维护短期记忆（近文摘要）+长期记忆（可更新关键词索引）+下步计划三件套，输出一段+更新后的记忆块——与我们「上下文.md 续写状态卡+单权威 state 派生」是同一问题的学术同构，其「记忆块显式更新」表述对按需注入缺口有参考价值。（文档宣称）
3. **Re3: Generating Longer Stories With Recursive Reprompting and Revision**（2022-10，arXiv 2210.06774）——修订环源头文献：计划→草稿→多轮改写的长故事管线，修订环谱系（Re3→DOC→RecurrentGPT）的起点。（文档宣称）
4. **Generating Long-form Story Using Dynamic Hierarchical Outlining with Memory-Enhancement**（NAACL 2025，arXiv 2412.13575）——动态层级大纲+记忆增强：大纲在写作过程中可回改而非一次定型，对多卷并发/大纲回调场景有参照意义。（文档宣称）
5. **FACTTRACK: Time-Aware World State Tracking in Story Outlines**（NAACL 2025，arXiv 2407.16347）——**大纲中的时间感知世界状态跟踪**：实体状态随情节推进在大纲层同步更新，与 mo-shu「单权威 state+细纲」双账对账问题直接对口。（文档宣称）
6. **Codified Foreshadowing-Payoff Text Generation**（2026-01，arXiv 2601.07033）——伏笔-回收对的编码化生成：把「埋设→回收」作为受控任务，与我们伏笔.md 悬置章距机制同一问题域的最新工作。（文档宣称）
7. **Lost in Stories: Consistency Bugs in Long Story Generation by LLMs（ConStory-Bench）**（2026-03，arXiv 2603.05890，同 Picrew 组织，带代码）——长篇一致性 bug 分类基准：系统性归类 LLM 长篇生成的一致性错误类型，对百万字防走形缺口的「错误分类学」有直接参考价值。（文档宣称）
8. **SuperWriter: Reflection-Driven Long-Form Generation**（2025-06，arXiv 2506.04180）——反思驱动长文生成：生成中自反思改进长文质量，修订环谱系近期代表。（文档宣称）

---

## 4 不学清单冲突核查

| 项 | 涉及条目 | 判定 |
|---|---|---|
| perplexity-improver（本地 LLM 困惑度检测反 AI 味，`Claude-Book/README.md:88-104`） | §6「外部 AI 检测器依赖进主链路」 | **不学**：属检测器依赖（本地 Ministral-3-8B，需 ~16GB VRAM）；且 mo-shu deslop skill 已覆盖同职能；附带触反模式 #8（检测需 GPU 跑 LLM） |
| AIStoryWriter Todo 拟议 sbert 知识图谱（`Todo.md:10`，未实施） | §6「RAG/向量检索」 | **不学**，一句话带过：代码中无任何检索实现，仅作者待办方向 |
| Claude-Book claude-code-action CI（`.github/workflows/claude.yml`，@claude 触发） | 反模式 #8「CI/守卫跑 LLM 或联网」（施工纪律） | **不学**：CI 内跑 LLM |
| Claude-Book state/chapter-NN 每章状态目录 | §6「每章全量快照」（辨析） | **不引入**：其为 4 个小状态文件的版本化非正文快照，严格说不触该条；但 mo-shu 追踪事务重放已等价覆盖且成本更低，无增量 |
| AIStoryWriter 无人值守整书生成形态 | §6「自动连写污染传播」（无暂存无作者定稿的连写） | **不学其形态**：其机制（模型矩阵 M9、二元门禁 M12）转述为策略层借鉴，落地物均为「作者在环」的 skill 约定 |
| Claude-Book CLAUDE.md 编排 | §6「LLM 导演黑盒自治」（辨析） | **不冲突**：编排器是确定性文档流程、顺序固定、作者发起，非水平 agent 自治通信 |

其余机制（M1/M3-M8/M9/M12）均不触 §6 十四条。

---

## 5 （推断）与存疑

1. **（推断）timeline 全量日志不可扩展**：Claude-Book 18 章（约 4 万字儿童文学）的 history.md 已达 2256 行/约 4.5 万 token（Read 实测）。据此推断百万字网文下该设计崩溃，反证 mo-shu「派生视图+按需注入」方向的必要性——但「按需注入」的具体裁剪规则两仓均无可抄答案，仍需自研。
2. **（代码事实→推断）守卫数字漂移实例**：Claude-Book style_checker.py:30-31（2800-3200 词）与 bible/style.md:126（1500-2500 词）不一致。推断为后期调参未回写文档——外部印证 mo-shu 反模式 #1/#6 的必要性。
3. **（代码事实）AIStoryWriter 终编遍死代码**：`Write.py:343-347` 调用 EditNovel 后无条件覆盖其结果，且 `NovelEditor.py:26` 引用不存在的 Config 槽——推断该功能从未在当前形态下运行过。教训：可选遍须有生效性守卫。
4. **（代码事实→推断）摘要注入断线**：ChapterGenerator.py:77-108 生成「上一章摘要」后未实际并入 DetailedChapterOutline（变量计算后被弃）。推断为半途重构残留。
5. **（存疑）外部元数据**：三星数与最后 push 日期取自任务书（2026-08-27 快照），未在线复核；两主仓均为浅克隆（git log 仅 1 commit），开发活跃度与贡献者结构无法从本地判定。
6. **（存疑）清单归属**：awesome 仓 remote 为 Picrew/awesome-llm-story-generation，但其 README 引用 bibtex 署名 lijunjie（`README.md:409-415`）——（推断）仓库可能迁移或换手；不影响条目内容，但条目可信度以「链接核验制」为限，故第 3 节全部标文档宣称。
7. **（推断）「组件×模型」跨仓收敛**：Claude-Book（opus 创作/sonnet 审查提取）与 AIStoryWriter（13 槽位+实测注释「70B 指令模型当写手很差」）在互不依赖的前提下收敛到「创作与判定分档」——推断该策略对 Claude Code 场景亦成立，值得作为 mo-shu agents 模板的成文默认。
8. **（推断）Claude-Book agent 的 tools 字段不对称**（planner/writer 未声明、三 reviewer 声明全量白名单）：推断为审查者需跨文件 Grep/Read 而创作 agent 只需写盘的刻意安排，无文档确证。

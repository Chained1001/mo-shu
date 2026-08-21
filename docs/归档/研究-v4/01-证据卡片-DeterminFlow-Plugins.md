# 01-证据卡片 · DeterminFlow-Plugins（bishu-novel 笔枢插件）

| 项 | 值 |
|---|---|
| 研究对象 | DeterminFlow-Plugins 仓库 `plugins/bishu-novel`（笔枢插件，纯资源插件无后端代码） |
| 版本标注 | bishu-novel v0.2.2（`extension.toml:4`），commit `a252ea8`（见研究-v3 档案01 §1） |
| 证据基准 | 下文路径均为 **bishu-novel 插件根相对**（即 `otherMaterials/referProject/DeterminFlow-Plugins/plugins/bishu-novel/` 下），与研究-v3 档案01 §1 的"无前缀=插件根相对"约定一致 |
| 复用说明 | 七条 Workflow/32 节点 mvp/真源哲学/33 Agent/确定性纪律等全景已结，见研究-v3 档案01；本轮只记六维增量 |
| 证据分档 | 【事实】= 代码/定义可复现；（推断）= 研究者推断；存疑 = 需进一步验证 |

---

## 维度 1 · 资产分层（设定/大纲/卷纲/细纲/正文的文件与真源-派生关系）

| # | 机制一句话 | 证据（相对路径:行号） | 档案 | 版本 |
|---|---|---|---|---|
| 1-1 | 全书资产落五目录：`world/`（6 维世界观 JSON）、`meta/`（世界观/角色/故事引擎/风格/伏笔/债务 MD）、`outline/`（卷纲+近纲 MD）、`story/<章节>/`（正文+逐章状态+差异文件）、`archive/`（伏笔/债务索引 JSON） | `resources/skill-bundles/writing-assistant/references/workspace.md:22-62`（完整目录树）；`resources/skill-bundles/writing-assistant/references/workspace.md:66`（五目录=阶段判断证据） | 【事实】 | v0.2.2 |
| 1-2 | 真源/派生双轨：JSON（`cache/`、`world/`、`archive/`）是机器真源，MD（`meta/`、`outline/`、`story/`）是可读渲染，由 `render` 节点统一转换；`archive/hooks.json`↔`meta/hooks.md` 明确"不要只改一边制造不一致" | `resources/script-library/nvl/local_archive/local_archive.py:278-286`（`_render_files` inputs/outputs 一一对应）；`resources/skill-bundles/writing-assistant/references/workspace.md:70-71`；`resources/script-library/nvl/local_archive/local_archive.py:270-275`（`body.json` 特例直取 `body` 字段） | 【事实】 | v0.2.2 |
| 1-3 | 长期区（`world/meta/outline/story/archive`）与可审计中间区（`cache/`）分离，`cache/` 可整体清理 | `resources/skill-bundles/writing-assistant/references/workspace.md:64-69` | 【事实】 | v0.2.2 |
| 1-4 | 卷纲文件=单卷叙事边界（定位/三幕/冲突/节点/出场角色/卷末落点），真源 `cache/vo/volume.json` 派生 `outline/volume_outline.md` | `resources/script-library/nvl/vo_post/vo_post.py:24-80`（`render_volume` 字段）；`resources/workflows/outline/definition.json:104-107`（checkpoint `volume.json,volume_outline.md`） | 【事实】 | v0.2.2 |
| 1-5 | 近纲文件=逐章规划（章节范围/弧线/角色弧线/决策点），真源 `cache/no/near_term.json` 派生 `outline/near_term_outline.md` | `resources/script-library/nvl/no_post/no_post.py:33-59`（`render_full` 字段）；`resources/workflows/outline/definition.json:187-189`（checkpoint `near_term.json,near_term_outline.md`） | 【事实】 | v0.2.2 |
| 1-6 | 细纲=分镜（storyboard）=四维度意图卡片（剧情/人物/叙事/风格导演），逐章落 `story/<章>/storyboard.md`，真源 `cache/se/se_output.json` | `resources/script-library/nvl/se_post/se_post.py:2`（"四维度意图卡片"）+ `se_post.py:24-28`（plot/character/narrative/style 四子块）；`resources/workflows/mvp/definition.json:186-190`（se_post 落 `storyboard.md`） | 【事实】 | v0.2.2 |
| 1-7 | 正文=`story/<章>/chapter.md`，真源 `cache/si/body.json`（单写手与整合写手两路径同落此文件）；单章指导=`single_chapter_guide.md`（真源 `cache/od/guide.json`） | `resources/workflows/mvp/definition.json:821-827`（`render body.json→chapter.md`）；`resources/workflows/mvp/definition.json:633`、`:656`（两写手同落 `cache/si/chapter.json`）；`resources/workflows/mvp/definition.json:762-766`（`render guide.json→single_chapter_guide.md`） | 【事实】 | v0.2.2 |
| 1-8 | 世界观双层：静态设定（`world/` 6 维 JSON → `meta/world_foundation.md`）+ 逐章动态状态（`cache/we/world_state.json`+`world_events.json` → `story/<章>/world_state.md`+`world_events.md`）；后者含 forces/undercurrents/power_shift 力量格局字段 | `resources/script-library/nvl/we_post/we_post.py:13-30`（state/events 字段含 `power_shift`）；`resources/workflows/mvp/definition.json:721-737`（render world_state+world_events） | 【事实】 | v0.2.2 |
| 1-9 | 角色双层：静态档案（`cache/character/{skeleton,beliefs,{name}_deep,voice}.json` → `meta/character_profiles.md`+`meta/character_voice.md`）+ 逐章动态状态（`cache/cm/character_states.json`+`minor_characters.json` → `story/<章>/character_state_long.md`+`character_minor.md`） | `resources/script-library/nvl/cm_post/cm_post.py:12-18`；`resources/workflows/character/definition.json:238-242`（merge→`meta/character_profiles.md`）、`:322-325`（voice→`meta/character_voice.md`）；`resources/workflows/mvp/definition.json:791-796`（render character_state+minor） | 【事实】 | v0.2.2 |

---

## 维度 2 · 修订机制（影响分析/级联/stale/回滚/版本管理/触发点与代价）

| # | 机制一句话 | 证据（相对路径:行号） | 档案 | 版本 |
|---|---|---|---|---|
| 2-1 | 静态设定层修订=重跑覆盖，无级联影响分析：`build`/`character`/`story-plan`/`outline`/同章 `mvp` 都覆盖固定输出；重建世界观前仅"解释连续性风险+备份工作区"（人肉影响说明，非自动波及） | `resources/skill-bundles/writing-assistant/references/workflows.md:26`；`resources/skill-bundles/writing-assistant/references/workspace.md:76-77` | 【事实】 | v0.2.2 |
| 2-2 | 卷纲修订=按卷号的段落级替换：`replace_volume_section` 用正则 `## 卷{N}` 定位旧卷段落替换，未命中则追加（非全量级联） | `resources/script-library/nvl/vo_post/vo_post.py:83-100`；`resources/workflows/outline/definition.json:42-43`（"目标卷号 ≤ 最大已有卷号 → 重写该卷…输出覆盖旧内容"） | 【事实】 | v0.2.2 |
| 2-3 | 卷纲重写语义=可推翻旧定位/冲突/节点/角色，不背旧内容包袱 | `resources/prompts.json:486`（"重写意味着可以调整定位、冲突、节点、角色"） | 【事实】 | v0.2.2 |
| 2-4 | 近纲修订=覆盖/追加双模式由 `is_new_volume` 控制（true 覆盖、false 追加）；但 agent 首消息两分支都写 `is_new_volume=true`，追加分支疑似不可达（存疑） | `resources/script-library/nvl/no_post/no_post.py:78-97`（覆盖/追加分支）；`resources/workflows/outline/definition.json:125-126`（两分支均 true）；`resources/prompts.json:412`（novel-outliner 新卷/重写均 `is_new_volume=true`） | 【事实】+存疑 | v0.2.2 |
| 2-5 | 索引级修订=幂等合并：hooks/debts 按 `id` 去重 merge（同 id 后值覆盖前值），条目缺 `id` 直接报错 | `resources/script-library/nvl/local_archive/local_archive.py:95-120`（`_merge_index`） | 【事实】 | v0.2.2 |
| 2-6 | 章后对照修订机制（observer/arbiter 两级）：observer 只逐条对照提取差异不做判断，arbiter 对世界事实三分类裁决 adopt/pending/conflict | `resources/prompts.json:1936`（observer description）、`:1940`（"只做对照…不做判断、不分类、不裁决、不建议"）；`:2002`（arbiter description）、`:2016`（adopt/pending/conflict 三裁决） | 【事实】 | v0.2.2 |
| 2-7 | 裁决保守化规则：低风险自动 adopt、涉及力量体系默认 pending、只在直接明确矛盾才判 conflict；pending 比 adopt 安全 | `resources/prompts.json:2016`（"涉及力量体系默认 pending"）；`:2046`（"pending 比 adopt 安全，conflict 只在直接矛盾时才判"） | 【事实】 | v0.2.2 |
| 2-8 | 修订产物落盘为"差异文件"而非回写真源：`_post_hoc` 写 `diff_world_resolved.json`/`diff_story_confirmed.json`/`diff_character.json`（story/<章>/），再把 new_hooks/new_debts 幂等合并进 archive 索引 | `resources/script-library/nvl/local_archive/local_archive.py:323-351`（`_post_hoc`） | 【事实】 | v0.2.2 |
| 2-9 | 修订回流：下一章 mvp 把上一章 `diff_world_resolved`/`diff_story_confirmed`/`diff_character` 作为输入注入世界状态机/大纲导演/角色维护师 | `resources/workflows/mvp/definition.json:1114-1124`（`prev_diff_world`）、`:1186-1196`（`diff_story_file`）、`:1221-1232`（`prev_diff_character`）；`resources/workflows/mvp/definition.json:42`（agent_we 首消息"上一章后验裁决"） | 【事实】 | v0.2.2 |
| 2-10 | 未发现：自动影响分析（波及哪些下游）/ stale 标记 / schema 版本管理 / 自动回滚——修订只覆盖单文件或单段落，下游一致性靠两条人肉约定：润色改情节事实须重跑 post-hoc、覆盖前复制整个工作区备份 | `resources/skill-bundles/writing-assistant/references/workflows.md:73-74`（"若最终正文事件…发生变化，后续必须重新做 post-hoc"）；`resources/skill-bundles/writing-assistant/references/workspace.md:81`（"没有版本控制或恢复副本时，建议复制整个工作区再运行"） | 未发现该机制（无代码佐证）+【事实】（人肉约定存在） | v0.2.2 |
| 2-11 | 修订触发点与代价：卷纲重写触发=目标卷号≤已有最大卷号、近纲重写触发=目标卷号≤已有近纲最大卷号、世界观重建触发=重跑 build、正文重写触发=同章重跑 mvp；代价=覆盖前需人工备份（无版本管理） | `resources/workflows/outline/definition.json:252`（"传数字则重写对应卷"）；`resources/skill-bundles/writing-assistant/references/workspace.md:76-82`（覆盖类四步确认）；`resources/skill-bundles/writing-assistant/references/workflows.md:64-65`（同章 mvp 覆盖 chapter.md） | 【事实】 | v0.2.2 |

---

## 维度 3 · 构建-执行分离（构思/设定/大纲 vs 写章如何切分；细纲归哪层）

| # | 机制一句话 | 证据（相对路径:行号） | 档案 | 版本 |
|---|---|---|---|---|
| 3-1 | 七条 Workflow 硬切两层：构建链 `build→character→story-plan→outline` 与单章循环 `mvp→polish(可选)→post-hoc`，各为独立 workflow（独立节点图/会话 Task） | `resources/skill-bundles/writing-assistant/references/workflows.md:7-18`（顺序表）；`resources/skill-bundles/writing-assistant/SKILL.md:107-113` | 【事实】 | v0.2.2 |
| 3-2 | 构建层"只定义力的性质与规律，不定义落地"：story-planner 明确产出是下游力学基础，且"绝不做下游的事" | `resources/workflows/story-plan/definition.json:42`（"只定义力的性质和规律，不定义力在哪一章以什么事件落地"）；`resources/prompts.json:1639`（"你绝不做下游的事"） | 【事实】 | v0.2.2 |
| 3-3 | 细纲（分镜 storyboard）归执行层：由 mvp 内 `agent_se`（意图导演）逐章生成，与卷纲/近纲（构建层）分离 | `resources/workflows/mvp/definition.json:369-390`（agent_se 节点，落 `cache/se/se_output.json`）、`:186-190`（se_post 落 `story/<章>/storyboard.md`） | 【事实】 | v0.2.2 |
| 3-4 | 单章指导（`single_chapter_guide.md`）也归执行层：由 mvp 内 `agent_od`（大纲导演）逐章产出，不是构建层的卷/近纲 | `resources/workflows/mvp/definition.json:203-224`（agent_od 节点）、`:762-766`（render→`single_chapter_guide.md`） | 【事实】 | v0.2.2 |
| 3-5 | 构建层 agent 与执行层 agent 分属不同 workflow：卷纲规划者/近纲规划者在 `outline`；世界状态机/大纲导演/意图导演/角色维护师/裁剪器/写手群在 `mvp` | `resources/workflows/outline/definition.json:37-141`（agent_vo/agent_no）；`resources/workflows/mvp/definition.json:37-59`（agent_we）、`:203-224`（agent_od）、`:286-307`（agent_cm）、`:369-390`（agent_se）、`:392-413`（agent_trimmer） | 【事实】 | v0.2.2 |
| 3-6 | 卷纲↔近纲↔单章指导↔分镜的粒度递进链（管线站位）：故事引擎 → 卷纲 → 近纲 → 单章导演 → 分镜导演，每层"画边界不画路线" | `resources/prompts.json:1639`（"你位于管线第3站…卷纲→近纲→单章导演→分镜导演"）；`resources/prompts.json:486`（卷纲"画边界，不画路线"） | 【事实】 | v0.2.2 |

---

## 维度 4 · 技能/角色架构（功能划分原则/角色清单/数量与过度拆分）

| # | 机制一句话 | 证据（相对路径:行号） | 档案 | 版本 |
|---|---|---|---|---|
| 4-1 | 功能划分原则=边界铁律（每个角色只回答一个问题、只做一件事）：大纲导演"只回答这一章发生了什么为什么，不回答怎么写"；卷纲"只定义必须发生什么不定义怎么发生"；近纲"不写正文/不管理伏笔/不裁决世界事实"；observer"只做对照不裁决"；arbiter"只裁决差异不重读正文" | `resources/prompts.json:10`（大纲导演边界铁律）；`:486`（卷纲）；`:442`（近纲）；`:1940`（observer）；`:2046`（arbiter"正文好坏与你无关"） | 【事实】 | v0.2.2 |
| 4-2 | 33 个 Agent（agents.json 33 条目，temperature/max_turns 各 33 对）；生成型与消费型分列：生成型=6 worldbuilder+character 四件套+story-planner+style-profiler+volume-outliner+outliner+写手群；消费/裁决型=世界状态机 observer+章节观察员+仲裁器+角色维护师+上下文裁剪器+意图分发器 | `resources/agents.json`（33 条目，grep `temperature`/`max_turns` 各 33 匹配）；生成/消费分列见 `resources/workflows/build/definition.json:7-143`（6 worldbuilder）、`resources/workflows/mvp/definition.json:37-59,286-307,392-413,475-636` | 【事实】 | v0.2.2 |
| 4-3 | 温度三档按任务类型（规划 0.9 / 事实裁决 0.3 / 批评 0.4）+ max_turns 按职责收紧（single-writer=1、trimmer=15、intent-distributor=20）——见研究-v3 档案01 §5.1，此处补单行证据 | `resources/agents.json:19`(0.9)、`:88`(0.3)、`:157`(0.4)、`:263`(max_turns=1)、`:699`(max_turns=15)、`:655`(max_turns=20) | 【事实】 | v0.2.2 |
| 4-4 | 过度拆分教训=多写手群成本高：写手群=骨架写手+5 专项写手(dialogue/action/internal/description/transition)+整合写手，但 single 是默认路由，SKILL 明示"多写手成本和整合复杂度更高" | `resources/workflows/mvp/definition.json:475-636`（nw+5 专项+si）；`:1053-1076`（条件网关 `writer_type==muti` 才走写手群，默认 single）；`resources/skill-bundles/writing-assistant/SKILL.md:79-80` | 【事实】 | v0.2.2 |
| 4-5 | 写手群细分到"槽位级"职责：骨架写手只产出带 `[SLOT_X]` 标记的叙事骨架，5 专项写手各自只填一类槽，整合写手再替换槽+重排+润色 | `resources/workflows/mvp/definition.json:480`（"带 [SLOT] 标记的叙事骨架"）、`:505`（对话写手"只填充 [SLOT_DIALOGUE_X]"）、`:527`/`:551`/`:574`/`:597`（各专项槽）、`:620`（整合"替换槽"） | 【事实】 | v0.2.2 |

---

## 维度 5 · 上下文衔接（构建产物如何喂给写作；写作变化如何回流构建层）

| # | 机制一句话 | 证据（相对路径:行号） | 档案 | 版本 |
|---|---|---|---|---|
| 5-1 | 构建产物喂给写手=单个 `wroter_context` textarea 变量全量拼接，按标题分节拼好风格指南/角色声音锚/长线角色状态/本章大纲(单章指导)/本章世界状态/裁剪后世界观/次要角色注册表 | `resources/workflows/mvp/definition.json:1510-1519`（`wroter_context` default 全文分节拼接） | 【事实】 | v0.2.2 |
| 5-2 | 上下文减法裁剪：trimmer LLM 只出减法列表（不重写内容），`trimmer_post.py` 才动数据；世界按"维度→二级字段"删，角色"整进整出" | `resources/script-library/nvl/trimmer_post/trimmer_post.py:27-39`（世界二级字段删）、`:42-51`（角色整进整出）；`resources/workflows/mvp/definition.json:392-413`（trimmer 出 `subtract.json`）、`:425-433`（trimmer_post 执行） | 【事实】 | v0.2.2 |
| 5-3 | 上下文合成=确定性拼接（非检索）：`prepare --context` 把 6 维世界观合 `cache/sync/world.json`、角色四件套按 name 合 `cache/sync/characters.json`、近纲摘录合 `cache/sync/near_term_we.md` | `resources/script-library/nvl/local_archive/local_archive.py:123-138`（`_build_world_cache`）、`:157-196`（`_build_character_cache`）、`:199-224`（`_render_near_term_context`） | 【事实】 | v0.2.2 |
| 5-4 | 写作中的变化回流：post-hoc 产出三差异文件+hooks/debts 合并，下一章 mvp 以 `prev_diff_world`/`diff_story_file`/`prev_diff_character` 注入消费 | `resources/script-library/nvl/local_archive/local_archive.py:330-351`（差异落盘+索引合并）；`resources/workflows/mvp/definition.json:1114-1124,1186-1196,1221-1232`（prev_diff_* 变量） | 【事实】 | v0.2.2 |
| 5-5 | 世界状态机逐章演化世界状态，只读近纲时间推进与上一章后验裁决，不读正文（"水面以下"演化与正文隔离） | `resources/prompts.json:300`（"你唯一的驱动来源是近纲中的世界时间推进…你不读任何章节正文"）；`resources/workflows/mvp/definition.json:42`（agent_we 输入"上一章后验裁决"） | 【事实】 | v0.2.2 |

---

## 维度 6 · 人机分工（修订流程的作者裁决点）

| # | 机制一句话 | 证据（相对路径:行号） | 档案 | 版本 |
|---|---|---|---|---|
| 6-1 | 修订的作者裁决点=覆盖/重写类操作前的"影响清单式确认"：先说明会覆盖哪些长期文件，无副本则建议备份整个工作区（人肉影响清单，非自动级联分析） | `resources/skill-bundles/writing-assistant/SKILL.md:81-82`；`resources/skill-bundles/writing-assistant/references/workspace.md:76-82`（四步：确认目标→说明受影响文件→建议备份→验证非空） | 【事实】 | v0.2.2 |
| 6-2 | 章后修订（observer/arbiter）的裁决是机器自动三分类，非作者裁决：adopt/pending/conflict 由 arbiter 直接产出，`_post_hoc` 无过滤无确认门地全量落 diff 文件，下一章自动消费——pending/conflict 无作者确认闸口（存疑：Core 引擎是否另呈报用户，bishu 脚本内未见） | `resources/prompts.json:2016`（arbiter 自动三裁决）；`resources/script-library/nvl/local_archive/local_archive.py:330-333`（`world_rulings` 全量落盘）；`resources/workflows/mvp/definition.json:42`（下一章直接读） | 【事实】+存疑 | v0.2.2 |
| 6-3 | 作者是最终决策者、不越过用户做关键创作决定；信息不足时给 2-3 个选项；已明确授权则不重复索要形式确认（一次授权原则） | `resources/skill-bundles/writing-assistant/SKILL.md:24-33` | 【事实】 | v0.2.2 |
| 6-4 | 节点级审批/流转开关（`enable_complete_node_task`/`auto_flow`/`max_reject_count`），审批只批"真实审批请求"并用最新 `attempt_count`——审批语义依赖 Core 引擎（存疑，见研究-v3 档案01 §13.2） | `resources/workflows/outline/definition.json:26-30`（auto_flow=false/enable_complete_node_task=true/max_reject_count=3）；`resources/skill-bundles/writing-assistant/SKILL.md:95-96` | 存疑 | v0.2.2 |
| 6-5 | 汇报协议：当前阶段必须由非空文件证明、只推荐一条下一步；失败时说明停在哪/保留了什么/用户需决定什么（把裁决权交回作者） | `resources/skill-bundles/writing-assistant/SKILL.md:121-134` | 【事实】 | v0.2.2 |

---

## 六维覆盖表

| 维度 | 覆盖 | 说明 |
|---|---|---|
| 1 资产分层 | ✅ | 设定/角色/故事引擎/卷纲/近纲/细纲(分镜)/单章指导/正文/逐章状态 九类资产 + JSON 真源↔MD 派生双轨 + 长期区/cache 区 |
| 2 修订机制 | ✅（含"未发现"标注） | 静态层重跑覆盖、卷纲段落替换、近纲覆盖/追加、索引幂等合并、observer/arbiter 章后对照、差异文件回流；未发现影响分析/stale 标记/版本管理/自动回滚 |
| 3 构建-执行分离 | ✅ | 七条 workflow 两链；细纲（分镜）与单章指导归执行层，卷纲/近纲归构建层 |
| 4 技能/角色架构 | ✅ | 33 Agent、边界铁律、温度三档+max_turns、多写手群过度拆分教训 |
| 5 上下文衔接 | ✅ | wroter_context 全量拼接、trimmer 减法裁剪、确定性合成、post-hoc diff 回流 |
| 6 人机分工 | ✅ | 覆盖类操作前影响清单+备份建议、机器自动裁决非作者裁决（存疑）、一次授权原则、汇报协议 |

---

## 主要证据文件清单（按引用频次）

| 文件 | 角色 |
|---|---|
| `resources/workflows/mvp/definition.json`（1694 行） | 章节生产 32 节点图、变量注入、写手群路由、wroter_context、prev_diff_* 回流 |
| `resources/workflows/outline/definition.json`（401 行） | 卷纲/近纲规划、重写触发词、checkpoint |
| `resources/workflows/post-hoc/definition.json`（326 行） | observer/arbiter 章后管线节点与变量 |
| `resources/workflows/build|character|story-plan/definition.json` | 世界观/角色/故事引擎构建层 |
| `resources/prompts.json`（2180 行） | observer/arbiter 裁决三分类、边界铁律、卷纲/近纲重写语义 |
| `resources/script-library/nvl/local_archive/local_archive.py`（394 行） | 真源哲学、幂等合并、post-hoc 差异落盘、上下文合成 |
| `resources/script-library/nvl/{vo_post,no_post,se_post,od_post,we_post,cm_post,trimmer_post}.py` | 各层渲染/拆分/覆盖/裁剪 |
| `resources/skill-bundles/writing-assistant/SKILL.md` + `references/workflows.md` + `references/workspace.md` | 人机分工、覆盖确认、目录分级、推进状态机 |

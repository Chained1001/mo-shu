# 证据卡片 · spark-arc-studio 六维增量证据挖掘

> 研究命题：大纲/卷纲/细纲/正文/设定（世界观/人物/力量体系）在实际写作中反复修订——它们是迭代演化的活资产。
> 研究对象：`otherMaterials/referProject/spark-arc-studio`（**绝对只读**，未做任何写入）。
> 路径约定：本文件所有路径**相对 `otherMaterials/referProject/spark-arc-studio/`**（与 `docs/研究-v3/02-spark-arc-studio-档案.md` 同一约定）。
> 版本标注：该目录无独立 git 历史（见研究-v3 档案02 头注），全部卡片标注「2026-08 快照」；凡引用项目自述文档（README/AGENTS.md/docs）者降级为「文档宣称」。
> 复用约定：标「见研究-v3 档案02」的条目为已有结论，本轮不重述，只补**增量**证据（server/story/ 解析与路由、agent_lorebook.py 设定形态、修订/版本/影响分析逻辑）。

---

## 维度 1 · 资产分层（设定/大纲/卷纲/细纲/正文：文件形态与真源/派生）

| 卡片 | 机制一句话 | 证据（相对路径:行号） | 档案 | 版本 |
|---|---|---|---|---|
| 1.1 | 五类资产落成五类文件：世界观（`世界观.txt`）、角色（独立角色记录）、梗概（`梗概.txt`）、节拍表（`节拍表.txt`）、大纲（`大纲.txt`），正文为 `stories/` 下 `.arc`/`.md` 场景文件 | `server/agents/structure_state.py:13-17`；`server/agents/tools/showrunner.py:49,65,81`；`server/agents/tools/lorebook.py:141`；`server/story/file_naming.py:9,129-154` | 【事实】 | 2026-08 快照 |
| 1.2 | 无独立「细纲/卷纲」文件：细纲=大纲.txt 内的场景契约字段（`### 场景` 下 objective/conflict/turn/post_state/知情边界/禁止铺垫等）；「卷」仅作为章节目录名（中文数字 · 标题） | `server/story/outline_parser.py:64-141`；`server/agents/prompts/showrunner.yaml:236-259`；`server/agents/tools/scriptwriter.py:54-55`（"章节/分卷"目录） | 【事实】 | 2026-08 快照 |
| 1.3 | 真源=大纲.txt：章节/场景身份与聚合顺序由 `大纲.txt` 解析决定，正文文件是派生（按大纲顺序聚合导出） | `server/story/novel_parser.py:237-247`；`server/story/novel_parser.py:352-380`；`server/agents/routes/context_builder.py:408-485` | 【事实】 | 2026-08 快照 |
| 1.4 | 正文文件身份（chapter_num/scene_num）优先由大纲契约签发，其次才从文件名 metadata 回退；文件名隐藏 metadata 存 `chap=/scene=/order=` | `server/agents/scriptwriter_prewrite.py:82-104`；`server/story/file_naming.py:129-154`；`server/agents/tools/scriptwriter.py:284-302` | 【事实】 | 2026-08 快照 |
| 1.5 | 梗概→节拍表→大纲是**显式记录的派生链**（`derived_from` 记上游 revision），真源/派生关系由结构状态文件固化 | `server/agents/structure_state.py:112-123`（`derived_from`）；`server/test/story_context/test_structure_state.py:21-22`（断言 `derived_from == {"synopsis":1}`） | 【事实】 | 2026-08 快照 |
| 1.6 | 设定（世界观/角色）与正文状态分界：世界观只记长期基座，正文最近状态/开放线索/修订工单归 StoryMemory，不写回设定 | `server/agents/prompts/lorebook.yaml:29-30`；`server/agents/prompts/lorebook.yaml:41,111` | 【事实】（文档=yaml prompt，代码在 story_memory 落盘，见研究-v3 档案02 §3.2） | 2026-08 快照 |

---

## 维度 2 · 修订机制（影响分析 / stale / 回滚 / 版本管理：触发点与代价）

| 卡片 | 机制一句话 | 证据（相对路径:行号） | 档案 | 版本 |
|---|---|---|---|---|
| 2.1 | 三级结构产物带 `revision` 计数 + `stale`/`stale_reason` 级联标记：保存 synopsis→标记 beat_sheet+outline 过期；保存 beat_sheet→标记 outline 过期（固定链，非动态依赖图） | `server/agents/structure_state.py:84-126`（`record_structure_save`）；`server/agents/structure_state.py:57-61`（revision≤0 不标 stale） | 【事实】 | 2026-08 快照 |
| 2.2 | stale 级联的**触发点**只挂在「完整保存」收口 `_save_project_markup`（前端编辑器保存 + 生成流 `write_result` 经此）；LLM 聊天/委派模式下的 `rewrite_*/patch_*` 工具直接写文件、**不触发** record_structure_save | `server/agents/routes/schemas.py:372-391`（唯一生产调用点，见 grep）；`server/agents/tools/showrunner.py:40-85`（rewrite_* 直接 `open(w)`）；`server/agents/tools/showrunner.py:88-109`（patch_* 走 `_apply_patch`） | 【事实】（grep 全仓仅 schemas.py 一处调用 record_structure_save） | 2026-08 快照 |
| 2.3 | stale 代价=**咨询性警告不阻断**：注入上下文的「结构版本警告」，明示"过期产物只能作为历史参考，不得覆盖较新的上游事实" | `server/agents/structure_state.py:129-138`（`format_structure_state_warning`）；`server/agents/context_provider.py:267-274,423-424`（注入仅对 showrunner/scriptwriter/director/critic） | 【事实】 | 2026-08 快照 |
| 2.4 | stale 标记**范围仅三结构产物**，世界观/角色/正文均无 revision/stale 跟踪 | `server/agents/structure_state.py:12`（`STRUCTURE_ARTIFACTS=("synopsis","beat_sheet","outline")`）；`server/agents/agent_lorebook.py:238-242`（世界观直接 `open(w)` 无 revision）；`server/agents/tools/lorebook.py:138-142`（patch_worldview 走 `_apply_patch` 无 revision） | 【事实】 | 2026-08 快照 |
| 2.5 | 大纲有独立**版本历史+回滚**机制（与 structure_state 并存）：`history/outline_history.json` 保留最近 20 条含 markup 全文，支持按 id 恢复/删除 | `server/agents/routes/schemas.py:291-315`（`_save_outline_to_history`，`history[:20]`）；`server/agents/routes/outline.py:120-133`（`restore_outline_from_history`）；`server/agents/routes/outline.py:106-117`（delete） | 【事实】 | 2026-08 快照 |
| 2.6 | 大纲历史回滚触发点由 `saveToHistory` 开关控制（默认关）：仅「保存到历史」时快照 | `server/agents/routes/outline.py:74,78-79`（`saveToHistory`）；`server/agents/agent_showrunner.py:99-100`（`save_to_history` 默认 False）；`server/agents/routes/structure.py:258-259` | 【事实】 | 2026-08 快照 |
| 2.7 | 项目级版本快照 `ProjectVersion`：novel 快照=markdown 聚合，script 快照=stories.db 副本；恢复仅支持 script DB，novel 快照明确不支持一键恢复 | `server/story/routes_version.py:83-118`（`_create_snapshot_for_format`）；`server/story/routes_version.py:339-361`（`restore_version`）；`server/story/routes_version.py:349-350`（novel 快照返回 400 不支持恢复） | 【事实】 | 2026-08 快照 |
| 2.8 | 修订粒度双轨=「全文覆盖 rewrite_*」vs「精确片段 patch_*」；patch 统一收口 `_apply_patch`（精确匹配→规范化空白匹配→失败提示，不得静默重写） | `server/agents/tools/common.py:45-135`（`_apply_patch`）；`server/agents/tools/showrunner.py:13-37`（Rewrite/Patch schema）；`server/agents/tools/scriptwriter.py:485-489`（局部失败"不得改用完整重写"） | 【事实】 | 2026-08 快照 |
| 2.9 | 正文文件的覆盖/新建由「规划身份」决定：同身份已有文件则覆盖，重复身份报错禁止静默覆盖 | `server/story/file_naming.py:17-25`（`DuplicateSceneIdentityError`）；`server/story/file_naming.py:320-357`（`resolve_planned_scene_file_path`）；`server/agents/tools/scriptwriter.py:325-326` | 【事实】 | 2026-08 快照 |
| 2.10 | 大纲修订→正文的**影响分析缺失**：stale 只到 outline 为止，不向已写正文（stories/*.arc）传播，无「大纲改了哪些已写章节受影响」的机制 | 反证：`server/agents/structure_state.py:12`（产物仅三结构）+ `server/agents/scriptwriter_prewrite.py:82-104`（场景身份解析无 stale 校验） | （推断） | 2026-08 快照 |

---

## 维度 3 · 构建-执行分离（构思/设定/大纲 vs 写章：切分方式，细纲归属）

| 卡片 | 机制一句话 | 证据（相对路径:行号） | 档案 | 版本 |
|---|---|---|---|---|
| 3.1 | 构建层=Showrunner（梗概/节拍表/大纲），执行层=Scriptwriter（章节/场景正文）；二者是**独立 Agent + 独立工具组**（见研究-v3 档案02 §4.1，增量=工具分组） | `server/agents/tools/registry.py:90-111`（SHOWRUNNER_STRUCTURE_TOOLS vs SCRIPTWRITER_BASE_TOOLS）；`server/agents/agent_showrunner.py:48-103`（execute/write_result 三操作） | 【事实】 | 2026-08 快照 |
| 3.2 | 细纲（场景契约）**归构建层**：由 Showrunner `generate_outline` 产出 `### 场景` 的契约字段（地点/目标/冲突/转折/离场状态/知情边界/禁止铺垫），明确"是下游 Scriptwriter 的创作边界，不是装饰性摘要" | `server/agents/prompts/showrunner.yaml:225-226`；`server/agents/prompts/showrunner.yaml:236-259` | 【事实】（yaml=prompt，产出经 outline_parser 解析落盘） | 2026-08 快照 |
| 3.3 | 构建→执行之间插入**独立 PreWrite 环节**（`prepare_script_creation`），最多 4 次模型请求做只读事实核对，签发落盘凭证 | `server/agents/scriptwriter_prewrite.py:26-28`（`PREWRITE_MAX_REQUESTS=4`）；`server/agents/tools/scriptwriter.py:156-192`（`prepare_script_creation`）；`server/agents/tools/scriptwriter.py:226-235`（无凭证拒绝落盘） | 【事实】 | 2026-08 快照 |
| 3.4 | 细纲喂给执行=「场景契约按需解析」：从全量大纲中解析当前场景契约，生成 Director→Scriptwriter 交接包 | `server/agents/routes/context_builder.py:408-485`（`resolve_outline_scene_contract`）；`server/agents/routes/context_builder.py:635-704`（`build_scriptwriter_handoff_context`）；`server/agents/scriptwriter_prewrite.py:82-104`（场景身份先查大纲契约） | 【事实】 | 2026-08 快照 |
| 3.5 | 手动生产流/自动写作/导演委派**共享同一写前上下文组装**（见研究-v3 档案02 §2.3，增量=统一入口） | `server/agents/routes/context_builder.py:1-27`（模块 docstring 五链路）；`server/agents/routes/context_builder.py:983-1089`（`build_scriptwriter_context` 返回 worldview/roles/full_outline/narrative_memory/context/guidance/current_beat） | 【事实】 | 2026-08 快照 |
| 3.6 | 大纲→正文有「导出到文件」通道：按大纲逐章生成 `.arc` 骨架（场景内容占位"待填写"），带冲突检测+覆盖开关——疑似与新版 chapter 目录+metadata+PreWrite 并存的旧路径 | `server/agents/routes/outline.py:136-220`（`export_outline_to_files`，`check_only`/`overwrite`/409 CONFLICT） | 【事实】/存疑（旧路径 vs 新版并存） | 2026-08 快照 |

---

## 维度 4 · 技能/角色架构（功能划分、角色清单、过度拆分教训）

| 卡片 | 机制一句话 | 证据（相对路径:行号） | 档案 | 版本 |
|---|---|---|---|---|
| 4.1 | 六专家+导演（见研究-v3 档案02 §4.1）；增量=每个 Agent 的**工具组**（生成型 vs 消费型）：Muse/Lorebook/Showrunner/Scriptwriter 有写盘工具，Critic 只有只读+可选研究工具 | `server/agents/tools/registry.py:75-143`（六个工具组）；`server/agents/tools/registry.py:143`（`CRITIC_BASE_TOOLS=SHARED_READ_TOOLS+OPTIONAL_RESEARCH_TOOLS`） | 【事实】 | 2026-08 快照 |
| 4.2 | 落盘工具与只读工具**二分显式清单**：`PIPELINE_PERSIST_TOOLS`（写盘）vs `SHARED_READ_TOOLS`（list/read 章节大纲原文） | `server/agents/tools/registry.py:128`（`SHARED_READ_TOOLS`）；`server/agents/tools/registry.py:202-217`（`PIPELINE_PERSIST_TOOLS`） | 【事实】 | 2026-08 快照 |
| 4.3 | 可被导演委派落盘的 Agent 白名单=4 个（muse/lorebook/showrunner/scriptwriter），**不含 critic/director** | `server/agents/tools/registry.py:60-65`（`PIPELINE_CAPABLE_AGENT_IDS`） | 【事实】 | 2026-08 快照 |
| 4.4 | Lorebook（设定专家）内部只拆 2 个 operation：`worldview` / `character`；角色写盘再分「整批 append」「整批覆盖」「单角色 update」三粒度 | `server/agents/agent_lorebook.py:75-92`（`execute` 两操作）；`server/agents/tools/lorebook.py:18-20`（`RewriteAllCharactersInput.append`）；`server/agents/tools/lorebook.py:80-102`（`update_character`） | 【事实】 | 2026-08 快照 |
| 4.5 | Showrunner 的连续性研究工具（StoryMemory/GraphRAG/章节读取）**按「是否已有正文」动态开放**，新项目只给结构工具 | `server/agents/tools/registry.py:180-193`（`_showrunner_runtime_tools`，`project_has_written_story_content` 才开放 continuity tools） | 【事实】 | 2026-08 快照 |
| 4.6 | 过度拆分教训：**未发现该机制**——代码中无显式"角色拆太细"的教训/文档（角色切分=6专家+导演已见研究-v3 档案02 §4.1；无更细 sub-agent 拆分证据） | （无对应代码/文档） | 未发现该机制 | 2026-08 快照 |

---

## 维度 5 · 上下文衔接（构建产物如何喂写作 / 写作变化如何回流构建层）

| 卡片 | 机制一句话 | 证据（相对路径:行号） | 档案 | 版本 |
|---|---|---|---|---|
| 5.1 | 构建产物**全量注入 + 预算裁剪**（见研究-v3 档案02 §3.4；增量=分 Agent 组装）：Showrunner/Scriptwriter/Critic 注入世界观+角色+全量大纲+叙事记忆，正式写作阶段由上下文预算裁剪 | `server/agents/context_provider.py:288-342`（分 Agent 组装）；`server/agents/routes/context_builder.py:17-21`（"全量加载，正式写作阶段由上下文预算裁剪"） | 【事实】 | 2026-08 快照 |
| 5.2 | 场景级**切片**：三圈记忆=当前章最近 3 场全文 + 最近 2 个前序章章末 + 梗概/节拍表（见研究-v3 档案02 §3.2；增量=常量与切片函数） | `server/agents/routes/context_builder.py:47-48`（`MAX_CURRENT_CHAPTER_FULL_SCENES=3`，`MAX_CROSS_CHAPTER_TAILS=2`）；`server/agents/routes/context_builder.py:802-918`（`build_scene_context`） | 【事实】 | 2026-08 快照 |
| 5.3 | 场景契约+节拍**按需切片**：`current_beat` 仅按大纲场景显式 `beat_refs` 取节拍，无显式引用则不注入（不按位置比例猜测） | `server/agents/routes/context_builder.py:951-977`（`get_current_beat`）；`server/agents/routes/context_builder.py:983-1089`（组装入口） | 【事实】 | 2026-08 快照 |
| 5.4 | 写作变化回流=**单向**正文→StoryMemory：`create_or_rewrite_script` 落盘后 `enqueue_scene_memory_write`（见研究-v3 档案02 §3.2；增量=触发点） | `server/agents/tools/scriptwriter.py:347-361`（`enqueue_scene_memory_write`）；`server/agents/routes/context_builder.py:11-14`（"普通保存不隐式写 StoryMemory，用户显式吸收才提交"） | 【事实】 | 2026-08 快照 |
| 5.5 | 正文状态**不回写大纲/设定**（回流方向单向）：世界观只记长期事实，临时状态/线索/修订工单留在 StoryMemory，除非用户明确升格 | `server/agents/prompts/lorebook.yaml:29-30,41,111`（canon_boundary + "不要把 StoryMemory 状态写进长期设定"） | 【事实】（prompt 约束） | 2026-08 快照 |

---

## 维度 6 · 人机分工（修订流程的作者裁决点：候选制/影响清单/确认时机）

| 卡片 | 机制一句话 | 证据（相对路径:行号） | 档案 | 版本 |
|---|---|---|---|---|
| 6.1 | 修订粒度裁决点=rewrite（整体）vs patch（局部）双工具，选择权在调用方/作者意图；patch 不得升级为全文重写 | `server/agents/tools/showrunner.py:13-37`（Rewrite/Patch schema）；`server/agents/prompts/lorebook.yaml:103`（"不得把局部修改升级为全文重写"）；`server/agents/tools/scriptwriter.py:485-489` | 【事实】 | 2026-08 快照 |
| 6.2 | 破坏性覆盖需**显式意图**（确认时机）：角色写盘 `append` 默认 true（增量 upsert），仅"清空重做/整体替换全部角色"才允许 `append=false`（全量覆盖） | `server/agents/tools/lorebook.py:18-20`（append 默认 true 的 schema 描述）；`server/agents/prompts/lorebook.yaml:108-110`；`server/agents/agent_lorebook.py:326-342`（`_write_characters_overwrite`：append→upsert，非 append→replace） | 【事实】 | 2026-08 快照 |
| 6.3 | 影响清单=结构版本警告（咨询性不阻断），把"是否重建下游"的裁决权交回作者：过期产物只能参考，不得覆盖较新上游事实 | `server/agents/structure_state.py:129-138`；`server/agents/context_provider.py:267-274,423-424` | 【事实】 | 2026-08 快照 |
| 6.4 | 审稿不写稿（见研究-v3 档案02 §2.1/§4.4 Critic；增量=代码佐证） | `server/agents/tools/registry.py:143`（Critic 无写盘工具） | 【事实】 | 2026-08 快照 |
| 6.5 | 大纲导出到正文有**冲突拦截 + 覆盖开关**（人裁决破坏性覆盖） | `server/agents/routes/outline.py:136-195`（`check_only`/`overwrite`/409 CONFLICT） | 【事实】 | 2026-08 快照 |
| 6.6 | 世界观生成→**机器校验拦截**（非人裁决）：识别到网页/代码围栏输出则重试一次，仍非法则 raise 拒绝写入 | `server/agents/agent_lorebook.py:34-61`（`_is_invalid_worldview_document`）；`server/agents/agent_lorebook.py:196-204`（重试后 `raise ValueError`） | 【事实】 | 2026-08 快照 |
| 6.7 | 候选制（多版本候选供作者挑选）：**未发现该机制**——修订流程无"生成多个候选版本让作者选"；最接近的是大纲 history 手动回滚（维度 2.5），但那不是候选制 | （无对应代码；`server/agents/routes/outline.py:120-133` 为手动回滚，非候选） | 未发现该机制 | 2026-08 快照 |

---

## 六维覆盖表

| 维度 | 覆盖 | 说明 |
|---|---|---|
| 1 资产分层 | ✅ | 文件形态、真源/派生链、细纲内嵌于大纲、正文身份由大纲签发均有代码证据（卡片 1.1–1.6） |
| 2 修订机制 | ✅ | revision/stale 级联、stale 范围边界、rewrite/patch 双轨、大纲 history 回滚、项目快照、影响分析缺失均有代码证据（2.1–2.10） |
| 3 构建-执行分离 | ✅ | Showrunner/Scriptwriter 切分、细纲归构建层、PreWrite 桥接、场景契约按需解析（3.1–3.6） |
| 4 技能/角色架构 | ✅ | 工具分组/生成型-消费型二分/委派白名单/动态工具开放；**过度拆分教训未发现**（4.1–4.6） |
| 5 上下文衔接 | ✅ | 全量注入+预算裁剪、三圈记忆切片、beat_refs 按需取节拍、正文→StoryMemory 单向回流（5.1–5.5） |
| 6 人机分工 | ✅ | rewrite/patch 粒度、append 默认增量、stale 影响清单、导出冲突拦截、机器校验；**候选制未发现**（6.1–6.7） |

---

## 主要证据文件清单（本轮增量勘察）

- `server/agents/structure_state.py`（138 行，修订/stale/派生链核心）
- `server/agents/routes/schemas.py`（`_save_project_markup` 触发点 + `_save_outline_to_history`）
- `server/agents/routes/outline.py`（大纲保存/历史回滚/导出到正文）
- `server/story/routes_version.py`（项目级版本快照/恢复）
- `server/agents/tools/showrunner.py`、`server/agents/tools/lorebook.py`、`server/agents/tools/scriptwriter.py`、`server/agents/tools/common.py`（rewrite/patch/append/_apply_patch 语义）
- `server/agents/agent_lorebook.py`、`server/agents/agent_showrunner.py`（设定形态、构建层生成流）
- `server/agents/scriptwriter_prewrite.py`（PreWrite 桥接环节）
- `server/agents/routes/context_builder.py`（场景契约解析、三圈记忆、统一上下文组装）
- `server/agents/context_provider.py`（分 Agent 上下文注入 + stale 警告注入）
- `server/agents/tools/registry.py`（六 Agent 工具分组、委派白名单、落盘工具清单）
- `server/story/outline_parser.py`、`server/story/file_naming.py`、`server/story/novel_parser.py`（大纲/正文解析、身份与聚合）
- `server/agents/prompts/lorebook.yaml`、`server/agents/prompts/showrunner.yaml`（canon_boundary、rewrite/patch/append 约束、场景契约字段）
- `server/test/story_context/test_structure_state.py`（stale 级联/派生链的契约测试，佐证机制意图）

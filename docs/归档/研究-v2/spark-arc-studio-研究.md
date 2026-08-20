# spark-arc-studio 研究档案（v2，源码级）

> 研究对象路径：`otherMaterials/referProject/spark-arc-studio/`（约 913 文件）
> 研究日期：2026-08-20。方法：单代理源码通读 + 关键函数逐行核对，全部论断落到文件/行号。
> 实际读过的关键文件清单（下文引用均相对仓库根 `spark-arc-studio/`）：
> `AGENTS.md`、`CLAUDE.md`、`docs/architecture.md`、
> `server/agents/communication.py`、`agent_utils.py`、`agent_tools.py`、`registry.py`、`agent_critic.py`、`agent_scriptwriter.py`（局部）、`auto_write_service.py`、`context_budget.py`（局部）、`prompt_layout.py`、
> `server/agents/tools/{registry,common,delegation}.py`、
> `server/agents/story_memory/{facade,jobs}.py`、
> `server/agents/agent_style/{__init__,workflow,unified_analyzer,utils}.py` + `prompts/style_analysis.yaml`、
> `server/agents/prompts/{critic,scriptwriter,director}.yaml`（局部）、
> `server/agents/routes/{auto_write_state,context_builder}.py`（局部）、`server/story/semantic_chunker/chunker.py`（局部）、
> `server/test/architecture/`（文件名）。

---

## 1. 项目概况

**是什么**：SparkArc（引火AI 创作台）是一个「多 Agent 自主集群驱动的网文/互动剧本创作平台」，打通「灵感→设定→节奏→大纲→写文→评审→发布→演出」全链路。人机三模式（你我共舞/我说你写/我写你修）由用户决定 AI 介入深度（README 定位，代码无直接对应常量，属产品层表述）。

**技术栈（代码事实）**：后端 Python + FastAPI + LangChain/LangGraph（`director_graph.py` 用 `StateGraph`/`SupervisorGraph`，`communication.py` 用 `langchain_core.messages.SystemMessage/HumanMessage`，工具用 `@tool(args_schema=...)` 定义）；LLM 经 `llm/agen_matchbox` 的 `matchbox().get_user_llm(...)` 按用户+Agent 取模型（`communication.py:1438`）；前端 Vue3 + TS（跳过细节）；`.arc` 自研场景文件格式 + `novel`(.md) 双态。

**规模与维护状态（代码事实）**：8 个注册 Agent（`registry.py:14-211` AGENT_REGISTRY：director/showrunner/scriptwriter/critic/muse/lorebook/style/utility）。代码注释多处标注 2026 年的重构记录（如 `unified_analyzer.py:11` "设计变更(2026-06)"、`agent_tools.py:10` "历史实现已迁移至 tools/*"），说明是一个**持续强重构中、规范沉淀非常重**的仓库（AGENTS.md 581 行、architecture.md 572 行，均以"禁止/收口"为基调）。

**核心组织原则（代码事实）**：AGENTS.md 反复强调「统一收口，不复制实现」「改一处全链路受益」，并明文规定 AI 只允许只读型 git 命令（`AGENTS.md:577-580`）。

---

## 2. 流程（含重点问题清单逐题答案）

### Q1 三模态提示词协议怎么实现？base 占位符与 _get_tool_prompt_references 注入机制？

**三种模态**对应 `prompts/<agent>.yaml` 的三个顶层字段：`system`（专有工作/面板按钮→`execute()`/具名方法，机器解析、禁寒暄）、`chat_system`（聊天模式）、`pipeline_system`（导演委派）。**运行态互斥选择**，不是叠加：

- `communication.py:1414-1418`（`chat()`）与 `1571-1575`（`chat_stream()`）：`skip_tool_confirmation=True → pipeline_system 优先，否则 chat_system 优先，都缺回落到 system`。即 AGENTS.md §4.5 的三元选择在此收口，两段 system 互斥、LLM 看不到另一段。

**base 占位符机制（代码事实）**：

- `agent_utils.py:134-145` `_flatten_base`：把 yaml 顶层 `base` 字典递归展平为 `base.xxx` 键，`setdefault` 注入 kwargs（**不覆盖用户显式传入值**）。
- `agent_utils.py:230-239`：子 prompt（`prompt_key` 非空）加载时先 `_load_full_yaml_for_base` 取完整 yaml 顶层 `base`（`164-177`），再展平。
- `agent_utils.py:303-325` `_replace_placeholders`：多轮替换（max 5 轮）直到稳定，支持 `{base.xxx}` 展开后内嵌 `{yyy}` 的二级替换；`None` 值替换为「（未提供）」。
- 各模态通过 `{base.identity}` 等引用共享片段（如 `critic.yaml:35-54` pipeline_system 引用 `{base.identity}`/`{base.review_dimensions}`/`{base.grade_mapping}`/`{base.json_fields}`）。

**`_get_tool_prompt_references` 注入（代码事实）**：

- 基类默认返回 `{}`（`communication.py:718-720`）；有落盘工具的 Agent 子类重写，返回 `{tool_name: [{"prompt_key":..., "field":"system"}]}`。实例：`agent_scriptwriter.py:249-262` `create_or_rewrite_script` 在 novel 态指向 `generate_novel.system`、arc 态指向顶层 `system`（`{"field":"system"}` 省略 prompt_key 即根）。
- 装配在 `_build_tool_prompt_reference_block`（`communication.py:726-782`）：遍历注册映射，若工具在当前 Agent 绑定工具集内，`load_prompt` 取对应 `system` 字段，拼成「当你决定调用工具 `xxx` 时，必须复用以下既有生成规范：...」追加到 system prompt 末尾。
- **占位符默认填充**：`_get_tool_prompt_reference_values`（`communication.py:722-724`，实例 `agent_scriptwriter.py:264-274`）给 `{arc_example}/{worldview}/{roles}` 等提供「（由当前项目提供）」类默认值，避免 LLM 看到字面 `{worldview}`。
- **`tool_rules` 自动加载**：`_build_tool_system_prompt` 内 `communication.py:656-666`，检测到工具绑定时 `load_prompt` 取 yaml 顶层 `tool_rules` 字符串追加；Director 例外（动态团队概览保留 Python 重写，见 `_build_runtime_tail:670-687` 只把 work_tracker 快照放尾部）。

### Q2 统一工具门面/registry 如何收口？agent→工具绑定真相源在哪？

- `agent_tools.py` 是**纯 re-export 门面**（`agent_tools.py:10-12` 注释「历史实现已迁移至 tools/*，本文件仅作兼容导出门面」），不再含实现。
- **真相源 = `tools/registry.py`**：`get_tools_for_agent(agent_id, user_id, pipeline_mode)`（`registry.py:246-264`）内 `tool_map` 字典是 agent→工具列表的唯一映射（`252-260`）。`TOOLS_BY_NAME`（`241-243`）由 `ALL_TOOLS` 去重生成，供 `_execute_tool_calls` 按名查工具执行（`communication.py:826`）。
- 运行态条件注入：`_with_skill_tools`（`registry.py:165-169`）按用户是否装了 Skill 追加 `SHARED_SKILL_TOOLS`；`_showrunner_runtime_tools`（`180-193`）按项目是否有正文动态开连续性工具；`pipeline_mode` 时给 `PIPELINE_CAPABLE_AGENT_IDS`（muse/lorebook/showrunner/scriptwriter，`60-65`）追加 `complete_pipeline_step`。
- **唯一公共底座**：`_apply_patch`（`tools/common.py:45-135`）——先精确 `in` 匹配，失败再做空白归一化行映射（`_normalize_ws`，`35-42`）后按行偏移替换；支持 `search_text=""` 末尾追加、`validate_json`、`validate_content` 写入前校验。AGENTS.md §2 明确「凡定位+替换必须复用此底层」。

### Q3 Critic 审核输出数据结构 + 工单闭环如何运转？

**输出结构（代码事实）**：`agent_critic.py` 的 `_normalize_review_result`（`116-162`）归一化出：
`decision`(PASS/REVISE/REJECT) + `overall_grade`(S/A/B/C/D) + `overall_summary` + `dimension_grades`（五维：`structure_ai_flavor`/`language_ai_flavor`/`dialogue_ai_flavor`/`literary_flatness`/`logic_and_character`，`58-80`）+ `hits`（每条含 `feature/severity/reason/suggestion/evidence[quote+reason]/fix_ticket`，`82-104`）+ `fix_tickets` + `rewrite_required` + `rewrite_brief` + 兼容字段 `status/critique/specific_feedback`。

**等级映射**：`agent_critic.py:122-128`：S/A→PASS，B→REVISE，其余→REJECT；`_normalize_grade`（`40-56`）还接受 0-100 数字分换算。prompt 侧 `critic.yaml:22-25` grade_mapping 与 `103-113` 五档语义一致。

**fix_ticket 结构**：`critic.yaml:135-140`（target/edit_goal/must_keep/operations）与 `149-156` 一致；`must_keep` 是「必须保留项」负向约束。

**工单闭环（代码事实，本项目最强机制）**：
1. **写后生成**：`story_memory/facade.py:1012-1098` `record_quality_review` 把 Critic 的 fix_tickets 落成 `quality_memory` 工单：`ticket_id=f"quality-{hash[:12]}"`、`status="open"`、三元定位（review_target/scene_name/source_path）+ must_keep/operations/evidence/overall_grade/decision。
2. **写前注入**：`facade.py:1326-1337` 筛选 `status=="open"` 工单，`1403-1417` 以「【未关闭修订工单 / 质量记忆】」段落注入 `compose_scene_task_pack` 返回的 `text`；`context_builder.py:842-854` 在 `build_scene_context` 顶部注入该任务包。
3. **复审关闭**：`facade.py:1100-1103` 判定「PASS 且无新 ticket」→ `_close_quality_tickets_for_review`（`1105-1143`）把同目标 open 工单置 `status="resolved"`、`resolution="critic_pass"`。
4. **默认关闭**：`auto_review` 默认 false（AGENTS.md §4.5.4、`auto_write_service.py:88`），手动保存绝不隐式触发 Critic。

### Q4 StoryMemory 状态吸收机制？

**存储形态（代码事实）**：项目目录下 `.story_memory/narrative_state.json`（`facade.py:16-17`），`@synchronized_json_state` 原子落盘（`316`）。8 类状态（`_default_state:210-225`）：`scenes/events/fact_claims/character_states/relationships/threads/conflict_risks/quality_memory`。

**写后回写（jobs.py 三层）**：
- `enqueue_scene_memory_write`（`jobs.py:88-124`）：**先同步写确定性快照**（`use_llm_extractor=False`，立即可见）→ 再异步 LLM 抽取（`use_llm_extractor=True` + `require_current_source_hash=True`）。
- 来源哈希防旧回写：`facade.py:349-364` `require_current_source_hash` 时若当前 scene 的 `source_hash` 已变，返回 `stale_enrichment_skipped`，迟到旧抽取不覆盖新正文。
- 同场景重写先撤销旧贡献：`_remove_scene_contributions`（`facade.py:460+`）在合并前清除该 scene_id 的旧状态。
- LLM 抽取在状态锁外完成：`prepare_scene_enrichment`（`facade.py:301-314`）先算 delta，提交阶段 `record_scene_write` 只做快速合并。

**显式吸收（代码事实）**：`enqueue_story_file_memory_write`（`jobs.py:182-206`，按文件路径后台回读解析）与 `enqueue_story_content_memory_write`（`288-311`，手动吸收接口用），后者注释「普通保存接口默认不调用它」。

**任务包**：`compose_scene_task_pack`（`facade.py:1158-1447`）按 `_scene_position` 过滤「目标场景之前」的历史，产出角色状态卡/关系卡/开放线索/历史事件/已确立事实/矛盾风险/未关闭工单/最近 2 场摘要（`SCENE_TASK_PACK_RECENT_SCENES=2`，`facade.py:20`），返回 `{pack, text}`。

### Q5 文风克隆档案结构 + 注入路径？

**档案结构（代码事实）**：Markdown 字符串，含 yaml frontmatter 存元数据（`workflow.py:1-9`、`utils.py:117-160`）。最终档案由 `style_analysis.yaml` 约束为：**6 个维度段落 + 「## 作者回避(负面约束)」 + 「## 风格执行卡」**（`style_analysis.yaml:22-31`、`197-203`）。负向约束**内联抽取**：每维度分析时发现作者明显回避的表达即在该维度末尾追加「作者回避:...」（`style_analysis.yaml:16-17`、`128-130`），汇总阶段整合为禁忌清单——**正向统计与负向约束同源产出**。

**分析链路**：`workflow.py:stream_save_style_profile` 30k tokens/块切分（`42`）→ `UnifiedStyleAnalyzer.analyze_chunk` 串行逐块分析，`previous_context`（剧情概括，3000 字截断）传递到下一块（`workflow.py:71-85`、`unified_analyzer.py:100-171`）；单块输出按「## 上下文摘要」切分（`unified_analyzer.py:200-214`）；末块直接产出完整档案（`unified_analyzer.py:144-160`）。

**注入路径**：`format_style_profile_for_prompt`（`utils.py:366-382`）把 Markdown 档案**直接透传**到下游 system prompt（「无需二次拼装」）；`agent_critic.py:12,23-27` 注入 Critic 审稿参照，`scriptwriter.yaml:49` 以 `{style_profile}` 占位注入编剧。

**重要（代码事实）**：`style_analysis.yaml:230` 存在 `validator:` 配置段，但 **`workflow.py`/`unified_analyzer.py` 均无任何 validator 调用**，`agent_style/agents/__init__.py:3` 注释「旧的多 Agent 并行 JSON 框架(StyleAnalysisAgent/ValidatorAgent/CoordinatorAgent)」已被移除。即 architecture.md §7.1 描述的「图灵回测闭环/自我对抗」是**纯文档残留，代码已不存在**。

### Q6 上下文预算与缓存前缀怎么落地？

**稳定前缀 + 动态尾部（代码事实）**：`prompt_layout.py:20-46` `build_current_user_message` 把本轮 `active_context`（当前编辑区/附件现场）+ `user_message` + `runtime_tail` 全部拼进**最后一条 user message**，system 只留稳定内容。前缀装配顺序（`communication.py:595-668` `_build_tool_system_prompt`）：语言策略 → 工具清单 → 确认规则/PIPELINE MODE → tool reference → tool_rules；`_build_runtime_tail`（`670-687`）把 work_tracker 快照放尾部而非 system。

**预算裁剪（代码事实）**：`context_budget.py:734-754` `DEFAULT_SPECIALIZED_SECTION_BUDGETS` 定义 protected 区块（当前场景事实包/契约/创作指导/审阅目标等，永不裁）+ 按 `min_chars`/`floor_ratio` 裁剪区块（世界观 2200、大纲 2600、角色 3600、前文 5200、风格 2400）。`_truncate_user_prompt_sections`（`693-731`）只裁 user prompt 内可恢复区块，不动 system（保缓存）；`_truncate_section_text`（`637-653`）保护高优先级前缀。

**工具循环后**：`chat` 每轮工具结果后 `rebudget_existing_messages`（`communication.py:1532`）+ `collapse_attachment_chunk_history`（`1531`）折叠旧附件分片。**命中率来自上游 API 的 `cached_prompt_tokens`，非本仓库测算**（AGENTS.md §5.2.1）。

### Q7 Auto-Write 断点续写游标数据结构？

- **状态游标**：`auto_write_state.py:100-146` `default_auto_write_state`，关键字段：`runId`、`status`(idle/running/chapter_paused/interrupted/error/complete)、`requestedStartChapterIndex/requestedStartSceneIndex`、`currentChapterIndex/currentSceneIndex`、`lastCompletedChapterIndex`、`availableResumeChapterIndex/availableResumeSceneIndex`、`generatedSceneFiles`、`lastSavedFilename`、`fromDirector`、`acknowledged`。
- **事件日志游标**：`auto_write_service.py:20-50` `AutoWriteTaskEntry` 维护 append-only `events: list[(seq, event)]` + `next_seq`，`wait_after(after_seq)` 只取 `seq>after_seq` 增量；`observe_auto_write_progress`（`212-231`）用 `cursor=after_seq` 断线续读。
- 进度计算策略：`build_auto_write_state_payload:380-392` —— running/chapter_paused 用 `generatedSceneFiles` 计数（防旧文件导致进度提前 100%），complete 强制=total，其余回退磁盘存在性。
- 支持 `start_scene_index` 续写 + 「从当前剧情进度开始」扫描已有场景文件推算下一场（architecture.md §3.5，代码见 `auto_write.py`，未细读）。

### Q8 Director 委派协议（handoff payload / 免确认 / pipeline 强制）？

- **delegate_task 哨兵**：`delegation.py:120-122` 返回 `__DELEGATE__:{json}`；`director_graph.py:575-578` 拦截该哨兵、`json.loads` 出 delegate_data 后 `normalize_handoff_payload` 归一。
- **handoff payload**：`normalize_handoff_payload`（`communication.py:271-352`）归一化 `delivery_mode`(direct_to_user/return_to_director)、`completion_mode`(report_to_user/return_to_director/silent_continue)、`requires_review`、`return_to`、`grant_baton_to`、`scene_*` 等。
- **免确认（代码事实）**：`communication.py:302-304` —— `delegated_by == "agent_director"` 时**强制** `user_confirmation_state=HANDOFF_CONFIRMATION_NOT_REQUIRED`；`341` 据此推导 `skip_tool_confirmation=True`。即导演委派天然免确认。
- **pipeline 模式强制**：`sub_agent_node`（`director_graph.py:717-720`）用 `skip_tool_confirmation` 调 `sub_agent.chat_stream(...)`（`800-809`），从而命中 `pipeline_system`。
- **落盘护栏**：`director_graph.py:793,898-904` —— 委派 Scriptwriter 且 pipeline 模式时 `suppress_scriptwriter_draft`，只输出草稿未调 `create_or_rewrite_script/patch_script` 落盘则判定「未完成落盘」打回导演（`route_after_sub_agent:997-1002` 返回 director）。
- **silent_continue**：`stop_after_pipeline_completion=completion_mode==silent_continue`（`806-808`），子 Agent 末批工具调用以 `complete_pipeline_step` 结束，`chat` 侧 `resolve_pipeline_completion`（`communication.py:1514-1521`）返回真实工具回执，不输出自然语言总结。

### Q9 基础建筑测试守的是什么协议？

`server/test/architecture/` 实际 7 个文件（**注意：AGENTS.md §10.0 只列了 6 个，漏了 `test_prompt_cache_layout_contracts.py`**）：
`test_agent_prompt_contracts.py`（三模态/pipeline 受众声明/tool reference 契约）、`test_tool_registry_contracts.py`（注册表/门面/工具 UI 元数据）、`test_chat_stream_contracts.py`（ChatTaskEntry/accumulator/observer/retry）、`test_streaming_bridge_contracts.py`（同步→异步桥接、语义帧）、`test_common_infrastructure_contracts.py`（`_apply_patch`/`TokenTextSplitter`/迁移路径）、`test_matchbox_startup_contracts.py`（火柴网关懒加载）、`test_prompt_cache_layout_contracts.py`（缓存前缀布局）。

守护原则（`AGENTS.md:419-517`）：**测协议不测实现、测收口不测使用点、测不变量不滥用快照、禁真实上游依赖（fake/monkeypatch/临时目录）、失败先判因再改测试、bug 回归下沉领域目录、临时验证放 `/.tmp/tests/` 用完即删**。判断口诀「只回答现在是否正常→临时验证并删；防止以后再坏→正式回归」。

---

## 3. 架构

**双基座正交组合（代码事实）**：`SparkBaseAgent`（`communication.py`，通讯/信标/聊天/工具调用底座）+ `SparkAgentExecutor`（`agent_utils.py:39-67`，`build_context→execute→write_result` 三段执行协议）。业务 Agent 同时继承两者，把「面板入口/聊天入口/工具入口/MCP 入口」收敛到同一执行链（`agent_utils.py:1-28` 文档）。

**三条入口一条管线**：面板按钮→`execute()`/具名方法（`system`+`user`，无工具）；聊天与导演委派共用 `chat_stream`，唯一差异 `skip_tool_confirmation`（同时决定 prompt 字段 + 工具是否免确认，architecture.md §2.1）。

**双层通信（architecture.md §1，代码印证）**：导演调度（LangGraph SupervisorGraph，`director_graph.py`）是垂直指令流，Director 有「上帝权限」绕过信标；信标总线（beacon/horn/baton 三件套，`communication.py:355-386` `transfer_baton` 等）是水平协作的可见性/发言权/接棒约束。两套并存而非冗余。

**工具层三层结构**：`agent_tools.py` 门面 → `tools/*` 按域实现 → `tools/registry.py` 唯一真相源（§2 Q2）。

**数据红线**：改模型→`gen_migration.py` 自动派生 Alembic→启动自动迁移（AGENTS.md §7）。

---

## 4. 思想

1. **「落盘才算完成」的机器状态机**：创作的正确性由「是否走了统一工具/是否落盘」判定，而不是由文本内容判定（`director_graph.py:898-904` 未落盘打回）。这是它与「人肉状态机」最本质的分野。
2. **「互斥选择而非叠加」的提示词协议**：三段 system 互斥、靠 tool reference 把产出规范从 `system` 复用到 `pipeline_system`，杜绝双份维护漂移（AGENTS.md §4.5.1，Muse 历史 Bug 是反面教材）。
3. **「写评分离 + 工单闭环」**：Critic 无落盘工具、只产出结构化 fix_ticket；写前注入 open 工单、复审通过才关闭，形成「审完不丢」的持久化闭环（`facade.py` quality_memory）。
4. **「零等待记忆 + 来源哈希」**：快照同步可见、LLM 增强异步、来源哈希防旧结果回写，把一致性/全面性/成本三者解耦（`jobs.py:88-124`）。
5. **「稳定前缀保缓存」**：system 只放低频内容，动态现场塞最后 user，专有预算器只裁 user 尾部不动 system（`prompt_layout.py` + `context_budget.py`）。
6. **「统一收口，禁止平行实现」**：`_apply_patch`/`TokenTextSplitter`/`SemanticChunker` 三大基建 + registry/facade 四大收口点，AGENTS.md 整篇以「禁止」为主基调。

---

## 5. 方法论

1. **AGENTS.md 即架构宪法**：581 行里同时写「收口点清单、三模态协议、反模式清单、测试分层纪律、AI 只读 git 红线」，把「怎么改才不堆屎山」写成硬约束。
2. **tool reference 自动注入**：用「工具→yaml system 字段」的注册映射，让 pipeline 模式复用专有模式的产出规范，而不是复制粘贴（`_build_tool_prompt_reference_block`）。
3. **来源哈希 + 异步增强 + 快照分离**：把「确定性可验证」和「LLM 语义增强」拆成两条时序，迟到的增强不覆盖新状态（`require_current_source_hash`）。
4. **测试按「守护对象」分层**：architecture/ 只放跨模块稳定不变量，业务回归下沉领域目录，临时验证放 `/.tmp/` 用完删，测试位置本身是审查项。
5. **哨兵字符串 + LangGraph 拦截**：`__DELEGATE__:json` 让 Director 的委派动作被图拦截后路由到 sub_agent 节点，暴露内层流式状态（`director_graph.py:575-578`）。

---

## 6. 上下游设计

- **上游（输入）**：用户三模式介入程度决定 AI 深度；AgentSkills 作为「写作质量参考层」按需 `search_skills/read_skill` 读取（quality_only 视图，不改格式/协议/落盘规则，`communication.py:619-628`）；MCP 灵感/控制服务只读查询从 `MCP_EXPOSED_QUERY_TOOL_NAMES` 派生、写盘走 Director 工单（`registry.py:272-284`）。
- **下游（输出）**：`.arc`/`.md` 场景文件落盘（文件名内嵌 `__spark__chap=001.scene=001.order=...` 机器身份，`auto_write_state.py:74-90`）；StoryMemory/quality_memory 轻量状态层回写；公开分享前有独立 `public_share_moderation` 审核（`critic.yaml:198-238`、`agent_critic.py:253-269`）。

---

## 7. 可借鉴清单（分成本）

### 低成本（改 prompt / 小函数即可）

1. **三模态提示词 + tool reference 自动注入**：机制见 §2 Q1。源码 `communication.py:726-782`、`agent_scriptwriter.py:249-262`。**为什么值得**：彻底解决「聊天模式被结构化格式套死 / 委派模式丢格式规范」的模态串味；mo-shu 的 skill 若有多入口（交互 vs 后台流水线），可直接复刻「互斥选择 + 工具→规范映射」避免双份 prompt 漂移。**落点**：mo-shu skill 的 system 拆「对话态/流水线态」，产出规范挂到落盘动作。
2. **`base.xxx` 占位符展平**：`agent_utils.py:134-145,303-325`。**为什么值得**：一个 ~20 行的递归展平 + 多轮替换，就能让多模态共享「身份/审核维度/等级映射」单点维护。**落点**：mo-shu skill 的共享 prompt 片段提取。
3. **Critic 的 `_normalize_*` 归一化层**：`agent_critic.py:40-162`。**为什么值得**：对 LLM JSON 输出做「等级别名/决策推导/兼容字段」容错归一，把脆弱解析隔离在薄层。**落点**：mo-shu 任何解析 LLM 结构化输出的环节。

### 中成本

4. **fix_ticket 工单闭环（最高价值）**：§2 Q3/Q4。源码 `facade.py:1012-1143` + `compose_scene_task_pack`。**为什么值得**：把「审完就丢」变成「审完持久化、写前注入、复审关闭」，是 mo-shu 最缺的一块拼图。**落点**：mo-shu 的 consistency-checker / deslop 产出机器可消费工单 + 写前注入 + 通过即关闭。
5. **写后零等待记忆 + 来源哈希**：`jobs.py:88-124`、`facade.py:349-364`。**为什么值得**：确定性快照立即可见 + LLM 增强异步 + 防旧结果覆盖，是「状态吸收」的成熟范式。**落点**：mo-shu 若引入运行期状态层（如 story-memory 类似物）。
6. **稳定前缀 + 动态尾部布局**：`prompt_layout.py:20-65` + `context_budget.py:734-754`。**为什么值得**：把「编辑区/附件/本轮请求」从 system 挪到末条 user，配合 protected 区块预算，直接提升缓存命中。**落点**：mo-shu 的 LLM 调用若需长上下文，按此布局降低 token 成本。
7. **落盘回执协议**：`director_graph.py:793,898-904`。**为什么值得**：用「是否走了落盘工具」而非「正文看起来完成」判定完成，杜绝「草稿当成品」。**落点**：mo-shu 任何 agent 链的完成判定。

### 高成本

8. **StoryMemory 任务包（compose_scene_task_pack）**：`facade.py:1158-1447` 完整的事实包组装 + 按场景时间点过滤。**为什么值得**：写前自动注入「只含已发生事实」的核对包，把「写前核设定」自动化。**落点**：mo-shu 若做大长篇连续性，这是核心参考；成本高（需状态层 + 抽取 + 过滤全套）。
9. **Director 委派协议（handoff payload 归一 + 哨兵 + 免确认）**：`communication.py:271-352`、`delegation.py:120-122`、`director_graph.py`。**为什么值得**：把「多 agent 委派的控制流（交付/完成/免确认/落盘护栏）」做成显式可归一的协议。**落点**：仅当 mo-shu 引入多 agent 编排时值得；否则过度设计。

---

## 8. 不可借鉴清单（与 mo-shu 定位/架构冲突）

1. **LLM 驱动的 Director 总控（LangGraph SupervisorGraph）**：`director_graph.py` 用 LLM 自主决策路由。**冲突**：mo-shu 是「确定性路由 + 人肉状态机」，主会话确定性路由比 LLM 总控更稳、更可预期；引入 Director 反而引入非确定性和成本。
2. **信标/号角/旗帜三件套总线**：`communication.py:355-386`。**冲突**：为「多 agent 水平自主协作」设计，mo-shu 目前无此场景，属预留复杂度；过早引入是堆屎山。
3. **重运行时状态机（LangGraph 流式 state + json_state 原子锁 + auto_write_state 多游标）**：`director_graph.py`、`facade.py` `@synchronized_json_state`、`auto_write_state.py`。**冲突**：这套为「长后台无人值守写作 + 断线重连」服务，mo-shu 的 Claude Code skill 架构没有对应运行期宿主，直接照搬会凭空多出一层状态管理。
4. **文风克隆的「风格执行卡 + 作者回避」LLM 全自动档案**：`style_analysis.yaml`、`workflow.py`。**冲突**：mo-shu 的文风库走「确定性数值化（句长/标点）+ 锚点切片可 grep 回查」路线，比 SparkArc 的「全靠 LLM 自觉、脱敏短例不可溯源」更可验证；且 SparkArc 的 validator 已删除（无确定性验证）。mo-shu 不应放弃确定性优势转投纯 LLM 克隆。
5. **「`{base.xxx}` 多轮替换 + `{worldview}` 默认填充」的全量 prompt 展平复杂度**：`agent_utils.py:303-325`。**冲突**：mo-shu skill 规模小，若 prompt 嵌套层级浅，引入多轮占位符替换 + base 展平是过度设计。

---

## 9. 与 mo-shu 差异定位

| 维度 | spark-arc-studio | mo-shu |
|---|---|---|
| 状态机归属 | **机器状态机**：上下文自动组装、落盘自动校验、进度自动持久化，人只触发确认 | **人肉状态机**：确定性由脚本承担、品味由作者拍板、AI 只做语义 |
| 架构形态 | 聊天平台（FastAPI 常驻服务 + 前端 + 多 agent 运行时） | Claude Code skill（进程级、按需调用） |
| 失控防护 | 落盘护栏（不落盘不算完成）+ 状态机 + 预算保护 | 停靠点 + 机检守卫 + Gate 硬门槛 |
| 质量闭环 | Critic 工单 + 写前注入 + 复审关闭（LLM 判 AI 味） | 确定性 check-ai-patterns + deslop 7 Gate（机器化可复扫） |
| 文风 | 学「你自己/任一作者」，认知层，LLM 全自动，无确定性验证 | 表层统计数值化 + 锚点可 grep + 反 AI 腔解耦，可验证 |

**一句话定位**：SparkArc 是「把写前核设定→写中推逻辑→写后验质量做成自动管道的聊天平台」，用稳定前缀保缓存、protected 区块保关键、成功才落盘统一全面性与成本；mo-shu 是「用确定性脚本承担防呆、AI 承担语义、作者拍板品味的 skill」。

---

## 10. 待验证问题

1. **「实测缓存命中率 ~94.5%」**：旧文档转述，代码中无该数字出处，命中率应由上游 API `cached_prompt_tokens` 返回。**存疑**。
2. **「PreWrite 工具循环 ≤4 次模型请求」**：旧文档给精确数字，但未读 `scriptwriter_prewrite.py`（21KB）核对，**存疑**。
3. **`architecture.md §7.2「7 维度」 vs `style_analysis.yaml:22「6 个 ## 维度段落」**：文档与 prompt 维度数不一致，**需核对 style_analysis.yaml 实际维度标题**。
4. **`AGENTS.md §10.0 列 6 个 architecture 测试，实际目录 7 个**（多 `test_prompt_cache_layout_contracts.py`），文档滞后。
5. **`auto_write.py` 的 `generate_script_stream`**（Auto-Write 实际生成循环 + 「从当前剧情进度开始」的扫描逻辑）未细读，续写游标细节以此为准。

---

## 11. 旧研究文档勘误（`docs/sparkarc-研究.md`，已于 2026-08-20 删除，本节为历史对照记录）

> 总评：旧文档整体准确度较高（8 个 Agent、五维 Critic、8 类 StoryMemory 状态、三圈记忆 3 场/2 章末、大纲契约字段、fix_ticket 结构等均与源码吻合）。以下为**与源码不符或过度解读**之处，按严重程度排序：

1. **【最严重·低估】「Style validator 未接线」——实为「ValidatorAgent 已删除」**：旧文档 §3 说「无确定性验证（validator 未接线）」，但源码中 `agent_style/agents/__init__.py:3` 明确注释「旧的多 Agent 并行 JSON 框架(StyleAnalysisAgent/ValidatorAgent/CoordinatorAgent)」已被移除，`workflow.py`/`unified_analyzer.py` 无任何 validator 调用。负向约束已改为分析时**内联抽取**（`style_analysis.yaml:16-17,128-130`「作者回避」→「## 作者回避(负面约束)」），不是 validator 自我对抗产出。`architecture.md §7.1` 的「图灵回测闭环」是纯文档残留。

2. **【严重·未标存疑】「实测缓存命中率 ~94.5%」**：旧文档 §2 当作已确认事实。代码中 `context_budget.py` 只实现预算裁剪与 checkpoint，不产生命中率统计；命中率只能来自上游 API 的 `cached_prompt_tokens`（AGENTS.md §5.2.1 也仅说明「由上游返回」）。该数字属文档/实测宣称，旧文档应标「存疑/来源为文档而非代码」。

3. **【中等·未标存疑】「PreWrite 工具循环 ≤4 次模型请求」**：旧文档 §1 Scriptwriter 行给了精确数字「≤4 次」，但旧文档未给行号、本次研究也未读 `scriptwriter_prewrite.py` 核对，属「未标注存疑的精确断言」。

4. **【轻微·过度概括】「导演……不做内容生产」**：旧文档 §1。源码 `registry.py:129-142` 的 `DIRECTOR_BASE_TOOLS` 实际含 `organize_scenes_to_chapter`（整理场景到章节）与 `replace_from_search`（基于搜索替换文本），属于轻度内容组织/修改操作；「不做内容生产」应改为「不产正文，但可做章节整理与批量替换」。

5. **【轻微·口径】「StoryMemory 运行期 8 类状态」**：旧文档 §3。源码 `facade.py:210-225` 确为 8 类且**持久化**到 `.story_memory/narrative_state.json`（`facade.py:16-17`），「运行期」一词易被误读为「内存态」，应为「持久化轻量状态层」（AGENTS.md §4.5.4 同此口径）。

（其余：三圈记忆「3 场全文 + 2 章末锚点」= `context_builder.py:47-48` 的 `MAX_CURRENT_CHAPTER_FULL_SCENES=3`/`MAX_CROSS_CHAPTER_TAILS=2`，**与源码一致**；Critic 五维、S/A→PASS、B→REVISE、大纲契约字段、fix_ticket 结构，**均与源码一致**。）

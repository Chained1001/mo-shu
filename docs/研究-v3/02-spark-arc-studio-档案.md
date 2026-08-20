# spark-arc-studio（引火AI / SparkArc）研究档案

| 项 | 值 |
|---|---|
| 研究日期 | 2026-08-20 |
| 研究对象 | `otherMaterials/referProject/spark-arc-studio`（工作区快照，**只读**） |
| 版本信息 | 客户端 `client/package.json` version=0.0.1（代码事实，非发布版本号）；`sparkarc.json` schemaVersion=1；仓库内未发现集中版本常量，本档案以 2026-08 快照为准，**无历史 git 可考**（见下） |
| 形态 | FastAPI 后端（`server/`，Python）+ Vue3 前端（`client/src/`，TS）+ Tauri 2 桌面端（`client/src-tauri/`）+ WinForms presenter（`presenter/`）+ Unity SDK（BETA）+ Docker/CI 部署 |
| 版本演进史 | **存疑/不可考**：该目录位于 mo-shu 仓库 `otherMaterials/` 下，`git rev-parse --show-toplevel` 返回 mo-shu 仓库根，即 spark-arc-studio 自身不是独立 git 仓库，无 git log 可用。所有"历史 Bug"均来自项目自述文档（README/AGENTS.md/architecture.md），标为「文档宣称」 |
| 修订说明 | v3 初版（承接 docs/研究-v2/01-审计报告 与 05-试错史 中 SparkArc 移植条目的深化研究）【总纲侧注 2026-08-20：此句系研究子代理从当时工作区旧 AGENTS.md 头部沿用的溯源表述，本轮从零研究并未读取该两文件，其内容未进入本档案任何论断；该路径现已归档至 docs/归档/研究-v2/】 |

阅读约定：所有路径相对 `otherMaterials/referProject/spark-arc-studio/`；「代码事实」= 本次源码勘察直接验证；「文档宣称」= 项目文档自述未实测；「（推断）」= 研究员判断。

---

## 一、项目概况

### 1.1 定位与边界（P0）

**定位**：面向创作者的"AI 工作室"——剧本/小说双形态创作，多 Agent 流水线（灵感→世界观→节拍/大纲→正文→审稿），文风克隆 + 反 AI 味为核心卖点，附带多租户 SaaS、分享/试玩、MCP 接入（代码事实：README.md:1-105、目录结构）。

**明确不做 / 明确搁置清单**（对 mo-shu 附录 C 极有参照价值）：

| 不做/搁置项 | 证据 | 说明 |
|---|---|---|
| Agent 水平自主通信 | README.md:566-578「信标总线……目前为**预留能力**——评估发现主流模型尚不完全具备处理多轮、多角色、长交互的能力」 | 基础设施（信标/号角/旗帜三件套）已全部实现（communication.py:465-503 `open_beacon/raise_horn/take_baton`，代码事实）但**未启用**——"已接线但主动关闭"而非删除 |
| 聊天历史不自动向量化 | docs/context-management.zh-CN.md:151-162 | 隐私边界：不授权把私人聊天发给云端 Embedding；给出了未来启用的 5 个前置条件 |
| 持久聊天历史 ≠ 长期记忆/用户画像 | docs/context-management.zh-CN.md:15「系统不会从聊天中自动构造用户画像、跨项目偏好、置信度或遗忘曲线」 | 明确拒绝 Mem0 式记忆系统（§10 研究依据） |
| 聊天摘要不写成剧情事实 | docs/context-management.zh-CN.md:192-199 §9 StoryMemory 边界四"不得" | 短期上下文与剧情状态严格分层 |
| 不训练专有 AI 检测分类器 | README.md:465-473（文档宣称）「优先利用大模型的判别与归因能力……LLM Judge / Editor」 | Critic 用五维等级而非概率分数 |
| GraphRAG 默认不挂载 | README.md:461-464「已生产化，但默认不挂载任何 Agent，可按需灰度启用」；代码事实 registry.py:59 `OPTIONAL_RESEARCH_TOOLS = [story_memory_tool, graph_rag_tool]` | 检索是可选灰度而非默认依赖 |

### 1.2 规模速览（代码事实，2026-08-20 实测）

| 指标 | 数值 | 复现命令 |
|---|---|---|
| 后端测试文件 | 65 个 `test_*.py` | `find server/test -name "test_*.py" \| wc -l` |
| 前端测试文件 | 66 个 `*.spec.ts` | `find client/src -name "*.spec.ts" \| wc -l` |
| 架构契约测试 | 7 个（`server/test/architecture/`） | `ls server/test/architecture` |
| Agent prompt YAML | 7 个共 1499 行（critic/director/lorebook/muse/scriptwriter/showrunner/utility） | `wc -l server/agents/prompts/*.yaml` |
| AGENTS.md | 44.8KB / 581 行 | `wc -c AGENTS.md` |
| architecture.md | 44.6KB | `wc -c docs/architecture.md` |
| core agents 文件 | communication.py 1964 行、context_budget.py 1330 行、director_graph.py 1135 行、story_memory/facade.py 1655 行 | `wc -l` |
| 专业 Agent | 6 个（director/muse/lorebook/showrunner/scriptwriter/critic）+ style 子集群 + utility | `server/agents/agent_*.py` |

---

## 二、端到端流程（流程层）

### 2.1 创作主流程（文档宣称 + 目录结构佐证）

```
用户 → Director(LangGraph SupervisorGraph 多轮工具调用调度)
  ├─ delegate_task → Muse(灵感种子) / Lorebook(世界观+角色卡)
  ├─ → Showrunner(梗概→节拍表→树状大纲)
  ├─ → Scriptwriter(构思链 conception → .arc 剧本 / 小说 Markdown，工具落盘)
  │     └─ 可选灰度：GraphRAG 事实约束 / StoryMemory 状态注入
  ├─ → Critic(五维审稿 S/A/B/C/D + fix_tickets，不直接改写)
  └─ trigger_auto_write → Auto-Write 后台任务（无人连写，独立事件流）
```

证据：README.md:390-534 智能体集群章节；`server/agents/tools/registry.py:22-130`（工具按 Agent 分组的完整清单，代码事实）。

### 2.2 三条入口、一条管线（代码事实）

AGENTS.md:111「三条入口，一条管线」（architecture.md §2.1）：面板按钮（`agent.execute()` 具名方法）、用户聊天（`chat_stream(skip_tool_confirmation=False)`）、导演委派（`delegate_task → chat_stream(skip_tool_confirmation=True)`）全部收敛到同一个 `chat()` 执行循环——communication.py:1390-1547（代码事实）：加载模态 prompt → `_build_tool_system_prompt` 注入工具块 → `build_chat_prompt_layout` 布局 → `prepare_chat_messages_with_budget` 预算 → `get_tools_for_agent(pipeline_mode=...)` → while 循环 `invoke → 解析 tool_calls → _execute_tool_calls → rebudget_existing_messages`。

### 2.3 内部状态机 / 事务（P0）

| 状态机 | 位置 | 要点 |
|---|---|---|
| Chat 流事件时序 | routes/chat.py + ChatTaskEntry（AGENTS.md:51-70） | append-only event_log + stream_seq，刷新后 task_snapshot + afterSeq 游标回放；运行中复用同一条 assistant DB 记录增量 checkpoint |
| 上下文压缩事务 | context_budget.py + docs/context-management.zh-CN.md §5.1 | **候选先行、成功才落盘**：模型请求完整成功才幂等保存 checkpoint；取消/失败/重试中间态一律不保存——这是"事务性摘要"，防脏摘要污染历史 |
| 编辑失效 | ChatManager（docs §5.2） | 用户编辑/删除被 checkpoint 覆盖的原文 → 自动删除对应 checkpoint，下次从原文重建 |
| Auto-Write 事件流 | auto_write_service.py:17-50 `AutoWriteTaskEntry` | 有界事件日志（LIMIT=2048）+ 条件变量 + seq 游标等待，支持重连续读 |
| 结构状态 | structure_state.py:11-25 | `.structure_state.json` 记录 synopsis/beat_sheet/outline 三工件 revision/stale/stale_reason——**派生工件过期标记**机制 |
| 迁移自愈 | core/auto_migrate.py（docs/database-migration.md §1） | 孤儿版本自愈、head 漂移保护（默认报错而非悄悄修库） |

### 2.4 异常与降级路径（P0，代码事实）

| 异常 | 处理 | 证据 |
|---|---|---|
| 短窗口模型装不下最小集合 | 抛 `context_window_incompatible`（不可重试），前端提示换模型，**不静默裁掉用户约束**；同一不兼容请求不会重试三次 | docs/context-management.zh-CN.md:61-67；communication.py:1532-1535 `NonRetryableChatError` 直接 re-raise |
| 压缩失败 | 抛 `context_compaction_failed`；**不会静默删最旧消息换"成功"** | docs §3.2 |
| 模型流重试 | `stream_model_turn_with_retry` + `ModelTurnRetryExhaustedError`（communication.py:184-235） | 重试通知为一等公民 |
| 管线写盘判定 | `resolve_pipeline_completion`（communication.py:155-183）：导演委派下若只输出草稿未调落盘工具，判定未完成，不得宣称章节完成 | AGENTS.md §4.5.4 第 1 条的代码实现 |
| 工具失败语义 | `is_pipeline_tool_result_failure`（communication.py:96）区分管线工具失败 | — |
| checkpoint 保存失败 | 记录错误但不重放已成功的模型/工具调用（docs §5.1） | 幂等优先 |

---

## 三、架构层

### 3.1 分层与收口（核心思想：统一收口，不复制实现）

AGENTS.md §2 列出**全部收口点清单**（前后端各 6-7 个），并配"反模式清单"（§9，11 条）逐条给出"错误做法→正确收口"。三大"大统一基建"（AGENTS.md:35-39）：

1. **`_apply_patch`**（tools/common.py:45）：一切"在已有文本中定位并替换"必须复用，禁止各 Agent 自写正则/replace（反模式 §9.10）。
2. **`TokenTextSplitter`**（core/file_ingest/chunking.py）：一切按 Token 切分复用（反模式 §9.11）。
3. **`SemanticChunker`**（server/story/semantic_chunker/）：一切语义分块复用。

（推断）mo-shu 的 shared-assets 同步机制本质是同一思想在纯 skill 形态下的对应物。

### 3.2 数据/状态设计：三层真相源分离（P0）

docs/context-management.zh-CN.md:7-15，三层易混淆数据严格分界：

| 层 | 真相源 | 是否自动发给模型 |
|---|---|---|
| 短期上下文（工作窗口） | context_budget.py 生成的 messages | 是 |
| 持久聊天历史（原文） | users.db.chat_messages | 否（只发 checkpoint 之后原文） |
| 剧情领域状态 | story_memory/（JSON 文件状态机） | 创作链路按需注入 |

StoryMemory（facade.py，1655 行）：以"场景写回"为原子（`record_scene_write`:317），增量抽取状态 delta（启发式或 LLM 抽取，`extract_state_delta`:562），角色/关系/线索（threads）按 scene_id 可回滚合并（`_remove_scene_contributions`:460）——即**状态是写的副产品，可按场景增量回滚**，而非全量快照（代码事实）。（推断）这与 mo-shu"不做每章全量快照"决策同源，但 SparkArc 走得更远：delta + 归一化 + 幂等 hash。

### 3.3 数据库迁移策略（docs/database-migration.md，全文精读）

核心纪律：**改 models.py → `gen_migration.py` 自动生成 → 启动时自动升级；严禁手写/手改迁移文件**（有专门禁令文件 `server/alembic/DO NOT MANUALLY EDIT MIGRATION FILES!.md`）。

工程亮点（文档宣称，机制在 auto_migrate.py/gen_migration.py 有对应代码）：
- 生成迁移不读真实库，用临时 head DB 对比 Models，防开发机污染；
- 重命名自动识别交互确认（防"先删后增"丢数据）；DROP COLUMN/TABLE 强制拦截；
- 孤儿版本自愈 + head 漂移默认报错（两个救急环境变量默认关）；
- 原子写：`core/json_state.py` 的 `save_json_file_atomic` + `json_state_lock`（work_tracker/structure_state 均用，代码事实）。

### 3.4 上下文管理与前缀缓存（P0，本档案最高价值区之一）

布局铁律（AGENTS.md §5.2.1 + docs/context-management.zh-CN.md §8，代码事实 prompt_layout.py 73 行小文件）：

```
[稳定 system 前缀] Agent身份/模态prompt/语言策略/工具清单/tool reference/tool_rules
[中段] checkpoint + 历史 + 压缩摘要 + 工具结果
[尾部] 当前编辑区/附件现场/本轮用户请求 ← build_current_user_message()
```

- 预算公式（docs §3）：连续比例预留 `reserved = max(min(20K, 10%·max), 6.25%·max)`，不硬切窗口；
- 工具循环后必须 `rebudget_existing_messages()`，禁止手写裁剪（AGENTS.md §5.2.1 第 3 条）；
- 缓存命中文档宣称实测：DeepSeek V4 flash max 连续导演对话第二轮命中 10752 token / ~94.5%（README.md:544，**文档宣称，未复现**）；
- 缓存失效因素显式列举（换模型/改 prompt/改工具绑定/语言策略），并约束"文档和 UI 不得暗示缓存跨这些变更仍稳定命中"（AGENTS.md §5.2.1 第 6 条）——**把 prompt cache 当受测协议对待**；
- 架构测试 `test_prompt_cache_layout_contracts.py` 用 MARKER 断言稳定块在动态块之前（代码事实，见 §6.3）。

### 3.5 检索/知识层

- GraphRAG（agents/graphrag/）：角色关系图谱服务，可选灰度；建图固定 Fast 槽位、查询跟随调用 Agent 模型（README.md:461-464，文档宣称）。
- 语义索引：每项目本地 LanceDB `.vector_index_lancedb`，无 pgvector（database-migration.md §5.2）。
- AgentSkills（skill_packs.py）：导入外部 skill 包时按 `QUALITY_SECTION_SIGNALS`（质量段信号词，中英双语集合，skill_packs.py:29-44）与 `RUNTIME_SECTION_SIGNALS` 剥离运行时内容，生成 `QUALITY_ADAPTER.md`，读取视图标 `quality_only`（:451, :645-693，代码事实）——**外部 skill 只当"写作质量参考库"，不当执行插件**，脚本类扩展名直接黑名单（:26 `SCRIPT_FILE_EXTENSIONS`）。
- `search_chat_history`：只读、房间隔离（参数中无 user_id/project，服务端注入）、literal/regex 两模式、正则 1000 字符/200ms 超时、摘录上限（docs §6，代码事实 tools/chat_history.py 存在）。

---

## 四、智能体层

### 4.1 职责切分（六专家 + 导演）

| Agent | 职责 | 模型配置 |
|---|---|---|
| Director | 全局入口、LangGraph 调度、上下文管理 | 每用户每 Agent 独立模型配置（matchbox 网关，`get_user_llm(user_id, agent_name=...)`，communication.py:1426，代码事实） |
| Muse / Lorebook / Showrunner / Scriptwriter | 创意→设定→结构→正文 | 同上；工具按 Agent 分组（registry.py:69-130） |
| Critic | 审稿不写稿；S/A/B/C/D + fix_tickets | 同上 |

### 4.2 三模态提示词协议（P0，全档案最精华机制）

每个 Agent 的 YAML 有三个顶层 system 字段（代码事实：communication.py:1407-1411 模态选择逻辑；critic.yaml:14-76 结构）：

| 模态 | 字段 | 受众 | 输出 |
|---|---|---|---|
| 专有工作 | `system`+`user` | 机器解析器 | 严格结构化、可落盘、禁寒暄 |
| 用户聊天 | `chat_system` | 真人 | 自然对话、可发散、不强制格式 |
| 导演委派 | `pipeline_system` | 上游 Agent（导演） | 结构化 + 调工具落盘 + 向导演简报 |

关键设计细节：
- `skip_tool_confirmation=True` → `pipeline_system`；`normalize_handoff_payload` 强制把 `user_confirmation_state` 提升为 `not_required`（communication.py:271，代码事实）——用**协议字段而非提示词措辞**保证子 Agent 进入管线模式。
- `pipeline_system` 硬约束（AGENTS.md:159-165）：①第一句受众声明"你的受众是导演，不是用户"；②三件套主干（调工具/一步到位/简报）；③格式规范走 tool reference 不复述；④**严禁"格式同 system"式引用**——两段在代码里互斥选择，LLM 看不到另一段（这是极容易被忽视的 prompt 工程陷阱）；⑤禁止头脑风暴式软约束。
- 历史真实 Bug（文档宣称，AGENTS.md:178）：Muse 未注册 tool reference，导演委派时 LLM 丢失 7 条格式规范→"导演委派灵感 Agent 时跑去构建世界观"的模态串味。

### 4.3 Prompt 工程三件套（P0）

1. **tool reference 自动注入**（格式规范唯一真相源）：`_get_tool_prompt_references()` 返回 `{tool_name: [{prompt_key, field}]}`，`_build_tool_prompt_reference_block()`（communication.py:726）在绑定工具时展开为"当你决定调用工具 X 时，必须复用以下既有生成规范：…"拼到 system 末尾。**产出规范挂在工具上而非写在 pipeline_system 里**，避免双份维护漂移。例外：无落盘工具的 Agent（critic）必须在 pipeline_system 内嵌规范摘要。
2. **`base` 字段共享段**：YAML 顶层 `base` 被 `load_prompt` 递归展平为 `base.xxx` 占位符注入（agent_utils.py:134-180，代码事实），各模态用 `{base.identity}`/`{base.review_dimensions}` 引用（critic.yaml 实测：identity/五维/等级映射/json_fields 四段全共享）。
3. **`tool_rules` 字段**：工具使用补充规则（调用顺序/输出纯度/反注入）只在 chat/pipeline 模式自动追加（AGENTS.md §4.5.3），已从 Python 硬编码迁移到 YAML，Director 例外保留（运行时动态团队概览不可静态化）。

（推断）这三件套解决的是 mo-shu 同样面临的问题：**同一段规范要在"多个入口/多个模板"复用而不漂移**。mo-shu 的对应物是 agent-references 副本 + shared-assets 同步，但 SparkArc 用"占位符 + 挂载点注入"把复用做进了运行时。

### 4.4 多 Agent 编排与确认点（人机分工）

- 垂直调度（Director，LangGraph SupervisorGraph）与水平协作（信标总线，预留未启用）**双系统分立**，明确"为何需要两套"（architecture.md §1.3）——水平自主通信因模型能力不足而主动冻结，是对"LLM 导演黑盒自治"风险的工程化回答。
- 确认点设计：用户聊天模式 `skip_tool_confirmation=False`（工具确认开）；导演委派自动免确认；`auto_review`（边写边审）**默认关闭**，须用户显式开启或导演收到明确意图（AGENTS.md §4.5.4 第 4 条，代码事实 registry.py 可见工具分组）。
- 手动保存 `.arc/.md` 只回写 StoryMemory，不得隐式触发 Critic 或重写正文（§4.5.4 第 5 条）——**保存是保存，审查是审查**，防自动连写污染。

---

## 五、技能层（对 mo-shu 最直接相关的形态研究）

SparkArc 的 AgentSkills 是"外部 skill 的只读消费端"，与 mo-shu"skill 即产品本体"形态相反，但其**导入与降险机制**极具参考价值（skill_packs.py，715 行，代码事实）：

| 机制 | 位置 | mo-shu 映射意义 |
|---|---|---|
| 目录白名单 `ALLOWED_TEXT_DIRS = {references, templates, resources...}` | :27 | 只读参考目录隔离 |
| 脚本扩展名黑名单 + 大小上限（skill 2MB / 单文件 500KB） | :26-28 | 防注入与防爆仓 |
| 质量段/运行时段信号词双语集合，按 section 头分类 | :29-44, :170 | **内容分级读取视图**：一段内容"当参考书读"还是"当代码执行"是可机检的 |
| 生成 `QUALITY_ADAPTER.md` + 索引标 `quality_only` | :430, :451 | 导入即降险，读取端无需再判断 |
| 工具入口仅 search_skills / read_skill / read_skill_reference，按需检索 | tools/registry.py:61-63 | Skill 内容是动态工具结果，**不自动拼入 system 前缀**（AGENTS.md §5.2.1 第 4 条）——防 prompt cache 失效 + 防外部内容覆盖输出协议 |

---

## 六、工程层

### 6.1 确定性纪律：三层分工

AGENTS.md 通篇体现的分工：（推断）这是 mo-shu AGENTS.md §2 三层分工（脚本确定性/文件证据/agent 判断）的源头：
- **代码管协议**：模态选择、免确认提升、缓存布局由 Python 强制，LLM 无发言权；
- **YAML 管内容**：prompt 全部出代码进 YAML，带 base/tool_rules 结构化字段；
- **LLM 只管生成**：输出必须过解析器/落盘工具才算完成。

### 6.2 防呆与自愈

迁移危险操作拦截与救急开关默认关、head 漂移默认报错不悄悄修（§3.3）；Auto-Write 事件日志有界防内存膨胀；checkpoint 编辑失效自动重建；工具参数占位符默认填充防 LLM 看到字面 `{worldview}`（AGENTS.md:208）。

### 6.3 质量保障与测试文化（P0）

**架构测试（基础建筑测试）**目录 `server/test/architecture/` 仅 7 文件，准入三条件（AGENTS.md §10.0"测试放置决策"7 条，代码事实）：
1. 守护跨模块稳定不变量；2. 直接覆盖统一 registry/facade/protocol；3. 普通迭代不会频繁改断言。
凡主要断言 prompt 措辞、供应商参数、单接口结果、README 字符串者**禁止入 architecture/**。

测试协议（§10.0.2 八条，与 mo-shu 验收哲学高度同源）：
- **测协议不测实现**：断言事件名/事件形状/状态机终态/注册表一致性/回放能力；
- **测收口不测使用点**；
- **禁止脆弱快照**（整段 HTML/prompt/生成结果）；
- **禁止真实上游**（LLM/联网/API key）；
- **失败先判因，禁止改断言变绿**（第 6 条，逐字与 mo-shu 施工纪律同源）；
- 例外印证：`test_prompt_cache_layout_contracts.py` 用注入 MARKER 的 values 断言**块顺序**而非文案——测"布局不变量"的优雅范例（代码事实）。

**临时测试生命周期**（§10.0.1）：仓库只允许两种测试状态——临时验证（`/.tmp/tests/<任务>/`，verify_*/probe_* 命名，用完即删）与正式回归（领域目录）。判断口诀："只回答'现在是否正常'就用临时验证并删除；要防止'以后再次坏掉'才写正式回归测试。"（mo-shu AGENTS.md §1.4 的直接出处，代码事实）。

**测试文件顶部"守护对象"声明模板**（§10.0.2 末尾）：docstring 写明守护对象 + 本测试禁止事项。

### 6.4 安全权限

无 SECURITY.md（代码事实：根目录无此文件）。安全约束内嵌 AGENTS.md §12"AI 权限安全红线"：git 只读默认、禁止把自动批准当用户意图（mo-shu AGENTS.md §1 前两条的出处，代码事实）。项目级安全：MCP 写盘必须走 Director 工单不直接暴露写盘工具（AGENTS.md:138）；`validate_project_name` 统一路径校验防路径穿越（:139）；聊天检索房间隔离（§3.5）。

### 6.5 部署分发

Docker（五持久卷 + 原子换容器 + 受管文件同步）+ Gitea/GitLab/GitHub 三平台 CI（cicd-deployment.md）+ Tauri 2 桌面三平台 + Android APK + 客户端热更策略（client-runtime-update-strategy.zh-CN.md）。（推断）对 mo-shu 参考价值低，唯"GitHub/Gitea 双兼容 Token 变量、裸 git 检出绕过 checkout 兼容问题"（cicd-deployment.md §1）是跨平台 CI 小技巧。

---

## 七、治理层（P0）

### 7.1 AGENTS.md = 治理宪法

44.8KB 强约束文档，结构值得逐段研究：铁律（§1）→ 统一收口清单（§2）→ 双主链路辨析（§3）→ 扩展规则+自检清单（§4-5）→ 协议边界（§6）→ 数据红线（§7）→ 新增流程推荐模板（§8）→ **反模式清单（§9，11 条，每条"错误做法→正确方式"）** → 测试体系（§10，含临时测试协议/维护测试站协议）→ 提交前自检（§11）→ AI 权限红线（§12）。

（推断）mo-shu AGENTS.md 的"移植来源"（mo-shu AGENTS.md 头部自述"来源：SparkArc AGENTS.md 移植"）主要是 §11 提交前自检 + §12 权限红线 + §10.0.1 临时测试；**尚未移植**的是：反模式清单的"错误做法→正确方式"双栏格式、§8"新增流程推荐模板"（新增能力先判断"接现有收口还是开新管线"的决策树）、§4.6/§5.3 新增 Agent 双端同步自检清单。

### 7.2 文档先行与 CLAUDE.md 兼容层

CLAUDE.md 仅 7 行：指向 AGENTS.md 为唯一权威 + 核心指令摘要（代码事实）。这是"单一宪法 + 多入口薄壳"模式：避免 CLAUDE.md/AGENTS.md 双份漂移。

### 7.3 开发流程闭环

（推断，从 AGENTS.md 结构反推）SparkArc 无 spec→implement→check 的显式批规格流程（那是 mo-shu 自创），其闭环是"宪法约束 + 架构测试护栏 + 提交前自检"三件套，靠常驻约束而非逐批规格。

---

## 八、交互层

- **人机分工**：Director 是唯一对话入口；专家 Agent 也可直接聊天（chat_system 模态）但输出不落盘；正文落盘必须走工具（§2.4 管线完成判定）；Critic 只出意见不改稿（"保留创作者主导权"，README.md:459）。
- **打断/接管**：stop_event 贯穿 chat_stream（communication.py:1554 参数）；取消不保存 checkpoint；Auto-Write 有独立取消/遮罩。
- **透明度**：工具事件 UI 元数据由后端注入（`build_tool_stream_event`），前端不自行维护映射（AGENTS.md §4.4）；压缩动画覆盖真实等待时间"不是完成后补播"（docs §7）；缓存命中显示规则（不混入子 Agent、为 0 不显示）。
- **内容资产形态**：梗概.txt/节拍表.txt/大纲.txt + .arc 剧本 + Markdown 小说 + 角色卡 + 风格档案 + StoryMemory JSON（structure_state.py:16-20 中文文件名工件，代码事实）。（推断）与 mo-shu 的"文件即作品"的差异：SparkArc 有 DB（users.db/stories.db），项目文件是"导出/快照"语义。

---

## 九、可借鉴清单（形态转译：mo-shu 是纯 skill 仓库，无后端运行时）

### 低成本（改文档/模板即可）

| # | 借鉴点 | 源码位置 | mo-shu 落点建议 |
|---|---|---|---|
| L1 | **CLAUDE.md 薄壳指向 AGENTS.md** | CLAUDE.md:1-7 | mo-shu 若需 CLAUDE.md 兼容，仅写指向 + 3 条核心指令，杜绝双份漂移 |
| L2 | **反模式清单双栏格式**（错误做法→正确收口） | AGENTS.md §9 | mo-shu AGENTS.md 增加"反模式清单"节，把散在批规格里的禁止事项集中为 8-10 条双栏条目 |
| L3 | **新增流程推荐模板**（"接现有收口还是开新管线"决策树） | AGENTS.md §8 | 写入实施总纲：新增能力前先过"能否挂现有 skill/references/脚本"判定，防平行管线 |
| L4 | **禁止"格式同 system"式 prompt 互引**（两段互斥，LLM 看不到对方） | AGENTS.md:164 | 写入 agent 模板写作规范：moshu-* 各模板引用规范必须内嵌或指真实文件路径，禁止"同上/参照上文" |
| L5 | **测试文件顶部"守护对象+禁止事项"docstring** | AGENTS.md:504-518 | mo-shu 回归测试脚本（test_*.py/.sh）统一加头部声明 |
| L6 | **架构测试准入三条件 + 禁止脆弱快照断言** | AGENTS.md:454-462 | mo-shu 行为契约（behavior-contracts）增加准入条件与"禁断言 prompt 全文"条款 |
| L7 | **缓存失效因素显式列举 + "UI/文档不得暗示跨变更命中"** | AGENTS.md §5.2.1 第 6 条 | （转译）Claude Code 场景下 = agent 模板/references 任何改动都会使会话内前文失效，长会话使用指引应写明"改模板后需新会话生效" |
| L8 | **保存≠审查的边界**（手动保存只回写状态，不隐式触发审查/重写） | AGENTS.md §4.5.4 第 5 条 | moshu-write 的保存/收尾步骤声明：不得隐式触发 review 或文风重写，须显式命令 |
| L9 | **`auto_review` 默认关闭、须显式意图** | AGENTS.md §4.5.4 第 4 条 | mo-shu 审查 skill（review）与写作分离已有；补一条"自动边写边审默认关"到产品边界 |

### 中成本（写脚本/改 skill 结构）

| # | 借鉴点 | 源码位置 | mo-shu 落点建议 |
|---|---|---|---|
| M1 | **三模态提示词分离**（面板工作/用户对话/管线委派） | communication.py:1407-1411；prompts/*.yaml | mo-shu agent 模板已是类似结构（写作模式/对话）；增量：为"被上层流程调用的子角色"（如文风 explorer 快捷路径）显式定义 pipeline 版模板 + 受众声明首句 |
| M2 | **规范挂工具/挂载点注入而非复制**（tool reference 机制） | communication.py:726-783 | （转译）mo-shu 无运行时注入，但可用"锚点段 + 脚本拼装"近似：写作规范集中在 references 单文件，各 workflow 用显式锚点引用（已在做）；增量是**机检脚本验证锚点存在且无第二副本**（扩 check-shared-files） |
| M3 | **base 共享段 + 占位符展平** | agent_utils.py:134-186 | agent-references 已有副本同步；增量：跨模板重复的身份声明/禁止事项抽成共享段文件，部署脚本拼装展开 |
| M4 | **上下文布局三段式 + 稳定前缀优先**（固定→动态→历史） | prompt_layout.py；AGENTS.md §5.2.1 | moshu-write 写前上下文组装顺序规范化：设定/文风/卷纲（稳定）→ 本章细纲/上一章尾（动态）→ 历史；写入 agent 模板并配机检（顺序断言） |
| M5 | **MARKER 顺序断言测布局**（不测文案测顺序） | test/architecture/test_prompt_cache_layout_contracts.py | mo-shu 新增布局契约测试：注入标记字符串到模板占位符，断言稳定块先于动态块 |
| M6 | **JSON 原子写 + 文件锁**（save_json_file_atomic/json_state_lock） | core/json_state.py:76 行 | mo-shu 状态文件（9 序状态机等）写脚本统一走"临时文件+rename"原子写 |
| M7 | **结构工件 stale 标记**（revision/stale/stale_reason） | structure_state.py:11-40 | 设定/大纲被改后，派生物（细纲/章节摘要）标 stale；日更前置检查提示重生成 |
| M8 | **迁移危险操作拦截 + 救急开关默认关** | database-migration.md §2.1 | mo-shu schema migrate 脚本已有备份；增量：删列/删文件类操作交互确认 + 修复型开关默认关 |
| M9 | **创作型压缩摘要 schema**（保留否决方案/版本覆盖/审美禁区/原话锚点，非会议纪要） | docs/context-management.zh-CN.md §4 | mo-shu 卷复盘/长会话压缩提示词（若有）照此 9 要素设计；尤其"已否决方案及理由"防反复 |
| M10 | **外部内容 quality_only 分级读取**（信号词分类 + 导入即降险） | skill_packs.py:29-51 | （转译）mo-shu 拆文库/对标原文导入时，机检脚本按 section 头分类"可执行参考"vs"纯素材"，生成适配层声明 |

### 高成本（结构性改造，谨慎评估）

| # | 借鉴点 | 源码位置 | 说明 |
|---|---|---|---|
| H1 | **StoryMemory 场景级增量状态 + 可回滚合并** | story_memory/facade.py:188-960 | 剧情事实库按场景 delta 写入、threads 合并、scene 级回滚。mo-shu v2 规划（U3）已是此方向；SparkArc 1655 行工程量提示：**启发式抽取兜底 + LLM 抽取可选**（facade.py:588-629）的分层值得照搬，降确定性风险 |
| H2 | **事务性 checkpoint（候选先行、成功才落盘、编辑失效重建）** | context_budget.py + docs §5 | mo-shu 长写作会话（若有状态持久化单元）的落盘纪律蓝本 |
| H3 | **文风克隆串行分析 + Validator 自我对抗回测** | README.md:478-509（文档宣称）；agent_style/ 目录 | 30k 块串行 7 维分析 + 模仿自评 + 负向约束生成闭环；moshu-style 可借鉴"图灵回测"思想（写伪作自检），但注意 mo-shu 05 档案已有"validator 删除后文档残留图灵回测"教训——若借鉴须代码与文档同步 |

---

## 十、不可借鉴清单

| # | 项 | 理由 |
|---|---|---|
| N1 | 信标/号角/旗帜水平 Agent 通信 | 项目自己承认"主流模型尚不具备该能力"而冻结（README.md:566）；且 mo-shu 明确不做"LLM 导演黑盒自治"（附录 C），水平自治更远 |
| N2 | LangGraph SupervisorGraph 运行时编排 | 纯 skill 形态无运行时；mo-shu 的编排=SKILL.md 步骤 + 文件状态机，引入框架依赖违背纯 skill 定位 |
| N3 | NDJSON/SSE 双流协议、chatStore、前端 i18n 四语 | 前后端形态专属；mo-shu 无 UI 层 |
| N4 | 多租户 SaaS / 兑换码 / 分享试玩 | 产品商业化层，与 mo-shu 个人创作工具定位无关 |
| N5 | Alembic 多库迁移体系整体 | mo-shu 数据=JSON 文件+脚本 migrate 已够；整套 DB 迁移是过度工程（但其**纪律**——禁手写、危险拦截、默认报错不悄悄修——已被 M8 借鉴） |
| N6 | GraphRAG / LanceDB 向量检索 | mo-shu 附录 C 显式不做 RAG/向量检索 |
| N7 | ARC 互动剧本格式 | 领域不同（互动剧本 vs 网文）；但其"人机双读混合格式"动机（README.md:617-622）对 mo-shu 章节文件格式设计有思想参照（仅思想，不学格式） |
| N8 | work_tracker 任务板 | （注意）SparkArc 有 work_tracker.py（每 Agent 一个 JSON 任务板，work_tracker.py:27-33），但 mo-shu 附录 C 显式不做 work_tracker 任务板——保持决策 |
| N9 | Tauri/Docker/CI 分发体系 | 形态不匹配，仅 cicd 小技巧可摘 |

---

## 十一、差异定位（spark-arc vs mo-shu）

| 维度 | spark-arc-studio | mo-shu |
|---|---|---|
| 形态 | 全栈应用（server+client+桌面端） | 纯 Claude Code skills 仓库 |
| 确定性来源 | Python 代码强制协议 | 脚本机检 + 文件系统证据 |
| Prompt 管理 | YAML + 运行时注入/占位符 | Markdown 模板 + 部署时副本同步 |
| 编排 | LangGraph 运行时图 | SKILL.md 声明式步骤 |
| 状态 | DB + JSON 状态机三层 | 文件即真相（9 序状态机） |
| 治理 | AGENTS.md 宪法 + 架构测试 | 批规格 + 验收命令 + AGENTS.md（后者源自前者移植） |
| 记忆 | StoryMemory 领域状态 + chat checkpoint | 显式拒绝同类重设施（附录 C） |
| 共同基因 | 收口思想、测协议不测实现、临时测试纪律、git 只读红线、失败先判因、明确不做清单 | （同左，多为移植或同源） |

---

## 十二、待验证问题

1. 文风克隆集群（agent_style/）与 Validator 回测的**代码现状**未逐行勘察（README 宣称完整闭环）——mo-shu 05 档案曾记"validator 删除后文档残留图灵回测"教训，SparkArc 自身是否文档-代码一致需专查 agent_style/ 目录。
2. director_graph.py（1135 行）的 SupervisorGraph 节点/边结构、delegate_task 工单协议细节未深入——若 mo-shu v2 U5 审查闭环要参考其"工单"形态需补查 tools/delegation.py。
3. 缓存命中 94.5% 为文档宣称，无复现路径；mo-shu 引用时必须标注。
4. presenter/（WinForms）与 Unity SDK 与主链路关系未查（低优先）。
5. （存疑）项目自称版本演进史无从考证（无独立 git），"历史 Bug"（如 Muse tool reference 丢失）均为自述，但对应测试 test_director_skip_confirmation.py 等真实存在，可信度较高。

---

## 十三、错误清单（SparkArc 犯过的错/踩过的坑 → mo-shu 教训）

| # | 错误 | 证据 | 修复方式 | mo-shu 教训 |
|---|---|---|---|---|
| E1 | Muse 未注册 tool reference → 导演委派时 LLM 丢失 7 条格式规范 → 模态串味（跑去构建世界观） | AGENTS.md:178（文档宣称）+ 对应测试 test_director_skip_confirmation.py 存在 | 建立 tool reference 注册契约 + 三模态架构测试 | **有落盘动作的角色必须机检其"规范挂载点"存在**；mo-shu 对应：agent 模板引用的 references 文件由 guard 验证存在（已在做，保持） |
| E2 | pipeline_system 里写"格式同 system"式引用失效（两段互斥，LLM 看不到） | AGENTS.md:164 列为"严禁" | 写成显式硬约束第 4 条 | 模板互引必须可解析（L4）；mo-shu 曾有裸文件名引用 bug（git log eb92ecc），同类 |
| E3 | 多处重复实现文本替换/切分（"避免 3 次以上重复实现"） | AGENTS.md:37、§9.10-9.11 | 下沉三大统一基建 + 反模式禁止 | shared-assets 收口思想同源；新脚本先问"是否已有" |
| E4 | Python 侧硬编码 tool_rules 与 YAML 漂移 | AGENTS.md:245-260 迁移规则 | 逐字迁移 YAML，删子类重写；Director 动态内容例外保留 | 模板规范从代码/流程文档迁 references 时逐字迁移并删源，防双份 |
| E5 | 测试运行产物污染 Git 跟踪的测试目录 | AGENTS.md §9.8 | /.tmp/ 强制 + 提交前检查 Git 状态 | mo-shu AGENTS.md §1.4 同款（移植） |
| E6 | 短平快修补破坏长期可维护性 / 临时入口不接 registry | AGENTS.md §1 铁律、§9.6 | 四大收口注册同步为硬要求 | 新 skill/脚本接入索引+契约清单（mo-shu §3 自检 1/2，保持） |
| E7 | 把自动批准当用户意图做 git 写操作 | AGENTS.md §12 | git 只读红线 | mo-shu §1.1/1.2（移植，保持） |
| E8 | 为图省事静默删最旧消息换压缩"成功"（被否的设计） | docs/context-management.zh-CN.md §3.2"系统**不会**……因为这种做法会让创作约束和用户原话无声消失" | 改为显式失败错误码 | 降级路径宁可显式失败不可无声丢用户约束——写入 mo-shu 异常处理原则 |
| E9 | 缓存命中率展示混入子 Agent 误导用户 | AGENTS.md:314 详细纠正规则 | 显示规则收口到单一数据源，0 不显示 | 展示类数字必须单一真相源 + 边界声明（mo-shu 文档数字同理） |
| E10 | 迁移链被上游重置 / 开发机真实库污染 autogenerate | database-migration.md §1.3、§1.8 | 临时库生成 + 孤儿自愈 + head 漂移默认报错 | 数据迁移永远不动用户真库做基准；自愈只兜简单增删 |

---

## 十四、22 维覆盖自评表

| # | 维度 | 覆盖 | 关键证据节 |
|---|---|---|---|
| 1 | 定位与边界 | 深 | §1.1 |
| 2 | 版本演进史/试错史 | 浅（无 git，仅文档自述） | 头注/§12.5/§13 |
| 3 | 端到端流程 | 深 | §2.1-2.2 |
| 4 | 状态机/事务 | 深 | §2.3 |
| 5 | 异常与降级 | 深 | §2.4 |
| 6 | 分层与模块边界 | 深 | §3.1 |
| 7 | 数据/状态设计 | 深 | §3.2 |
| 8 | DB 迁移策略 | 深 | §3.3 |
| 9 | 检索/知识层 | 中 | §3.5 |
| 10 | Agent 职责切分 | 中 | §4.1 |
| 11 | Agent 设置（模型/工具/约束） | 中 | §4.1/registry.py |
| 12 | Prompt 工程【P0】 | 深 | §4.2-4.3 |
| 13 | 多 Agent 编排 | 中（director_graph 未逐行） | §4.4 |
| 14 | Skill 设计 | 中 | §5 |
| 15 | 确定性纪律 | 深 | §6.1 |
| 16 | 防呆与自愈 | 中 | §6.2 |
| 17 | 测试文化【P0】 | 深 | §6.3 |
| 18 | 性能成本 | 中（缓存宣称未复现） | §3.4 |
| 19 | 安全权限 | 中 | §6.4 |
| 20 | 部署分发 | 浅（形态不相关） | §6.5 |
| 21 | 治理宪法【P0】 | 深 | §7 |
| 22 | 用户体验/人机分工 | 中 | §8 |

覆盖统计：深 11 / 中 9 / 浅 2（版本史受客观限制、部署分发形态不相关）。P0 六维全部深/中覆盖。

---

## 附：本档案证据复现命令（只读）

```bash
cd otherMaterials/referProject/spark-arc-studio
find server/test -name "test_*.py" | wc -l        # 65
find client/src -name "*.spec.ts" | wc -l          # 66
ls server/test/architecture                        # 7 个契约测试
wc -l server/agents/prompts/*.yaml                 # 1499 总行
wc -c AGENTS.md CLAUDE.md docs/*.md
grep -n "skip_tool_confirmation" server/agents/communication.py   # 模态选择
grep -n "QUALITY_SECTION_SIGNALS" server/agents/skill_packs.py    # quality_only
```

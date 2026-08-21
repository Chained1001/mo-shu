# 证据卡片 · DeterminFlow 主仓（辅 · 增量）

| 项 | 值 |
|---|---|
| 研究对象 | DeterminFlow 主仓（即 DeterminFlow Core，通用确定性工作流运行时） |
| 仓库版本 | `0.1.0`（`pyproject.toml:7` version）；git HEAD `fe217de`（2026-08-11） |
| 研究路径 | `otherMaterials/referProject/DeterminFlow`（绝对只读） |
| 路径基准 | 全部相对 **DeterminFlow 主仓根**（如 `src/workflow/execution_flow.py:309`） |
| 定位 | 主仓 = 编排引擎宿主，**不含写作领域实现**（`docs/architecture.md:5`）。写作资产与 33 个写作 Agent 全在 DeterminFlow-Plugins 仓，已覆盖，见研究-v3 档案 01 |

> 核心判断（【事实】）：主仓与笔枢插件不重叠、而是**上下层关系**——插件定义写作 Workflow 与 Agent，主仓提供"节点引擎/回滚/快照/审批/变量注入"通用机制。本轮增量即这些通用机制；写作语义层（设定/大纲/卷纲/细纲/正文文件）在主仓**不存在**。研究-v3 档案 01 §13.2 曾把"Core 引擎如何消费/审批语义"列为存疑待验证，本卡片补上该部分。

---

## 维度 1 · 资产分层

**1.1** | 主仓不含设定/大纲/卷纲/细纲/正文任何写作资产分层——它是通用工作流运行时，明确"不包含长期记忆或小说领域实现" | `docs/architecture.md:5`、`pyproject.toml:8`（description="Deterministic workflow runtime"）、`config/` 全量 grep 无 outline/worldview/character 写作 agent（唯一命中 `config/prompts_config.json:60` 为通用工作流执行路径文案） | 【事实】 | v0.1.0

**1.2** | Core 自身的资产三层结构：`definition.json`（可复用模板，可修订）→ Task `snapshot_definition`（创建时冻结的快照）→ 共享 workspace（运行产物）；真源是模板，快照保证运行不受后续修订影响 | `src/core/defaults/skills/workflow-guide/SKILL.md:20-21`（"definition.json 是可复用的工作流模板 / Task 是创建时冻结模板快照的运行实例"）、`src/workflow/manager.py:473`、`src/workflow/manager.py:547`（`snapshot_definition=def_dict`） | 【事实】 | v0.1.0

**1.3** | 写作语境下的资产分层（设定/大纲/卷纲/细纲/正文，真源哲学、meta/outline/story/world/archive 双区结构）在主仓**未发现该机制**——见研究-v3 档案 01 §4.2 | — | 未发现 | —

## 维度 2 · 修订机制

**2.1** | 下游节点可拒绝上游产出并触发回滚重试（`reject_upstream`），带拒绝次数上限（默认 3）与完整拒绝审计历史（rejection_history 记录 reason/error_codes/retry_index/resolution） | `src/workflow/execution_flow.py:309`（`MAX_REJECTION_COUNT = 3`）、`src/workflow/execution_flow.py:417-458`（拒绝计数 + rejection_history 追加 + max_reject 上限）、`src/workflow/nodes/agent.py:92-105`（enable_reject_upstream/max_reject_count 参数） | 【事实】 | v0.1.0

**2.2** | 审批节点驳回同样触发回滚到上游节点，用反馈消息重跑上游会话（最多 3 次）；驳回原因经 `_with_rejection_feedback` 拼进上游首消息 | `src/workflow/execution_flow.py:651-688`（approval 驳回 → 回滚上游）、`src/workflow/execution_flow.py:41-57`（拒绝反馈注入 first_message）、`src/workflow/prompt_injector.py:35` | 【事实】 | v0.1.0

**2.3** | 工作流模板（定义）版本化：创建 `version=1`，每次 update_workflow / 增删改 execution_scheme 都 `bump_version()` 递增 | `src/workflow/manager.py:273`、`src/workflow/manager.py:307-320`（old_version+1）、`src/workflow/definition.py:417-419`（bump_version） | 【事实】 | v0.1.0

**2.4** | Task 创建时冻结模板快照（bk-sops 模式）——之后修改模板不影响运行中的 Task；历史任务优先读自身 snapshot_definition | `src/workflow/manager.py:473`（"保存当前工作流定义的快照，确保任务不受后续编辑影响"）、`src/workflow/task_queries.py:30`（"优先使用任务自身的 snapshot_definition，确保历史任务不受后续编辑影响"）、`src/core/defaults/skills/workflow-guide/SKILL.md:226-227` | 【事实】 | v0.1.0

**2.5** | Script Library 身份冻结 + 漂移检测：Task 创建时 `attest`（owner/revision/entrypoint_sha256/files_sha256），执行前 `verify_attestation` 重算比对，漂移即拒绝执行 | `src/workflow/script_library.py:260-312`（attest）、`src/workflow/script_library.py:314-341`（verify_attestation，337 行 "已漂移，拒绝执行"）、`docs/architecture.md:75-77` | 【事实】 | v0.1.0

**2.6** | 扩展 Workflow 资源 provision 的 stale/orphan 处理：上游已删除的文件，用户未修改的同步删除；用户修改过的保留并记入 `orphaned_files`（reason=user_modified） | `src/extension_host/workflow_provisioning.py:162-203`（stale_files / orphaned_files / user_modified 保留）、`docs/architecture.md:65` | 【事实】 | v0.1.0

**2.7** | 未发现该机制：无"上游修改→自动标记下游 stale/级联失效"的影响分析清单——影响传递靠运行时 `reject_upstream`（下游发现矛盾才打回），无构建期被动影响分析；版本管理靠 definition version 字段 + 快照，无 git 书仓托管 | — | 未发现 | —

## 维度 3 · 构建-执行分离

**3.1** | 编辑与运行分离：工作流模板（构建/定义层）与 Task（运行实例）是两个对象，操作前必须先区分"模板 / 已有 Task / 新 Task"；Node 类型由 Core 独占（agent/script/approval/subprocess 四类） | `src/workflow/manager.py:461`（"任务管理（编辑与运行分离）"）、`src/core/defaults/skills/workflow-guide/SKILL.md:18-35`、`docs/architecture.md:16`（"Workflow Node 类型由 Core 独占，Extension 只能组合"） | 【事实】 | v0.1.0

**3.2** | Task 创建（冻结快照 + 填参）与启动（run_task）是两个独立步骤；安全顺序固定 create→set_workflow_variable→start→（审批/重试）→get_task_result | `src/workflow/manager.py:464-573`（create_task）、`src/workflow/manager.py:575+`（run_task）、`src/core/defaults/skills/workflow-guide/SKILL.md:196-205`（Task 安全顺序） | 【事实】 | v0.1.0

**3.3** | 未发现该机制：主仓无"细纲归构建还是执行"的写作语义切分——构建型节点（大纲/细纲生成）与执行型节点（脚本拆分/渲染）在同一 workflow 模板内顺序编排，无独立命令/会话切分；写作层的切分发生在插件仓 workflow 设计，见研究-v3 档案 01 §3.1（build→character→story-plan→outline 前置链 vs mvp 单章循环） | — | 未发现 | —

## 维度 4 · 技能/角色架构

**4.1** | Core 默认资源是 6 个"元技能"（操作/设计指南），非写作角色；划分原则是"通用流程 → workflow-guide，专项设计 → 各自 Core Skill（agent-definition/prompt-template/script-library/skill-rule-authoring/automation）" | `src/core/default_resources.py:34-99`（provision_core_skills 同步 6 个 SKILL）、`src/core/defaults/skills/`（6 目录清单）、`src/core/defaults/skills/workflow-guide/SKILL.md:3-4`（description 指向各专项 Skill） | 【事实】 | v0.1.0

**4.2** | 生成型/消费型写作角色（33 Agent：worldbuilder/outliner/director/写手群等）不在主仓——全在插件仓 bishu-novel，见研究-v3 档案 01 §5.1；主仓 config 无任何写作 agent 定义 | `config/agents_config.json`（grep 无 outline/worldview/character 匹配）、`docs/architecture.md:5` | 【事实】 | v0.1.0

**4.3** | 角色以"Agent 类型（agent_type）"被节点引用，运行时不内联定义、按 agent_type 创建子会话；模型可任务级覆盖但只允许 agent 节点（node_model_overrides，冻结进快照） | `src/workflow/task_overrides.py:84-133`（apply_node_model_overrides，125-129 行限制 node_type=agent）、`src/core/defaults/skills/workflow-guide/SKILL.md:29-30`（"list_agent_types 确认 agent_type 仍存在"） | 【事实】 | v0.1.0

## 维度 5 · 上下文衔接

**5.1** | 构建产物喂给写作 = 运行时变量池 + 占位符替换（`{{key}}` / `{{list[0]}}` / `{{dict.key}}` / 循环 `for item in list`），file 变量把 workspace 内文件全文读入变量值；无 RAG | `src/workflow/variable_resolution.py:137-253`（resolve_placeholders + file 变量读取）、`src/workflow/variable_resolution.py:121-134`（resolve_workspace_file_path 越界即拒）、`src/core/defaults/skills/workflow-guide/SKILL.md:145-168` | 【事实】 | v0.1.0

**5.2** | 上游产物流向下游的四条通道：Agent `output_variable` 写入变量池、`save_output_to_file` 落共享 workspace、Script stdout `<WF_VAR>key:value</WF_VAR>` 注入、`source_type: output` 节点产出变量；条件网关的变量池 = 全部 completed 节点 outputs 合并 | `src/core/defaults/skills/workflow-guide/SKILL.md:130-161`、`src/workflow/execution_flow.py:840-843`（variable_pool 合并 completed 节点 outputs）、`src/workflow/nodes/agent.py:108-153` | 【事实】 | v0.1.0

**5.3** | 写作中的变化回流构建层 = `reject_upstream` 反馈通道（下游把"上游产出不符"以拒绝原因回流，注入上游重试消息）；主仓无把写作变化**持久化**回流到设定/大纲文件的机制（无写作语义） | `src/workflow/execution_flow.py:373-477`（on_reject_upstream 回调）、`src/tools/communication_tools.py:185-226`（reject_upstream 工具） | 【事实】；"无持久化设定回流"为（推断，主仓无写作层故无从佐证） | v0.1.0

## 维度 6 · 人机分工

**6.1** | 审批节点：人工在 UI 审核**指定文件清单**（`file_paths` 逐行配置，运行时读取内容推送前端），通过/驳回（驳回原因实时填写），阻塞等待最长 24h | `src/workflow/nodes/approval.py:22-42`（file_paths/rejection_reason_placeholder 参数）、`src/workflow/nodes/approval.py:149-183`（wait 86400s + approved/rejected） | 【事实】 | v0.1.0

**6.2** | 逐节点审批开关 `main_takeover`（默认 false：Main 只跟踪、节点自动流转；显式 true 才每个 Agent 节点产出进 Main 审批）；显式 Approval 节点不受该参数影响——两种审批契约独立 | `src/workflow/tools.py:568`、`src/workflow/tools.py:782`、`src/workflow/tools.py:818`、`src/core/defaults/skills/workflow-guide/SKILL.md:61-64` | 【事实】 | v0.1.0

**6.3** | 裁决点是"候选制"：审批请求消息带完整 TaskRef + `attempt_count`，控制工具要求客户端提交当前 `expected_attempt_count` 做 CAS，过期/并发操作返回 `node_control_stale`；拒绝时提供可执行反馈（供上游重试） | `src/workflow/prompt_injector.py:103-127`（审批消息带 attempt_count）、`src/workflow/main_node_control_tools.py:71`（"过期请求会返回 node_control_stale"）、`src/core/defaults/skills/workflow-guide/SKILL.md:210` | 【事实】 | v0.1.0

**6.4** | 另有命令级人工审批（execute_command 四模式 allow_all/approve_all/blacklist/whitelist + 超时 pending 池），属编码命令安全门禁，与写作修订裁决同源但不同域 | `src/core/approval_manager.py:9-20`（四模式）、`src/core/approval_manager.py:70-84`（check_command）、`src/core/approval_manager.py:124-149`（wait_for_approval 超时） | 【事实】 | v0.1.0

---

## 六维覆盖表

| 维 | 名称 | 覆盖 | 说明 |
|---|---|---|---|
| 1 | 资产分层 | ✅（通用层）/ 未发现（写作层） | 主仓只存在 definition.json→Task 快照→workspace 三层通用资产；设定/大纲/卷纲/细纲/正文分层见研究-v3 档案 01 §4.2 |
| 2 | 修订机制 | ✅ | 回滚（reject_upstream + 审批驳回，各限 3 次）、模板版本化、Task 快照冻结、脚本漂移检测、provision stale/orphan 齐全；**未发现**影响分析/级联 stale 标记/git 版本管理 |
| 3 | 构建-执行分离 | ✅（通用层）/ 未发现（写作层） | 模板与 Task 分离、create/run 两步、四类节点；无细纲归属语义 |
| 4 | 技能/角色架构 | ✅（部分） | Core 6 个元技能 + agent_type 角色引用；写作角色全在插件仓（见档案 01 §5.1） |
| 5 | 上下文衔接 | ✅ | 变量池 + 占位符 + file 变量注入 + 上游 outputs 合并 + reject 反馈回流；无 RAG |
| 6 | 人机分工 | ✅ | Approval 节点（文件清单审核）、main_takeover 逐节点审批、attempt_count CAS、reject 候选制 |

**增量结论**：主仓与笔枢插件为上下层关系（引擎/语义），非重叠。增量集中在**修订机制与审批回滚的确定性引擎实现**——恰好补上研究-v3 档案 01 §13.2 标注存疑的"Core 引擎审批/reject 语义"部分；写作资产与角色架构无增量，标"见研究-v3 档案 01"。

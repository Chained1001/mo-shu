# DeterminFlow-Plugins 研究档案（供 mo-shu 借鉴）

| 项 | 值 |
|---|---|
| 档案版本 | v1.0（2026-08-20 首版） |
| 研究对象 | DeterminFlow-Plugins 仓库 @ commit `a252ea8`（bishu-novel v0.2.2 / public-api v0.1.31） |
| 研究路径 | `otherMaterials/referProject/DeterminFlow-Plugins`（绝对只读） |
| 研究方法 | 源码通读 + `git log`/`git show` 考古 + 资源 JSON 结构化解析；全部论断标注证据相对路径:行号 |
| 证据分档 | 【事实】= 代码/提交可复现；（推断）= 研究者推断；存疑 = 需进一步验证 |
| 路径基准 | **两种基准混用**（2026-08-20 终验补注）：带 `plugins/bishu-novel/`、`plugins/public-api/` 前缀的路径为**仓库根相对**；无前缀的 `docs/`、`evals/`、`tests/`、`resources/`、`script-library/` 路径为 **bishu-novel 插件根相对**（即实际位于 `plugins/bishu-novel/` 下，已逐个核实存在）。引用时须还原全路径。 |
| 复现入口 | 仓库根执行 `git log --oneline`（17 个提交全量可见）；`python -c "import json;..."` 解析 resources 下 JSON |

> 修订说明：首版覆盖 8 层 22 维中 21 维（1 维部分覆盖，见 §12 自评表）。

---

## 1. 项目概况

**DeterminFlow-Plugins** 是桌面端多 Agent 编排产品 DeterminFlow Core 的官方插件仓库，含两个插件（`plugin-repository.toml:1-11`）：

| 插件 | 版本 | 形态 | 一句话定位 |
|---|---|---|---|
| `bishu-novel` | 0.2.2（`plugins/bishu-novel/extension.toml:4`） | 纯资源插件（无后端代码） | 网文长链路生产的 7 条 Workflow + 33 个 Agent + 本地文件存档 |
| `public-api` | 0.1.31（`plugins/public-api/determinflow_plugin_public_api/backend/extension.py:39`） | 后端插件 | 公益模型服务的登录/凭据/目录/Provider 适配 |

**关键事实**：bishu-novel 是一个「写作类 skill 仓库的同构物」——它的本质是**用 JSON 声明的 Agent 编排 + 确定性 Python 脚本 + 纯文件存档**，与 mo-shu「脚本/模板/LLM 三层分工」高度同构，只是宿主是 DeterminFlow Core 而非 Claude Code。

**明确不做清单**（代码事实）：
- 不做数据库：`local_archive.py:6-9` 文档字符串声明 "never opens a database or creates an external identifier"；无书籍/章节 UUID（`docs/local-archive.md:5-7`）。
- 不做模型绑定：Agent Definition 不声明模型，全部继承 Core `main.model`（commit `de88598`；`docs/workflows.md:33-36`）。
- 插件代码不拼接资源前缀、不自带 Node 类型（`docs/workflows.md:6-8,24`）。
- 不收集账号密码、不保存模型 Key 副本（`plugins/public-api/README.md:12-16`）。
- 不导入 Core 内部实现，只调稳定 HTTP API（同上）。

---

## 2. 版本演进史 / 试错史【P0】

17 个提交（2026-08-02 → 08-11），两次重大自我否定式重构是本档案最值钱的部分。

### 2.1 演进时间线

| 日期 | Commit | 事件 | 性质 |
|---|---|---|---|
| 08-02 | `b7645e6` | 发布 v0.1.0：bishu-novel 为**数据库后端插件** | 起点 |
| 08-03 | `541cf96` | **推倒重来**：删除 13413 行后端，改为纯文件存档（+606 行） | 自我否定① |
| 08-04 | `de88598` | Agent 不固定模型，继承 Core 默认 | 架构修正 |
| 08-04 | `1fb7004` `5d42237` | 新增 writing-assistant Skill（Main 会话内助手+主管） | 增量 |
| 08-08 | `052f264` | **删除外部 AI 检测依赖**（humanize-chinese，-497 行脚本） | 自我否定② |
| 08-09~11 | `531f4cb`…`a252ea8` | public-api 独立成插件；随后 6 连 fix 修登录/额度状态保持 | 增量+连续修补 |

### 2.2 自我否定①：数据库后端 → 纯文件（`541cf96`，最核心教训）

被删除的东西（`git show 541cf96 --stat`）：
- 5 个 SQL migration 文件（baseline/product_schema/book_scale_params/soft_delete/runtime_schema，共约 389 行）
- `db_sync.py`（1670 行）、`json_to_db.py`（1032 行）
- `engine_auth_middleware.py`（367 行）、`engine_signing.py`（221 行）、`nonce_store.py`（107 行）、`secret_files.py`（67 行）——一整套 HMAC 签名+防重放
- `routes.py`（1325 行）、`dao.py`（524 行）、`edits.py`（553 行）、`jobs.py`（610 行）
- 10 个测试文件（含 `test_engine_auth_middleware.py` 397 行、`test_migration_runner.py` 425 行）
- 每条 workflow 目录下的散装脚本（`validate_plan.py`、`split_storyboard.sh`、`backup_chapter.py`、`sleep_2s.py` 等）

换成的：一个 394 行的 `local_archive.py` + workflow 内嵌 `local_archive` 脚本引用 + 工作区目录结构。【事实】

（推断）失败原因：数据库 + 鉴权 + 迁移 + DAO 的维护成本远超一个本地单机写作插件的价值；文件目录天然获得"复制即备份、目录名即身份、无需注册"三重收益（`docs/local-archive.md:21-26` 把这写成卖点）。

**对 mo-shu 的教训**：mo-shu 的《实施总纲》附录 C「不做 RAG/向量检索/每章全量快照/文件即真相重构」与这次推倒方向一致——本项目用 13413 行的真实代价验证了同一判断。

### 2.3 自我否定②：删除外部 AI 检测（`052f264`）

polish 流程原有一个 `script_ai_detect` 节点调用外部 `ai_detect.py`（497 行，humanize-chinese 检测），产出 `cache/ai_issues.txt` 注入自审 Agent。v0.2.x 整体删除：节点、边、隐藏变量 `ai_issues_file`、execution scheme 中的节点引用同步清理，`test_resources.py` 同步改断言。【事实，`git show 052f264`】
（推断）动因是"外部依赖不可复现/不可分发"。注意删除时的**三端同步**纪律：definition.json 节点+边+变量+scheme、SKILL.md、references/workflows.md、README、测试六处全改——这是 mo-shu「删代码必须同步删文档残留」的正面范本。

### 2.4 public-api 的连续修补（08-10~11，6 个 fix）

`b7603e3`→`a252ea8` 全在修同一类问题：登录过程中/失败后/切账号时**额度与身份状态丢失或误导**。每个 fix 均带测试（`test_service.py`/`test_plugin_contract.py` 同步扩）。【事实】
教训：有状态 UI（状态机跨异步事件保持）比登录本身难写得多；该项目用"每个状态保持 bug 一个提交一个回归测试"的方式收敛。

### 2.5 遗留历史包袱（对 mo-shu 的镜鉴）

- 多写手兼容值是源码错拼 `muti`（非 `multi`），SKILL 明确告诫"不要自行改成 multi"（`resources/skill-bundles/writing-assistant/SKILL.md:79`、`references/workflows.md:60`）。
- mvp 隐藏变量名 `wroter_context`（writer 拼错，`resources/workflows/mvp/definition.json` variables 列表）。
——**错拼一旦进入数据契约就只能文档化兼容，改不了**。mo-shu 的 current-contract/schema 命名应一次性审拼写。

---

## 3. 端到端流程

### 3.1 七条 Workflow（`docs/workflows.md:7-19`）

新书前置链：`build → character → story-plan → outline`；单章循环：`mvp → polish(可选) → post-hoc → 下一章`。所有 Workflow 用同一 `workspace_override` 目录，文件即阶段凭证。

### 3.2 mvp（章节生产，32 节点，definition.json version 2）

节点级流水线（`resources/workflows/mvp/definition.json`，节点 id 逐个核对）：

```
script_sync_down(local_archive prepare --context --require meta/...)
→ agent_we(novel-observer 世界状态) → we_post → sync_up_we(checkpoint)
→ agent_id(novel-intent-distributor 意图分发) → parse_intent
→ agent_od(novel-director 单章指导) → od_post → sync_up_od(checkpoint --merge-hooks --merge-debts)
→ agent_cm(novel-character-maintainer) → cm_post → sync_up_cm
→ agent_se(novel-settler 意图卡片) → se_post(storyboard.md)
→ agent_trimmer(novel-world-context-trimmer 上下文减法) → trimmer_post → render
→ 写手群（single 路径: agent_sw；multi 路径: agent_nw 骨架+SLOT → dw/aw/iw/dsw/tw 专项填充 → agent_si 整合）
→ si_post → sync_up_si(checkpoint) → 4 个 render 节点落盘 story/
```

**每条 Agent 输出必跟一个 *_post 脚本 + 一个 checkpoint**：LLM 只产 JSON（引擎按 `save_output_to_file` 落 `cache/`），确定性脚本负责拆分/校验/渲染 MD，`local_archive checkpoint` 负责"文件非空校验 + 索引合并"。这是全项目最核心的分层纪律。【事实】

### 3.3 post-hoc（后验，4 节点）

`prepare --require story/N/chapter.md → agent_obs(观察者提取差异) → agent_arb(裁决器) → local_archive post-hoc(回写) → render`。
裁决三分类：世界事实 adopt/pending/conflict（力量体系默认 pending，仅直接矛盾判 conflict）；故事差异 landed/missed/deviated/unplanned；计划外事件 hook/debt/discard（拿不准偏 hook）（`resources/prompts.json` novel-arbiter 的 nar_world/nar_story/nar_events 段）。
幂等回写：`_merge_index` 按 `id` 去重合并进 `archive/hooks.json`/`debts.json`，条目无 id 即报错（`local_archive.py:110-120`）。

### 3.4 polish（三段：自审→人文化→专业润色）

`self-critic(T=0.4) → polisher(T=0.4) → professional-polisher(T=0.7) → polish_post 覆盖 story/N/chapter.md`。覆盖前 SKILL 要求向用户说明风险并建议备份整个工作区（`SKILL.md:82-83`）。润色改变情节事实后须重跑 post-hoc（`docs/workflows.md:19-21`）。

### 3.5 异常与降级路径【P0】

- **读失败≠没有数据**：`_require_files` 区分 missing（FileNotFoundError，提示"缺少本地存档文件"）与 empty（ValueError，提示"本地存档文件为空"）（`local_archive.py:77-88`）——上游 Agent 落了空文件和根本没跑是两种错误。
- **缺上游→回上游，不伪造**：SKILL 规定"缺少前置时回到最近的上游流程，不通过手工伪造文件或跳过准备节点绕过检查"（`SKILL.md:52`）；evals case 3 正是测这个（`evals/evals.json:34-41`）。
- **完成判定只认文件**："只有状态为 completed 且预期长期文件存在、非空时，才向用户报告完成"；"不要用健康检查、Task 创建成功或模型回复代替最终产物验证"（`SKILL.md:104`、`SKILL.md:134`）。
- **失败分类处置**：路径错误→核对工作区；缺文件→补上游；模型输出错误→才安全重试；"不要盲目重跑整个流程，也不要跳过负责落盘和索引的 Script Node"（`SKILL.md:98`）。
- **裁决保守化**：arbiter "不确定时偏向保守：pending 比 adopt 安全，conflict 只在直接矛盾时才判"（nar_discipline 段）。
- **裁剪保守化**：trimmer "默认全保留……拿不准就保留"，输出的是**减法列表**而非白名单（nwct_principles 1-2 条）。

---

## 4. 架构层

### 4.1 分层与模块边界

| 层 | 载体 | 职责 | 证据 |
|---|---|---|---|
| 编排引擎 | DeterminFlow Core（不在本仓库） | Node 执行、变量注入、`{{file}}` 文件注入、execution scheme | `extension.toml:8-15` capabilities |
| 声明资源 | agents.json / prompts.json / workflows/*/definition.json / skills.json | Agent 参数、Prompt section、节点图、Skill 注册 | `extension.toml:20-26` |
| 确定性脚本 | script-library/nvl/*（12 个库）+ local_archive | JSON 拆分/渲染/索引/校验/落盘 | `tests/test_resources.py:19-31` |
| LLM | 33 个 Agent | 只产结构化 JSON（32/33 强制 json_object） | §5 |

插件只组合 Core 提供的 Node 类型，不自带运行时（`docs/workflows.md:24`）。资源闭包纪律：agents/prompts/脚本库**只包含 workflow 实际引用的资源**，且有测试强制（`test_resources.py:67-105`：referenced_agents == set(agents)，referenced_libraries == EXPECTED_SCRIPT_LIBRARIES）。

### 4.2 数据/状态设计【P0】：真源哲学

- **工作区目录是唯一真源**："The current workflow workspace is the single source of truth"（`local_archive.py:4-5`）。Core Task 状态与存档分离："DeterminFlow 自己仍会管理 Workflow Task 状态；笔枢不读取或保存 Core 的 Task ID"（`docs/local-archive.md:32`）。
- **目录即身份**：无 UUID，"目录名就是本地书籍身份。移动、复制或备份整个目录即可迁移、复制或备份一本书"（`docs/local-archive.md:24-26`）。
- **双区结构**：`meta/ outline/ story/ world/ archive/` 为长期存档，`cache/` 为可审计中间产物、可整体清理（`docs/local-archive.md:17-20`）。LLM 原始输出全留 `cache/`（审计），人读 MD 全落长期区（render 节点）。
- **schema 版本**：无 DB migration 后，版本锚点转为 workflow `definition.json` 的 `"version": 2`（有测试断言全部为 2，`test_resources.py:83`）+ extension.toml `api_version = "1"`。文件 schema 本身无版本字段——（推断）靠"存档即中间产物可重渲染"回避迁移问题；对长篇连载这是弱点（存疑：老书存档升级路径未见处理）。
- **幂等**：hooks/debts 按 id 合并去重（`local_archive.py:110-120`）；卷纲"目标卷号 ≤ 最大已有卷号 → 重写该卷"（outline definition.json agent_vo first_message）；近纲按 `is_new_volume` 决定覆盖或追加（`no_post.py:1-7`）。
- **安全边界**：脚本只允许工作区内相对路径，拒绝绝对路径与 `..` 穿越（`local_archive.py:30-40`，resolve 后再 `is_relative_to` 复检）。

### 4.3 检索/知识层（上下文供给）

无 RAG。上下文构造 = 确定性拼接（`prepare --context` 把 6 维世界观合成 `cache/sync/world.json`、角色四件套按 name 合成 `cache/sync/characters.json`、近纲摘录合成 MD，`local_archive.py:122-197`）+ LLM 减法裁剪（trimmer 输出减法列表，`trimmer_post.py` 执行，粒度锁死"世界=二级子字段、角色=整进整出"）。写手收到的 `wroter_context` 是一个 textarea 变量，按标题分节拼好风格指南/角色声音/长线状态/本章大纲/世界状态/裁剪后世界观/次要角色表（mvp definition.json `wroter_context` default）。

---

## 5. 智能体层

### 5.1 职责切分（33 Agent，`resources/agents.json` 全量核对）

| 族 | Agent（例） | 温度 | 特点 |
|---|---|---|---|
| 规划 | volume-outliner / director / outliner | 0.9 | 高发散 |
| 世界观 | 6 个 worldbuilder-* | 0.7 | 六维并行 |
| 状态/裁决 | observer(0.3) / arbiter(0.3) / character-maintainer(0.3) | 低 | 事实类低温 |
| 意图 | intent-distributor(0.3, max_turns=20) | 低 | 纯归类不创作 |
| 裁剪 | world-context-trimmer(0.3, max_turns=15) | 低 | 最小 Agent |
| 写手群 | single-writer(max_turns=1!) / dialogue/action/internal/description/transition-writer(0.8) | 高 | single 一次成稿 |
| 润色 | self-critic(0.4) / polisher(0.4) / professional-polisher(0.7) | 分段 | 逐级升温 |

**温度按任务类型三档化**（0.3 事实/0.7-0.9 创作/0.4 批评）+ **max_turns 按职责收紧**（trimmer 15、意图分发 20、single-writer 1）是可直接抄的参数纪律。所有 Agent `tools: null`（无工具）、thinking_enabled=true、reasoning_effort=high 全线统一（agents.json 各条目）。

### 5.2 Prompt 工程【P0】

prompts.json 结构：每 Agent = `{description, sections[], preambles{}, template_variables}`；每个 section = `{name, content, token_estimate, cache_break, cache_break_reason, enabled, workflow_only, order}`（`resources/prompts.json` novel-single-writer 条目实测）。即**section 可单独开关/排序/缓存控制**，由引擎按 order 组装。

- **共享 section 复用**（实测计数）：`session_meta`（`{{session_meta}}` 注入占位）复用 25 次、`no_em_dash`（"禁止使用破折号"一行）18 次、`file_structure` 10 次、`nw_importent` 5 次——mo-shu 的共享 base 段等价物。
- **P 协议编号化**：single-writer 核心 = P1 信息密度/P2 感官优先/P3 角色差异化/P4 节奏段落/P5 衔接 + 替换策略 R1-R8（sw_core/sw_replace 段）。每条都给出可执行判据（如"每 250-400 字至少一句读者能说清新知道了什么"、"独段比例 ≤5%"）。
- **输出纯度铁律**：所有产出段写"直接输出一个纯 JSON 对象，不要 Markdown 围栏，不要解释文字。引擎自动保存"（nar_output 等）；arbiter 另有 🔴 JSON 完整性铁律（ASCII 直引号/禁未转义换行/禁尾随逗号）——这是被坑过之后补的（存疑：具体事故无提交记录，但措辞强度说明踩过）。
- **自检清单内嵌**：arbiter "产出前自检：四个区都有吗（空数组也要写）？landed 条目是 dict 不是字符串吗？"（nar_discipline）。
- **首消息（first_message）模板**：节点级用户消息带变量注入，用 `==== 标题 ====` 大分节把 4-5 份文件内容隔开（outline agent_vo first_message）；输出要求（"直接输出纯 JSON，引擎自动保存"）重复出现在每个 agent 节点首消息首部——双保险。

### 5.3 多 Agent 编排

- 写手群两种模式由变量路由（single 走 agent_sw；muti 走 nw 骨架+SLOT → 5 专项写手 → si 整合，输出同落 `cache/si/chapter.json`，mvp definition.json）。多写手成本更高，SKILL 要求提醒用户（`SKILL.md:80-81`）。
- 意图分发器把 `human_intent` 拆成 od_intent/se_intent 两路（nid_rules 的四行决策表），"节奏/张力"类两路都发。
- post-hoc 的 observer/arbiter 两级：提取与裁决分离，裁决者不重读正文只读差异（nar_role："正文好坏与你无关，你只裁决 Observer 提取的差异"）。

---

## 6. 技能层（Skill 设计）

writing-assistant Skill（`resources/skill-bundles/writing-assistant/SKILL.md`，134 行）：
- **双身份设计**：Main 同时是"写作助手"（对人的创作顾问）和"写作工作流主管"（对流程的执行监督者）（SKILL.md §服务身份）。
- **薄哲学**：SKILL 本体只放流程与协作规则，静态细节下沉 `references/workflows.md`（94 行）与 `references/workspace.md`（85 行），且反复强调"实际定义高于本 Skill 的静态摘要"——先 `list_workflows`/`get_workflow` 读真实定义再行动，禁止凭记忆拼 ID（SKILL.md:49-55）。这是"文档只是入口、运行时为准"的示范。
- **防呆细节**：章节号四位化（0001/0000）写进两处；`muti` 错拼告诫；`named_shared` 跨会话不能重连旧目录的陷阱明示（SKILL.md:63-68）。
- **人机分工**："不要越过用户替他做关键创作决定"；"用户已经明确授权执行时，不重复索要形式确认"（SKILL.md:24-27）——一次授权不反复确认。
- 注册即用：skills.json 设 `auto_inject: true`、group `default`、priority 70（`resources/skills.json`），用户可在 Skill 页关掉。

---

## 7. 工程层

### 7.1 确定性纪律（三层分工）

脚本只做四类事：校验（require/空文件）、转换（JSON→拆分→MD 渲染）、索引合并（幂等 merge）、上下文合成。凡是"判断"（该裁什么、裁决什么）交低温 LLM，凡是"执行"（裁掉、合并、落盘）交脚本。trimmer 是范本：LLM 只出减法清单，`trimmer_post.py` 才动数据。

### 7.2 防呆与自愈

- 章节号 `_normalize_chapter` 强制 1-6 位数字→四位补零（`local_archive.py:90-93`）。
- render 的 `--inputs`/`--outputs` 数量必须一致（`local_archive.py:280-282`）；hooks/debts 条目缺 id 直接报错（`local_archive.py:117-118`）。
- 路径穿越双重防护（§4.2）。
- workflow definition 内大量 `hidden: true` 变量：文件路径默认值对用户隐藏，只有 `chapter_number`/`human_intent`/`world_intent`/`target_word_count`/`language` 等创作参数暴露（mvp definition.json variables）。

### 7.3 质量保障与测试文化【P0】

| 测试文件 | 测什么 | 性质 |
|---|---|---|
| `test_resources.py` | 资源闭包：workflow 引用的 agent/脚本库 == 声明集合；33 个 agent 与 prompts 一一对应；manifest 无 backend/settings；SKILL 覆盖公开契约（关键 API 名必须在文中出现） | 测协议不测实现 |
| `test_plugin_portability.py` | 插件可移植性 | 同上 |
| `test_od_post.py` | 脚本黑盒：给 JSON 输入，断言输出目录**恰好只有**三个产物文件（sorted 列表相等） | 子进程隔离跑真脚本 |

特点：
- **清单类断言集中在一处**（EXPECTED_WORKFLOWS/EXPECTED_SCRIPT_LIBRARIES 常量），改资源只改一个文件。
- **"恰好只有"式断言**（`test_od_post.py:48-52`）防止脚本偷偷多写文件。
- 删功能必删测试：`541cf96` 删 10 个后端测试、`052f264` 同步改 `test_resources.py` 断言——测试随实现同生共死，无僵尸测试。
- **evals.json**：3 个场景级评测（建书/续写/前置缺失），expectations 是行为断言（"不重跑 build"、"0012/0011"、"human_intent 不误放 world_intent"），且 `test_resources.py:64-67` 断言 evals 存在且非空——评测本身也有回归。
- 测试运行方式写进 CONTRIBUTING（含 Core 校验器 `validate_definition.py` 命令，`CONTRIBUTING.md:10-17`），需 PYTHONPATH 指向 Core（存疑：本仓库内不可独立复现，未实测）。

### 7.4 性能成本

- 上下文减法（trimmer）显式控制写手输入规模（§4.3）。
- section 带 `token_estimate` + `cache_break` 字段：Prompt 组装层预留了缓存友好性（engine 侧消费；本仓库只声明）。
- single-writer `max_turns=1`：一次成稿控制轮次成本。
- SKILL 明示多写手"成本和整合复杂度更高"（SKILL.md:81）。

### 7.5 安全权限

- bishu-novel：无网络、无 DB、无凭据；脚本路径禁穿越（§4.2）；CONTRIBUTING 禁提交真实小说数据与绝对路径（`CONTRIBUTING.md:8`）。
- public-api：平台门禁（仅 `DETERMINFLOW_DESKTOP=1` + win32，`extension.py:20-33`）；开发开关仅绕过门禁并放行 loopback HTTP（`extension.py:69`）；浏览器 OAuth 式登录不碰密码（`browser_auth.py`）；状态文件不重复保存模型 Key（README §开源边界）。

### 7.6 部署分发

plugin-repository.toml 声明式目录（id+subdirectory）；extension.toml 声明资源路径与 namespace prefix；安装后 prefix 可被覆盖，因此 SKILL/文档不硬拼 `bishu-novel-*` 全 ID（`docs/workflows.md:38-42`）。

---

## 8. 治理层【P0】

- 治理文档极薄：根 README 1123 字节、CONTRIBUTING 887、SECURITY 613——治理重心不在文档而在**测试断言**（test_resources.py 即宪法）。（推断）与 v0.1.0 的重后端时代相比是刻意瘦身。
- CONTRIBUTING 四条硬规则：新 Workflow 必须有明确输入/输出/失败策略/不依赖真实凭据的测试；改资源必跑 Core 校验器+插件测试；Conventional Commits；AGPL-3.0-only（`CONTRIBUTING.md:6-20`）。
- 无 AGENTS.md/CLAUDE.md 类 AI 协作宪法（与 mo-shu 差异点，见 §10）。
- 文档-代码一致性靠测试强制（SKILL 必含 `list_workflows` 等契约词、workflows.md 必含全部 7 个 workflow 名，`test_resources.py:51-66`）——"文档即契约，测试守护文档"。

---

## 9. 交互层

- **作者确认点**：关键创作决定（题材/情节走向）留给用户；覆盖长期文件前说明风险、无副本时建议备份工作区（SKILL.md:82-83）；审批只批"真实审批请求"且用最新 attempt_count（SKILL.md:95-96）。
- **一次授权原则**：明确授权后直接执行，不重复索要形式确认（SKILL.md:27）。
- **汇报协议**：固定五列表格（当前书籍/当前阶段/本轮动作/运行证据/下一步），且"当前阶段"必须由非空文件证明、只推荐一条下一步（SKILL.md §对用户的汇报方式）。
- **失败汇报**：直接说明停在哪、保留了什么、用户需要决定什么（SKILL.md:130-132）。
- 内容资产形态：JSON（机器真源，cache/ 与 world/）+ MD（人读渲染，meta/ story/）双轨；body.json 特例直取 `body` 字段渲染正文（`local_archive.py:268-270`）。

---

## 10. 可借鉴清单

成本分级：低=直接抄思路/文案；中=需设计适配；高=涉及架构决策。

| # | 借鉴点 | 成本 | 源码位置 | mo-shu 落点建议 |
|---|---|---|---|---|
| 1 | 完成判定只认非空落盘文件，"Task 启动≠完成" | 低 | SKILL.md:104,134 | 写作 skill 的 9 序状态机文案补"非空文件"措辞 |
| 2 | 读失败三分类：缺文件/空文件/内容坏，各自不同处置路径 | 低 | local_archive.py:77-88; SKILL.md:98 | 判定脚本的错误分类与提示语 |
| 3 | 温度三档纪律（0.3 事实/0.7-0.9 创作/0.4 批评）+ max_turns 按职责收紧 | 低 | resources/agents.json 各条目 | agent 模板的 model_params 规范 |
| 4 | JSON 完整性铁律文案（ASCII 引号/转义换行/禁尾随逗号）+ 输出前自检清单 | 低 | prompts.json nar_output/nar_discipline | 所有"产 JSON"环节的 base 段 |
| 5 | 共享 section（no_em_dash 一行式禁令复用 18 次、session_meta 占位 25 次） | 低 | prompts.json sections 计数实测 | mo-shu shared base 段的粒度参考：小而高频 |
| 6 | P1-P5 协议 + R1-R8 替换策略的编号化写作铁律（每条带可数判据） | 低 | prompts.json sw_core/sw_replace 段 | 写手 agent prompt 直接对照移植 |
| 7 | 裁决三分类保守化（pending>adopt；拿不准偏 hook） | 低 | prompts.json nar_world/nar_events | 后验/一致性裁决 agent 的默认偏向 |
| 8 | LLM 出减法清单、脚本执行裁剪（候选类机检永不拦截的等价物） | 中 | mvp trimmer 节点 + trimmer_post.py | 上下文瘦身层：LLM 提名、确定性执行 |
| 9 | 意图分发决策表（情节→OD/写法→SE/节奏两路） | 中 | prompts.json nid_rules 段 | 用户指令→各 agent 的路由表 |
| 10 | 幂等索引合并（按 id 去重 merge，无 id 报错） | 低 | local_archive.py:110-120 | hooks/债务类清单的回写脚本 |
| 11 | "恰好只有"式测试断言 + 资源闭包断言（引用集==声明集） | 中 | test_od_post.py:48-52; test_resources.py:67-105 | behavior-contracts 增加资源闭包检查 |
| 12 | evals 行为断言 + 测试守护 evals 存在 | 中 | evals/evals.json; test_resources.py:64-67 | mo-shu 增加场景级 eval（低成本起步 3 条） |
| 13 | 双轨资产：JSON 真源 + MD 渲染，render 节点统一转换 | 中 | local_archive _render_* | 已类似；补"正文类直取 body"特例简化 |
| 14 | hidden 变量隐藏文件路径、只暴露创作参数 | 中 | mvp definition.json variables | 参数面设计：作者只见创作项 |
| 15 | SKILL 薄壳+references 下沉+运行时为准（禁凭记忆拼 ID） | 低 | SKILL.md:49-55 | skill 文档结构通则 |
| 16 | 汇报五列表格 + 只推荐一条下一步 | 低 | SKILL.md §汇报方式 | 交互协议模板 |
| 17 | 覆盖前风险告知+备份建议；润色改事实须重跑后验 | 低 | SKILL.md:82-83; workflows.md:19-21 | 覆盖类操作的确认点设计 |
| 18 | 删功能六处同步（定义/边/变量/scheme/文档/测试） | 低 | git show 052f264 | 删除类改动的 checklist |
| 19 | 章节号四位化 + 归一化函数 | 低 | local_archive.py:90-93 | 章节目录命名规范 |
| 20 | 有状态 UI 的"状态保持"专项回归（public-api 6 连 fix 模式） | 中 | git log 08-10~11 | 每修一个状态 bug 沉淀一个测试 |
| 21 | 文件即身份：目录名=书，复制=备份，无 UUID | 高 | docs/local-archive.md:24-26 | 与 mo-shu 现有取向一致，强化其论据 |
| 22 | 长期区/cache 区分离（LLM 原始输出可审计可清理） | 中 | docs/local-archive.md:17-20 | 工作区目录规范 |

低 12 条 / 中 8 条 / 高 1 条。

---

## 11. 不可借鉴清单

| # | 项 | 理由 |
|---|---|---|
| 1 | DeterminFlow 的节点图引擎依赖 | mo-shu 宿主是 Claude Code skills，无 Node/变量注入/execution scheme 运行时；借鉴的应是编排思想而非格式 |
| 2 | `response_format: json_object` 强约束 | 依赖宿主 API 参数；Claude Code 场景只能靠 prompt 铁律近似（§5.2 的文案部分才可借） |
| 3 | Agent 不固定模型、全继承 main.model | 适合产品化统一切换；mo-shu 按角色差异化选型的需求相反（de88598 的动机不适用于 skill 仓库） |
| 4 | api_version="1" 式插件 ABI / prefix 覆盖机制 | 宿主特有概念 |
| 5 | public-api 整体（登录/凭据/Provider 注册/平台门禁） | 与写作 skill 无关；仅测试文化可借 |
| 6 | 无 schema 版本字段的文件真源 | 长篇连载下老存档升级无路径（存疑但风险真实）；mo-shu 已有 migrate+备份机制，优于该项目 |
| 7 | 极薄治理文档（无 AI 协作宪法） | 该项目由单一团队+测试守护；mo-shu 是 flash 施工+人审协作，需要 AGENTS.md 级约束 |
| 8 | 多写手群（SLOT 骨架+5 专项+整合） | 成本高、项目自己也把 single 设为默认并告诫成本（SKILL.md:80-81）；（推断）multi 路径实际使用率低 |

---

## 12. 差异定位（vs mo-shu）

| 维度 | DeterminFlow-Plugins | mo-shu |
|---|---|---|
| 宿主 | 自家产品 Core（可控运行时） | Claude Code skills（prompt 即接口） |
| 真源 | 工作区文件（无版本字段） | 文件 + current-contract + schema migrate |
| 编排 | 引擎执行 JSON 节点图 | skill 文档 + 确定性脚本引导 |
| LLM 约束 | API 级 json_object + prompt 铁律双保险 | 仅 prompt 层 → 更需 §5.2 文案 |
| 治理 | 测试即宪法，文档极薄 | AGENTS.md + 规格 + 多重 check 脚本 |
| 演进 | 允许推倒重来（AGPL 单团队） | 分批规格 + 一批一提交 |
| 共同点 | 脚本/模板/LLM 三层分工、文件非空为完成凭证、删改同步文档测试、反对 DB/RAG 重后端 | 同 |

---

## 13. 待验证问题

1. Core 引擎如何消费 `cache_break`/`token_estimate`/`execution_schemes`？（引擎不在本仓库，存疑）
2. mvp 的 `enable_complete_node_task`、`auto_flow`、`enable_reject_upstream`/`max_reject_count: 3` 的实际审批语义？（推断：auto_flow=true 的节点自动流转，false 的需确认；需读 Core 源码验证）
3. 老书存档跨 definition version（v1→v2）的迁移路径是否存在？（未见证据，存疑）
4. 33 Agent 中 `novel-storyboard-integrator` 与写手群的实际质量差（需真跑，本环境不可复现）。
5. evals.json 的 3 条是否有自动化跑法（未见 runner，推断为人工/CI 外部评估，文档宣称）。

---

## 14. 错误清单（项目犯过的错→修法→对 mo-shu 的教训）

| # | 错误 | 修法（证据） | mo-shu 教训 |
|---|---|---|---|
| 1 | v0.1.0 给本地写作插件上数据库+HMAC+nonce+DAO+migration（13413 行） | `541cf96` 整体删除换 394 行文件脚本 | 附录 C 的"不做清单"每一条都有真实代价背书；重后端诱惑要顶住 |
| 2 | 外部 AI 检测依赖不可分发 | `052f264` 删节点+脚本，六处同步清理 | 外部不可复现依赖不进主链路；删除时按 checklist 同步六处 |
| 3 | Agent 固定模型导致切换困难 | `de88598` 改为继承 Core 默认 | 模型绑定策略要一开始想清楚（mo-shu 方向相反但同理：绑定要显式） |
| 4 | 数据契约错拼 `muti`/`wroter_context` 无法修正 | 文档化兼容+告诫用户别改（SKILL.md:79） | 契约命名进冻结前先审拼写；错误拼进入接口就是永久债 |
| 5 | 登录/切号/失败时额度状态丢失（public-api 6 连 fix） | 每个状态保持 bug 一个提交+回归测试 | 异步状态机的"中间态保持"要专项测试，不是一次性实现 |
| 6 | LLM 输出脏 JSON（破折号、围栏、尾随逗号——由铁律措辞反推，存疑具体事故） | nar_output 加 🔴 JSON 完整性铁律 + 输出前自检 | 输出纯度约束按"踩过的坑"逐条固化成 base 段 |
| 7 | Task 启动被误报为完成 | SKILL.md 多处强调"completed+非空文件才算完成"、evals case1 断言 | 状态判定只吃文件系统证据，与 mo-shu 9 序状态机同理 |

---

## 15. 22 维覆盖自评表

| # | 维度 | 覆盖 | 章节 |
|---|---|---|---|
| 1-1 | 定位与边界（含不做清单） | ✅ | §1 |
| 1-2 | 版本演进史/试错史【P0】 | ✅ | §2 |
| 2-1 | 端到端流程 | ✅ | §3 |
| 2-2 | 内部状态机/事务 | ✅ | §3.2-3.3（节点流+幂等合并；Core 级状态机存疑标注 §13.2） |
| 2-3 | 异常与降级路径【P0】 | ✅ | §3.5 |
| 3-1 | 分层与模块边界 | ✅ | §4.1 |
| 3-2 | 数据/状态设计【P0】 | ✅ | §4.2 |
| 3-3 | 检索/知识层 | ✅ | §4.3 |
| 4-1 | 职责切分 | ✅ | §5.1 |
| 4-2 | agent 设置 | ✅ | §5.1 |
| 4-3 | Prompt 工程【P0】 | ✅ | §5.2 |
| 4-4 | 多 Agent 编排 | ✅ | §5.3 |
| 5-1 | Skill 设计（薄厚/铁律/入口/路由） | ✅ | §6 |
| 6-1 | 确定性纪律 | ✅ | §7.1 |
| 6-2 | 防呆与自愈 | ✅ | §7.2 |
| 6-3 | 质量保障与测试【P0】 | ✅ | §7.3 |
| 6-4 | 性能成本 | ✅ | §7.4 |
| 6-5 | 安全权限 | ✅ | §7.5 |
| 6-6 | 部署分发 | ✅ | §7.6 |
| 7-1 | 文档/治理宪法【P0】 | ✅ | §8 |
| 7-2 | 开发流程闭环 | ✅ | §8（CONTRIBUTING 流程+测试门槛） |
| 8-1 | 用户体验/人机分工+内容资产 | ⬜部分 | §9 覆盖交互与资产；"介入模式"仅审批点一处，深度有限（材料所限） |

覆盖：21/22 全覆盖 + 1 部分覆盖。

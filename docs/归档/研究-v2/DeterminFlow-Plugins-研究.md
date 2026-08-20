# DeterminFlow-Plugins 研究档案（v2，源码级）

> **研究对象路径**：`C:\Users\1\Desktop\skillDev\mo-shu\otherMaterials\referProject\DeterminFlow-Plugins`
> **研究日期**：2026-08-19（源码级，本轮只读，未跑构建/未装依赖）
> **实际读过的关键文件**（约 45 个）：根 `README.md`/`plugin-repository.toml`/`CONTRIBUTING.md`/`SECURITY.md`/`.github/workflows/ci.yml`；`plugins/bishu-novel/` 下 `extension.toml`、`README.md`、`docs/*.md`、`resources/agents.json`、`resources/prompts.json`（2180 行全量）、`resources/skills.json`、`skill-bundles/writing-assistant/{SKILL.md,references/*.md}`、`evals/evals.json`、7 个 `workflows/*/definition.json`、`workflows/{build,character}/script/*.py`、`script-library/nvl/**/*.py`（12 个）、`tests/*.py`；`plugins/public-api/` 下 `extension.toml`、`pyproject.toml`、`backend/*.py`、`tests/*.py`。
> **纪律**：论断标注源码相对路径（相对仓库根）+行号；区分"代码事实"/"（推断）"/"存疑"；以代码为准，README 只作入口。

---

## 1. 项目概况

**是什么**：`DeterminFlow` 官方插件仓库，含两个插件：`bishu-novel`（"笔枢"本地小说生产，纯资源型）、`public-api`（公益模型登录/Provider 接入，含 Python 后端）。

**形态与规模**（代码事实）：
- `bishu-novel` 是**纯资源型插件**：`extension.toml` 无 `backend`/`installation`/`settings`/`lifecycle` 段（`plugins/bishu-novel/extension.toml:1-26`；`tests/test_resources.py:38-57` 显式断言），只声明 agents/prompts/skills/skill_bundles/workflows/script_libraries。
- 规模：**7 条 workflow**（`tests/test_resources.py:8-16`）、**33 个 Agent**（`tests/test_resources.py:120` `assert len(agents)==33`，且 `set(prompts)==set(agents)`）、**12 个脚本库脚本**（`tests/test_resources.py:17-30`）+ 2 个内联脚本（`workflows/build/script/render_worldview.py`、`workflows/character/script/extract_names.py`）。prompts.json 330KB/2180 行。
- `public-api` 是**运行时插件**：`extension.toml:7` 声明 `backend=...create_extension`，capabilities `["api.routes","model.providers"]`（:9），依赖仅 `httpx`（`requirements.txt:1`）。

**技术栈**：声明式 JSON workflow DAG + Python 脚本节点（确定性转换）+ FastAPI/Pydantic/httpx（public-api）。prompt 是 section 组合式 JSON。

**维护状态**：bishu-novel `0.2.2`、public-api `0.1.31`，api_version `1`；CI 拉取主仓库跑 workflow 校验器 + pytest（`ci.yml:25-33`）。AGPL-3.0-only。README 明示"Plugin 与 Core 同机运行，拥有主进程可用的系统权限"（`README.md:24`）——受信任同进程代码，非沙箱隔离。

---

## 2. 流程

### 2.1 端到端生产链（7 条 workflow，`docs/workflows.md:16-18`）

```
build（六维世界观串行）→ character（骨架→信念→逐角色循环→声线）→ story-plan（故事引擎+风格档案）
→ outline（卷纲+近纲）→ 每章: mvp → 可选 polish → post-hoc → 下一章 mvp
```

落盘（各 `definition.json` 的 `output_file_path`）：`build`→`world/*.json`+`meta/world_foundation.md`；`character`→`meta/{character_profiles,character_voice}.md`；`story-plan`→`meta/{story_plan,style_profile}.md`；`outline`→`outline/{volume_outline,near_term_outline}.md`；`mvp`→`story/{4位章号}/` 下 `chapter.md`+`world_state.md`+`world_events.md`+`single_chapter_guide.md`+`character_state_long.md`+`character_minor.md`+`storyboard.md`+trimmed 文件；`post-hoc`→`story/{章}/diff_{world_resolved,story_confirmed,character}.{json,md}`+更新 `archive/{hooks,debts}.json`+`meta/{hooks,debts}.md`；`polish`→覆盖 `chapter.md`，保留 `cache/sc/critique.json`。

### 2.2 mvp 内部状态机（核心，1694 行 DAG）

串行主链 + 一个写手分支 + 一处并行扇出（`mvp/definition.json`）：

1. `script_sync_down` `prepare --context --require 7 前置文件`（:21-22）——门禁 + 构建 `cache/sync/{world,characters,near_term_we}`。
2. 世界状态机 `agent_we`（novel-observer）→ `we_post` → `render_we` → `sync_up_we`。**不读正文**，只由"近纲时间推进 + 上章世界状态/事件/后验裁决"驱动（`prompts.json:300`）。
3. 意图分发 `agent_id` 把 `human_intent` 拆 `od_intent`/`se_intent`（`parse_intent.py` 回写 `<WF_VAR>`）；`world_intent` 独立直入世界状态机。
4. 大纲导演 `agent_od` → `od_post` → `sync_up_od`（`--merge-hooks/--merge-debts`）。
5. 角色维护 `agent_cm` → `cm_post` → `sync_up_cm`；6. 意图导演 `agent_se` → `se_post`（storyboard.md）。
7. 上下文裁剪 `agent_trimmer` → `trimmer_post`（确定性裁剪）→ 渲染 trimmed 文件。
8. 写手分支（条件网关 `gw-mqdqscyd-0`，:1057-1076）：`writer_type=="muti"` 走多写手群（骨架写手→并行 fork 5 专项写手→converge→整合写手）；否则单写手 `agent_sw`。两路落 `cache/si/chapter.json`。
9. `si_post` → `render_si`（`cache/si/body.json`→`chapter.md`）→ `sync_up_si`。

**多写手兼容值是源码拼写 `muti`**（非 `multi`），SKILL 要求不改（`SKILL.md:79-80`）——为兼容历史数据保留的 typo（代码事实）。

### 2.3 post-hoc 后验闭环（观察/裁决分离）

`post-hoc/definition.json`：`sync_down`（require chapter.md）→ 观察员 `agent_obs`（只对照不裁决）→ 裁决器 `agent_arb`（只裁决不评质量）→ `local_archive post-hoc --chapter N` → `render`。

观察员四类差异（`prompts.json:1990`）：`world_diff`（新地点/势力/规则变更/超规格物品/矛盾，每条带正文段落证据）、`story_diff`（landed/missed/deviated/unplanned）、`character_diff`（新角色/关系/状态/物品/生命周期异常）。裁决器三裁决（`prompts.json:2015-2043`）：①世界事实 adopt/pending/conflict（低风险自动 adopt、涉力量体系默认 pending、仅直接矛盾才 conflict）；②故事差异四区；③未提事件归类 hook/debt/discard（拿不准偏 hook）。

---

## 3. 架构

### 3.1 数据层：无数据库、无 UUID，目录即身份

书籍身份 = `workspace_override` 目录名（`docs/local-archive.md`）。结构（`references/workspace.md:22-62`）：`archive/`（hooks.json+debts.json 唯一权威索引）、`cache/`（可审计中间产物）、`meta/`（可读 MD）、`outline/`、`story/{0001}/`（每章快照）、`world/`（6 维原始 JSON）。**双写一致性**：`archive/*.json` 权威、`meta/*.md` 可读渲染，警告"不要只改一边制造不一致"（:71）。

### 3.2 数据契约与脚本协议

- **Agent 产出契约**：统一"直接输出纯 JSON，引擎自动保存"（`save_output_to_file` + `output_file_path`），prompt 禁 markdown 围栏。
- **脚本→变量回写**：`<WF_VAR>key:value</WF_VAR>`（`extract_names.py:97` 产 `character_names` 供循环；`parse_intent.py:22-23` 产 od/se_intent）+ `<script_out>` 日志。
- **路径安全**：`local_archive.py:32-40` `_workspace_path` 拒绝绝对路径与 `..` 穿越（SECURITY.md:6-7 承诺的落地）。
- **章节号规范化**：`local_archive.py:82-85` 强制 1-6 位数字→4 位补零。
- **索引幂等合并**：`local_archive.py:95-120` `_merge_index` 按 id 去重、后者覆盖、保持首现顺序。

### 3.3 Agent 体系（33 个 = 拆碎的单一职责）

`agents.json` 每条 description 是"职责+产出文件"。按职能：建书前置 15（6 worldbuilder + 4 character + story-planner + style-profiler + volume-outliner + outliner）；单章生产 14（novel-observer【世界状态机，注意与 chapter-observer 不同名】+ intent-distributor + director + character-maintainer + settler + world-context-trimmer + writer 群 + single-writer）；润色 3（self-critic + polisher + professional-polisher）；后验 2（chapter-observer + arbiter）。

**模型参数按职能**（`agents.json` model_params）：规划/创意 temp 0.8-0.9、维护/观察/裁决 0.3、自审 0.4+top_p 0.7、整合写手 `thinking_budget:4000`（:160）、分发器/裁剪器 `thinking_enabled:false`（:662,:706）。**不声明 model**，继承 Core `main.model`（`tests/test_resources.py:195-204` 断言无 model/model_override）。

### 3.4 public-api 架构（Provider 接入）

- **运行时门禁**：`extension.py:23-31` 仅 `DETERMINFLOW_DESKTOP=1` 且 win32 启用；非 Windows 仅 `DETERMINFLOW_PUBLIC_API_DEVELOPMENT=1` 且只放行 loopback HTTP。
- **登录**：PKCE（S256）外部浏览器 + 127.0.0.1 短时回环回调（`browser_auth.py:19-153`），本地不存账号密码；**api_key 不落盘**——`service.py:447` `parsed.pop("api_key")`。
- **凭据生命周期**：`service.py` 单服务全权管理，`state.json` 原子写（`os.replace`+`0o600`，:105-121）、15 分钟续签调度（:31）、续签提前量匿名 6h/登录 1d（:33-34）。
- **Provider 接入（关键）**：`provider.py:32-116` 用 `httpx.ASGITransport(app=app)` 进程内 HTTP 调 Core 稳定 API（`/api/model-providers` GET/POST/PUT/DELETE + `/priority`），**不 import Core model_manager 内部实现**（`tests/test_plugin_contract.py:52-58` 断言）。注册形态：`provider_type="openai_compatible"`、`maxContextTokens:128000`、`managed_by`、本地化 `error_messages`（:84-95）。
- **模型目录**：`catalog.py` 动态拉取 + 严格归一化（provider_type 白名单、价格逐项校验、unit 必须 `per_million_tokens`、按凭据 allowed 过滤，:75-218）。

---

## 4. 思想

1. **引擎+脚本承担流程控制与落盘，LLM 只留在有判断价值的节点**（核心哲学）。确定性转换全下沉 12 个脚本，可独立单测（`tests/test_od_post.py` 用 subprocess 跑真脚本）。
2. **判断按"对照 vs 裁决"拆两个 agent**：observer"你就是一台对照机器"（`prompts.json:1940`）与 arbiter"敢拍板"（:2006）职责分离——观察员"宁可多记不要漏"，裁决器"保守默认 pending 比 adopt 安全"。
3. **"只定义力，不定义落地"的力学分层**：story-planner"只定义力的性质规律，不定义力在哪章落地"（`prompts.json:1639`）；卷纲"画边界不画路线"；导演"回答发生了什么为什么，不回答怎么写"（:10）；意图导演"永远给意图，永远不给清单"（:366）。
4. **"去 AI 味"是贯穿写手→自审→润色的显式工程目标，且"同一套规则双向复用"**：15 条中文硬性禁令在写手侧是遵守清单、在自审侧翻成 15 个枚举标签（`prompts.json:1749` 标签表 ↔ `:1839` 15 条规则块）。渲染脚本兜底 `replace("——","，")`（`json_to_md.py:366`、`vo_post.py:20`）。
5. **（推断）连续性第一性**：每章快照 + `{{prev_chapter}}` 模板注入上一章产物（`mvp/definition.json:1090-1231` prev_* 变量族），使"下一章"永远建立在"已裁决的上一章状态"上——这是"post-hoc 必须在下一章前完成"的架构级原因。

---

## 5. 方法论（确定性纪律 / 防呆 / 提示词工程）

### 5.1 确定性纪律（脚本门禁 = 防呆）

- **前置门禁**：`prepare --require` 缺失或**空文件**抛错（`local_archive.py:67-79` `_require_files` 查 `st_size==0`）；mvp 一次 require 7 个前置文件。
- **阶段校验**：每个 agent 后接 `checkpoint --files`；build 里 6 维各是"agent→persist checkpoint"串行单元。
- **LLM JSON 容错修复**：`extract_names.py:17-56` 去围栏/智能引号转 ASCII/去尾逗号/**丢弃孤立文本行**并回写修复后 JSON（:59-75），让"角色管线不因一个坏 JSON 全盘失败"。
- **空输出兜底**：`json_to_md.py:327-356` voice.json 无 characters 时用 skeleton 生成"待补充"最小声音锚，不阻断管线。

### 5.2 提示词工程

- **section 式组装**：每 agent 由 `sections[]` 组成，每段带 `name/content/token_estimate/cache_break/enabled/workflow_only/order`——支持 token 预算、按段启停/缓存。
- **共享段复用**：`nw_importent`（原文拼写）被多写手复用（:255,746,822,898,974,1050,1166）；15 条禁令块被 self-critic/polisher 复用（`custom_1781186638389` 与 `custom_1780919570646` 逐字相同）。
- **"先自检后提交"清单**：director 有 `od_modes` 段 10+ 条自检；自审有"检测顺序"（中文硬性禁令>通用 AI>人文化缺失）。
- **JSON 完整性铁律**：产出 section 末尾统一附"🔴 JSON 完整性铁律"（ASCII 直引号/不转义换行/无尾逗号/无围栏）——把"坏 JSON 阻断下游"前移为 prompt 约束。
- **参数化占位**：`{{变量}}` 贯穿 first_message 与 file 变量默认值；Agent 不硬编码路径，全部"首条消息注入"。

### 5.3 防呆边界观察（代码质量）

`mvp/definition.json` 存在**边 id 与 source/target 不一致**：如 `edge-agent_se-agent_trimmer` 的 source=agent_se、target=script_se_post（:1027-1030）；`edge-script_render_trimmer-agent_nw` 的 target=script_render_trimmed_chars（:1042-1046）。（推断）图形编辑器改边未同步 id，说明**引擎按 source/target 执行、id 仅标识**——"声明式 DAG 的 id 与语义解耦"反面教材。

---

## 6. 上下游设计

### 6.1 与 Core 的上游接口

- **manifest 契约**：`[extension]` id/name/version/api_version/capabilities + `[resource_namespace] prefix` + `[resources]` 路径映射。
- **前缀隔离**：插件内用本地 ID，加载时 Core Resource Resolver 映射为带 `bishu-novel-` 前缀的最终 ID；前缀可被安装者覆盖，SKILL 反复要求"先 list_workflows/get_workflow 核对实际 ID"（`SKILL.md:59-62`）。
- **版本锁定**：安装填精确 Commit/Tag + Subdirectory，Core 锁定精确 Commit（`README.md:16-22`）。
- **不依赖 Core 内部**：public-api 走稳定 HTTP API + owner 头 `X-DeterminFlow-Provider-Owner`（`provider.py:54`）；bishu-novel 有 portability 测试直接 import Core manifest 解析器验证（`test_plugin_portability.py`）。
- **模型服务接入**：agent 不锁模型（继承 main.model），切换 Core 默认模型即统一切换整套工作流；public-api 把公益凭据注册成普通 openai_compatible Provider 由 Core 调度。

### 6.2 数据契约 / 回滚 / 兼容

- **输入契约**：`variables[]` 区分 `input`（用户填）与 `file`（默认值=工作区相对路径，支持 `{{prev_chapter}}` 模板，多为 hidden）。
- **工作区模式陷阱**：Chat 面 `named_shared` 按 Main 会话隔离，新会话同名 `workspace_ref` 连不回旧目录；跨会话须续原会话或用 Web/API 固定 `workspace_override`（`references/workspace.md:8-18`）。
- **覆盖/回滚**：多数 workflow 覆盖固定输出，无内建版本回滚，恢复靠"整目录复制"（目录即身份，复制即备份，`docs/local-archive.md:23`）。
- **幂等/重跑语义**：vo_post 按卷号"替换段落/追加"（`vo_post.py:83-100`）；no_post 由 agent 的 `is_new_volume` 决定覆盖/追加（`no_post.py:78-83`）；索引合并幂等。
- **后验顺序依赖**：polish 若改情节事实必须重跑 post-hoc，纯措辞调整不必（`docs/workflows.md:17-18`）。

---

## 7. 可借鉴清单（分成本）

> "落点"基于旧研究文档对 mo-shu 的认知（Claude Code skill 架构 + `tracking_commit.py` 单一事务工具 + `_tracking-state.json` 单一权威 + 主会话按文档执行）。

### 🟢 低成本

1. **文件门禁脚本化**（`prepare --require`/`checkpoint --files`，缺失或空文件 fail，禁伪造空文件跳门禁；`local_archive.py:67-79`）。落点：`tracking_commit.py` check 扩展为写前门禁。
2. **同一套规则双向复用**（写作约束↔检测标签；`prompts.json:1749`↔`:1839`）。落点：narrative-writer 质量规则抽公共引用，consistency-checker 按同文件标签版检测。
3. **意图两路分发**（情节 vs 写法，只归类不判断，有分发规则表；`prompts.json:1913` + `parse_intent.py`）。落点：日更意图确认拆"情节指令/写法指令"两栏。

### 🟡 中成本

4. **观察/裁决双 agent + 世界事实裁决**（observer 提取带证据差异、arbiter 保守裁决 adopt/pending/conflict）。落点：章后对照升级；**必须保留作者确认点**（见 §8-2）。
5. **叙事债务独立维度**（hook 读者好奇 vs debt 角色欠角色，各自 id/expected_payoff/from/to，到期核对；`local_archive.py:26-29` + nd_output/nar_events）。落点：追踪 schema 加 debts 域。
6. **执行方案子集**（execution_schemes 定义多套节点子集；`polish/definition.json:266-288`）。落点：lean/full、检查/修复显式化为命名方案。
7. **上下文减法加载**（agent 只输出减法列表，脚本确定性裁剪；"默认全保留+保守删除+场景级可感保留/系统级结构不保留"；`trimmer_post.py` + `prompts.json:2158`）。落点：本章设定包改"减法清单+脚本裁剪"。

### 🔴 高成本

8. **SLOT 骨架 + 专项写手并行填槽**（骨架写手产 `[SLOT_*]` 骨架，5 专项写手并行填槽，整合写手拼装；`mvp/definition.json` 写手分支 + `prompts.json:236`）。落点：仅高潮/关键章启用（token 翻倍，笔枢默认 single）。
9. **"去 AI 味"三级润色**（自审只诊断+15 类标签+FEELS HUMAN → 人文化 7 优先级+改动<10% → 出版级 7 维+长度保护 60%-140%+Slot 清理；`prompts.json:1732-1893`）。落点：deslop 增加可选"出版级润色"第二道。

---

## 8. 不可借鉴清单

1. **声明式 DAG 引擎**：mo-shu 是 Claude Code skill 文本协议（主会话按文档执行），改造成可执行 DAG 是架构重写。只学"脚本节点做确定性转换+文件门禁"思想。
2. **纯 AI 裁决（post-hoc 无作者确认点）**：无审批节点，arbiter 明说"敢拍板"（`prompts.json:2006`），裁决直接回写 world/hooks/debts。**与 mo-shu"作者掌控"哲学冲突**——须把 adopt/pending/conflict 变"建议+作者确认"。
3. **每章全量快照（多副本）**：每章目录 9+ 文件（`references/workspace.md:44-54`），牺牲空间换可审计，靠整目录复制备份。**与 mo-shu 单一权威+派生视图冲突**（多副本易漂移）。
4. **33 个 agent 数量**：数量是"职责拆到最细"的结果不是目标；同等 token 预算下对 mo-shu 主会话架构是编排/会话负担。只学"职责单一化"思想。
5. **无 ID 极端简化**：不生成书籍/章节/Job ID，全依赖目录名。个人单机可行；若 mo-shu 需跨会话重连/多书管理/审计则成障碍（笔枢自己承认 Chat 面跨会话连不回旧目录，`references/workspace.md:16-18`）。

---

## 9. 与 mo-shu 差异定位

| 维度 | DeterminFlow-Plugins | mo-shu（旧文档认知） |
|---|---|---|
| 编排 | 可执行 DAG（引擎保证顺序/并行/循环/条件） | SKILL 文本协议（主会话按文档执行） |
| 确定性 | 12 脚本+2 内联，独立可测 | tracking_commit.py 单一事务工具 |
| 权威数据 | 每章快照+archive 双索引（多副本） | _tracking-state.json 唯一权威+派生视图 |
| 后验 | observer/arbiter AI 双角色，无作者确认点 | 章后对照一条龙，作者裁决点保留 |
| 审查 | self-critic 只诊断→polisher 才改（AI 诊断） | deslop 7 Gate+check-ai-patterns（机器化） |

**差异实质（推断）**：笔枢"多快照+引用"牺牲空间换可审计，判断交给拆分后的专用 agent；mo-shu"单权威+派生"牺牲直观换一致性，判断留给作者。互补——笔枢的"观察/裁决分离""叙事债务维度""文件门禁脚本化"是 mo-shu 可吸收增量，mo-shu 的"作者确认点"恰是笔枢短板。

---

## 10. 待验证问题

1. **`wroter_context` 组装**：`mvp/definition.json:1510-1519` 用 textarea 变量内嵌多段 `{{style_guide_file}}` 等引用，展开时机/是否递归展开未在插件内定义——存疑，需 Core 引擎源码确认。
2. **`agent_nw` 的 `template_values`**：`:487` `"nervous_habits":"{{writer_type}}"` 字段名与语义疑似残留/笔误——存疑，需 Core node 渲染器确认。
3. **边 id 与 source/target 不一致**（:1027-1030,:1042-1046）：引擎是否完全忽略边 id——存疑，需 Core DAG 执行器确认。
4. **多写手 `muti` 分支完整可用性**：分支存在但默认 single，evals 无多写手路径覆盖——存疑。
5. **`cache/` 清理后可恢复性**：`prepare --context` 依赖 `cache/sync/*` 重建，但 `cache/character/*_deep.json` 等中间件若被清、下游合并是否可重建——存疑。
6. **`maxContextTokens:128000` 硬编码**（`provider.py:90`）与动态目录模型的适配性——存疑。
7. **evals.json 运行机制**：只有 prompt/expected_output/expectations，无跑分逻辑，如何被 Core 消费（人工 or LLM-as-judge）——存疑。

---

## 11. 旧研究文档勘误

> 对照旧档案 `docs/bishu-研究.md`（105 行；已于 2026-08-20 删除，本节为历史对照记录）。总体：主结论（7 workflow、observer/arbiter 分离、文件门禁、去 AI 味、info_boundary/info_voids、trimmer 减法加载）**基本准确**；有 1 处硬数据错误、2 处过度解读、1 处张冠李戴、1 处存疑、1 处轻微不精确。

1. **【硬数据错误】"Script Library（11 个 Python 脚本）"（旧文档第 12、71 行）**：与源码不符。实际 **12 个脚本库**（`tests/test_resources.py:17-30` 的 `EXPECTED_SCRIPT_LIBRARIES` 列出 12 个：cm_post/json_to_md/local_archive/no_post/od_post/parse_intent/polish_post/se_post/si_post/trimmer_post/vo_post/we_post），再加 2 个内联脚本（`workflows/{build,character}/script/*.py`），共 **14 个 .py**。"11"少算 1 个且未计入内联脚本。代码事实。

2. **【过度解读】"约 20 个独立角色 + 14 个'换皮变体'"（第 20 行）**：推断，代码无"换皮变体"概念。33 个 agent 在 `agents.json` 是独立条目、`prompts.json` 各自独立 sections（`tests/test_resources.py:121` 断言 `set(prompts)==set(agents)`）。虽有结构复用（6 worldbuilder 共享 nwb1-6、5 slot 写手共享 ndw/naw/niw2/ndw2/ntw、`nw_importent` 多写手复用），但"14 个换皮变体"是主观归类，非代码事实。

3. **【张冠李戴/存疑】"已知弱点（笔枢 reference-review 自认）：arbiter 是 AI 裁决，作者被架空"（第 44 行）**：仓库内**无** `reference-review` 文档（全库 grep 零命中）。"arbiter 是 AI 裁决、无作者确认点"这个判断**可从代码成立**（post-hoc 无审批节点，`prompts.json:2006` 明说"敢拍板"，裁决直接回写），但归因"笔枢 reference-review 自认"张冠李戴。

4. **【存疑】"settler（……每条 ≤60 汉字**禁比喻**）"（第 50 行）**：前两项已核实（"永远给意图永远不给清单"在 `prompts.json:366`；"每条字段不超过 60 汉字"在 `:376` 禁令一）。但"禁比喻"本轮 grep 未命中；"禁止用比喻制造余韵"实际出现在 transition-writer 的 `ntw_concrete` 第⑤条"拆掉物化结尾"（`prompts.json:2112`），可能被误植到 settler。

5. **【过度解读】"trimmer……主角/对手永不裁"（第 63 行）**：代码无此规则。真实原则是"默认全保留+保守删除+最小粒度二级子字段+场景级可感保留/系统级结构不保留"（`prompts.json:2158`），无"主角/对手永不裁"；`trimmer_post.py:42-51` 按减法列表 name 整进整出裁剪角色，**无主角保护**。"主角/对手永不裁"是把"保守删除"倾向过度具体化为不存在的硬规则。

6. **【轻微不精确】"polish（三级润色）"（第 16、97 行）**：源码准确表述是"自审+两阶段润色"（`docs/workflows.md:14`），即 SC→PL→PP 三节点。"三级润色"把"自审"也计为"润色"一级，措辞略偏。

**其余核对通过（非勘误，供参考）**：7 workflow（✓）、33 agent（✓）、`<WF_VAR>/<script_out>` 协议（✓ `extract_names.py:96-98`、`parse_intent.py:22-23`）、prepare/checkpoint 门禁与 --merge 幂等合并（✓ `local_archive.py`）、agent 不锁模型（✓ `tests/test_resources.py:195-204`）、execution_schemes（✓ `polish/definition.json:266-288`）、模型参数按职能（✓ `agents.json`）、"novel-observer 世界状态机 ≠ novel-chapter-observer 章节观察员"提示（✓ 准确且重要）、info_boundary/info_voids（✓ `prompts.json:40`，type=motive_gap/detail_gap/rhythm_gap）。

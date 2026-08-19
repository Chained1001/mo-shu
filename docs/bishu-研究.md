# 笔枢 bishu-novel 研究存档

> 研究对象：`DeterminFlow-Plugins/plugins/bishu-novel`（DeterminFlow 工作流引擎的纯本地小说生产插件——无数据库、无 UUID、全部本地文件）。
> 研究日期：2026-08-19。方法：2 轮子代理（workflow 架构 / agent 与 prompt），全部机制实读代码确认。
> 本地副本：`otherMaterials/referProject/DeterminFlow-Plugins/plugins/bishu-novel/`。
> 定位：mo-shu 已借鉴过它的三件套（细纲认知边界 info_boundary/info_voids、trimmer 设定减法加载、章后对照）——本存档确认原型 + 找出剩余增量价值。

---

## 0. 项目概览

**形态**：7 条声明式 workflow（`definition.json` DAG）+ 33 个 Agent/Prompt（agents.json + prompts.json）+ Script Library（11 个 Python 脚本）+ writing-assistant Skill。

**七条 workflow**（建议顺序）：
```
build（六维世界观串行）→ character（骨架→信念→逐角色循环→声线）→ story-plan（故事引擎+风格档案）
→ outline（卷纲+近纲）→ 每章: mvp（章节生产）→ 可选 polish（三级润色）→ post-hoc（后验回写）→ 下一章 mvp
```

**核心哲学**：**引擎+脚本承担流程控制与落盘，LLM 只留在有判断价值的节点，判断再按"对照 vs 裁决"拆分**——33 个角色是同一台流水线上被拆碎的单一职责，不是 33 个自由人格（约 20 个独立角色 + 14 个"换皮变体"）。

## 1. Workflow 架构

**definition.json = 纯声明式 DAG**：nodes[]（agent/script 两种）+ edges[]（含条件边）+ gateways[]（parallel/condition/loop/converge）+ variables[]（file/text/textarea/list，file 变量默认值=工作区相对路径支持模板 `story/{{prev_chapter}}/world_state.md`）+ execution_schemes[]（节点子集方案：polish 定义「润色」/「仅检查」两套）。

**Agent Node 协议**：产出契约统一为"直接输出纯 JSON，引擎自动保存"（save_output_to_file + output_file_path）；prompt 不碰文件路径，只有 {{变量}} 注入内容。**Agent 不固定模型**，全部继承 Core main.model，只配 model_params（temperature/reasoning_effort/thinking_budget）。

**脚本协议**：`<WF_VAR>key:value</WF_VAR>` 脚本→工作流变量回写（parse_intent 拆意图、extract_names 产循环列表）；`<script_out>` 日志回传。

**文件门禁**（local_archive.py）：`prepare --require a,b,c`（前置文件缺失或**空文件**直接抛错）；`checkpoint --files x,y`（阶段产物校验，`--merge-hooks/--merge-debts` 按 id 幂等合并进全量索引）；`render`（JSON→MD）；`post-hoc --chapter N`。

**存档结构**：`world/`（6 维原始 JSON）· `meta/`（可读 MD：world_foundation/character_profiles/story_plan/style_profile/hooks/debts）· `outline/` · `story/{4位章号}/`（每章全量快照：chapter.md + world_state + character_state + storyboard + diff_*）· `archive/`（hooks.json + debts.json 唯一权威索引）· `cache/`（可审计中间层）。警告"不要只改 MD 制造不一致"；`_normalize_chapter` 4 位；`_workspace_path` 拒绝绝对路径与 `..`。

## 2. post-hoc 闭环（核心机制）

**novel-chapter-observer（观察员=对照机器，只提取不裁决）**：读终稿+全部状态文件，逐条输出四类差异 JSON——`world_diff`（新地点/势力/规则变更/超规格物品/矛盾，每条带正文段落证据）、`story_diff`（landed/missed/deviated/unplanned）、`character_diff`（新角色/关系/状态/物品/生命周期异常）、`unplanned_events`。

**novel-arbiter（裁决器，只裁决不评质量）**：①世界事实 world_rulings：adopt/pending/conflict（**保守默认：低风险自动 adopt、涉势力体系默认 pending、仅直接矛盾才 conflict**）；②故事差异 story_confirmed；③未提事件归类 hook/debt/discard；④产出 new_hooks/new_debts。

**归档**：local_archive post-hoc → diff_*.json + 合并 hooks/debts 索引（source: 后验 标记）→ render 成 meta MD。

**为什么必须在下一章前完成**（代码级证据）：mvp 的 file 变量直接引用上一章后验产物——prev_diff_world（世界状态机吸收裁决）/ prev_diff_character（角色状态维护师吸收）/ diff_story_file（大纲导演补回 missed、核对 deviated）。不做 post-hoc，下一章就拿"未裁决"的上一章状态开工。文档明确：**polish 若改变情节事实必须重跑 post-hoc**（纯措辞调整不必）。

**已知弱点**（笔枢 reference-review 自认）：arbiter 是 AI 裁决，**作者被架空**——mo-shu 借鉴必须保留作者确认点。

## 3. Agent 设置（33 个的本质）

**建书前置（15）**：6 个 worldbuilder（同构模板变体，六维：corelaws/spacetime/society/historyculture/existence/information）+ 4 个 character（skeleton/belief/deep 逐角色循环/voice）+ story-planner（力学层，不规划情节）+ style-profiler（风格档案）+ volume-outliner + outliner（近纲）。

**单章生产（14）**：novel-observer（**世界状态机**——注意与 chapter-observer 不同名！推进世界时间/势力暗线/世界事件）+ intent-distributor（人类意图→OD 情节/SE 写法，只归类不判断）+ director（单章战略，管理伏笔/债务/信息黑洞）+ character-maintainer + settler（**意图导演："永远给意图，永远不给清单"**，每条 ≤60 汉字禁比喻）+ world-context-trimmer（减法列表）+ writer 群（骨架写手 → 5 专项写手**并行填 SLOT** → 整合写手）+ single-writer（单写手替代）。

**润色（3）**：self-critic（**只诊断不修复**，10 维通用+15 类中文硬性标签，必须引用原文带 severity，空结果 FEELS HUMAN）+ polisher（人文化，改动 <10%）+ professional-polisher（出版级七维，temp=0.7）。

**后验（2）**：chapter-observer + arbiter（见上）。

**模型参数按职能配置**：规划/创意 temp 0.8-0.9、维护/观察/裁决 0.3、自审 0.4+top_p 0.7、整合写手 thinking_budget 4000、distributor/trimmer 关 thinking。

## 4. 已借鉴原型的确认（mo-shu 与笔枢的渊源）

| mo-shu 已借鉴 | 笔枢原型 |
|---|---|
| 细纲认知边界三件套（视角/信息差/认知边界 + 信息留白 + INF 登记） | director prompt 的 guide.info_boundary（protagonist_knows/doesnt_know）+ info_voids（motive_gap/detail_gap/rhythm_gap + instruction + director_note）；storyboard info_gaps（resolve_ids/defer_ids） |
| trimmer 设定减法加载（本章设定包） | novel-world-context-trimmer + trimmer_post.py：只输出减法列表，脚本确定性裁剪；默认全保留、最小粒度=二级子字段、主角/对手永不裁 |
| 章后对照（workflow-daily 第 9 步） | post-hoc 的 observer/arbiter（mo-shu 是文本压缩版，无职责分离、无世界事实裁决） |

## 5. 与 mo-shu 的架构对比结论

| 维度 | 笔枢 | mo-shu |
|---|---|---|
| 编排 | 可执行 DAG（引擎保证顺序/并行/循环） | SKILL 文本协议（主会话 LLM 按文档执行，纪律靠文档） |
| 确定性 | 11 个小脚本（职责单一可独立测试） | tracking_commit.py 单一事务工具（更集中） |
| 权威 | 每章快照 + archive 双索引（多份副本） | _tracking-state.json 唯一权威 + 派生视图（可 check 比对） |
| 后验 | observer/arbiter AI 双角色（作者被架空，自认弱点） | 章后对照主会话一条龙（作者裁决点保留） |
| 审查 | self-critic 只诊断 → polisher 才改 | deslop 7 Gate + check-ai-patterns 确定性脚本（更机器化） |

**差异实质**：笔枢"多快照+引用"牺牲空间换可审计；mo-shu"单权威+派生"牺牲直观换一致性。mo-shu 追踪=已发生事实，笔枢 meta/=创作意图，互补。

## 6. 可借鉴点评估（对 mo-shu 的新增价值）

### 🟢 高价值（并入修改方案）

| # | 机制 | 落点 |
|---|---|---|
| B1 | **observer/arbiter 双 agent 分离 + 世界事实裁决**（章后对照升级：observer 只提取四类差异带证据 → arbiter 只裁决，保守默认 adopt/pending/conflict；**必须保留作者确认点**——笔枢自认 AI 裁决架空作者的弱点） | workflow-daily 第 9 步升级；世界事实裁决进追踪 timeline_events |
| B2 | **叙事债务（debts）独立追踪维度**（角色间承诺/悬置因果/到期核对；与伏笔 hook 分开管理："掀1埋2"、到期检查） | 追踪 schema 加 debts 域（并入 U3 一次性升级）+ 章前到期核对 |
| B3 | **文件门禁脚本化**（prepare --require / checkpoint --files：缺失与空文件 fail，禁伪造文件跳门禁） | tracking_commit.py check 扩展为写前门禁（细纲/卷纲/上下文卡非空） |

### 🟡 中价值

| # | 机制 | 落点 |
|---|---|---|
| B4 | **同一套规则双向复用**（写作约束 ↔ 检测标签：15 条禁令在 writer 是遵守清单、在 self-critic 翻面成枚举标签） | 把 narrative-writer 质量规则抽公共引用文件，consistency-checker 按同文件标签版检测（并入 U5） |
| B5 | **执行方案子集**（execution_schemes：同一 DAG 定义「润色」/「仅检查」两套） | moshu-review 的 lean/full、deslop 的检查/修复显式化为命名方案 |
| B6 | **意图分发两路**（human_intent → OD 情节/SE 写法；world_intent 独立世界级入口必须带因果链） | 日更意图确认显式拆"情节指令/写法指令"两栏（与现有世界级意图分流衔接） |
| B7 | **三级润色管线**（自审只诊断 → 人文化 → 专业出版级，长度保护 60%-140%） | deslop 增加可选第二道"专业润色"（面向出版/签约） |
| B8 | **SLOT 骨架+专项写手**（高潮章可选启用；成本高，token 翻倍） | narrative-writer 可选"骨架+专项"路径（仅特定章） |

### ⚪ 不学

- **声明式 DAG workflow**：mo-shu 是 Claude Code skill 架构，改造不可行；学"文件门禁/脚本节点做确定性转换"思想即可（B3）
- **33 agent 数量**：不学数量，学"职责拆分到最细"思想（P8 已覆盖）
- **每章全量快照**：与单权威冲突（漂移风险）；review 按章读快照可作轻量替代
- **纯 AI 裁决**：作者架空，违背 mo-shu"作者掌控"哲学（B1 已注明保留确认点）

**总体结论**：笔枢的价值密度低于前两个项目（mo-shu 已借鉴其三件套），剩余增量集中在 **B1（章后对照升级为 observer/arbiter 分离 + 世界事实裁决）、B2（叙事债务维度）、B3（文件门禁脚本化）**——三者都并入现有修改方案（B1→U4 渲染规则/章后对照、B2→U3 schema 升级、B3→U2/U3 门禁扩展），不新增独立批次。

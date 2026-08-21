# 证据卡片 · webnovel-writer（v7 主 / v6 辅增量）

> 命题：大纲/卷纲/细纲/正文/设定（世界观/人物/力量体系）在实际写作中反复修订——它们是迭代演化的活资产。
> 本轮只挖六维**增量**证据；已由研究-v3 档案 03 覆盖的全景结论（单入口状态机 / 写章八阶段 / 书仓布局 / 知识三段切片 / 候选制）不重做，复用标「见研究-v3 档案 03」。
>
> 路径约定（相对各项目根）：
> - v7 根 = `otherMaterials/referProject/webnovel-writer-v7/`；证据内 `v7/...` 指 `v7/` 实现，`docs/architecture/...` 指仓库根 docs。
> - v6 根 = `otherMaterials/referProject/webnovel-writer/webnovel-writer/`；证据内 `skills/...`、`scripts/...`、`agents/...`、`templates/...` 指该根下。
>
> 档案标注：**【事实】** = 代码/规格可证；**（推断）** = 由代码/文档推出；**存疑** = 证据不足拿不准；**文档宣称** = 仅 README/PRD 自述，无代码佐证。
>
> 铁律复核：全程只读 otherMaterials/referProject/**，未改任何参考文件；未执行 git 写操作；未读 docs/归档/ 与 docs/规格-V2/。

---

## 维度 1 · 资产分层（设定/大纲/卷纲/细纲/正文的文件与真源/派生关系）

### 1.1 【v7】书仓四区 + 逐层资产文件名是唯一真源
大纲/总纲.md、大纲/卷纲/第NN卷.md、大纲/创作设计/、大纲/灵感池.md、大纲/伏笔|悬念|感情线/；定稿/正文|设定|摘要/；作品契约/；文风/；工作区/；.cache/ 一一对应文件形态，作者可见即真相。
证据：`v7/../docs/architecture/story-repo-spec-2026-06-10.md:74`（一本书=一个 git 仓库，四区一句话）；`:115-170`（目录总览全文）；`:78`（不变量 1「文件即真相」）。档案：【事实】。版本：v7。

### 1.2 【v7】派生状态只有 .cache，删光可全量重建
`.cache/index.db`（node:sqlite）是唯一持久派生物，gitignored，正文+摘要+条目 Markdown 即全部状态。
证据：spec:79（不变量 2「派生物可丢弃」是 CI 验收项）；`:633`（唯一允许的持久派生物）；`:635`（改源流程自刷缓存）。档案：【事实】（CI 验收项本身标「部分核验」，见研究-v3 档案 03 §十二）。版本：v7。

### 1.3 【v7】设定走「计划对象 → 事实对象」两阶段生命周期
建书/大纲/对象设计确认的设定先入 `大纲/创作设计/设定|人物/`（计划，可改可放弃不触发吃书）；正文首次定稿后无冲突事实才随章节原子转入 `定稿/设定/`。
证据：spec:251-253（计划对象可修改、改名或放弃，不触发吃书）；spec:275（factChanges 转正语义）；spec:731（决策 48 两阶段生命周期）。档案：【事实】。版本：v7。

### 1.4 【v7】设定与大纲单向依赖（不变量 13）
`定稿/设定/` 只记已发生客观事实，不写排程；依赖方向单向——`大纲/` 引用设定正名，设定不反向引用大纲条目编号/卷号排程；改文风/进度只动大纲与文风，不牵连设定。
证据：spec:90（不变量 13 全文）；spec:279（角色卡只记设定原意与已发生事实，排程归大纲/卷纲）；spec:801（决策 26 单向依赖入宪来源）。档案：【事实】。版本：v7。

### 1.5 【v7】细纲是工作区文件，未定稿可丢，归宿是章 front matter
`工作区/细纲.md` 固定四段（全书近况/本章提案/本章要写到的事/备选），作者唯一要看；「本章要写到的事」最终归宿是章节 front matter。
证据：spec:477-479（工作区默认 gitignored，最终归宿是 front matter）；spec:481-503（细纲四段模板）；spec:505（确认后原子写细纲+快照）。档案：【事实】。版本：v7。

### 1.6 【v7】作品契约.md 是唯一书级真源，知识选择记录是证据存档
下游（规划/备料/两审）只读作品契约，不回读通用条目；知识选择记录只存实际采用/拒绝/修改证据，不进日常上下文。
证据：spec:433-435（6.3 作品契约）；spec:473（知识选择记录不保存全量候选）；spec:730（决策 47）。档案：【事实】。版本：v7。

### 1.7 【v6】v6 资产是「设定集 + 大纲三件套」平铺，与 v7 四区不同
v6 设定集：`设定集/世界观.md`、`设定集/力量体系.md`、`设定集/主角卡.md`、`设定集/反派设计.md`、`设定集/女主卡.md`、`设定集/金手指.md`、`设定集/主角组.md`；v6 大纲：`大纲/总纲.md`、`大纲/第N卷-节拍表.md`、`第N卷-时间线.md`、`第N卷-详细大纲.md`。
证据：`skills/webnovel-plan/SKILL.md:101-104`（Step 2 补齐设定基线四文件）；`:112-124`（Step 4/5 节拍表+时间线）；`templates/output/设定集-力量体系.md:1-59`（力量体系模板：体系公理/体系类型/能力来源/等级体系/晋级条件/资源系统/战斗规则/禁忌与限制）。档案：【事实】。版本：v6（与 v7 差异增量）。

### 1.8 【v6】v6 大纲三层架构（骨架/分卷/章节）+「大纲是地图不是枷锁」
三层：骨架大纲（必需 30%）、分卷大纲（建议 50%）、章节大纲（可选 20%）；明确「如果灵感爆发，可以偏离大纲（但要记得回来修正大纲）」。
证据：`skills/webnovel-plan/references/outlining/outline-structure.md:6`（核心原则）；`:10-78`（三层架构与比例）；`:82`（可偏离但要回来修正）。档案：【事实】。版本：v6（方法论层，v7 无对应章节层大纲文件）。

### 1.9 【v6】v6 派生状态多路投影（state.json/index.db/vectors.db 五面）——与 v7 单一 cache 的根本差异
写章投影五项 state/index/summary/memory/vector，全部 done 才算完成；与作者手改冲突是 v6→v7 六大病根之一。
证据：`skills/webnovel-write/SKILL.md:249`（projection 五项 done/skipped）；`v7/../docs/architecture/v7-design-discussion-notes-2026-06-11.md:16`（派生状态与作者手改冲突无解，#100/#77/#63/#67/#70/#71/#89）。档案：【事实】（病根为文档自述 + issue，见研究-v3 档案 03 错误清单 #2）。版本：v6（反差增量）。

---

## 维度 2 · 修订机制（影响分析/级联/stale 标记/回滚/版本管理 + 触发点与代价）

### 2.1 【v7】影响分析 `impact`：改设定/吃书前 grep 出引用清单，分已发布/未发布
纯脚本：grep 正文 + 条目履历 + 时间线，按 book.yaml `已发布到章` 把命中章分「已发布/未发布」两清单。
证据：`v7/src/state-machine/flows/impact.js:11-43`（analyzeImpact 全文）；`v7/src/commands/impact.js:7-9`；spec:593（未发布→直接改或吃书，已发布→顺势圆）。档案：【事实】。版本：v7。

### 2.2 【v7】吃书 `retcon`：显式改定稿的留痕通道
commit 前缀 `retcon(N): 原因`，设定/条目同步，commit 写明原因「留痕可查」；失败按写入集合逐文件 restore 回滚，不误伤作者手改。
证据：`v7/src/state-machine/flows/retcon.js:13-46`（retcon 流程 + commit 留痕）；`:48-60`（回滚收窄到本次写入集合）；spec:592（吃书显式流程）。档案：【事实】。版本：v7。

### 2.3 【v7】回到第 N 章 `goto-chapter`：展示影响范围 + 作者确认 + 救援 ref 备份 + 脏树拒绝
执行前展示 willLose 提交清单；confirm 才 reset；先建 `rescue/goto-<ts>` ref；跟踪面有未登记手改则拒绝（与序 2 同源判定）。
证据：`v7/src/state-machine/flows/goto-chapter.js:35-48`（needsConfirm + willLose 展示）；`:50-64`（脏树拒绝）；`:66-80`（rescue ref 备份 + resetHard）。档案：【事实】。版本：v7。

### 2.4 【v7】改稿三档语义（设计原则）——修订的三种代价分级
未发布=直接改+自动重入账；已发布=只读出「顺势圆」方案；设定/大纲=跑影响分析出两清单。
证据：design-notes:30（原则 5 手改是一等公民）；design-notes:45（改稿三档语义）；spec:593（已发布→顺势圆）。档案：【事实】（「顺势圆」实现留 M4，见 retcon.js:9 注释「圆设定留 M4」）。版本：v7。

### 2.5 【v7】契约修订强制携带「证据 + 影响范围 + 作者确认」，核心分类变化需「影响分析已确认」
validateContractUpdatePayload 要求非空「证据」「影响范围」「作者已确认」；改变类型/副题材/流派/创意约束时额外要求 `影响分析已确认:true`。
证据：`v7/src/knowledge/contract.js:104-140`（validateContractUpdatePayload）；`:108-110`（证据/影响范围必填）；`:127-131`（coreClassificationChanged → 影响分析已确认）。档案：【事实】。版本：v7。

### 2.6 【v7】契约版本严格递增 + 生效起章 = 下一未定稿章（单版本真源，无延迟生效）
新契约版本必须 = 旧版本 + 1；生效起章必须精确等于下一未定稿章；禁止提前覆盖文件假装延迟生效。
证据：`v7/src/knowledge/contract.js:217-229`（mode update 校验）；`:184-189`（契约版本/生效起章正整数）；spec:475（当前只有一份契约文件）。档案：【事实】。版本：v7。

### 2.7 【v7】契约失效守卫：级联失效未发布章 + 待提交证明 hash 绑定
契约更新把全部未发布章原子放进「待重做」集合（`契约失效.json` guard + 作者可见 marker）；受影响批次章标「契约变更」；待提交证明绑定章号/契约版本/批次目录/定稿包原始字节 sha256，commit confirmed 才释放。
证据：`v7/src/staging/contract-invalidation.js:148-192`（checkChapterContractInvalidation 四态判定）；`:258-264`（guardBlocksChapter）；`v7/src/staging/index.js:900-1027`（prepareContractInvalidation 标记受影响章+工件）。档案：【事实】。版本：v7。

### 2.8 【v7】手改检测 `relink`：系统适应作者，事后自愈不报错
启动发现作品契约/定稿/大纲/文风有未登记手改 → 细纲前问「补登吗」→ `relink` 以 `fix(手改): 说明` 入档并刷缓存。
证据：SKILL.md:23（序 2 手改补登）；spec:595（手改检测与 relink）；spec:78（不变量 1 永不报错拒绝）。档案：【事实】。版本：v7。

### 2.9 【v7】大纲漂移是决策点不是 bug（双向处理：拉回/改纲/进灵感池）
写稿偏离细纲/卷纲时，下一章细纲给三选：拉回 / 改纲 / 存进 `大纲/灵感池.md`。
证据：design-notes:44（大纲漂移是双向的：偏离是决策点不是 bug）；spec:515（三选与灵感池）；spec:144（灵感池目录）。档案：【事实】。版本：v7。

### 2.10 【v7】计划对象可改可放弃不触发吃书；事实对象才需吃书（修订代价分级）
计划对象在创作设计目录内可修改、改名、放弃，目录本身表示计划状态；只有「已定稿事实」的改写才走吃书。
证据：spec:253（计划对象可修改/改名/放弃，不触发吃书）；spec:80（不变量 3 定稿只增不改，真要改走显式吃书）；spec:275（事实转正与章节同一 commit）。档案：【事实】。版本：v7。

### 2.11 【v6】v6 大纲动态调整：变更日志 + 三条调整红线
大纲变更要写「变更日志」（日期/变更内容/新方案/影响范围）；红线=主角人设、力量体系、核心主线不可轻改。
证据：`skills/webnovel-plan/references/outlining/outline-structure.md:105-124`（动态调整与红线）。档案：【事实】（方法论文档，非代码强制）。版本：v6。

### 2.12 【v6】v6 大纲↔设定冲突示例给三方案（调整大纲/补设定/加奇遇）
冲突示例：大纲第 50 章突破金丹 vs 设定 16 岁正常 20 年才金丹 → 方案 A/B/C 三选。
证据：outline-structure.md:176-187。档案：【事实】（示例文档）。版本：v6。

### 2.13 【v6】v6 plan 的 BLOCKER 阻断机制：发现设定冲突先阻断等用户裁决
「若发现总纲与设定冲突，先阻断，再等用户裁决」；Step 2/8 发现设定冲突标记 `BLOCKER` 等待裁决；Step 9 `BLOCKER=0` 才通过。
证据：`skills/webnovel-plan/SKILL.md:17`（执行原则 4）；`:24`（BLOCKER 等待用户裁决）；`:166`（硬规则标记 BLOCKER）；`:170`（验证 BLOCKER=0）。档案：【事实】。版本：v6。

### 2.14 【v6】v6 事件触发合同修订提案（amend proposal）——自动提案、pending 状态、覆盖账本
`AmendProposalTrigger` 按事件类型（world_rule_broken/relationship_changed/power_breakthrough/artifact_obtained/character_state_changed/world_rule_revealed/open_loop_created/closed/promise_created/paid_off）生成修订提案，写入 `override_contracts` 表（record_type=amend_proposal/soft_deviation，status=pending）。
证据：`scripts/data_modules/override_ledger_service.py:49-82`（AmendProposalTrigger.RULES）；`:85-134`（persist_amend_proposals 入表 pending）。档案：【事实】。版本：v6（v7 已归零此「事件级投影+自动提案」路线，见 design-notes:9）。

### 2.15 【v6】v6 总纲写回 `master-outline-sync`：只更新总纲 V+1 卷锚 + 伏笔表，不重写全纲
规划结束生成结构化写回 JSON（next_volume_anchor + foreshadow_writeback + open_loop_writeback），脚本只追加/更新总纲的卷表与伏笔表行，禁止从卷纲自由文本推断。
证据：`scripts/update_master_outline.py:240-276`（sync_master_outline）；`skills/webnovel-plan/SKILL.md:172-198`（写回 JSON + master-outline-sync 命令）。档案：【事实】。版本：v6。

### 2.16 【v6】v6 断点续跑检测「章纲更新晚于正文」→ 停下询问，不得覆盖作者手改
`run-ledger write-resume` 只给续跑建议不自动覆盖；正文被手动改过、章纲更新晚于正文、已 accepted 又重跑时必须停下用有限选项询问。
证据：`skills/webnovel-write/SKILL.md:297-306`（write-resume 续跑契约）。档案：【事实】。版本：v6。

### 2.17 【v6】v6 增量补齐原则：只增量不重写整份总纲/设定集
「只做增量补齐，不重写整份总纲或设定集」「增量补齐，不清空、不重写整文件」。
证据：`skills/webnovel-plan/SKILL.md:10`（主 agent 职责）；`:14`（执行原则 1）；`:99`（Step 2 增量补齐）。档案：【事实】。版本：v6。

---

## 维度 3 · 构建-执行分离（构思/设定/大纲 vs 写章的切分；细纲归构建还是执行）

### 3.1 【v7】单入口状态机 7 序把「构建态」与「执行态」统一路由（见研究-v3 档案 03 §2.1，此处补修订侧序点）
序 1 建书、序 2 手改补登、序 4 卷复盘、序 6 起草细纲是构建/修订入口；序 3 断点续跑按工作区工件映射回执行阶段。
证据：spec:604-612（序表）；SKILL.md:19-27（各序动作）；spec:618-627（序 3 续跑映射表）。档案：【事实】（全景结论见研究-v3 档案 03）。版本：v7。

### 3.2 【v7】细纲归「构建」，写稿起归「执行」——八阶段内环的切分点
八阶段：起草细纲（脚本+AI）→ 作者确认细纲 → 备料 → 写稿 → 机检 → 两审 → 作者审稿 → 定稿；「确认细纲」是构建与执行的切分点，作者确认后才备料。
证据：spec:519-528（八阶段表）；SKILL.md:27（序 6 起草细纲 + persist-outline）；SKILL.md:32-45（写章流程 1-4）。档案：【事实】（八阶段全景见研究-v3 档案 03 §2.2）。版本：v7。

### 3.3 【v7】构建/修订落盘由脚本原子执行，AI 只出结构化 DTO，不碰文件
建书（persistCreateBook）、卷复盘（persistVolumeReview）、契约修订（persistWorkContract）均「AI 提交 DTO → 本层映射路径写出 + git commit」，失败 restore 回滚。
证据：`v7/src/state-machine/persist.js:32-35`（AI 态产物回流落盘，AI 不碰文件）；`:96-140`（建书原子落盘+commit）；`:142-229`（契约修订原子替换+commit+失败回滚）。档案：【事实】。版本：v7。

### 3.4 【v7】「全自动 ≠ 无控制，是控制上移到大纲层」——构建层作者确认粒度可变
作者逐卷确认卷纲，一次确认管几十章；自动模式与手动模式差异只是确认粒度（逐章 vs 按批次），状态机与八阶段零改动。
证据：design-notes:58（控制点滑杆）；spec:575（全自动≠无控制）；spec:586（两开关全关=逐章流程不变）。档案：【事实】。版本：v7。

### 3.5 【v7】写评分离：写稿与两审强制不同上下文
不变量 6：写稿与评审必须在不同上下文中进行；机检先于 AI 评审。
证据：spec:83（不变量 6）；design-notes:79（写手与审稿分离，「自己审自己会自我辩护」）。档案：【事实】。版本：v7。

### 3.6 【v6】v6 构建/执行按 8 个 skill 命令切分（init/plan/write/review/query/learn/dashboard/doctor）
plan 管总纲→卷纲→章纲构建，write 管单章执行，query 管知识/记忆查询，learn 管学习，dashboard/doctor 管产品化与诊断。
证据：`skills/` 下 8 个 `webnovel-*/SKILL.md`（webnovel-init/plan/write/review/query/learn/dashboard/doctor，目录清单）；`skills/webnovel-plan/SKILL.md:10`（主 agent 职责：增量细化卷纲/时间线/章纲）。档案：【事实】（8 命令全景见研究-v3 档案 03 §五）。版本：v6（增量：v6 是命令切分，v7 内化为单入口状态机）。

### 3.7 【v6】v6 章纲归构建（plan 生成），写章消费章纲（chapter_directive）
plan 输出 `大纲/第N卷-详细大纲.md`（每章含目标/阻力/代价/时间锚点/爽点/节点等）；write 的写作任务书优先级第一项即 chapter_directive.goal/time_anchor 等硬性约束。
证据：`skills/webnovel-plan/SKILL.md:144`（每章必须包含字段）；`:158`（输出详细大纲）；`skills/webnovel-write/SKILL.md:73-80`（chapter_directive 优先 + 五段排序）。档案：【事实】。版本：v6。

### 3.8 【v6】v6 写章六阶段 + 4 subagent 编排（context/reviewer/data/deconstruction）
写章流程：context-agent 生成任务书 → 起草 → reviewer 审查 → 润色 → data-agent 提事实 + chapter-commit → 备份；每章 3 subagent（context/reviewer/data）。
证据：`skills/webnovel-write/SKILL.md:16-20`（模式表）；`:84-97`（Step 1 context-agent）；`:122-134`（Step 3 reviewer）；`:184-212`（Step 5 data-agent + precommit）；`:267`（Step 6 备份）。档案：【事实】（每章 3 subagent 的 token 失控代价见 design-notes:17）。版本：v6。

---

## 维度 4 · 技能/角色架构（功能划分原则、角色清单、数量与过度拆分教训）

### 4.1 【v7】单 SKILL.md 入口 + 2 个角色任务书（事实审查/编辑审）
v7 把 v6 的 4 agent 收敛为 2 个角色任务书（roles/事实审查.md、编辑审.md）；SKILL.md 单入口，流程知识压进脚本 DTO 返回值。
证据：`v7/skills/webnovel-writer/SKILL.md:1-7`（单入口 + 铁律）；`v7/roles/事实审查.md:1-7`；`v7/roles/编辑审.md:1-7`。档案：【事实】（单入口薄厚哲学见研究-v3 档案 03 §五）。版本：v7。

### 4.2 【v7】角色任务书即 prompt：输入=脚本绑定的 ReviewInput，输出=严格 JSON
两审任务书约定「只用传入的 ReviewInput 核对，不读文件、不调脚本」「输出严格 JSON 无其他文本」；事实审查 9 个 category，编辑审 4 个 category。
证据：`v7/roles/事实审查.md:7`（只用 ReviewInput）；`:25-31`（严格 JSON + factChanges）；`:12-21`（9 个 category）；`v7/roles/编辑审.md:12-16`（4 个 category）。档案：【事实】。版本：v7。

### 4.3 【v7】职责边界显式化：评事实不评文笔 / 评结构把情节决定权留给作者
事实审查「只报可验证问题，评事实不评文笔」；编辑审「评结构与商业性，把情节决定权留给作者」。
证据：`v7/roles/事实审查.md:41`；`v7/roles/编辑审.md:34`。档案：【事实】。版本：v7。

### 4.4 【v6】v6 4 个 subagent（context-agent / data-agent / reviewer / deconstruction-agent）+ 职责单源
context-agent 生成写作任务书；reviewer 统一审查（只查 5 维度、不评分）；data-agent 提取事实生成 commit artifacts；deconstruction-agent 拆解。
证据：`agents/context-agent.md`、`agents/data-agent.md`、`agents/reviewer.md`、`agents/deconstruction-agent.md`（四文件）；`agents/reviewer.md:13-17`（只查 5 维度、不评分）；`agents/data-agent.md:11-13`（三份 artifact schema 唯一真源）。档案：【事实】（四 agent 全景见研究-v3 档案 03 §四）。版本：v6（增量：角色数量从 4→2 的收敛）。

### 4.5 【v6】v6 主流程强制用 Agent 工具调 subagent，禁止口头代替——过度拆分的机制代价
「必须使用 Agent 工具调用指定 subagent；不得用主流程口头代替 subagent 输出」；reviewer「不持 Write」，主流程负责写回 JSON。
证据：`skills/webnovel-write/SKILL.md:25`（硬规则）；`:84`（context-agent 必须 Agent 工具）；`:122`（reviewer 必须 Agent 工具）；`:134`（reviewer 是 artifact 非写入方）。档案：【事实】。版本：v6（增量：该「每章 3 subagent」是 v7 归零的 token 失控病根，design-notes:17）。

---

## 维度 5 · 上下文衔接（构建产物喂写作的方式 + 写作中变化回流构建层）

### 5.1 【v7】备料 `prepare-chapter` 组装「本章写作材料」，默认精准片段
脚本零 AI 组装：全书近况+要写到的事+定稿/批内事实+信息差边界+近章结尾+反复读清单+文风锚点+契约小节+显式计划对象+细纲所选知识「落笔时」切片。
证据：`v7/src/commands/prepare-chapter.js:8-14`；spec:523（备料第 3 步组装清单）；SKILL.md:33（读材料写草稿）。档案：【事实】。版本：v7。

### 5.2 【v7】精准读取接口族（20+ read-*/list-*/report-*）：AI 非必要不整读
每类数据文件配「定位读取」脚本命令（读伏笔履历/读卷纲小节/读章结尾 500 字/读时间线在场过滤/读角色卡 front matter/read-design 等）。
证据：spec:644-659（11.1 接口清单）；`v7/src/commands/` 目录（read-design.js/read-outline.js/read-character.js/read-timeline.js/read-thread.js/read-secret.js/read-chapter.js/grep-story.js/list-*.js 等）。档案：【事实】（三段切片+精准读取全景见研究-v3 档案 03 §3.3）。版本：v7。

### 5.3 【v7】知识三段切片按消费阶段喂（规划时/落笔时/审稿时）
同一条知识按阶段切好片：细纲读「规划时」，备料只注入已选条目「落笔时」切片，编辑审只注入「审稿时」切片；通用条目改动不得改变本章已冻结来源。
证据：spec:509（备料只读快照落笔时、编辑审只读审稿时）；spec:511（章档案写入最终选择，来源追溯唯一输入）；spec:16（章级知识按节拍/场景/技法/追读给少量候选）。档案：【事实】（见研究-v3 档案 03 §3.3.2）。版本：v7。

### 5.4 【v7】写作中变化回流构建层：定稿包七类回流字段一次 commit 入档
定稿包含 threadCreates/threadUpdates/characterUpdates/rosterUpserts/timelineRows/secretWrites/factChanges，定稿时正文+设定/条目/时间线/名册/摘要/章摘要同一 git commit 原子转正。
证据：SKILL.md:45（定稿包字段清单）；spec:562（定稿一次 commit 包含）；spec:80（不变量 3 定稿只增不改）。档案：【事实】。版本：v7。

### 5.5 【v7】批内叠加视图：后章可用前章未定稿事实（版本链）
写批内后续章时备料/审稿/机检组装「定稿/ + 待定稿批次预登记」叠加视图；第 K+1 章可用第 K 章预登记事实；staged 数据只存工作区文件，不进缓存。
证据：spec:579（叠加视图与版本链）；`v7/src/staging/index.js:176-347`（stagedFacts 叠加事实包）；spec:580（stagedFacts 只接纳未失效章）。档案：【事实】。版本：v7。

### 5.6 【v7】细纲知识快照在确认时冻结来源 sha256，防下游串味
确认细纲原子写 `细纲.md` + `细纲知识快照.json`（outlineSha256 + 知识选择）；快照缺失/hash 不符 fail closed，禁止从当前知识库重建历史来源。
证据：spec:509-511（快照冻结 + 缺失 fail closed）；`v7/src/state-machine/persist.js:53-79`（persistDraftOutline 契约校验后原子写两文件）。档案：【事实】。版本：v7。

### 5.7 【v6】v6 context-agent 生成「写作任务书」+ 五段固定排序
任务书顺序：本章硬性约束（chapter_directive）→ CBN/CPNs/CEN → 本章禁区 → 风格指引 → dynamic_context 补充；chapter_focus 只能来自 chapter_directive.goal 或真实 query，不得从 dynamic_context 摘要继承。
证据：`skills/webnovel-write/SKILL.md:73-80`（五段排序）；`:84-97`（context-agent 任务书产物）。档案：【事实】。版本：v6。

### 5.8 【v6】v6 Story System 合同树（MASTER_SETTING/volume/chapter/review）喂写作
story-system 命令按 query+genre 生成 `.story-system/` 合同（MASTER_SETTING.json 调性/禁忌、volume 卷级节奏、chapter 必须节点/禁区），作为写章主链输入；合同含 override_policy（locked/append_only/override_allowed）。
证据：`scripts/data_modules/story_system_engine.py:111-162`（master_setting + chapter_brief 结构）；`:127-131`（override_policy 三值）；`skills/webnovel-write/SKILL.md:71`（必备文件缺失则阻断）。档案：【事实】（Story System 主链全景见研究-v3 档案 03 §一）。版本：v6（增量：合同树 vs v7 作品契约+细纲快照的衔接差异）。

### 5.9 【v6】v6 跨卷状态读取用记忆查询命令（query-entity-state/relationships/get-open-loops）
plan 跨卷状态读取用 `knowledge query-entity-state --at-chapter`、`query-relationships`、`memory-contract get-open-loops` 取最近状态与活跃伏笔。
证据：`skills/webnovel-plan/SKILL.md:83-94`（跨卷状态读取命令）。档案：【事实】。版本：v6。

---

## 维度 6 · 人机分工（修订流程的作者裁决点：候选制/影响清单/确认时机）

### 6.1 【v7】作者裁决点仅 2+2 个：确认细纲、审稿 + 卷复盘、契约修订
逐章/按批两处 + 卷复盘确认与作品契约修订确认；契约有问题时「只提出修订候选，作者确认前不得落盘」。
证据：SKILL.md:25（序 4 卷复盘：有问题只提修订候选）；SKILL.md:27（序 6 作者确认整份细纲）；spec:475（信号只产生修订候选，作者确认前不得落盘）。档案：【事实】（裁决点全景见研究-v3 档案 03 §八）。版本：v7。

### 6.2 【v7】候选制：每维最多 3 条候选，「候选是材料不是固定答案」
细纲阶段章级知识每维最多三条，可组合/变体/拒绝/自定义；不展示全量菜单、不自动选答案。
证据：SKILL.md:27（每维最多三条，只是材料不是固定答案）；spec:507（每维最多三条候选，不自动选答案）；spec:16（候选随整份细纲确认）。档案：【事实】（见研究-v3 档案 03 §3.3.3）。版本：v7。

### 6.3 【v7】候选永不拦截：issues 阻断 / candidates 只呈报
`unregistered_thread`（疑似伏笔无条目）恒 blocking=false，交作者裁决；机检泄密扫描「只出候选清单，不拦截」。
证据：`v7/roles/事实审查.md:36`（unregistered_thread 恒 blocking=false）；spec:557-560（未登记伏笔检测只出候选永不拦截）；spec:305（信息差泄密扫描只出候选）。档案：【事实】。版本：v7。

### 6.4 【v7】事实冲突/歧义用 options + applyChange 显式布尔，作者裁决后原样回传
每个选项必须显式 `applyChange`（false=不写事实不删计划，true=执行）；作者裁决保留 options 原样、填 resolution+optionId，执行层只从所选项派生，禁止按编号/文案猜测。
证据：`v7/roles/事实审查.md:31`（options/applyChange 规则）；SKILL.md:44（作者裁决后原样保留字段重提）；spec:275（执行层只从所选项派生 applyChange）。档案：【事实】。版本：v7。

### 6.5 【v7】吃书必须写明原因留痕（commit message 即人读审计）
「吃书必须写明原因（commit 留痕可查）」；commit 前缀 retcon(N): 原因。
证据：`v7/src/state-machine/flows/retcon.js:15`（必须写明原因）；spec:592（要求 commit message 写明原因，留痕可查）。档案：【事实】。版本：v7。

### 6.6 【v7】作者界面零机器味 + git 隐身：作者永远不直面 git 报错
作者可见目录/字段遵守术语表；任何 git 操作由 AI 代为运行，异常有人话修复流程。
证据：spec:85（不变量 8 git 隐身铁律）；spec:89（不变量 12 作者界面零机器味）；spec:600（git 健康检查，作者永远不直面 git 报错）。档案：【事实】。版本：v7。

### 6.7 【v6】v6 BLOCKER + AskUserQuestion 裁决：有限选项 + 影响说明
blocking issue 无法定点修复时用 AskUserQuestion 让用户裁决（接受当前/手动修复/放弃）；需要用户裁决时给 2-3 个有限选项并说明每个选项影响。
证据：`skills/webnovel-write/SKILL.md:162`（blocking 用 AskUserQuestion）；`:310`（有限选项+影响说明）；`skills/webnovel-plan/SKILL.md:246-248`（裁决用有限选项并说明影响）。档案：【事实】。版本：v6。

### 6.8 【v6】v6 少打扰确认策略：默认继续推进，仅四类场景才问
「默认继续推进；只有创作方向、事实一致性、文件覆盖风险或 blocking issue 无法定点处理时才问」。
证据：`skills/webnovel-write/SKILL.md:310`；`skills/webnovel-plan/SKILL.md:246`（只有总纲/设定冲突、时间线回跳、卷末钩子取舍、覆盖已有规划时才询问）。档案：【事实】。版本：v6。

### 6.9 【v6】v6 提交前变更面校验（只读 git diff）：作者手改/越权写入的兜底
precommit 前只读 `git diff` 校验变更面，不得出现插件目录、其他书项目、其他章节正文或非本章流程手写状态文件；只读、不 stage、不 commit。
证据：`skills/webnovel-write/SKILL.md:223-232`（git diff 变更面校验）。档案：【事实】。版本：v6。

---

## 六维覆盖表

| 维度 | v7 | v6 | 备注 |
|---|---|---|---|
| 1 资产分层 | ✅ | ✅ | v7 四区+两阶段生命周期；v6 设定集+大纲三件套+三层架构 |
| 2 修订机制 | ✅ | ✅ | v7 impact/retcon/goto/relink/契约失效守卫/版本递增；v6 BLOCKER/amend 提案/总纲写回/变更日志 |
| 3 构建-执行分离 | ✅ | ✅ | v7 序 1/4/6 构建 vs 八阶段执行；v6 plan/write 命令切分 |
| 4 技能/角色架构 | ✅ | ✅ | v7 单入口+2 角色；v6 8 skill+4 agent |
| 5 上下文衔接 | ✅ | ✅ | v7 备料/精准读取/三段切片/定稿包回流/叠加视图；v6 任务书/合同树/记忆查询 |
| 6 人机分工 | ✅ | ✅ | v7 2+2 裁决点/候选制/applyChange；v6 BLOCKER/AskUserQuestion/少打扰策略 |

六维全部覆盖，无「未发现」维度。

---

## 主要证据文件清单

**v7（主，`otherMaterials/referProject/webnovel-writer-v7/` 下）**
- `docs/architecture/story-repo-spec-2026-06-10.md`（格式法律文本，821 行，资产分层/修订机制/状态机/上下文接口的核心依据）
- `docs/architecture/v7-design-discussion-notes-2026-06-11.md`（改稿三档/大纲漂移双向/控制上移）
- `v7/skills/webnovel-writer/SKILL.md`（单入口 + 命令面）
- `v7/src/state-machine/flows/impact.js`、`retcon.js`、`goto-chapter.js`（影响分析/吃书/回滚实现）
- `v7/src/staging/contract-invalidation.js`、`v7/src/staging/index.js`（契约失效守卫/批次级联/叠加视图）
- `v7/src/knowledge/contract.js`（契约修订校验：证据/影响范围/版本递增/生效起章）
- `v7/src/state-machine/persist.js`（建书/卷复盘/契约修订/细纲落盘原子性）
- `v7/roles/事实审查.md`、`v7/roles/编辑审.md`（角色任务书）
- `v7/src/commands/prepare-chapter.js`、`v7/src/commands/impact.js`（命令面）
- `v7/templates/AGENTS.md`、`v7/references/README.md`（模板/知识库，部分见研究-v3 档案 03）

**v6（辅，`otherMaterials/referProject/webnovel-writer/webnovel-writer/` 下）**
- `skills/webnovel-plan/SKILL.md`（构建流程 + BLOCKER + 总纲写回）
- `skills/webnovel-plan/references/outlining/outline-structure.md`（三层大纲/动态调整/红线/冲突三方案）
- `skills/webnovel-write/SKILL.md`（写章六阶段 + 4 subagent + 断点续跑 + 变更面校验）
- `scripts/data_modules/override_ledger_service.py`（事件触发合同修订提案）
- `scripts/data_modules/story_system_engine.py`（Story System 合同树）
- `scripts/update_master_outline.py`（总纲写回脚本）
- `templates/output/设定集-力量体系.md` 等（v6 资产模板）
- `agents/context-agent.md`、`data-agent.md`、`reviewer.md`、`deconstruction-agent.md`（角色清单）

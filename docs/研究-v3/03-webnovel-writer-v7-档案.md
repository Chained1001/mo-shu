# webnovel-writer v7 研究档案

> 版本：1.0（2026-08-20 初版）
> 研究对象：lingfengQAQ/webnovel-writer（v6.2.0 及 v7.0.0-alpha 重写版）
> 材料快照：`otherMaterials/referProject/webnovel-writer-v7/`（git 仅 1 个 squash commit `fc9702d`，**无逐版本历史可考**，版本演进史依据文档自述 + 文物层对比，均标注）
> 路径约定：仓库根 = `otherMaterials/referProject/webnovel-writer-v7/`；`v7/` = v7 重写实现；`webnovel-writer/` = v6 旧版实现（同仓共存，文物层）。
> 修订说明：首版。8 层 22 维全覆盖尝试，P0 维度逐条给证据。

---

## 一、项目概况

| 项 | 内容 | 证据 |
|---|---|---|
| 定位 | 跑在 Claude Code 等多宿主 CLI 上的中文网文长篇创作系统，目标"200 万字不崩" | `v7/../docs/architecture/v7-prd.md:16` |
| 一句话哲学 | "AI 负责写和审，脚本负责数和记，作者只做三件事——确认细纲、审稿、拍创作决策" | v7-prd.md:16 |
| 形态 | v6：Claude Code 插件（8 skill 命令 + Python 脚本 + SQLite/RAG + Dashboard）；v7：npx 分发的工作目录布局（1 个 SKILL.md 单入口 + Node 脚本 + 纯 Markdown 书仓） | README.md:70-77；v7/package.json |
| 语言/运行时 | v6：Python 3.10+；v7：Node ≥22.13（内置 `node:sqlite` 做缓存），依赖仅 `js-yaml` | v7-prd.md:275；v7/package.json |
| 版本现状 | 仓库快照内 v7 为 `7.0.0-alpha`（M5 预发版号），spec 现行 0.21，PRD 1.7 | v7/package.json:4；story-repo-spec-2026-06-10.md:1；v7-prd.md:3 |
| 知识资产 | v7 通用知识库 286 条、十维（题材19/流派24/创意约束11/设定27/人物28/命名17/节拍63/场景37/技法49/追读11） | v7/references/README.md:37 |
| 测试 | v7 用 Node 内置 test runner，121 个 `.test.js`；v6 用 pytest | `find v7/test -name "*.test.js" | wc -l` = 121；根 pytest.ini |

### 版本演进史【P0】（据文档自述，无 git 逐提交佐证——快照为 squash）

v5.3 追读力系统 → v5.4 RAG/Marketplace → v5.5 长期记忆 + Dashboard → v6.0 **Story System 主链**（合同种子 + runtime contract + CHAPTER_COMMIT + 事件审计 + 投影到 state.json/index.db/vectors.db）→ v6.1 运行时加固（doctor/write-gate/projection 重放/hooks/behavior eval）→ v6.2 报告与断点续跑 → **v7 全面自我否定重写**（PRD 2026-06-12 起，RFC Discussion #118 征求意见，快照已推进到 7.0.0-alpha + spec 0.21）。证据：README.md:314-327（版本表）；CHANGELOG.md；v7-prd.md:3。

### v6→v7 自我否定的六大病根【P0】（v7-prd.md:20-31 + design-notes:11-22，两处互证）

| # | 病根 | issue 证据（文档自述，无法独立核验） |
|---|---|---|
| 1 | 用 prompt 驱动确定性状态机，模型不遵守（385 行写章流程规范） | #91/#66/#87/#76 |
| 2 | 派生状态（SQLite/投影）与作者手改冲突无解 | #100/#77/#63/#67/#70/#71/#89 |
| 3 | Token/时间失控（每章 3 subagent + 4 份 JSON + 多道 gate） | #58/#92/#106 |
| 4 | 安装门槛高（Python 依赖 + .env + RAG key） | #90/#103/#69 |
| 5 | 禁词表治不了 AI 味（朱雀检测 100%） | #94 |
| 6 | 连写缺失/质量漂移 | #79/#95/#74 |

**核心教训原文（宪法级）："v6 信任流程、不信任模型和作者；v7 信任 markdown 和作者，把流程压到最薄。"**（v7-prd.md:31）

归零清单：Story System、SQLite 双库、RAG/向量、Python runtime、8 个命令、Dashboard 常驻服务（v7-prd.md:36）。继承清单：37 题材模板（重写策展后为 19 题材+24 流派）、追读力知识、审查维度、踩坑记录（v7-prd.md:35；迁移映射 v7-prd.md:401-417）。

### 明确不做清单（封死，v7-prd.md:305-311）

RAG/向量库做事实召回主路径、常驻服务、敏感词/合规、AI 检测器承诺、大一统 YAML、事件级 witnesses 投影、自建提交链、模型自由评文笔、模型裸奔编纲、旧 schema 双读兼容、作者侧知识投稿/评分/自动扩库、固定路由替作者选创意、术语禁用词 CI。**与 mo-shu《实施总纲》附录 C 的"明确不做"高度同构——两个项目在相同地方踩过相同坑后得出相同结论（推断：各自独立收敛）。**

---

## 二、端到端流程【P0】

### 2.1 单入口状态机（v7 核心，v6 的 8 命令全部内化）

作者只说"继续"，跑 `next --json`，按序判定命中即停（v7-prd.md:209-223；实现 `v7/src/state-machine/index.js` 146 行 + `detectors.js` 224 行）：

| 序 | 条件 | 动作 |
|---|---|---|
| 前0 | git 健康检查（半提交/冲突/锁/损坏/网盘冲突副本 "(1).md"） | 自动修复或人话指引（`src/state-machine/git-health.js` 132 行） |
| 0 | 任一源文件解析失败 | 修复确认（AI 提议保留意图的修复，作者确认）——永不带堆栈崩溃 |
| 1 | 无书/当前书不存在 | 建书引导（问答→作品契约+总纲+卷纲+知识选择一次落盘 `persist-book`） |
| 2 | 跟踪面（`作品契约/定稿/大纲/文风/` + book.yaml）有未入账手改 | 提议补登 `relink`（系统适应作者，不报错） |
| 3 | 工作区有未完成流程 | 断点续跑（最深工件优先推断从哪继续，detectors.js:172-208） |
| 4 | 最新定稿章收卷且未复盘 | 卷复盘（同时复盘作品契约，只提修订候选） |
| 5 | 章号到体检周期 | 体检 |
| 6 | 其余 | 起草新章细纲 |

关键实现细节：跟踪面前缀常量 `TRACKED_SOURCE_PREFIXES = ['作品契约/','定稿/','大纲/','文风/']`（detectors.js:18），序2 手改检测 / relink 补登范围 / goto 回滚脏树拒绝**三处同源判定，防双写漂移**（detectors.js:16-17 决策 D6）。序3 断点续跑是"现存工件类型→续跑点"的纯函数映射（细纲→出示作者；材料→写稿；草稿→机检两审；审稿.md→等作者裁决；待定稿/→批次续跑），**状态即文件系统证据，无独立状态存储**。

### 2.2 写章八阶段（v7-prd.md:194-207；SKILL.md:32-45）

细纲（脚本出全书近况+AI 拟+章级知识每维≤3 候选）→ **作者确认细纲** → 备料 `prepare-chapter`（脚本组装"本章写作材料"，默认精准片段）→ 写稿（AI 干净上下文）→ 机检 `mechanical-check`（脚本零 token，只查可计数项）→ 两审（事实审查+编辑审，各自新鲜上下文）→ **作者审稿**（接受/改完接受/打回）→ 定稿 `finalize`（脚本原子 git commit，成功才清工作区）。

定稿原子性（v7-prd.md:205）："一次 git commit：正文入定稿、无冲突事实转正、计划对象删除、设定/时间线/名册更新、条目履历写入、章摘要入档；commit 成功后才清工作区。要么完成要么原样保留。"实现 `src/finalize/index.js`（428 行）+ `finalize/git.js`。

### 2.3 自动模式（连写）——控制上移而非放开

前提：卷纲已确认；批次默认 8 章；批内草稿与预入账数据攒工作区**不定稿**（`stage-chapter`），后章材料从"定稿+待定稿批次"叠加组装；停止条件：写满/体检不过线/卷纲耗尽/连续 3 章无账本变动（v7-prd.md:82-95）。停止后 `batch-status` 出全貌，作者四选：整批接受 `finalize-batch` / 改某几章 / 从第 K 章打回 `batch-reject` / 整批弃 `batch-discard`。错误污染上限=一个批次（SKILL.md:47-56）。**"全自动≠无控制，是控制上移到大纲层"**（design-notes:58）。

### 2.4 异常与降级【P0】

| 异常 | 处理 | 证据 |
|---|---|---|
| 源文件解析失败 | 序0 修复确认；全角标点结构性错误预修复只报不问 | v7-prd.md:216 |
| git 异常（含网盘冲突副本） | git-health 自动修 or 人话指引；作者永不直面 git 报错 | v7-prd.md:211；git-health.js |
| 作者手改真源 | 序2 提议补登，永不报错拒绝 | v7-prd.md:41 |
| 无 subagent 宿主 | 两审单上下文顺序自审，mode 标 `degraded`，如实声明降级 | SKILL.md:40-42 |
| 备料/审稿输入缺料 | 带 `degraded` 段先呈报作者确认再继续，禁止静默残缺写作/审稿 | SKILL.md:33,35 |
| 重试预算耗尽 | 机检自动修复≤2 轮、两审自动重审≤1 轮，超限交作者（`--author-confirmed` 单独记账不恢复额度） | v7-prd.md:241-243；`src/retry-policy/index.js`（580 行，fail-closed，记录损坏宁停勿猜） |
| 事实冲突/歧义 | 事实审查出 `options[]`（每项显式布尔 `applyChange`），作者裁决后原样保留字段重提，**禁止按编号/文案猜测** | roles/事实审查.md:31,39 |
| 中断续跑 | 序3 按工作区工件续 | detectors.js:172 |
| 回滚 | `goto-chapter` 先备份再回滚；脏树拒绝（与序2 同源） | SKILL.md:59 |

---

## 三、架构

### 3.1 分层【P0】

```
SKILL.md（单入口，12KB，条件编译 {{#if hasHooks/agentCapable}}）
 └─ CLI 命令层 src/commands/*（50+ 子命令，next/persist-*/prepare-chapter/mechanical-check/
    review-input/save-review/finalize/stage-*/batch-*/read-*/report-*/knowledge-*）
     └─ 领域模块 state-machine/prep/review/mechanical-check/finalize/staging/knowledge/
        retry-policy/health-check/style-stats/cache/migrate/export/storage/util
roles/ 事实审查.md、编辑审.md（两审任务书，AI 角色单源）
references/ 十维知识库（286 条，只读分发）
adapters/ 三宿主支持说明 + templates/AGENTS.md（工作目录指路块）
```

分工铁律："能数的交脚本，要判断的交两审"（SKILL.md:7）；AI 只吃整理好的 DTO，按提供的上下文工作，不自由读文件（SKILL.md:68）。所有 AI 产出走"先写 JSON 文件再 `--file`/`--payload` 提交"（SKILL.md:70），杜绝超长 argv 与命令注入。

### 3.2 数据/状态设计【P0】

- **真源哲学**：正文+摘要+条目 Markdown 即全部状态；`.cache/index.db`（node:sqlite）是唯一派生物，删了全量重建且是 CI 验收项（v7-prd.md:165,319）。这是对 v6"state.json/index.db/vectors.db 多路投影"的直接否定。
- **书仓四区**：`定稿/`（只进不改，git 跟踪）｜`大纲/`（作者意图，含伏笔/悬念/感情线三类账本每条一文件）｜`文风/`｜`工作区/`（不定稿的一切，默认不进 git）（v7-prd.md:125-166）。
- **版本常量与迁移**：`RETRY_POLICY_SCHEMA_VERSION = 1` 且记录损坏 fail-closed 不静默恢复（retry-policy/index.js:11）；v6→v7 用 `/migrate` 一次性脚本，源只读、失败自动回退、出人话迁移报告含"待校对"清单（SKILL.md:63；v7/docs/migration-guide.md）。明确不做旧路径双读/旧 schema 兼容（v7-prd.md:309）。
- **幂等**：同一草稿重复机检幂等不重复计数（v7-prd.md:242）；裁决重提用同一审稿输入令牌不算新两审轮次。
- **防呆方言**：系统写出的 YAML 一律平铺、块列表、危险值加引号；多条记录每条一文件（v7-prd.md:280）。防"AI 写 YAML 会出嵌套/锚点炸弹"。

### 3.3 检索/知识层【P0·重点】

v7 对 v6 RAG 的否定方案，四件套：

1. **精准读取接口**（宪法级）：每类数据文件配"只读所需一段"的脚本命令（`read-thread`/`read-character`/`read-timeline`/`read-chapter`/`grep-story`/`list-*`/`report-*` 等 20+ 个，见 src/commands/），AI 默认读片段不整读（v7-prd.md:225-236）。
2. **十维知识库**：三层十维（作品契约层：题材/流派/创意约束；故事对象层：设定/人物/命名；篇章执行层：节拍/场景/技法/追读）。每条三段式 `规划时/落笔时/审稿时` 切片——细纲阶段读"规划时"，备料只注入已选条目的"落笔时"切片，编辑审只注入"审稿时"切片（references/README.md）。**同一条知识按消费阶段切好片再喂，是上下文预算的核心手法。**
3. **候选制**：每维最多 3 条候选，可组合/变体/拒绝/自定义，"候选是材料不是固定答案"；近期选择史只软降权不硬禁（v7-prd.md:198,260）。`路由.csv` 只做名称归一，不决定创意。
4. **维度宪章治理**：每条知识必答三问（谁在什么阶段调用/解决什么问题/调用后什么可观察结果），唯一 canonical 归属，禁止复制到多目录（v7/docs/knowledge/维度宪章.md:9-31）。知识来源存证 `路径@sha256`，自定义标 `作者自定义`/`对谈共创`（SKILL.md:30）。
5. 细节召回兜底：Grep 正文——"正文本身就是无损数据库"（v7-prd.md:234）。

### 3.4 上下文预算与降级

分层摘要（章≤200字/卷≤500字/全书骨架按需拼接不落盘）；备料不回读通用书级条目；机检零 token；两审每章 AI 调用上限：完整模式 4 次（初审 2 + 自动整轮重审 2）、降级模式 2 次（v7-prd.md:277）。Codex skill 列表 8k 字符预算→description 精简纪律+validator 检查（v7-prd.md:360）。

---

## 四、智能体层

### 4.1 职责切分

v6 四 agent（context/data/reviewer/deconstruction，`webnovel-writer/agents/`）→ v7 砍到 **2 个角色任务书**：事实审查（可验证问题清单+factChanges 结构化提案）、编辑审（结构/节奏/商业性/作品契约）。写稿与两审强制不同上下文（写评分离，"自己审自己会自我辩护"，design-notes:79）。subagent 只做增强不做依赖，无 subagent 宿主走兼容模式（design-notes:67）。

### 4.2 Prompt 工程【P0】

- **角色任务书即 prompt**（`roles/事实审查.md` 3.6KB / `编辑审.md` 2KB）：输入=脚本绑定好的 ReviewInput（含草稿全文+要写到的事+全书近况+契约+相关角色状态+条目含履历+时间线片段+信息差候选+计划对象+批内待转正事实）；输出=严格 JSON 无其他文本；维度受控枚举（9 个 category）；severity 枚举，critical 自动 blocking，`unregistered_thread` 恒不 blocking（候选制——**机检/审查发现的"疑似伏笔"永不拦截流程，只出候选交作者**）。
- **令牌防伪**：审稿输入带"审稿输入令牌"，两份报告必须逐字原样回传且外层令牌相等（SKILL.md:43-44）——廉价防"subagent 没读输入就编报告"。
- **AI 裁决边界**：事实审查"只报可验证问题，评事实不评文笔"；冲突歧义"如实写 decision，不能替作者裁决"；`applyChange` 显式布尔防猜测（roles/事实审查.md:38-41）。
- **写前反制和解倾向**：AI 对齐训练的和解倾向对网文是毒药，写作 prompt 前置反制、按题材配浓度（design-notes:46）。宽恕合法性交给作品契约"冲突与关系结算原则"裁决而非题材默认档位（v7-prd.md:258）。
- **AI 味分层**：禁词表只够第一层；主力=句式体检脚本（句长方差/段落分布/高频开头，`src/style-stats/`）+ 高频意象统计（零 token）+ 文风锚定 few-shot（7.x）；诚实边界="读者不出戏"不承诺过检测器（design-notes:50-54；v7-prd.md:261）。

---

## 五、技能层【本项目重点】

| 维度 | v6 | v7 |
|---|---|---|
| 入口 | 8 个 skill 命令（init/plan/write/review/query/learn/dashboard/doctor），`webnovel-writer/skills/` | **1 个 SKILL.md 单入口**（"说继续/写下一章/建书/回到第N章/吃书即进状态机"），v7/skills/webnovel-writer/SKILL.md |
| 厚度 | write 流程 385 行规范（病根之一） | SKILL.md 全文 71 行/12KB，**流程知识压进脚本 DTO 返回值**，skill 只写"按返回的序/DTO 执行" |
| description | 各自描述 | 单条精简（Codex 8k 预算），动词化中文触发词 |
| 模板编译 | 无（Claude 专属插件） | `{{#if hasHooks}}`/`{{#if agentCapable}}` 条件块，安装时由 host-shells 生成器定稿，不靠运行时判断（design-notes:73；src/host-shells/generate.js+validator.js drift check） |
| 铁律 | 分散 | SKILL.md 尾部 5 条铁律集中（事实只经定稿入 git / 能数交脚本 / 只吃 DTO / 通用库只读 / JSON 先落文件） |

**薄厚哲学**：skill 是"路由+裁决礼仪"，确定性全在脚本，语义判断全在 roles 任务书。skill 变薄不是删功能，是**把"模型该做什么"从自然语言流程改成机器 DTO 指令**（next --json 返回序号+DTO+message）。

---

## 六、工程层

### 6.1 确定性纪律【P0】

机检十项（`src/mechanical-check/index.js:18-50`）：字数/禁词/禁句式/复读/**新专名比名册（候选）**/front matter 格式/信息差关键词（候选）/条目声明形式/**高频意象（候选，消费体检缓存，机检不做全书扫描）**/**句式偏离（候选，vs 配置区间文体基线指纹）**。拦截项与候选项严格分离——issues 阻断、candidates 只呈报。文体基线：`文体基线起..止` 闭区间完整定稿后才建立，章段不随新章扩大（防基线漂移，v7-prd.md:240）。

### 6.2 质量保障与测试文化【P0】

121 个 Node 内置 test runner 测试，目录按领域镜像 src（commands/state-machine/integration/mechanical-check/...），含：中文路径全链路集成测试（`test/integration/chinese-path.test.js`）、CLI 主循环、git 健康、自动模式、finalize 守卫、事实裁决工作流、行为级 `batch-review-workflow.test.js`。另有 `scripts/pack-install-e2e.mjs`（打包安装 e2e）、host-shells validator drift check。spec 声称"删光 .cache 全量重建"是 CI 验收项（v7-prd.md:319，快照内未见 CI workflow 目录——**文档宣称，待验证**）。发布判据硬编码：beta=真实写一本书到 50 章；7.0.0=/migrate 在≥3 个真实 v6 项目跑通（v7-prd.md:314-321）。

### 6.3 部署分发

放弃 Claude Code 插件市场（v6 渠道），改 npx：`npx webnovel-writer init` 生成工作目录（AGENTS.md 指路块 + `.webnovel/` 本体 + books.jsonl 书单 + 各平台壳）；强制项目级安装（目录结构全网统一→可诊断）；`update` 用模板哈希清单：用户没改过的直接更新、改过的提示（Trellis 模式，v7-prd.md:115-117）。多宿主：SKILL.md 开放标准零适配拷目录即用；角色单源 markdown 构建时生成三平台壳 + drift check；hook（SessionStart）只是 Claude 上的增强，关键能力不依赖 hook（v7-prd.md:281；SKILL.md:11-17）。

### 6.4 安全/权限

alpha 不装 PreToolUse hook（#113 教训：hook 只能 ask 不能 deny）；书目录 AGENTS.md 指路防误启动；书仓 `.gitignore` 默认排除工作区与导出。

---

## 七、治理层【P0】

- **文档先行且分宪法层级**：PRD（产品法律文本）→ story-repo-spec（格式规格，0.5→0.21 持续演进，含"设计不变量（法律条款）"§1 与"防呆方言"§2.3）→ multi-agent-adaptation-spec（多宿主适配）→ 知识维度宪章/策展规则/调用者与字段矩阵。PRD §10 逐条记录"对旧 spec 的下行修订指令"——**spec 修订有审计链**。
- **决策留痕**：PRD 头部状态行记录每轮决策（如 1.7：文体基线完整区间后冻结、机检两轮、alpha 延后 PreToolUse）；20 条 ADR 存 `.trellis/tasks/`；RFC 公开发 Discussion 征求意见≥1 周 + 反馈合并报告（v7-rfc-feedback-report-2026-06-16.md）——**RFC 反馈直接改设计**（如批次叠加一致性规则、Node patch 下限、履历结构化锚点三项实施前修正）。
- **术语表即法律**（v7-prd.md:324-347）：作者界面词汇四原则——网文圈原生词优先/没有的用大白话/**财务工程数据库隐喻禁止**/不自造两字精简词。逐条映射旧词→新词（盘面→全书近况、上下文包→本章写作材料、棘轮→删除该比喻）。“账本”一词只许开发文档用。机器协议（commit 前缀/book.yaml/表名）属机器域作者不见。
- **版本治理**：v6 留 master 只修致命 bug；v7 新 major + 一次性迁移；无双读兼容。

---

## 八、交互层

- **作者裁决点**（仅 2+2 个）：确认细纲、审稿（逐章或按批次）+ 卷复盘确认、作品契约修订确认。控制滑杆两开关（自动确认细纲/连写批次大小）一套实现（v7-prd.md:264）。
- **体验底线**：全程看不到 git、报错堆栈、英文术语；书的核心内容只在五个中文目录（v7-prd.md:68）。
- **日常开卷报全书近况**（写到哪/伏笔悬了太久/连续几章钩子弱）→"继续"或自然语言改稿指令（v7-prd.md:62-63）。
- **章节资产**：`定稿/正文/0152-北境的雪.md`，正文+front matter 自包含档案（章号/标题/卷/字数/章定位/钩子类型与强弱/情绪定位/知识选择）；干净导出去 front matter 落工作区/导出/。
- **改稿三档**：未发布直接改+自动重入账；已发布只读出"顺势圆"方案；设定/大纲改动跑影响分析出已发布/未发布两清单（design-notes:30）。

---

## 九、可借鉴清单（mo-shu 落点）

### 低成本（直接抄思想或小机制）

1. **单入口状态机 + DTO 返回**：`next --json` 返回"序号+state+needsAI+message+DTO"，skill 层只写"按序执行"。mo-shu 已有 9 序状态机（AGENTS.md §2.6），可借鉴的是**把流程指令从 skill 正文移进脚本 DTO**，让 skill 恒薄。源：v7/src/state-machine/index.js、v7/src/commands/next.js。
2. **三处同源常量防双写**：手改检测/补登范围/回滚拒绝共用 `TRACKED_SOURCE_PREFIXES`（detectors.js:16-23）。mo-shu 任何"检测面"机制应同样收敛到单一常量。
3. **候选永不拦截**：机检 candidates 与 issues 分离；`unregistered_thread` 恒 blocking=false。mo-shu 机检/审查类脚本应显式分这两列。
4. **审稿输入令牌**：subagent 报告必须逐字回传输入令牌，外层校验相等。零成本防编造，mo-shu 多 agent 流程可即用。源：SKILL.md:43-44、roles/事实审查.md:29。
5. **知识条目三段切片**（规划时/落笔时/审稿时）：mo-shu references 体系若出现"一条知识多阶段消费"，切片比整条注入省 token 且防串味。源：references/README.md。
6. **知识来源存证**：`来源：路径@sha256` / `作者自定义` / `对谈共创` 三值枚举，杜绝"知识来历不明"。源：SKILL.md:30。
7. **维度宪章三问**：谁在什么阶段调用/解决什么问题/调用后什么可观察结果，答不上不准入库。mo-shu references 治理可直接采用。源：v7/docs/knowledge/维度宪章.md:9-14。
8. **AI 产出先落文件再 `--file` 提交**：所有 JSON 载荷走文件，不进 argv。源：SKILL.md:70。
9. **术语表即法律 + 机器域/作者域分离**：v7-prd.md §8 整表。mo-shu 写作 skill 的作者界面词汇同样值得立表禁隐喻。
10. **机检消费体检缓存**：高频意象/文体基线由体检（周期性）产出、机检（每章）只消费，每章零全书扫描。源：mechanical-check/index.js:15-17。

### 中成本

11. **重试预算按章持久化 + fail-closed**：`工作区/重试预算.json`，schemaVersion、自动/作者两路由分开记账、损坏宁停勿猜。mo-shu 的 LLM 调用预算管理可整体移植。源：src/retry-policy/index.js（580 行，实现质量高）。
12. **断点续跑=工作区工件映射**：无独立状态存储，"现存什么文件→从哪继续"纯函数。mo-shu 写作流程可照此把中断恢复做成只读推断。源：detectors.js:172-213。
13. **信息差登记表**（每条一文件：知情人/读者已知/关键词）+ 机检关键词出候选 + 写作材料注入人物知识边界 + 事实审查判真伪。中文网文"装逼打脸=信息差兑现"的独特建模，mo-shu 强相关。源：story-repo-spec §4.3、v7-prd.md #3。
14. **三类账本统一引擎**（伏笔/悬念/感情线，每条一文件+front matter+履历+"悬了太久"分级阈值），且明确"不进账本的"清单（钩子→章属性、剧情线→卷纲正文、冲突→不设类）。mo-shu 若做伏笔追踪，这份正反清单都是现成答案。源：v7-prd.md:172-192。
15. **计划对象→事实转正生命周期**：设定先入 `大纲/创作设计/`（计划），正文首次定稿才转事实，冲突交作者裁决且选项显式 `applyChange` 布尔。源：v7-prd.md #1、roles/事实审查.md:31。
16. **批次暂存连写**：stage-chapter 叠加"定稿+待定稿批次"视图、错误污染上限一个批次、四选批次处置命令族。mo-shu 若做连写，这是现成安全设计。源：SKILL.md:47-56、src/staging/。
17. **防呆 YAML 方言**：平铺/块列表/危险值加引号/多条每条一文件。mo-shu 所有系统写出的 front matter 应立同样规范。源：v7-prd.md:280、spec §2.3。
18. **两审分工 + 降级诚实**：事实审查（可验证、结构化、不评文笔）与编辑审（品味、契约、商业性）分任务书；无 subagent 顺序自审标 degraded；degraded 输入区"视为无法核实而非确认无问题"（roles/事实审查.md:10）。mo-shu 写/审分离的成熟模板。

### 高成本（需 mo-shu 先修总纲再做）

19. **精准读取命令族**（20+ read-*/list-*/report-* 脚本）：每类数据文件配片段级读取接口。这是 v7 治 v6 token 失控的根治手段，但要求 CLI 覆盖全部数据形态——mo-shu 当前 bash/python 脚本体系需大改。
20. **多宿主角色单源 + 构建期壳生成 + drift check**：源：src/host-shells/。mo-shu 目前单宿主，不必做。
21. **npx 工作目录安装器 + 模板哈希 update**：分发形态变更，mo-shu 未到该阶段。

---

## 十、不可借鉴清单

| 项 | 理由 |
|---|---|
| "文件即真相"重构为 v7 式纯 Markdown 书仓 | mo-shu《实施总纲》附录 C 已显式不做"文件即真相"重构；且 mo-shu skill 是创作方法论层，不接管作者书仓 git。v7 自己也为此付出整个 v7 重写代价。 |
| 每书一 git 仓库 + git 隐身全套 | mo-shu 是 skill 集不是运行时产品，无书仓管辖权。 |
| 自建状态机接管全部入口 | mo-shu 各 skill 有独立流程，单入口状态机是"运行时产品"形态；mo-shu 的 9 序状态机哲学（只吃文件系统证据）已经够用且方向一致。 |
| RAG/向量（v6 路线） | 双重不可借鉴：v7 已证伪（BM25 兜底体验无损复杂度全卸，design-notes:26）；mo-shu 附录 C 亦显式不做。 |
| Dashboard/常驻服务、npx 分发 | 两版（v6 建、v7 删）都说明是产品化负担；mo-shu 是技能集。 |
| PreToolUse hook 门禁 | v7 明确 "#113 教训：hook 只能 ask 不能 deny"，alpha 干脆不装。mo-shu 任何 hook 设计同守此界。 |
| 8 命令→1 命令的极端收敛 | v7 是面向小白作者的产品决策；mo-shu 用户是技能使用者，多 skill 分域入口（现形态）更合理。 |
| 兼容模式单上下文两审 | （推断）v7 是为弱宿主不得已；mo-shu 主宿主有 subagent，不必引入降级复杂度。 |

---

## 十一、差异定位

| 维度 | webnovel-writer v7 | mo-shu |
|---|---|---|
| 形态 | 运行时产品（安装器+CLI+书仓格式规格） | 技能集（SKILL + 模板 + 确定性脚本） |
| 对象 | 零基础网文作者（非工程师） | 使用 Claude Code 写网文的作者（技能消费者） |
| 真源 | 书仓 Markdown（产品托管） | 作者自己项目 + mo-shu 流程状态文件 |
| 知识 | 十维通用知识库（产品策展、只读分发） | references 体系（写作方法论知识） |
| 状态机 | next 单入口 7 序（含建书） | 9 序写作状态机（吃文件系统证据） |
| 共同点 | 脚本/AI 分界、候选不拦截、作者裁决点、禁 RAG、禁模型裸奔编纲、防呆 front matter、fail-closed | 二者趋同，互为佐证 |

---

## 十二、待验证问题

1. ~~v7 是否真有"删光 .cache 全量重建"CI？~~ 已核验：根仓 `.github/workflows/v7-ci.yml` 存在，含 ubuntu+windows 双矩阵、"单元测试（含中文路径用例）"与"安装链路端到端（npm pack → 中文路径 init → 建书 → next → update）"步骤；PRD 所称"删光 .cache 全量重建"具体步骤名未在 grep 中出现，推断并入测试用例（`v7/test/cache/rebuilder.test.js` 存在），标"部分核验"。
2. RFC 反馈三项修正（批次叠加一致性规则/Node patch 下限/履历结构化锚点）是否已落进 spec 0.21？（spec 头部标 0.21，未逐节核对）。
3. 286 条知识基线数字：references/README.md:37 自述，逐目录实测为题材19/流派24/创意约束11/设定27/人物28/命名17/节拍63/场景37/技法49/追读11，合计=286，**核验一致**（find 计数）。
4. v6 behavior eval（`webnovel-writer/agents/evals/`）的具体形态——对 mo-shu 的测试文化或有借鉴，本次未深入。
5. 121 测试是否全绿：未运行（只读纪律），仅计数。

---

## 十三、错误清单（陷阱与本案自警）

1. **同名机制两版含义不同（本项目最大陷阱）**：`大纲/` 在 v6 是总纲卷纲混放、v7 是作者意图区含三类账本；"references" 在 v6 是题材模板、v7 是十维知识库；`工作区/` v7 新增。凡引用本项目概念必须先标 v6/v7。
2. **v6→v7 否定原因不能简化为"技术升级"**：六病根里 5 个是**产品/交互层**（安装门槛、手改冲突、token 成本、作者确认点缺失、连写缺失），只有 RAG 属技术选型。v7 的答案也主要在产品层（单入口、批次定稿、术语表、git 隐身）——**mo-shu 借鉴时应学产品层答案而非只学 Node/SQLite 细节**。
3. **"朱雀 100%"类实测数字**：仅 issue #94 文档自述，无复现路径——按本案纪律标"文档宣称"。
4. **git 考古受限**：快照为单 squash commit，所有版本演进叙述均来自文档自述（README 版本表/CHANGELOG/PRD 状态行），好在 PRD/spec 的修订指令链（§10、RFC 反馈报告）本身是高质量的一手决策记录，可信度高于一般 README。
5. **PRD 自身承认的历史口径漂移**：PRD §10 明言"三审等旧口径已由后续决策替代"、"当时曾要求连写批次与体检周期同值，现行已改"（v7-prd.md:373,380）——引用 v7-prd 任何条款必须以头部状态行的最新决策为准，旧节仅是历史。
6. **Codex 8k 字符预算**：design-notes:72 自述（2026-06 核验），未独立复核，标"文档宣称"。

---

## 十四、22 维覆盖自评表

| # | 维度 | 层 | 覆盖 | 关键证据节 |
|---|---|---|---|---|
| 1 | 定位与边界 | 产品 | ✅ | §一 |
| 2 | 版本演进史【P0】 | 产品 | ✅（文档自述为主，git 受限已标） | §一 |
| 3 | 不做清单 | 产品 | ✅ | §一 |
| 4 | 端到端流程【P0】 | 流程 | ✅ | §2.1-2.3 |
| 5 | 状态机/事务 | 流程 | ✅ | §2.1、§3.2 |
| 6 | 异常与降级【P0】 | 流程 | ✅ | §2.4 |
| 7 | 分层与模块边界 | 架构 | ✅ | §3.1 |
| 8 | 数据/状态设计【P0】 | 架构 | ✅ | §3.2 |
| 9 | 检索/知识层 | 架构 | ✅ | §3.3 |
| 10 | 职责切分 | 智能体 | ✅ | §4.1 |
| 11 | agent 设置 | 智能体 | ✅ | §4.1 |
| 12 | Prompt 工程【P0】 | 智能体 | ✅ | §4.2 |
| 13 | 多 agent 编排 | 智能体 | ✅（subagent 增强+降级） | §4.1 |
| 14 | Skill 薄厚哲学【重点】 | 技能 | ✅ | §五 |
| 15 | 确定性纪律 | 工程 | ✅ | §6.1 |
| 16 | 防呆与自愈 | 工程 | ✅ | §2.4、§6.1 |
| 17 | 质量保障与测试【P0】 | 工程 | ✅ | §6.2 |
| 18 | token/上下文预算 | 工程 | ✅ | §3.4 |
| 19 | 安全权限 | 工程 | ✅（简） | §6.4 |
| 20 | 部署分发 | 工程 | ✅ | §6.3 |
| 21 | 治理宪法【P0】 | 治理 | ✅ | §七 |
| 22 | 交互层（裁决点/续写/资产形态） | 交互 | ✅ | §八 |

覆盖：22/22（其中"版本演进史"受 git squash 限制降级为文档自述级证据，已在错误清单 #4 声明）。

# 规格 · 批 B76：build 拆分——moshu-outline + moshu-volume + 统一创作流程模板入宪

- 版本：v1.1（2026-08-29 旗舰修订。v1.0 八处问题：①子步误号 80a-d→76a-d ②漏 `skills/moshu-build/scripts/` 5 脚本迁移 ③漏 `.claude-plugin/marketplace.json` build 条目替换 ④漏 current-contract/behavior-contracts 两契约面 ⑤共享副本迁移机制错误（27 md+32 题材卡源在 write、build 是副本——不应 git mv 副本、不应反转源）⑥下游批次号交叉引用过时（evaluator 新型是 B77 非 B81；方法论萃取是 B78-B80；采风融合是 B81）⑦原则计数错（「第 10 条」→第 7 条）⑧注册表更新错排在 80d（子步中间态红）。v1.1 全部修正 + 补挂盲区对照节。）
- 性质：**全仓最大架构重构**——拆一个技能为两个、统一流程模板入宪、审查缺口标注。分**四个子步**执行。
- **目的**：解决 build 193K/36 项的结构性臃肿（开书与卷规划两类语义不同的工作挤一个技能）；统一创作技能内部流程为五步模板（FULL/LIGHT 两档）；审查覆盖按技能独立设计——**每个产物的写-审配对可逐一对账**。

## 设计说明（盲区对照，2026-08-28 清单 §1 逐项）

| # | 项 | 结果 |
|---|---|---|
| 1 目的声明 | 见版本行「目的」 | 通过 |
| 2 预算实测 | doc-budget 口径=node 非空白 UTF-16：workflow-build 现 18900/18900（余量≈0）、revision-workflow 3100、build SKILL 1800；AGENTS.md 裸长 9315→约 9850（<11000 阈值）。重写与新增的预算锁定值见 §七-8 | 通过 |
| 3 涟漪面含 .json | 已全量 grep：shared-assets/spawn-contracts/capability-wiring/current-contract/behavior-contracts/doc-budget/**marketplace.json** 六注册表 + evals 场景 + 根 README×2 + CONTRIBUTING，全部列入改动清单 | 通过（v1.0 漏 marketplace 与两契约） |
| 4 共享副本 | §三-2 专节：源全在 write，只改 targets，不 git mv 副本、不反转源 | 通过（v1.0 机制错误已纠正） |
| 5 跨技能接口 | §四读写面声明 + current-contract 重写（新增 outline→volume/write 生产者契约）；volume 只读 追踪/上下文.md 不变 | 通过 |
| 6 存量兼容 | 无存量书项目在仓（书项目在用户侧，文件结构不变——拆分只改技能侧路径）；书项目内无任何路径指向 skills/ 目录，**无存量影响** | 通过 |
| 7 端到端走查 | §七-9：人工走查清单（开书意图→outline→volume→write 四段路由） | 通过（v1.0 缺） |
| 8 幂等性 | 纯文件迁移与文本编辑，无时间戳工件 | 不适用 |
| 9 验收可复现 | 全部为本地 grep/守卫/node 命令，Windows python 探测链按 README §7 | 通过 |
| 10 热路径字数 | AGENTS.md 9315→约 9850（+~540，模板原则块）；两新 SKILL.md 预算=实测×1.05；volume-workflow 重写预算锁定不超现值 | 通过 |
| 11 token 成本 | 拆分本身降热路径（开书会话不再加载卷规划内容）；无新 agent、无新 spawn | 通过 |
| 12 决策树 | 不新增机制文件；两新技能是拆分产物非平行管线；挂现有收口（shared-assets/契约/守卫） | 通过 |

## 一、统一创作流程模板（入宪法 §9，新增第 7 条原则）

现有 §9 原则 6 条（兼容四原则/证据溯源/三层分工/苏格拉底三要素/功能模仿/接口单一真源），本批加第 7 条：

```
统一创作流程模板（B76 入宪，所有创作技能共享骨架）

FULL 模式（书级/卷级——moshu-outline 与 moshu-volume 默认）：
  Phase 1 PREPARE——「先想清」
    读上游产物（文件即接口）/ 采风触发 / 点名装配 / [可选]探索稿
  Phase 2 DRAFT——「先动笔」
    创作模式（禁自我评判）/ 落盘 / 完成即停
  Phase 3 REVIEW——「先挑剔」
    独立评审（evaluator，只呈报不拦截）/ 机检 / 采风复核
  Phase 4 POLISH——「再回头」
    按评审修改 / 一次修一维 / REVIEW⇄POLISH 循环
  Phase 5 COMMIT——「定稿」
    作者确认 / 状态更新 / 追踪记录

LIGHT 模式（章级日更——moshu-write 默认）：
  PREPARE（轻量：点名清单即可）→ DRAFT（快写）→ REVIEW（机检为主）→ POLISH（三遍法第2/3遍）→ COMMIT（D段事务）
```

## 二、产物归属映射

### moshu-outline（故事架构技能——Stage 1-3）

| 归属 | 文件/目录 | 原属 |
|---|---|---|
| **产出** | 设定/题材定位.md、关系.md、题材正文提示卡.md、理想书评.md、角色/*.md、势力/*.md、世界观/*.md | build Stage 1-3 |
| **产出** | 大纲/大纲.md（全书卷级鸟瞰+每卷骨架表） | build Stage 2 |
| **读** | 拆文库/{书}/概要.md、角色卡（对话 DNA 带入） | analyze 产物 |
| **读** | 自有 references：genre-catalog、genre-core-mechanics、character-design-methods、character-relations 等 | — |
| **读** | 题材卡文风样张按需跨技能只读 `moshu-volume/references/genre-prose-cards/`（文件即接口） | volume 副本 |

### moshu-volume（卷规划技能——Stage 4-6 + 开新卷 + 修订流 + 采风）

| 归属 | 文件/目录 | 原属 |
|---|---|---|
| **产出** | 大纲/卷纲_第X卷.md（含单元卡+情绪弧线+伏笔表+反转+线索矩阵+事件关系边） | build Stage 4-5 |
| **产出** | 大纲/场景表_单元{ID}.md（B68） | build Stage 4 |
| **产出** | 大纲/变更日志.md（修订留痕） | build 修订流 |
| **产出** | 设定/采风-CF*.md、虚拟对标.md | build 采风 |
| **产出** | 构建台账（ledger） | build |
| **执行** | 修订流五步（impact_scan/裁决/留痕/stale级联/回流） | build 修订流 |
| **执行** | 开新卷增量（cold-path Stage 4-6） | build cold-path |
| **执行** | 防撞对照（B65） | build |
| **执行** | 采风（五类+融合四步） | build |
| **读** | outline 产的设定+大纲.md | 跨技能文件读 |
| **读** | 拆文库/{书}/剧情/*.md、节奏.md、情绪模块.md | analyze 产物 |
| **读** | 追踪/上下文.md（消费侧只读） | write 产物 |

### moshu-write（不拆，归属确认不变）

| 归属 | 文件/目录 |
|---|---|
| **产出** | 大纲/细纲_第*.md、大纲/写作浮现.md、大纲/完结宣告.md |
| **产出** | 正文/*.md |
| **产出** | 追踪/（via tracking_commit） |
| **执行** | 细纲批次/日更/审查/卷复盘/完结章 |

## 三、references 与 scripts 迁移（36 项 = 35 个 md + 1 个题材卡目录）

### 1. build 独有文件（8 个，git mv 物理迁移）

| 文件 | 去向 |
|---|---|
| core-setting-template.md | moshu-outline/references/ |
| ideal-review-template.md | moshu-outline/references/ |
| caifeng-methods.md | moshu-volume/references/ |
| cold-path.md | moshu-volume/references/ |
| ledger-template.md | moshu-volume/references/ |
| revision-workflow.md | moshu-volume/references/ |
| virtual-benchmark-template.md | moshu-volume/references/ |
| workflow-build.md | moshu-volume/references/ 并**重命名 volume-workflow.md** |

### 2. 共享副本（27 个 md + genre-prose-cards 目录 32 张卡）——**源全在 moshu-write，禁止 git mv 副本、禁止反转源**

实测 shared-assets.json：这些文件 `src` 均为 `skills/moshu-write/references/…`，build 侧是同步副本。迁移机制 = **只改各组 targets 里的 build 路径为新技能路径，删除 build 侧旧副本，跑 `sync-shared-assets.py sync` 物化新副本，`check-shared-files.sh` 绿**。各文件新 target 按下表分配：

- **targets 改指 `skills/moshu-outline/references/`**（8 组）：character-basics、character-design-methods、character-relations、genre-core-mechanics、genre-catalog、plot-frameworks、reader-contract-and-progression、idea-seed
- **targets 改指 `skills/moshu-volume/references/`**（18 个 md 组 + 32 张卡各一组）：beat-cards、emotional-arc-design、emotional-methods、genre-prose-cards.md、genre-prose-cards/ 下 32 张卡、genre-readers、genre-writing-formulas、naming-cards、opening-design、outline-conflict、outline-methods、outline-rhythm、outline-structure-theory、outline-workflow、plot-core-methods、plot-emotion-system、plot-special-topics、reversal-toolkit、style-genre-modules
- **tracking-transaction.md 与 tracking_commit.py、pace_meter.py**：src 不动（write），build target 改 volume target

### 3. scripts 迁移（build/scripts/ 5 文件 + __pycache__ 删除）

| 脚本 | 去向 | 机制 |
|---|---|---|
| check_outline.py | moshu-outline/scripts/ | git mv（大纲结构校验，outline 产物守卫） |
| design_fingerprints.py | moshu-volume/scripts/ | git mv（修订流） |
| impact_scan.py | moshu-volume/scripts/ | git mv（修订流） |
| pace_meter.py | write 源不动 | shared-assets target build→volume |
| tracking_commit.py | write 源不动 | shared-assets target build→volume |
| __pycache__/ | 删除 | 不入库产物 |

迁后 grep `check_outline\|design_fingerprints\|impact_scan` 于 scripts/README.md、.github/workflows/、CONTRIBUTING.md，有路径引用则同步更新（实测当前无，防御性步骤）。

## 四、路由·状态机·注册表变更

### 新建两个 SKILL.md

**moshu-outline/SKILL.md**（薄壳原则同 build 现 SKILL 1784 字，流程在 references）：
```
name: moshu-outline
description: 故事架构技能——开书的故事层设计（题材定位/世界观/人物/全书大纲）。
触发：/moshu-outline、开书、设计故事、搭大纲、建世界观、人物设计。
产出设定/ 和 大纲/大纲.md。卷纲和细纲归 moshu-volume/moshu-write。

设定读写面——创建：设定/题材定位.md、关系.md、题材正文提示卡.md、角色/*.md、势力/*.md、世界观/*.md
设定读面——读取：拆文库/{书}/概要.md、角色卡（对话 DNA 带入）；题材卡文风样张按需读 volume 侧 genre-prose-cards/
采风触发面——结构采风（Stage 2）/角色采风（Stage 3）/机制采风（设定面）
```

**moshu-volume/SKILL.md**：
```
name: moshu-volume
description: 卷规划技能——每卷的单元卡/场景表/卷纲产出与修订、开新卷规划、采风、防撞。
触发：/moshu-volume、卷纲、开新卷、单元卡、修订设定、改大纲、采风。
读 moshu-outline 的设定与大纲，产出卷纲层文件。

设定读写面——修订：设定/*（修订流 impact_scan 影响分析后修改）
设定读面——读取：设定/（全部，单元卡消费）、大纲/大纲.md（骨架表）
采风触发面——情节采风（Stage 4）/情绪采风（Stage 5）/机制采风（应用层）/融合（researcher agent fusion 模式）
```

### moshu 路由 SKILL.md（实测 3 处）

- :14 意图行「开书/建设定」拆两行：开书/世界观/人物/大纲→`/moshu-outline`；卷纲/开新卷/单元卡/修订设定/采风→`/moshu-volume`
- :50 S3 行「设定/卷纲缺失才回 /moshu-build」→「设定缺失回 /moshu-outline；卷纲缺失回 /moshu-volume」
- :53 S6 行「下卷规划转 /moshu-build」→「下卷规划转 /moshu-volume」

### next_step.py（实测 3 处）

- :140-141 S2 建议：`/moshu-build 开书` → `/moshu-outline 开书（故事层）→ /moshu-volume（首卷）`，suggested_skill 改 moshu-outline
- :166 S3 行「设定/卷纲缺失才回 /moshu-build」→ 按上面口径分流
- :271-272 S6 建议：`/moshu-build` → `/moshu-volume`，suggested_skill 改 moshu-volume
- 对应 test-next-step 断言更新

### `.claude-plugin/marketplace.json`（v1.0 漏项）

- `plugins[]` 中 `moshu-build` 条目（version 1.3.0）**删除**，新增 `moshu-outline`（version 1.0.0，description/keywords 按 SKILL.md：开书/设定/大纲/worldbuilding/outline）与 `moshu-volume`（version 1.0.0：卷纲/开新卷/单元卡/修订/采风/volume）两条，`skills` 指向各自目录
- 根 `metadata.version` 2.4.0 **不动**（发版批才动）

### 契约三件 + capability-wiring（与文件移动同子步）

- `scripts/current-contract.json`：producer/consumer 为 moshu-build 的两块（:46-57、:76-86）改写——workflow-build/ledger-template/caifeng-methods 路径改 volume 侧；**新增**一条：producer `moshu-outline`、consumers `[moshu-volume, moshu-write]`、涉及 `大纲/大纲.md` 与 `设定/*`（文件即接口的生产者声明）
- `scripts/behavior-contracts.json`：:73 revision-workflow 路径改 volume 侧
- `scripts/capability-wiring.json`：3 处 build 路径（SKILL/revision-workflow/workflow-build→volume-workflow）更新
- `scripts/spawn-contracts.json`：4 个 caller 路径更新（cold-path/outline-workflow/revision-workflow/workflow-build→volume 侧新路径）

### 追踪系统归属确认

| 操作 | 拆分后归属 | 变化 |
|---|---|---|
| tracking init | volume Stage 6 末尾 | 调用者从 build 改为 volume |
| commit/check/report | write（不变） | 无 |
| pace_meter | write 源 + write/volume 双消费 | shared-assets target 更新 |
| impact_scan + design_fingerprints | volume 修订流 | git mv 至 volume/scripts |
| tracking_commit.py 副本 | 原 build 副本→volume | shared-assets target 更新 |

**不需要新建设定管理 agent**——三权分立已清晰（outline 创建 / write 增量 / volume 修订），一致性由追踪系统+修订流覆盖，查询通过文件即接口。采风的跨技能特性由 researcher agent 天然解决（agent 不属于任何技能）。

### 文档叙述面

- 根 README.md、README_EN.md、CONTRIBUTING.md 中 moshu-build 提及（技能清单/示例命令）→ outline/volume 双技能口径
- `evals/scenarios/开书/README.md` 路径与命令更新
- PRD（FSD）：分层架构图 build 拆两节点、能力全景 11→12 技能、用户旅程/文件走查中 build 段拆分（architecture.md 已被 PRD 吸收，**不存在独立 architecture.md**——v1.0 此项过时）

## 五、审查覆盖标注（每个产物的写-审配对；新型本批只标注，B77 实施）

### moshu-outline

| 产物 | 审查 | 状态 |
|---|---|---|
| 大纲骨架 | evaluator: outline | ✅ 已有 |
| 人物设计 | evaluator: character | ❌ 新增（B77） |
| 世界观/设定包 | evaluator: settings | ✅ 已有（B69） |

### moshu-volume

| 产物 | 审查 | 状态 |
|---|---|---|
| 单元卡 | evaluator: unit | ✅ 已有 |
| 场景表 | evaluator: scene | ❌ 新增（B77） |
| 开新卷卷纲 | evaluator: unit 或 full | ⚠️ 已有部分 |
| 采风融合 | evaluator: fusion-review | ❌ 新增（B77） |
| 修订包 | evaluator: revision | ✅ 已有（B69） |
| 防撞对照 | 独立 review 步骤 | ❌ 升格（B77） |
| 卷末情节体检 | evaluator: volume-review | ❌ 升格（B77） |

### moshu-write

| 产物 | 审查 | 状态 |
|---|---|---|
| 细纲批 | evaluator: detail-batch | ✅ 已有（B69） |
| 正文 | review 四 reviewer | ✅ 已有 |
| 完结清账/完结章 | evaluator: finale | ❌ 新增（B77） |

## 六、子步划分（76a-d；**子步是本地提交，批末一次推送**——中间子步守卫可短暂红，76d 全绿为批验收门，见规格 README §2.8）

### 子步 76a：统一流程模板入宪 + 新 SKILL + 路由/状态机

1. AGENTS.md §9 加统一创作流程模板（第 7 条原则；实测改后裸长约 9850<11000 阈值，报告数字进日志）
2. 新建 skills/moshu-outline/SKILL.md + skills/moshu-volume/SKILL.md（按 §四）
3. marketplace.json：删 moshu-build 条目、加 outline/volume 两条
4. moshu 路由 SKILL.md 三处 + next_step.py 三处 + test-next-step 断言
5. evals/scenarios/开书/README.md 更新

（本子步末 skills/*/SKILL.md 枚举=13，story-numbers 必红——已知中间态，76c 删 build 后回 12，76d 锁叙述）

### 子步 76b：references + scripts 迁移 + 注册表重组

1. §三-1 八个 build 独有文件 git mv（workflow-build→volume-workflow 重命名）
2. §三-2 shared-assets.json 各组 targets 改路径、删 build 侧旧副本、sync 物化、check-shared-files 绿
3. §三-3 三个脚本 git mv + __pycache__ 删 + 防御性 grep
4. 同步更新：spawn-contracts（4 caller）、capability-wiring（3 路径）、current-contract（改写+新增生产者条）、behavior-contracts（1 路径）、doc-budget（files 条目路径：build/SKILL 删除、workflow-build→volume-workflow、revision-workflow→volume 路径；paths 组「构建路径」改「卷规划路径」三文件新路径）
5. build/SKILL.md 内指向已迁移 references 的链接路径更新（此时 build 目录仍在，下子步删）

### 子步 76c：workflow 重写 + 删 build

1. volume-workflow.md 按统一模板五步重写（Phase A/B → PREPARE/DRAFT/REVIEW/POLISH/COMMIT；**重写必须保留全部 spawn 调用锚行原文**——check-spawn-contracts 三查绿后再提交本子步）
2. revision-workflow.md 保持独立（跨技能流程，仅 76b 已迁路径）
3. cold-path.md 开新卷节入口更新（引用卷规划新称谓）
4. ledger-template.md 归属句更新（volume）
5. **`git rm -r skills/moshu-build/` 整目录删除**（定死：不留重定向桩——桩会被 story-numbers 枚举为第 13 技能；build 意图已由 moshu 路由表承接，/moshu-build 旧命令 404 可接受）

### 子步 76d：守卫终验 + 产品文档

1. 全套守卫跑绿：static-check / shared-files / doc-budget / capability-wiring / spawn-contracts / current-contract / behavior-contracts / story-numbers（叙述计数 11→12：README/README_EN/CONTRIBUTING/scripts README/PRD）
2. PRD 更新（能力全景 12 技能/分层架构两节点/用户旅程/文件走查 build 段拆分）
3. CHANGELOG Unreleased 段（B76 条目：拆分+模板入宪+迁移）
4. doc-budget 预算锁定：volume-workflow 重写后实测（目标≤现 18900，超出走压缩→下沉→调高序并在日志偏差记录）；volume/SKILL.md 与 outline/SKILL.md 新条目=实测×1.05 取整；「卷规划路径」组值重锁

## 七、验收

1. AGENTS.md 统一模板在位（grep PREPARE/DRAFT/REVIEW/POLISH/COMMIT）且裸长 <11000（node 量法进日志）
2. moshu-outline/ 与 moshu-volume/ 结构完整（SKILL.md + references/ + scripts/），skills/*/SKILL.md 枚举=12
3. `git ls-files skills/moshu-build` 为空（整目录已删，无重定向桩）
4. 全套守卫绿（§六-76d-1 清单）
5. next_step 测试全绿（S2/S3/S6 新断言）
6. marketplace.json 无 moshu-build 条目、有 outline/volume 两条且 skills 路径存在
7. **残留 grep**：`grep -r "moshu-build" skills/ scripts/ .claude-plugin/ evals/ README.md README_EN.md CONTRIBUTING.md docs/mo-shu项目*.md` 零命中（docs/治理、docs/研究、CHANGELOG 历史条目除外）
8. doc-budget 全绿且新预算锁定值记录进施工日志（含量法：node 非空白 UTF-16）
9. **端到端走查**（AI 按清单走，非自动化）：①说「开书」→ 路由应指 /moshu-outline；②说「卷纲/开新卷/修订设定/采风」→ /moshu-volume；③next_step S2 无书态建议链 outline→volume→write 通顺；④volume SKILL 读面声明与 outline 产出文件名一一对应。走查结论四行进施工日志
10. PRD 能力全景 12 技能、分层架构两节点

## 八、禁止事项

1. **write 技能不拆**（本批只拆 build）
2. **设定管理 agent 本批不做**（拆分后视实际分布另批）
3. 审查新增 eval_type 本批只标注不做（B77 专项）
4. 采风 agent 融合模式（B81）本批不实施（规格在库，排拆分后修订路径再开工）
5. 方法论萃取（B78-B80）本批不实施（排拆分后——新内容直接进新技能；**其规格基线随本批落位重测**，见 §十）
6. 统一模板是**描述性骨架不是执行性管线**——各技能具体步骤可有差异，但 Phase 名称/顺序/语义必须一致
7. **禁止 git mv 共享副本或反转 shared-assets 源**（§三-2 机制）
8. **禁止改守卫断言/白名单变绿**（先判因；中间态红是本批设计内的，收口在 76d）

## 九、提交规范（四子步四提交，批末一次推送）

- 76a：`feat(宪法+路由): B76a 统一创作流程模板入宪（FULL/LIGHT 五步骨架）+ moshu-outline/moshu-volume SKILL 新建 + marketplace/路由/next_step 更新`
- 76b：`feat(迁移): B76b build references 36 项与 scripts 5 件迁移至新技能 + shared-assets/契约四件/doc-budget 注册表重组`
- 76c：`feat(volume): B76c volume-workflow 按统一模板重写（保留 spawn 锚行）+ 冷路径/台账归属更新 + moshu-build 整目录删除`
- 76d：`feat(守卫+PRD): B76d 全套守卫绿收口 + 叙述计数 12 技能 + PRD 拆分走查 + CHANGELOG Unreleased`

## 十、后续批次再基线（本批闭合后、下游开工前）

- B78（情节骨架）/B79（先想清再动笔）/B80（正文手艺）规格中 workflow-build/outline-workflow/chapter-core 的预算基线与路径**重测重写**（路径已变、现值已涨）
- B81（采风融合）规格中 build 路径引用改 volume 侧
- B77（审查补全）规格新立时直接用新路径与 12 技能口径

# 规格 · 批 B76：build 拆分——moshu-outline + moshu-volume + 统一创作流程模板入宪

- 版本：v1.0（2026-08-29，旗舰起草；来源：作者多轮架构讨论裁定。**目的**：解决 build 193K/35 文件的结构性臃肿；统一创作技能内部流程为五步模板（FULL/LIGHT 两档）；审查覆盖按技能独立设计——**每个产物的写-审配对可逐一对账**。）
- 性质：**全仓最大架构重构**——拆一个技能为两个、统一流程模板入宪、审查缺口标注。分**四个子步**执行。

## 一、统一创作流程模板（入宪法 §9）

所有创作技能共享以下骨架（写入 AGENTS.md §9 宪法原则，作为新增第 10 条原则）：

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
| **读** | genre-catalog、genre-core-mechanics、character-design-methods、character-relations | references |

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

### moshu-write（不拆，但确认归属不变）

| 归属 | 文件/目录 |
|---|---|
| **产出** | 大纲/细纲_第*.md、大纲/写作浮现.md、大纲/完结宣告.md |
| **产出** | 正文/*.md |
| **产出** | 追踪/（via tracking_commit） |
| **执行** | 细纲批次/日更/审查/卷复盘/完结章 |

## 三、references 文件分配（35 个文件重新归属）

### → moshu-outline/references/（12 个）

| 文件 | 用途 |
|---|---|
| character-basics.md | 角色卡模板 |
| character-design-methods.md | 角色设计方法论 |
| character-relations.md | 关系类型 |
| core-setting-template.md | 核心设定表模板 |
| genre-core-mechanics.md | 题材核心机制 |
| genre-catalog.md | 题材框架路由 |
| ideal-review-template.md | 理想书评模板 |
| idea-seed.md | 理想书评/概念设计 |
| naming-cards.md | 命名卡 |
| opening-design.md | 开头设计 |
| plot-frameworks.md | 故事框架 |
| reader-contract-and-progression.md | 读者契约与升级 |

### → moshu-volume/references/（16 个）

| 文件 | 用途 |
|---|---|
| beat-cards.md | 节拍卡 |
| caifeng-methods.md | 采风方法 |
| cold-path.md | 开新卷冷路径 |
| emotional-arc-design.md | 情绪弧线 |
| emotional-methods.md | 情绪方法论 |
| genre-prose-cards/ | 题材卡目录 |
| genre-prose-cards.md | 题材卡索引 |
| genre-readers.md | 读者画像 |
| genre-writing-formulas.md | 写法公式 |
| ledger-template.md | 台账模板 |
| outline-conflict.md | 冲突设计 |
| outline-methods.md | 大纲方法 |
| outline-rhythm.md | 节奏管理 |
| outline-structure-theory.md | 结构理论 |
| outline-workflow.md | 细纲模板（write 共享副本→本处源） |
| virtual-benchmark-template.md | 虚拟对标模板 |

### → moshu-volume/references/ 续（5 个）

| 文件 | 用途 |
|---|---|
| plot-core-methods.md | 情节核心方法 |
| plot-emotion-system.md | 情节情绪系统 |
| plot-special-topics.md | 特殊主题 |
| reversal-toolkit.md | 反转工具 |
| style-genre-modules.md | 流派模块 |
| tracking-transaction.md | 追踪事务（write 共享副本源） |
| workflow-build.md → **重命名 volume-workflow.md** | 卷规划工作流 |
| revision-workflow.md | 修订流 |

### 保留在 moshu-build 不动的（0 个——build 技能被完全替代）

### 跨技能共享（shared-assets 维持）

| 文件 | 副本 |
|---|---|
| outline-workflow.md | write 副本保留 |
| tracking-transaction.md | write 副本保留 |
| character-basics.md | write 副本保留 |
| genre 族文件 | setup agent-references 副本保留 |

## 四、路由与状态机变更

### SKILL.md 新建两个

**moshu-outline/SKILL.md**：
```
name: moshu-outline
description: 故事架构技能——开书的故事层设计（题材定位/世界观/人物/全书大纲）。
触发：/moshu-outline、开书、设计故事、搭大纲、建世界观、人物设计。
产出设定/ 和 大纲/大纲.md。卷纲和细纲归 moshu-volume/moshu-write。
```

**moshu-volume/SKILL.md**：
```
name: moshu-volume
description: 卷规划技能——每卷的单元卡/场景表/卷纲产出与修订、开新卷规划、采风、防撞。
触发：/moshu-volume、卷纲、开新卷、单元卡、修订设定、改大纲、采风。
读 moshu-outline 的设定与大纲，产出卷纲层文件。
```

### moshu 路由更新

SKILL.md 路由表更新：build 相关意图分流到 outline 或 volume。

### next_step.py 更新

- S2 状态：「有书但无正文」→ 建议动作改为 `/moshu-outline`（首次）→ `/moshu-volume`（首卷）→ `/moshu-write`（开始写作）
- S6 状态：「下卷规划」→ 建议动作改为 `/moshu-volume`

### 设定/采风跨技能声明（各技能 SKILL.md 内声明读/写面）

**moshu-outline SKILL.md**：
```
设定读写面——创建：设定/题材定位.md、关系.md、题材正文提示卡.md、角色/*.md、势力/*.md、世界观/*.md
设定读面——读取：拆文库/{书}/概要.md、角色卡（对话 DNA 带入）
采风触发面——结构采风（Stage 2）/角色采风（Stage 3）/机制采风（设定面）
```

**moshu-volume SKILL.md**：
```
设定读写面——修订：设定/*（修订流 impact_scan 影响分析后修改）
设定读面——读取：设定/（全部，单元卡消费）、大纲/大纲.md（骨架表）
采风触发面——情节采风（Stage 4）/情绪采风（Stage 5）/机制采风（应用层）/融合（researcher agent fusion 模式）
```

**不需要新建设定管理 agent**——三权分立已清晰（outline 创建 / write 增量 / volume 修订），一致性由追踪系统+修订流覆盖，查询通过文件即接口。采风的跨技能特性由 researcher agent 天然解决（agent 不属于任何技能）。

### 追踪系统归属确认

| 操作 | 拆分后归属 | 变化 |
|---|---|---|
| tracking init | volume Stage 6 末尾 | 调用者从 build 改为 volume |
| commit/check/report | write（不变） | 无 |
| pace_meter | write + volume（共享脚本） | shared-assets targets 更新 |
| impact_scan + design_fingerprints | volume 修订流 | 路径更新 |
| tracking_commit.py 副本 | 原 build 副本→volume | shared-assets targets 更新 |

### architecture.md 更新

分层架构图中 build 拆为两个节点。

## 五、审查覆盖标注（每个产物的写-审配对）

### moshu-outline

| 产物 | 审查 | 状态 |
|---|---|---|
| 大纲骨架 | evaluator: outline | ✅ 已有 |
| 人物设计 | evaluator: character | ❌ 新增（B81） |
| 世界观/设定包 | evaluator: settings | ✅ 已有（B69） |

### moshu-volume

| 产物 | 审查 | 状态 |
|---|---|---|
| 单元卡 | evaluator: unit | ✅ 已有 |
| 场景表 | evaluator: scene | ❌ 新增（B81） |
| 开新卷卷纲 | evaluator: unit 或 full | ⚠️ 已有部分 |
| 采风融合 | evaluator: fusion-review | ❌ 新增（B81） |
| 修订包 | evaluator: revision | ✅ 已有（B69） |
| 防撞对照 | 独立 review 步骤 | ❌ 升格（B81） |
| 卷末情节体检 | evaluator: volume-review | ❌ 升格（B81） |

### moshu-write

| 产物 | 审查 | 状态 |
|---|---|---|
| 细纲批 | evaluator: detail-batch | ✅ 已有（B69） |
| 正文 | review 四 reviewer | ✅ 已有 |
| 完结清账/完结章 | evaluator: finale | ❌ 新增（B81） |

## 六、子步划分

### 子步 80a：统一流程模板入宪 + 新 SKILL.md 骨架

1. AGENTS.md §9 加统一创作流程模板（FULL/LIGHT 两档）
2. 新建 skills/moshu-outline/SKILL.md + skills/moshu-volume/SKILL.md
3. moshu 路由 SKILL.md 更新路由表
4. next_step.py S2/S6 建议动作更新
5. architecture.md 状态机图更新

### 子步 80b：references 迁移 + shared-assets 重组

1. 按第三节的分配表，将 35 个 references 文件移入新技能目录
2. workflow-build.md → volume-workflow.md（重命名+内容重组）
3. shared-assets.json 重组（源路径变更）
4. sync 后 check-shared-files 绿

### 子步 80c：workflow 内容重写

1. volume-workflow.md 按 FULL 模板五步重写（Phase A/B → PREPARE/DRAFT/REVIEW/POLISH/COMMIT）
2. revision-workflow.md 保持独立（跨技能流程）
3. cold-path.md 归属 volume，开新卷节更新入口
4. 台账模板更新（归属 volume）
5. 原有 build/SKILL.md 和 workflow-build.md 删除

### 子步 80d：守卫+路由+产品文档

1. 全部 check-* 守卫更新路径引用
2. capability-wiring 更新消费者路径
3. spawn-contracts 更新 callers 路径
4. doc-budget 更新文件路径
5. PRD 更新（能力全景/用户旅程/文件走查）
6. CHANGELOG Unreleased

## 七、验收

1. AGENTS.md 统一模板在位（grep PREPARE/DRAFT/REVIEW/POLISH/COMMIT）
2. moshu-outline/ 和 moshu-volume/ 目录结构完整（SKILL.md + references/）
3. 原 moshu-build/ 删除（git rm）或重定向（SKILL.md 只留「已拆分→ /moshu-outline /moshu-volume」）
4. 全部守卫绿（static-check/shared-files/doc-budget/capability-wiring/spawn-contracts）
5. next_step.py 测试更新+全绿
6. PRD 能力全景从 11 技能改 12 技能
7. story-numbers 守卫更新技能计数

## 八、禁止事项

1. **write 技能不拆**（本批只拆 build）
2. **设定管理 agent 本批不做**（拆分后视实际分布另批）
3. 审查新增 type 本批只标注不做（B81 专项）
4. 采风 agent 融合模式（B79）本批不实施（规格在库，排拆分后）
5. 方法论萃取（B76-B78）本批不实施（排拆分后——新内容直接进新技能）
6. 统一模板是**描述性骨架不是执行性管线**——各技能的具体步骤可有差异，但 Phase 名称/顺序/语义必须一致

## 九、提交规范（四子步四提交）

- 80a：`feat(宪法+路由): B76a 统一创作流程模板入宪（FULL/LIGHT 两档五步骨架）+ moshu-outline/moshu-volume SKILL.md 新建 + 路由与状态机更新`
- 80b：`feat(迁移): B76b references 35 文件迁移至新技能 + shared-assets 重组 + workflow-build→volume-workflow 重命名`
- 80c：`feat(volume): B76c volume-workflow 按统一模板重写（PREPARE/DRAFT/REVIEW/POLISH/COMMIT）+ 台账/冷路径/修订流归属更新 + 原 build 删除`
- 80d：`feat(守卫+PRD): B76d 全部守卫路径更新 + capability-wiring/spawn-contracts 路径 + doc-budget 路径 + PRD 12 技能 + CHANGELOG`

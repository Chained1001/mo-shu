# moshu-import 审计报告

- 审计日期：2026-08-21
- 对象：`skills/moshu-import/`（8 文件：SKILL.md + 6 references + `scripts/tracking_commit.py` 副本）
- 方式：委派深审 + **本人独立复核 IM1 / IM2**

## 一、结论

**基础面全绿**：`tracking_commit.py` 与 write/review 两副本字节相同、6 references + 1 script 零死链零孤儿、术语零违例（含"拆解库/模块库"零命中）、marketplace 版本**无滞后**（1.1.1 == 1.1.1）、doc-budget 余量健康（2509/2600，余 91）。旧追踪迁移主链路与脚本行为一致（实测存档、无删除，NOTE 文案逐字相符）。

**主要问题**：①一条**过期的版本门禁**会让正确部署的项目恒久走降级串行；②Phase 2 有一个**空节**却被 SKILL.md 承诺；③`init` 已支持 `information_gaps` 但流程零指示；④初始化产物清单**漏 `信息差.md`**（三处）；⑤导入后 `suspension_warnings` 结构性失效且无提示。

## 二、阻断级：0 项

## 三、需修级：6 项

### IM1 `import-workflow.md:70` 写死 `agents_version: 27`，正确部署（29）恒判不通过 ✅本人复核成立

- **现象**：Phase 1 Step 5 环境检测把"只有 `agents_version: 27` 通过后"作为检查并行 agent 的前置条件。当前权威是 **29**，任何按 `/moshu-setup` 正确部署的项目都不满足该字面条件 → 恒定落入"agent 不可用"分支 → Phase 2 长篇逐章摘要**永久降级串行**。
- **证据（本人逐行核对）**：`skills/moshu-import/references/import-workflow.md:70`「只有 `agents_version: 27` 通过后，才按 `.claude/agents/moshu-chapter-extractor.md` 检查 Phase 2 长篇并行 agent。」；同 skill 顶部门禁写的是 29（`skills/moshu-import/SKILL.md:16`，且语义是"不匹配也照常 spawn，只提示"）；权威 29 见 `skills/moshu-setup/UPGRADING.md`。降级后果定义在 `:110`（"Stage 2 逐章摘要降级为串行处理，产物仍完整，仅速度变慢"）。
- **两条指令互相冲突**：SKILL.md 说不匹配也照常 spawn，workflow 说必须等于 27 才检查 → LLM 实际行为不确定。
- **守卫盲区（本人复核）**：`scripts/check-agents-version-sync.py:24-30` 只遍历 `skills/*/SKILL.md`（`sk = skill_dir / "SKILL.md"`），**`references/` 完全不在校验面**，所以这处 27 一路绿灯过了 v1.3.0 发布。批 7「版本链一次改全」（`施工日志.md:278` 偏差记录 2 自称"逐处核验无残留"）实际漏了它。
- **修法**：`:70` 改为不写死数字、与 SKILL.md 门禁一致的表述（"先执行 SKILL.md 顶部 Spawn 版本门禁（不匹配只提示不阻断），随后按 agent 文件是否存在决定并行/串行"）；**根治**：`check-agents-version-sync.py` 扫描面从 `SKILL.md` 扩到 `skills/**/*.md`。
- **改动量**：文档 1 行；根治 +2~3 行 + `test-agents-version-sync.py` +1 反向 fixture。
- **验收**：`bash scripts/check-agents-version-sync.sh` 绿；扩面后**必须能抓到**人为在 references 里写错的版本（反向验证）。

### IM2 Phase 2「### 质量检查」是空节，而 SKILL.md 明确承诺 ✅本人复核成立

- **证据（本人 `sed -n '168,175p'` 逐字节核对）**：`import-workflow.md:170` `### 质量检查`、`:171-172` 两个空行、`:173` `---`（确认空节）；承诺方 `skills/moshu-import/SKILL.md:44`「…调用契约、拆文库结构、恢复机制与**质量检查**见同节」。
- **影响**：执行者按索引跳到该节拿不到任何判据，Phase 2 出口质量无标准；`static-check.py` 不检查节内容是否为空，故长期无人发现。
- **修法**：填入现成的确定性判据三条（`_progress.md` 为 `schema_version: 2`、`剧情/节奏.md` 与 `剧情/情绪模块.md` 存在非空、摘要数 == 章节数——前两条可复用 `:104` 的当前拆文契约，第三条复用 `:156` 的计数验证）。**改动量**：+3~4 行。

### IM3 `init` 支持 `information_gaps` 但 Step 7 六项语义准备零指示（接线缺口）

- **证据**：脚本支持——`skills/moshu-import/scripts/tracking_commit.py:983-993`（init 读 `information_gaps`，`:988` 强制 `action == "register"`，`:989` 拦重复 id）、`:1005` 写入 state。子代理**实测**：带 1 条 G001 的 init → **exit 0**，state 得 `information_gaps: {"G001": {…}}`，并渲染出 `追踪/信息差.md` 表行。流程零指示——`import-workflow.md:307-321` Step 7 的 6 项语义准备无一提到它；字段说明只在共享 `references/tracking-transaction.md:184` 一句附注。
- **收益已被实测证明**：子代理跑 `volume-report --from-chapter 1 --to-chapter 10` → `"open_gap_count": 1`——**只要 import 登记，下游卷报告立刻可用**。
- **修法**：Step 7 插入第 3.5 项"信息差当前登记：从拆书产物反推截至 N 章仍成立的『谁知道什么』，按 `information_gaps` 数组写入 init JSON（`action` 固定 `register`，id `G\d{3,}`）；无证据不硬造，拿不准记入 `continuity_risks`"。**改动量**：+2~3 行。

### IM4 初始化产物清单漏 `信息差.md`（三处，含共享源文件）

- **证据**：代码无条件生成——`tracking_commit.py:1159-1165` `render_views` 字典含 `"信息差.md"`、`:1176-1181` 写全部视图、`:1216/:1223` init 走同一路径；子代理实测 init 后 `追踪/` 实有该文件。三处漏项：①`import-workflow.md:327-337` 目录树；②`:394` 完成报告追踪产物枚举；③共享 `references/tracking-transaction.md:11` 派生视图表（**影响 write/import/review 三份**）。
- **修法**：目录树 +1 行；完成报告 +1 短语；**改共享源文件** `skills/moshu-write/references/tracking-transaction.md:11` 后跑 `python scripts/sync-shared-assets.py sync`（保持三副本字节相等）。
- **改动量**：2 文件 + 1 源文件单元格 + 一次 sync。**验收**：`bash scripts/check-shared-files.sh` 零 mismatch。

### IM5 导入后 `suspension_warnings` 结构性失效，且零提示

- **证据**：`init` 把所有导入伏笔的 `updated_chapter` 统一置为 `last_chapter = N`（`tracking_commit.py:984-993` 以 `through_chapter=last_chapter` 归一化）→ 悬置章距 = N − N = 0。子代理实测：F001 `planted_chapter=2`、N=10 → `伏笔.md` 该行"最近变更章 = 第10章"；`check --warn-chapters 1`（最小合法阈值）**仍返回 `[]`**；`volume-report` `suspension_count: 0`。语义本身在共享 reference 里是诚实声明的（`tracking-transaction.md:188`"最近一次变动章起算的近似"）。
- **影响**：3b 悬置预警在导入项目上首个卷复盘窗口内恒为 0，作者会把"0 条预警"误读为"没有久悬伏笔"。属**设计语义 + 车道未说明**，非脚本 bug。
- **修法（不改脚本）**：`import-workflow.md` Step 7 第 3 项末补一句"导入伏笔的『最近变更章』会被 `init` 记为 N，因此 `suspension_warnings` 在续写满阈值前恒为空——原书久悬伏笔请在 `continuity_risks` 或卷纲另记"；完成报告"待补充项"加 1 行勾选项。**改动量**：+2 行。

### IM6 review 的两条边界 rubric 依赖 import 从不生成的表

- **证据**：消费端 `skills/moshu-review/references/review-workflow.md:60/:61` 与 `quality-rubric.md:35/:36` 对照 `设定/题材定位.md` 的「信息差登记表」与「创意约束表」；生产端在 write（`moshu-write/references/artifact-protocols.md:201/:221`，填写点 `workflow-setup.md:218/:238`）；import 侧 `git grep "信息差登记\|创意约束" -- skills/moshu-import` **零命中**。
- **影响**：导入书走 `/moshu-review` 时这两条边界类 rubric（防提前泄密、防金手指万能化）静默失效；`（如存在）` 的措辞让缺口看起来像正常缺省。
- **修法**：`import-workflow.md:398-406`「待补充项」+1 行勾选项（最小）；或 Step 8 输出空表骨架 + `[待补充]`（+6~8 行，与该 skill 现有惯例一致）。

## 四、候选级

| 编号 | 发现 | 证据 | 修法 |
|---|---|---|---|
| IC1 | 与派生视图**同名**的旧文件被直接覆盖，不入 `_旧追踪存档/`（与"旧内容不删除"承诺相悖） | 受管清单固定 6 项 + 1 glob（`tracking_commit.py:68-75`）；实测预置的旧 `追踪/伏笔.md` 被渲染覆盖、存档内无副本。**存疑**：受管清单未列 `伏笔.md`，可能旧协议本就同名、覆盖为有意 | 先改文档 1 句（"受管清单内的旧内容不删除；与当前派生视图同名的旧文件会被重建覆盖"）；脚本路线 +5~8 行 + 1 用例 |
| IC2 | `imported_through_chapter` 语义链完整（实测一致），仅 `:429` 补救路径未说明会为旧章生成逐章记录 | `:309`/`:429`、`tracking-transaction.md:148`、`workflow-revision.md:64` 四处一致；实测 state 得 `imported_through_chapter: 10`、`:1296` 约束续写起点 | +1 句 |
| IC3 | Phase 1 输入识别未做"缺文件/空文件/内容坏"三分类（反模式 §7） | `:40-51` 只有"提示用户提供源文件"一条路径 | +1 行 |
| IC4 | 导入车道无端到端走查剧本 | `evals/scenarios/` 三剧本均不涉及导入；IM1/IM2/IM4 正落在无剧本区 | 候选，不建议引 LLM |

## 五、覆盖矩阵

| 维度 | 结果 |
|---|---|
| 引用图 | 零死链、零孤儿 |
| 流程闭环 | 主链路闭合（Phase 1→2→3-L Step 1-10→4）；`imported_through_chapter` 一致；旧追踪迁移无删除；**Phase 2 空节（IM2）**、**版本门禁过期（IM1）** |
| schema v5 接线 | **未接线**（IM3）；产物清单三处漏（IM4）；导入后悬置预警失效（IM5） |
| 副本一致性 | 通过（SHA256 全等） |
| 守卫覆盖 | behavior-contracts **零覆盖**；有效覆盖来自 `test-tracking-workflow-contracts.py:116-136`、`check-current-skill-contracts.py:118-146/1156-1173`、`check-moshu-setup-deployment.sh:521/578`。**盲区：references 的 agents_version（IM1）、空节（IM2）、产物清单（IM4）改了都不会被发现** |
| 术语与可数声明 | 零违例；Stage 0-6 = 7 阶段 ✓、固定 7 栏 ✓、`>200 章` 分批规则自洽 ✓ |
| 版本口径 | marketplace 1.1.1 == SKILL.md 1.1.1（**10 个 skill 中无滞后的之一**） |

## 六、实测记录（节选）

| 检查 | 结果 |
|---|---|
| **本人复核 IM1** | `git grep agents_version -- skills/moshu-import` → SKILL.md:16 = 29、`references/import-workflow.md:70` = **27**；`check-agents-version-sync.py:24-30` 源码确认只扫 SKILL.md |
| **本人复核 IM2** | `sed -n '168,175p'` + `cat -A` → `### 质量检查` 后两空行直接 `---`，**空节坐实** |
| init（含 information_gaps） | exit 0；state `schema_version 5` / `imported_through_chapter 10` / `information_gaps.G001` |
| 旧追踪迁移 | NOTE 文案与 `import-workflow.md:25`、`:316`、`tracking-transaction.md:36` 逐字相符；`_旧追踪存档/` 保留原结构、无删除 |
| `check --warn-chapters 1` | `suspension_warnings: []`（IM5 机理实证） |
| `volume-report 1-10` | `open_gap_count: 1`（IM3 收益实证） |
| doc-budget | 2509/2600（余 91） |

## 七、整改计划

| 编号 | 级别 | 修法 | 改动量 | 依赖 | 验收 |
|---|---|---|---|---|---|
| **IM1** | 需修（最高优先，有功能影响） | `:70` 去掉写死版本、与 SKILL.md 门禁一致；**并**把 `check-agents-version-sync.py` 扫描面扩到 `skills/**/*.md` | 1 文档行 + 守卫 3 行 + 1 fixture | 无 | `check-agents-version-sync.sh` 正向绿 + 反向必红 |
| IM2 | 需修 | 空节填三条确定性判据 | +3~4 行 | 无 | `static-check.sh` |
| IM3 | 需修 | Step 7 增信息差登记项 | +2~3 行 | 与 W1/RM2 同批 | `check-behavior-contracts.sh` |
| IM4 | 需修 | 三处产物清单补 `信息差.md`（含改共享源 + sync） | 3 文件 + sync | 无 | `check-shared-files.sh` 零 mismatch |
| IM5 | 需修 | 补悬置预警语义说明 + 待补项 | +2 行 | 无 | 人工核对 |
| IM6 | 需修 | 待补充项加信息差/创意约束表勾选项 | +1 行 | 无 | 人工核对 |
| IC1-IC4 | 候选 | 见上表 | ≤10 行 | IC1 需作者裁定旧协议文件集 | — |

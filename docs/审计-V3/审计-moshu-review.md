# moshu-review 审计报告

- 审计日期：2026-08-21
- 对象：`skills/moshu-review/`（18 文件：SKILL.md + 12 references（含 rubrics）+ 5 scripts）
- 方式：委派深审 + **本人独立复核阻断级与关键需修级**（复核结果逐条标注）

## 一、结论

**基础面全绿**：`tracking_commit.py` 三副本 SHA256 完全相同（`B30572AB…F5E6`）、`sync-shared-assets.py check` 36 组/51 副本 OK、12 references + 5 scripts 零死链零孤儿、术语零违例、可数声明全部实测相符（rubrics 2 份 / reviewer 4 个 / dimension 9 类 / 英文 key 5 个 / AI 模式 12 种）。工单 schema 四方一致（脚本↔批 6 规格↔review-workflow↔workflow-revision），状态机单向流转实测成立（fixed 再 resolve → exit 2）。

**但批 6 的两条闭环在文档层没有真正合上**，且都已实测坐实：①**审稿令牌注入端完全缺失**，防编造机制恒为空转；②**复审"只验 open 项"无确定性依据**，重跑审查会把已处置项重新变 open。

## 二、阻断级：1 项

### RB1 审稿令牌注入链断裂——批 6 防编造机制恒为空转 ✅本人复核成立

- **现象**：4 个 reviewer agent 模板要求"输入首行含 `审稿令牌：<token>`"，但 moshu-review 侧**没有任何地方生成或注入令牌**，也没有任何地方调用 `verify-token`。reviewer 必然走"无令牌"兜底，写出 `审稿令牌：缺失`。
- **证据（消费端齐备）**：`skills/moshu-setup/references/templates/agents/` 下 `moshu-architect.md`、`moshu-character-designer.md`、`moshu-consistency-checker.md`、`moshu-narrative-writer.md` **各 2 处**「审稿令牌」（本人复核：`git grep -c` 四份均为 2），正文逐字相同。
- **证据（生产端缺失，本人复核）**：`git grep -n 审稿令牌 -- skills/moshu-review/references/review-workflow.md` → **仅 1 命中**（`:322`，且只是描述工单 JSON 的 `review_token` 字段，不是可执行步骤）；4 个 spawn prompt 模板（Agent 1 `:183-212` / Agent 2 `:218-241` / Agent 3 `:247-272` / Agent 4 `:278-302`）**均无令牌行**。
- **证据（校验端零调用，本人复核）**：`git grep -n verify-token -- skills/moshu-review skills/moshu-write` → 3 命中**全在 `review_tickets.py` 自身**（`:2` docstring、`:9` docstring、`:261` argparse），**流程文档零调用**。
- **旁证**：唯一可执行的"生成并注入"指令躺在走查剧本 `evals/scenarios/审查工单/README.md:10`——运行时读不到。
- **影响**：批 6 §4 声明的"防 subagent 未读输入编报告"在文档层不成立；`CHANGELOG.md:11` 与 `docs/规格-V2/审核记录.md:114` 均记为已交付（后者写"含 verify-token 集成"），属**声明与可执行流程不符**。同时 `scripts/doc-budget.json:40` 为此段显式调高了两处预算（narrative-writer 13150→13300、正文 agent 组 43600→43700）——**成本已付、收益未得**。
- **建议修法（最小，全部落 references，不动 SKILL.md）**：`review-workflow.md` Phase 2 开头加 1 句"本轮生成 8 位随机令牌 `<token>`，作为每个 spawn prompt 的**首行**写入"；4 个 prompt 模板各加 1 行首行 `审稿令牌：{token}`；Phase 4「工单落盘」前加 1 步"逐个 reviewer 报告首行比对令牌（`review_tickets.py verify-token`），不等则不采纳该报告并重跑"。
- **改动量**：1 文件 / +6~8 行。**注意**：绝不能写进 `SKILL.md`（余量仅 1 字，见 RM6）。
- **验收**：`bash scripts/check-behavior-contracts.sh` + `python scripts/test-review-tickets.py` 保持绿；人工走查 `evals/scenarios/审查工单` 时令牌断言可判真伪。

## 三、需修级：7 项

### RB2 复审闭环缺环：工单按分钟戳累积、`list` 跨文件不去重

- **现象**：`write` 每次按分钟戳新建文件，同一 `chapter_range` 可并存多份互相矛盾的工单；`list` 汇总全部文件、**不按 id 去重、无新旧优先级**。复审（重跑 review → 再 write）产生全新 `status: open` 副本，上一轮 fixed/dismissed **不被继承**。
- **证据**：`review_tickets.py:171` `stamp = …strftime("%Y%m%d-%H%M")`；`:173-181` 仅在目标文件名完全相同（同一分钟）时做幂等/冲突检查；`:209-229` `list_command` 逐文件收集，无 id 去重、无 precedence。子代理实测：同 `chapter_range [1,10]` 两份文件下 `list --status open` 返回 `2357 -> ['T002']`、`2358 -> ['T001']`——**两个都已在另一份里被处置过的 id 同时以 open 浮出**。
- **旁证（读法分叉）**：`skills/moshu-write/references/workflow-revision.md:81` 给了两条不等价读法（"`list --status open`（或直接读 `.moshu-review/tickets/` 最新文件）"），多文件时结论必然分叉。
- **影响**：直接落空批 6 §1 目标"复审只验 open 项"；作者被迫重复处置；`list --status open` 不能作为待办真源。
- **修法（二选一）**：①文档侧（更小）——`review-workflow.md`「工单落盘」加 1 条"同 `{起章}-{止章}` 已有工单文件时本轮为**复审轮**：只对上轮仍 `open` 的项重新落盘"，并删掉 `workflow-revision.md:81` 的"或直接读最新文件"；②脚本侧（更稳）——`write` 扫描同 range 既有文件，重复 id 且旧状态非 open 则拒绝或继承。
- **改动量**：①2 文件 / +3 行 −1 处；②`review_tickets.py` +12~15 行 + `test-review-tickets.py` +1 用例。

### RM1 `write` 接受 `status: fixed|dismissed`，构成绕过 `resolve` 的旁路 ✅本人复核成立

- **证据**：`review_tickets.py:30` `STATUSES = ("open","fixed","dismissed")`；`:114-115` 校验用全集；`:123-125` write 路径 `status_note` 允许空。**本人实测**：提交 `{"schema_version":1,…,"status":"fixed"}` → `ticket written: tickets_20260821-0018_1-2.json`，**exit 0**（接受）。对照 `批6-审查工单闭环.md:84` 禁止事项 4「禁止 status 逆向流转或手工编辑 JSON 绕过 resolve」。
- **影响**：批 6 硬约束在脚本层未闭合，处置证据可为空。`test-review-tickets.py` 无此反向用例。
- **修法**：write 路径增 `require(status == "open", …)`。**改动量**：`review_tickets.py` +3~4 行 + 测试 +1 反向用例。

### RM2 schema v5 三件套在 review 侧未接线（与 moshu-write 的 W1 同型）

| 项 | 现状 | 证据 |
|---|---|---|
| `information_gaps` | 消费**指错位置**——要求对照 `设定/题材定位.md` 登记表，而批 3a 权威视图是 `追踪/信息差.md`（review 全文零引用） | `review-workflow.md:60`、`references/quality-rubric.md:35`；权威定名 `docs/执行总纲V2.md:47` |
| `information_gap_changes` | 生产端零指示——「追踪文件维护」列举重算字段只有伏笔/时间线/快照/上下文 | `review-workflow.md:436-437` |
| `suspension_warnings` | 零消费说明——已要求跑 `check`（其输出就带该字段），但无一句"读取并作结构风险呈报" | `review-workflow.md:435`；实测 `check` 输出含 `"suspension_warnings":[]` |
| `volume-report` | 零提及——review 是唯一做整卷/整本审查的 skill，却不知道有这张确定性清账表 | 全仓仅 `moshu-write/references/volume-review.md:12` 调用 |

- **修法**：①`:60` 对照源改为"`追踪/信息差.md`（权威）+ `设定/题材定位.md` 登记表（如存在）"；②`:437` 字段清单加 `information_gap_changes`；③`:435` 后加半句"读 `suspension_warnings` 逐条作 S4 结构风险候选呈报（候选永不拦截）"；④Phase 1 范围为整卷/整本时加 1 行"先跑 `volume-report`，用 `追踪/卷报告_第A-B章.md` 替代裸眼清账"。
- **改动量**：`review-workflow.md` +4~6 行、`quality-rubric.md` +1 处（实测该组未登记 shared-assets，review 仅一份，可直接改）。

### RM3 总纲术语表关于「工单」的定义已过期（两处）

- **证据**：`docs/执行总纲V2.md:46` 把工单定义为 `审查/工单-第N章.json`、`:150` 同样写该路径且带 `created_by: "moshu-review"` 字段。实测真实路径为 `.moshu-review/tickets/tickets_{时间戳}_{起章}-{止章}.json`（脚本 `:4/:97/:173` + 规格 `批6:37` + 两份 workflow 四方一致）；`created_by` 字段实测被拒（`ERROR: ticket document contains unsupported fields: created_by`）。
- **影响**：术语表自称"全文唯一权威命名…规格与施工必须使用下列叫法"，却给出不存在的路径与被拒字段。
- **修法**：改 `:46` 路径、删 `:150` 的 `created_by`。**改动量**：1 文件 / 2 处。（同文件另有 agents_version/schema 数字过期，见总计划 G7。）

### RM4 eval 令牌断言虚化（标 [机检] 但脚本看不到 reviewer 报告）

- **证据**：`evals/scenarios/审查工单/README.md:22` 标 `[机检]`；而 `verify-token` 只比对**工单文件内 token** 与 `--token` 入参（`review_tickets.py:232-239`），不读报告文本——操作者把工单里的 token 抄进去即恒真。叠加 RB1（流程从不注入），诚实执行必然是"缺失→不过"。
- **修法**：`:22` 类型列 `[机检]`→`人工项`，断言改为"人工把 reviewer 报告首行令牌抄给 `verify-token`；报告首行为 `审稿令牌：缺失` 记不过"。机检项从 5 降 4（仍 ≥3，`check-eval-scenarios.sh` 仍绿）。**改动量**：1 行。

### RM5 behavior-contracts 对 review 零覆盖

- **证据**：11 条契约 `path` 全指 `skills/moshu-write/**`（本人实测守卫输出 11 条在位）。未覆盖面：`review-workflow.md:320-325`「工单落盘」全节、五个英文 key 契约（`:9-19`）、内置 rubric fallback（`:46-81`）、full/lean/solo 降级链措辞。**已覆盖面**（避免误报）：`test-tracking-workflow-contracts.py:163-177` 锁了 review 追踪维护 6 个字符串、`check-moshu-setup-deployment.sh:478-479` 锁了两句版本提示、`check-current-skill-contracts.py:669/687-689/711` 覆盖若干 rubric/SKILL 断言。
- **修法**：增 1 条 `{"id":"review-ticket-write","path":"skills/moshu-review/references/review-workflow.md","must_contain":"工单落盘",…}`。**改动量**：JSON +5 行。

### RM6 `moshu-review/SKILL.md` doc-budget 只剩 **1 字**（2899/2900）

- **证据**：本人 node 复算（与 `check-doc-budget.sh:28-32` 同度量）：`2899 / 2900`。收紧沿革见 `doc-budget.json` `_comment`（4000→2900，批 0）。
- **影响**：review 入口实质冻结，任何补充必须落 references。
- **修法**：纪律约束（0 改动）+ 配 RC2 删重复分隔线可回收 3 字；或随总计划 G5 统一调预算。

### RM7 marketplace 版本滞后：`moshu-review` 1.1.5 vs SKILL.md 1.2.0

见总计划 **G1**（同一批处理）。

## 四、候选级

| 编号 | 发现 | 证据 | 修法/改动量 |
|---|---|---|---|
| RC1 | `resolve --project` 是装饰参数，无归属校验（可用无关目录处置真实工单） | `review_tickets.py:187-206` 函数体从不使用 `project`；实测跨目录 resolve → exit 0 | 增 `require(ticket_path.is_relative_to(tickets_dir(project)))` / +1~2 行 |
| RC2 | `SKILL.md:38-40` 重复分隔线 | `:38` `---`、`:39` 空行、`:40` `---` | 删 2 行（同时为 RM6 回收 3 字） |
| RC3 | `reader-contract-and-progression.md` 不在「规范路径」表（该表明禁裸文件名），审查车道实质闲置 | `review-workflow.md:31-44` 表内无它；仅被 `quality-checklist.md` 一跳引用 | 表 +1 行；**存疑**：它是 shared-asset，可能只为部署顺带落地，需作者裁定 |
| RC4 | `write` 幂等只在同一分钟内成立 | `:171` 分钟戳 + `:174-181` 同名比对 | 随 RB2 处理；或补半句"幂等以同一分钟戳为界" |

## 五、覆盖矩阵

| 维度 | 结果 |
|---|---|
| 引用图 | 零死链、零孤儿 |
| 流程闭环 | 降级链完整（SKILL.md:18-21/25-36 ↔ review-workflow.md:16 的 7 种 Fallback 一致）；rubric 三级 fallback 完整；**令牌注入端缺失（RB1）**、**复审闭环缺环（RB2）** |
| schema v5 接线 | **未接线**（RM2 四项） |
| 副本一致性 | 通过（三份 `tracking_commit.py` SHA256 全等） |
| 守卫覆盖 | behavior-contracts **零覆盖**（RM5）；doc-budget 余 1 字（RM6）；`write` 非 open 状态无测试（RM1） |
| 术语与可数声明 | 零违例；rubrics 2 / reviewer 4 / dimension 9 / 英文 key 5 / AI 模式 12 全部实测相符 |
| 工单 schema 一致性 | 实现↔规格↔两份 workflow **四方一致**；总纲术语表过期（RM3） |
| eval 覆盖 | 5 条机检中 3 条实测成立；令牌条虚化（RM4）；review-log 行式条未验（存疑） |

## 六、实测记录（节选，含本人复核）

| 检查 | 结果 |
|---|---|
| **本人复核 RB1** | `review-workflow.md` 审稿令牌 1 命中（`:322` 字段描述）；`verify-token` 3 命中全在脚本自身；4 agent 模板各 2 处令牌段 → **注入链断裂坐实** |
| **本人复核 RM1** | `write` 提交 `status: fixed` → `ticket written`，**exit 0** → 旁路成立 |
| `sync-shared-assets.py check` | 36 组 / 51 副本 OK |
| 三副本 SHA256 | 全等 `B30572AB…F5E6` |
| `verify-token` 相等/不等 | `token ok` exit 0 / `ERROR: token mismatch` exit 2 |
| `resolve` 单向流转 | fixed 再 resolve → `already fixed` exit 2 |
| 负向 8 例 | 坏 dimension/坏 severity/重复 id/非法 id/令牌 5 位/令牌空/`created_by` 未知字段 → 全 exit 2 |
| doc-budget 复算 | review SKILL.md 2899/2900 |

## 七、整改计划

| 编号 | 级别 | 修法 | 改动量 | 依赖 | 验收 |
|---|---|---|---|---|---|
| **RB1** | **阻断** | review-workflow 补令牌生成+4 处首行注入+采纳前 verify-token | 1 文件 / +6~8 行 | 无（落 references，不受预算约束） | `check-behavior-contracts.sh` + `test-review-tickets.py` + 走查剧本 |
| **RB2** | 需修 | 复审轮只重落 open 项（文档路线）+ 删 workflow-revision 的分叉读法 | 2 文件 / +3−1 行 | 无 | `test-review-tickets.py` |
| RM1 | 需修 | write 限定 `status == open` + 反向用例 | 2 文件 / +7 行 | 无 | `test-review-tickets.py` |
| RM2 | 需修 | 四项接线（信息差权威源/事务字段/悬置呈报/卷报告） | 2 文件 / +5~7 行 | 与 W1 同批 | `check-behavior-contracts.sh` |
| RM3 | 需修 | 总纲术语表工单路径与字段勘误 | 1 文件 / 2 处 | 无 | 人工核对 |
| RM4 | 需修 | eval 令牌断言改人工项 | 1 行 | RB1 之后 | `check-eval-scenarios.sh` |
| RM5 | 候选 | behavior-contracts 增 review 契约 | +5 行 | 无 | `check-behavior-contracts.sh` |
| RC1-RC4 | 候选 | 见上表 | ≤5 行 | 无 | `test-review-tickets.py` |

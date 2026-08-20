# 批 3 规格：U3 一次性 schema 4→5（工单/经验/债务/追读力/evidence）

> 状态：待实施 | 前置：批 2（名册协议） | 预计量：schema+迁移+渲染+三端同步+测试，拆 4 子步 | 风险：**全项目最高**（动唯一权威 schema，须 migrate+备份+每子步全绿）
> 依据：SparkArc `story_memory/facade.py:1012-1143`（工单闭环）、`agent_critic.py`（fix_tickets）；笔枢 `local_archive.py`（debts 索引）；v7 `review/schema.js`（evidence）、`references/追读/`（8 钩子）、`节拍/PA-107-微兑现.md`（7 类）
> **v2 修正**：无 240 护栏；foreshadow 不新增 type 字段（前缀派生）；"悬置信息差"标注 mo-shu 自定；分 4 子步实施。

## 1. 目标

一次 schema 升级补齐 5 个域：审查工单（审完不丢）、叙事债务（角色亏欠）、经验库（带筛选）、追读力（量化）、evidence（溯源）——避免多次迁移。

## 2. 现状事实

- `skills/moshu-write/scripts/tracking_commit.py`：`TRACKING_SCHEMA_VERSION=4`、`INPUT_SCHEMA_VERSION=1`；顶层 8 域（schema_version/book_title/last_committed_chapter/imported_through_chapter/state_revision/context/characters/foreshadow/timeline）；foreshadow 已用 summary 前缀区分 伏笔/悬念/感情线/债务（**类型派生走前缀，零 schema 增量**）；三副本（write/import/review）shared-assets 守护；`check` 逐字比对；`expected_state_revision` 乐观校验（串行写假设）。
- 审查现状：`.moshu-review/` 会话态不持久化；consistency-checker 只报 CONFLICTS。
- 工单消费方（moshu-write 写前准备）与 review/deslop 调用链在 `workflow-chapter.md`/`review-workflow.md`。

## 3. 实施子步（**每步 migrate+check+测试全绿才进下一步**）

### 子步 3.1 quality_tickets 域（最高价值，先做）
- schema v4→v5 域 `quality_tickets: [{ticket_id, target(chapter+location+dimension 三元，复用 Findings location), severity(S1-S4), edit_goal, must_keep, operations(可空), evidence, status: open|resolved, created_at, resolved_at}]`
- 写入：review 主会话 Phase 3 翻译 consistency-checker CONFLICTS + Critic 式 fix_tickets → `ticket-open`；**一致性类工单 operations 可空**；作者裁决点填 operations
- 注入：写前按文本相关性取 open 工单 ≤3 条 + 全量兜底（不做 chapter 硬过滤——跨章工单不能漏）
- 关闭：复审 PASS 且无新 ticket → 按 target 三元匹配 `ticket-close`
- 迁移：老 state → 新域空数组；`migrate` 幂等 + 迁移前自动备份 `_tracking-state.json.bak-v4`

### 子步 3.2 debts + evidence 域
- `debts: [{debt_id, debtor, creditor, promise, due_chapter, status: open|paid|void, evidence}]`（对照笔枢 debts 索引）；章前"到期核对"步骤进 workflow-chapter 写前准备；卷复盘按 id 清账
- changes 各项可选 `evidence: ["chapter:12:event"]` 纯增；check 校验格式
- 债务三类：角色间承诺/悬置因果（笔枢原字段）+ **悬置信息差（mo-shu 自定扩展，重叠伏笔两边都写）**

### 子步 3.3 learned_patterns 域
- `learned_patterns: [{pattern_type, description, source_chapter}]`；渲染进 `追踪/经验.md` 派生视图
- **注入条件：细纲文本确定性字符串命中才进任务书**（mo-shu 自定筛选法，区别于 U4 已弃用的"LLM 子串相关性"；v6 只写不筛=死数据的教训）；作者/卷复盘确认后随事务提交

### 子步 3.4 reading_power 域
- delta 加 `reading_power: {hook_type(8 种枚举：危机/悬念/渴望/情绪/选择/时间倒计时/支票/断章), hook_strength, coolpoint_patterns, micropayoffs(7 类：信息/关系/能力/资源/认可/情绪/线索)}`
- AI 判断标注（明确非确定性）；**标注带正文 sha256**（正文改写后旧标注不得覆盖——G26）
- 配套 `references/追读力-taxonomy.md`（8 钩子 + 7 微兑现精编，新冷路径文件）
- 卷复盘消费追读力趋势（workflow-volume-review 补一步）

## 4. 文件级改动清单（跨子步汇总）

| 文件 | 改动 |
|---|---|
| `skills/moshu-write/scripts/tracking_commit.py` | schema 常量 4→5（`INPUT_SCHEMA_VERSION` 1→2 评估新字段是否进输入负载）；commit 子命令支持新 delta 域，**delta JSON 一律走 `--delta-file <路径>` 文件传递、禁命令行内联**（防 Windows 中文管道编码，v7 SKILL 铁律，总纲 F.2 裁决）；check 校验新域格式；migrate 子命令 |
| 同文件（三副本同步） | `skills/moshu-import/scripts/`、`skills/moshu-review/scripts/` 经 `sync-shared-assets.py` 同步 |
| `skills/moshu-write/references/workflow-chapter.md` | 写前准备注入 open 工单 ≤3+兜底；章前债务到期核对 |
| `skills/moshu-write/references/volume-review.md` | 卷复盘补：债务清账 + 追读力趋势统计 |
| `skills/moshu-review/references/review-workflow.md` | 审查输出接 fix_tickets 三件套 + Phase 3 翻译层（作者裁决点） |
| `skills/moshu-setup/references/templates/agents/moshu-consistency-checker.md` | 明确只报 CONFLICTS、operations 可空（翻译在 review 主会话） |
| **新建** `skills/moshu-write/references/追读力-taxonomy.md` | 8 钩子 + 7 微兑现精编（冷路径） |
| `scripts/test-tracking-commit.py` | 扩展：5 域构造/渲染/check 比对/迁移幂等/工单注入筛选/标注 hash 防覆盖/债务到期 |
| `scripts/current-contract.json` | `progress_schema_version` 或新增 tracking schema 版本字段随动 |

## 5. 验收（每子步 + 总验收）

```bash
python scripts/test-tracking-commit.py
python scripts/test-tracking-workflow-contracts.py
bash scripts/check-shared-files.sh
# 迁移冒烟：构造 v4 老 state → migrate → 新域空值 + 派生视图重建 + check 通过 + 备份文件存在
# 工单闭环冒烟：审查 S1 → ticket-open → 下章写前注入出现工单约束 → 复审 PASS → ticket-close
# 标注防覆盖冒烟：改正文后旧 reading_power 标注被 hash 拒绝
```

## 6. 回滚

migrate 不可逆（丢弃新域即可恢复 v4 语义）；备份 `_tracking-state.json.bak-v4` 兜底；schema 常量回 4 + 渲染 revert = 完整回滚。

## 7. 禁止事项

- 禁止跳过子步顺序；禁止无备份 migrate
- 禁止新域字段进 old 事务 append 的必填（全部可选增量）
- 禁止工单注入做 chapter 硬过滤；禁止 240 护栏类自造容量设计（注入 ≤3+全量兜底已定）
- 禁止 foreshadow 加 type 字段（前缀派生 + check 校验即可）

## 8. 提交规范

每子步一个提交：
```
feat(U3.1): schema 4→5 quality_tickets 域——工单开/注入/关闭环 + 翻译层 + migrate 幂等
feat(U3.2): debts+evidence 域——债务到期核对 + 溯源纯增
feat(U3.3): learned_patterns 域——细纲命中筛选注入 + 经验.md 视图
feat(U3.4): reading_power 域——8 钩子/7 微兑现标注 + 正文 hash 防覆盖 + taxonomy 冷路径
```

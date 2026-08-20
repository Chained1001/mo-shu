# moshu-write 审计报告

- 审计日期：2026-08-21
- 对象：`skills/moshu-write/`（88 文件 / 81 md / 6 运行时脚本 + 1 pyc）
- 方式：只读审计（引用图静态分析 + 全量流程文档通读 + 守卫直跑 + 运行时脚本 fixture 实测）

## 一、结论

**结构与卫生：优秀。** 引用层零死链、零孤儿（80 份 references 全部有入边，32 张题材卡索引全覆盖）；术语表零违例；容量常量文档与代码逐一对齐；**清单类断言全部准确**（craft-cards 6 / beat-cards BC-001~012 / scene SC-001~006 / naming NC-001~005 / 人物主题卡 8，实测与声明一一相符）。

**真正的问题只有一类：V2 批 3a / 批 5 / 批 6 三个新能力，在三条写作车道（日更 / 写指定章 / 大修）上接线不完整。** 脚本层全部建成且实测可用，缺的是"谁指示 AI 用它"的生产端入口。这不是施工违规——`docs/规格-V2/批3a-信息差域.md` §3 改动清单从未要求改日更/单章的事务字段清单；属规划层的接线缺口，正对上《执行总纲V2》附录 D 雷区 #4「未接线 vs 已删除」。

## 二、阻断级：0 项

无违反规格、无破坏契约、无脚本失效、无副本不一致。

## 三、需修级：1 项

### W1 信息差链路缺"登记入口"，下游两个消费者恒空转

- **现象**：批 3a 的信息差域（G-ID 体系）在 moshu-write 的写作流程文档里没有任何写入指令，导致派生视图 `追踪/信息差.md` 在真实日更路径下永远为空表。
- **证据**：
  - 建成端 ✓：`skills/moshu-write/scripts/tracking_commit.py:50-54`（`GAP_ID`/`READER_KNOWN`/`GAP_STATUSES`/`KNOWERS_MAX`）、`:600-618`（`render_information_gaps`）、`:734`+`:775-802`（delta 键 `information_gap_changes`）、`:893`（state 域 `information_gaps`）、`:1164`（派生视图 `信息差.md`）。
  - 消费端 ✓：`skills/moshu-write/scripts/check-prose-candidates.js:132-171`（解析 `| G\d{3,}` 行出 `gap_touch` 候选）；`tracking_commit.py` 的 `volume-report`「信息差未兑现清单」。
  - 生产端 ✗：`skills/moshu-write/references/workflow-daily.md:85` 明确枚举每章事务要提取的键——`result / character_changes / foreshadow_changes / timeline_events / constraints / next_chapter_commitments`，**不含 `information_gap_changes`**；`skills/moshu-write/references/workflow-chapter.md:85`（步骤 12 更新追踪）同样不含。
  - 全 `skills/moshu-write/**/*.md` 中 `追踪/信息差.md` **零命中**。唯一那行由批 3a 加进 `volume-review.md`（`git show daaf1da -- skills/moshu-write/references/volume-review.md`），批 3c 重写第一步时整行替换掉了（`git show 57b3fdf -- 同文件`）。
  - 双轨未搭桥：写前准备用的是另一套信息差——`设定/题材定位.md` 的「信息差登记表」+ **INF-ID**（`references/artifact-protocols.md:221-229` 定义，`references/workflow-chapter.md:30`、`:62`、`references/workflow-setup.md:238` 消费），与追踪 schema 的 **G-ID** 并行，无任何文档说明二者如何对应。
- **影响**：批 5 三类候选中的「信息差兑现」在实操中永不触发；批 3c 卷报告的「信息差未兑现清单」恒空；批 3a 的 schema 投入没有产出。
- **建议修法（最小改动，纯文本、不动代码）**：
  1. `workflow-daily.md:85` 的键枚举追加 `information_gap_changes`（标注可选），并指向 `tracking-transaction.md`「信息差事务」节（该节 `:150-184` 已有完整字段表与示例）；
  2. `workflow-chapter.md` 步骤 12 同步一句；
  3. `workflow-chapter.md` 写前准备 (13) 或 `artifact-protocols.md:229` 补一句 INF↔G 关系（`设定/题材定位.md` 表=写前规划登记；`追踪/信息差.md`=写后事务登记，正文兑现后由事务更新 G 条目）。
- **预估改动量**：3 个文件、约 4-6 行。**注意预算**：`workflow-daily.md` 当前 doc-budget 余量为 0（见 W4），加字前须先删等量旧文本或显式调高 budget。
- **验收**：`bash scripts/check-behavior-contracts.sh`、`bash scripts/check-doc-budget.sh`、`bash scripts/static-check.sh` 全绿；`bash scripts/test-writing-pipeline.sh` 保持绿。

## 四、候选级：4 项

### W2 候选机检只在日更车道
- **现象**：`check-prose-candidates.js` 全仓仅 1 处调用点。
- **证据**：`references/workflow-daily.md:130`（批末确定性收尾链）是唯一命中；`references/workflow-chapter.md:148-149`「确定性收尾」只列 `check-ai-patterns.js` → `check-outline-copy.js` → `normalize-punctuation.js` → `check-degeneration.js`；`SKILL.md:46`「写指定章」走 Phase 4 → `workflow-chapter.md`，不加载 daily；大修经 `references/workflow-revision.md:96` 引用继承 workflow-chapter，因此同样没有。
- **影响**：单章 / 大修路径拿不到候选呈报（不影响正确性，只损失信息）。
- **修法**：`workflow-chapter.md`「确定性收尾」末尾加一句"（候选机检 `check-prose-candidates.js` 可在收尾后运行，永不拦截）"。改动量：1 文件 1 行（同样受预算约束，余量 51）。

### W3 工单只在大修车道
- **现象**：日更流程不查 open 工单。
- **证据**：`review_tickets.py` 在 moshu-write 侧仅 `references/workflow-revision.md:81-83` 提及；`references/workflow-daily.md:25`「审查记录」只读 `.moshu-review/review-log`。
- **影响**：日更批前若有未处置的 blocking 工单，流程看不见——与批 6「防审查发现无人跟进」的意图有缺口。
- **修法**：`workflow-daily.md:25` 补半句"并查 `review_tickets.py list --status open`（有 open 项先按 workflow-revision 工单处置节处理）"。改动量：1 文件 1 行。

### W4 热路径预算余量枯竭
- **现象**：`references/workflow-daily.md` 用量 11500 / 预算 11500，**余量 0**。同组：`SKILL.md` 余 114、`workflow-chapter.md` 余 51、`anti-ai-writing.md` 余 36、`banned-words.md` 余 23；路径组「长篇日更主会话」余 215、「长篇开书」余 224、「正文 agent 上下文」余 97。
- **证据**：用 `scripts/check-doc-budget.sh` 同一度量（去空白字符数）复算，OVER 0 项但全线 <1% 余量。
- **影响**：W1/W2/W3 三项文本级修法都会立刻撞墙，必须成对做"删旧+加新"。
- **修法**：在做 W1-W3 时同批处理——优先删 `workflow-daily.md` 内与 `workflow-chapter.md` 重复的写前准备复述（该文件 `:5-9` 已声明"本文件不另立一套"，可再压缩），或在 `scripts/doc-budget.json` 显式调高并写清理由。

### W5 eval 断言虚化（永远为真）
- **现象**：`evals/scenarios/日更一章/README.md:21` 把「`追踪/信息差.md` 存在且非空（含 `| ID |` 表头）」列为 [机检] 项，但 `tracking_commit.py:601-607` 无条件输出表头——零登记时该断言也必过，**测不出"从没人登记过"**。
- **影响**：给人"信息差已在跑"的假信号，掩盖 W1。
- **修法**：W1 修好后，把断言改为"含至少一行 `| G` 数据行（若本章确有信息差登记）"，或降级为人工项。改动量：1 文件 1 行；须同步 `bash scripts/check-eval-scenarios.sh` 保持绿（该守卫校验 [机检] 标记数 ≥3/剧本）。

### W6 意象候选在"相邻重复"输入下自包含（最低优先）
- **现象**：造 6 个连续「灵光」时输出 5 条互含候选（灵光 11 / 光灵 5 / 灵光灵 5 / 光灵光 5 / 灵光灵光 5）；改成真实分布（8 次分散）后输出干净的 1 条。
- **证据**：实测（见六）；仓库自带 fixture `scripts/test-prose-candidates.js:23` 正是相邻重复写法。
- **影响**：真实语料无影响；仅让读测试的人误以为噪音正常。
- **修法**：不建议改检测器（真实场景已正确）。可选：把测试 fixture 改成分散分布，使断言更贴近真实语料。改动量：1 文件 1 行（**注意**：改测试 fixture 前须确认不弱化断言，遵守"禁止改断言变绿"）。

## 五、覆盖矩阵

| 收口 | 覆盖情况 |
|---|---|
| `scripts/behavior-contracts.json` | **11 条契约全部指向 moshu-write**（SKILL.md 2 / workflow-chapter 3 / workflow-daily 4 / tracking-transaction 1 / workflow-revision 1），含批 5「候选永不拦截」、批 6「工单处置」 |
| `scripts/shared-assets.json` | **36 组全部与 moshu-write 相关**；它是 22 组的 canonical 源（含 `tracking_commit.py`、`tracking-transaction.md`） |
| `scripts/doc-budget.json` | 7 个文件 + 3 个路径组登记（见 W4） |
| `scripts/current-contract.json` | 8 项 `required_outline_sections` 与 `workflow-chapter.md:15` 细纲必填字段逐项吻合 |
| 正式回归 | `test-tracking-commit.py`、`test-tracking-workflow-contracts.py`、`test-prose-candidates.js`、`test-writing-pipeline.sh`、`test-outline-copy.sh`、`test-ai-patterns.sh`、`test-degeneration.sh` |
| eval | `evals/scenarios/{日更一章,开书}`（审查工单剧本属 review 侧） |
| **盲区** | ①`references/` 的 80 份方法论内容质量无守卫（只守可达性与预算，属设计选择）；②三条车道的能力对称性无守卫（W2/W3 就是这么漏的）；③`.claude-plugin/marketplace.json` 的 version 无守卫（见总计划 G1） |

## 六、实测记录

| 命令 | 结果 |
|---|---|
| 引用图分析（python 内联，basename 双向匹配） | 死链 0 / 孤儿 0 / 32 张题材卡全部被 `genre-prose-cards.md` 索引命名 |
| `python scripts/static-check.py` | 0；Total 10 / Pass 10 |
| `python scripts/skill-numbering.py check` | 0；PASS 199 |
| `python scripts/check-behavior-contracts.py` | 0；11 条在位 |
| `python scripts/check-current-skill-contracts.py` | 0；全 PASS |
| `python scripts/check-agent-template-rules.py` | 0；7 模板 ok |
| `python scripts/sync-shared-assets.py check` | 0；36 组 / 51 副本 OK |
| `python scripts/test-tracking-workflow-contracts.py` | 0；14 tests passed |
| doc-budget 度量复算（node 内联，与守卫同算法） | OVER 0；余量见 W4 |
| `node skills/moshu-write/scripts/check-prose-candidates.js --prose … --gaps … --json` | 0；`gap_touch` 命中 G001、已兑现 G002 正确不报、`blocking_count: 0` |
| 同上不带 `--gaps` | 0；`degraded: ["style_not_provided","gaps_not_provided"]`，降级不报错 |
| 卡片计数（正则数标题） | craft 6 / beat 12 / scene 6 / naming 5 / 主题卡 8，全部与声明一致 |
| 术语禁用别称扫描（9 个别称 × 81 文件） | 1 命中，人工复核为假阳性（`workflow-daily.md:132`"为受影响章节提交"是正常句子） |

**环境限制（非缺陷）**：审计当时 `bash` 与子进程捕获被沙箱拒绝，`test-prose-candidates.js`（`spawnSync` pipe → `status=null`，`:36`）、`test-tracking-commit.py`/`test-review-tickets.py`（`tempfile` chmod → `WinError 5`）无法本地复跑；改用直接调用运行时脚本等价验证。策略放开后已另起全量守卫基线复跑。

## 七、整改计划

| 编号 | 级别 | 修法 | 改动量 | 依赖 | 验收命令 |
|---|---|---|---|---|---|
| W1 | 需修 | 日更/单章事务键枚举补 `information_gap_changes`；补 INF↔G 关系一句 | 3 文件 / 4-6 行 | 须与 W4 同批（预算） | `check-doc-budget.sh` + `check-behavior-contracts.sh` + `static-check.sh` + `test-writing-pipeline.sh` |
| W2 | 候选 | `workflow-chapter.md` 收尾节加候选机检一句 | 1 文件 / 1 行 | W4 | `check-doc-budget.sh` + `check-behavior-contracts.sh` |
| W3 | 候选 | `workflow-daily.md:25` 补查 open 工单半句 | 1 文件 / 1 行 | W4 | 同上 |
| W4 | 候选 | 腾预算：压缩 `workflow-daily.md` 与 chapter 重复叙述，或显式调高 budget 并写理由 | 1-2 文件 | 无（W1-W3 的前置） | `check-doc-budget.sh` |
| W5 | 候选 | 日更剧本信息差断言改为可判真伪（或降人工项） | 1 文件 / 1 行 | W1 之后 | `check-eval-scenarios.sh` |
| W6 | 候选 | （可不做）测试 fixture 改分散分布 | 1 文件 / 1 行 | 无 | `test-prose-candidates.js` |

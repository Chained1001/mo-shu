# 规格 · 批 B69：evaluator 三型扩展（细纲批/设定包/修订包评审）——写-审配对补全

- 版本：v1.1（2026-08-28 审核轮前置补入：settings 型加题材卡置信度复核——自 B71 改动5 移来，序 B69→B71 需补行先在。v1.0 旗舰起草；来源：作者裁定立项「写一般要搭配审核」。**目的：把审查隔离（宪法 Agent 判据 3）补到细纲/设定/修订三个自审盲区**——不新建 agent，扩展现有 evaluator 评审对象类型）
- **目的**：解决「细纲/设定/修订三个环节是主会话自己设计自己检查（写-审不配对，宪法审查隔离的现存违例）」；新增能力：细纲批评审（写正文前最后一道语义闸——错纲不落笔）、设定包评审（含防撞独立复核）、修订包独立视角（裁决前参考）。
- 性质：evaluator 模板扩展（agents_version 39→**40** bump 全套）+ 三处流程接线。单批单提交。

## 一、设计依据

| 新型 | 防的自审 | 现状（实证） |
|---|---|---|
| `detail-batch` 细纲批评审 | 设计细纲的和检查细纲的是同一主会话上下文（确认偏误）——错纲落笔=数千字白写+追踪污染 | 批末只有确定性核对（预算 Σ/交叉核对，:23-24），无独立语义评审 |
| `settings` 设定包评审 | 设定建档无语义评审，矛盾往往到正文才暴露 | 细纲后设定补全自动建档（outline-workflow「细纲后设定补全」节）零复核；B65 防撞三维是主会话自检 |
| `revision` 修订包评审 | 修订裁决前只有确定性影响分析（impact_scan），无「这改动伤不伤人物弧/伏笔链/读者契约」的独立视角 | 修订流①影响分析→②作者裁决（:9/:23），裁决缺独立输入 |

**与既有的关系**：正文已有四 reviewer（最强）、大纲/卷纲已有 evaluator 三型——本批补全后全产物域写-审配对齐。**防撞三维的定位（v1.0 定死）**：B65 流程不变（主会话构造对照表+登记免责），settings 型做**独立复核**（漏判高重合/免责滥用/多源判定误降），不接管构造。

## 二、现状事实（flash 开工前复核）

1. `skills/moshu-setup/references/templates/agents/moshu-evaluator.md`：130 行/3401 字，frontmatter model: sonnet / maxTurns: 15；eval_type 枚举 `outline | unit | final | full`（:122，B55 加 full+score 制）；三维度准则（编辑/作者/读者）与 JSON 输出结构在位；审稿令牌/只读 tools/fallback 自评在位。
2. 接线点：outline-workflow 批末清单五步（:20-24，本批加第 6 步）+「细纲后设定补全」节；revision-workflow ①影响分析（:9）与②作者裁决（:23）之间。
3. **排队预算账（三批叠加，一次算清）**：outline-workflow 实测 7230——B68a 预估 +450、B70 预估 +90、本批预估 +80 → 约 7850 ≤ B68 将调的 7900（**余量仅 ~50，三批全部落地后须 node 复测，超则压缩**）；revision-workflow 实测 2944——B70 +40、本批 +40 → 约 3024 **超 3000** → 本批随动调 3000→**3100**（why 记排队判因）。
4. agents_version 当前 **39**（bump 全套流程：preview→confirm+UPGRADING+指纹）。

## 三、文件级改动清单

**1. evaluator 模板（agents/moshu-evaluator.md）**：
- eval_type 枚举扩为 `outline | unit | final | full | detail-batch | settings | revision`；
- 「评审对象类型」表加三行（被评什么/典型来源）；
- 新增「三型差异化评审准则」节（每型×三维度，苏格拉底式问题，~40 行）：
  - **detail-batch**：编辑=钩子链连贯性（相邻章钩子-承接断没断）/预算分布（密点是否堆在同章）/与场景表·卷纲单元的一致性（B68 产物对照）；作者=一进一出呼吸（有没有一章清账或章章欠账）/密疏设计是否服务章节定位；读者=这批读完追读动力一句话/最可能的弃读章位与那里有什么兜底；
  - **settings**：编辑=设定内部一致性/与既有设定清单逐项矛盾/与题材定位冲突；**题材卡置信度复核（v1.1 前置补入，原 B71 改动5 移此——B69 先于 B71 施工）**——本书主题材卡的置信度标注与实测写作体验是否相符（偏高/偏低/相当，呈报）；作者=新鲜度（设定是不是套路堆砌）/防撞三维**复核**（对照表有没有漏判的高重合/「登记免责」是否被滥用/多源共性有没有误降）；读者=设定信息量是否超载（读者第几章能跟上）；
  - **revision**：编辑=影响面复核（影响分析列的波及面之外还有没有漏的——人物弧/伏笔链/时间线）；作者=改法工艺（最小改动达成目标还是过度修改）；读者=契约影响（读者已建立的期待是否被此改背叛——换书债视角）；
- 输出 JSON：`eval_type` 枚举随扩，其余结构复用（editor/author/reader/if_one_change/overall）；三型不填 score（score 仅 full）；
- spawn 契约（「被调用协议」节）加三型的 target/上下文参数说明：detail-batch 传 细纲批文件列表+场景表路径+卷纲路径；settings 传 新建设定文件清单+既有设定目录+B65 对照表路径（如有）；revision 传 变更提案+影响分析产物+受影响章清单。

**2. outline-workflow 接线（两处）**：
- 批末清单加第 6 步「**批末细纲评审（B69，写正文前最后一道语义闸）**」：spawn evaluator（eval_type=detail-batch），报告呈报作者处置后进正文；agent 不可用 fallback 主会话自评（对照三维度问句，标注 Fallback）；~+60 字；
- 「细纲后设定补全」节尾加一句：本批新建设定 ≥3 个文件时可选触发 settings 评审（eval_type=settings）；~+30 字。

**3. revision-workflow 接线（①②之间）**：加可选步「修订评审（B69）：裁决前可 spawn evaluator（eval_type=revision）取独立影响视角——只供作者裁决参考，不构成裁决依据」；~+40 字。

**4. agents_version 39→40**：bump preview→confirm 全套 + UPGRADING v40 条目 + 指纹重登记。

## 四、验收命令（fixture 放 `/.tmp/tests/B69/` 用完即删）

1. 模板：eval_type 枚举七值 grep；三型准则节三维度齐（每型 3 组问题）；spawn 契约三型参数说明在位；模板只读纪律/令牌/fallback 未动。
2. bump：agents_version 40 全 SKILL 一致 + UPGRADING v40 条目 + 指纹重登记 + check-agents-version-sync 绿。
3. 接线：批末第 6 步/设定补全触发句/修订流可选步 grep 在位；fallback 语句在位。
4. 行为级（评审模拟）：模板 JSON 输出结构以 eval_type=detail-batch 造一份合法样例过 validate（若模板含结构说明则人工对照；无脚本校验则文档级核验即可）。
5. 预算：revision-workflow 实测超 3000 → 调 3100（why 记排队判因：B70+B69 两批叠加，git diff 核对原值）；outline-workflow 增量入 7900 界内（**若 B68/B70 已先行落地，按三批叠加实测复核，超则先压缩再调**）；组随动。
6. 守卫矩阵全绿（static/behavior/current-skill/agent-template-rules——模板规则守卫须过）。

## 五、禁止事项

1. **不新建 agent**（扩展现有 evaluator——§5 决策树第 2 条）；tools 保持只读三件套；审稿令牌机制不动。
2. **B65 防撞流程不动**——settings 型只做对照表的独立复核，不接管构造/不改变判定规则。
3. 三型评审全部**只呈报不拦截**：detail-batch 报告作者处置后才进正文（处置=采纳修改或明示跳过）；revision 评审明确「不构成裁决依据」。
4. score 字段仅 full 型——三新型不引入打分（B60 前例：评分只做趋势信号，细纲/修订场景无分数消费方）。
5. agents_version bump 走完整流程；评审报告不落盘新产物类型（会话呈报，与现有 evaluator 模式一致——避免产物面扩散）。

## 六、预算耦合（排队账见 §二.3）

revision-workflow 3000→**3100**（B70+B69 叠加）；outline-workflow 增量并入 7900 界内（三批叠加后实测复核）；组 长篇开书/构建路径 随动按实测。evaluator 模板不在 doc-budget（部署物非热路径文档）。

## 七、提交规范

`feat(build+write): B69 evaluator 三型扩展——detail-batch 细纲批评审（写正文前语义闸）/settings 设定包含防撞复核/revision 修订包独立视角；写-审配对补全全产物域；agents_version 40`

## 八、风险与回滚

风险 1：细纲批评审每 5 章一次 spawn 的 token 成本（~3-5k/批）——批量为最高频触发点，实测门量实际值后再定是否设跳过阈值。
风险 2：评审意见与主会话设计冲突的裁决归属——报告只呈报，采纳与否归作者（与候选语义同构）。
回滚：模板+三接线 revert 即恢复；agents_version 40 回退走 bump 工具反向或 revert 提交。

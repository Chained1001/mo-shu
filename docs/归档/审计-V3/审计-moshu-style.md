# moshu-style 审计报告

- 审计日期：2026-08-21
- 对象：`skills/moshu-style/`（2 文件：`SKILL.md` 156 行 / `references/style-learn-sop.md` 129 行；**零运行时脚本**）
- 定位：最年轻的 skill（v1.0.0），产出 `文风库/文风.md`，是 moshu-write 每章写前准备 (d) 文风召回的**唯一来源**。

## 一、结论

**文档本身质量高**：范围声明清晰（表达层 vs 题材层的"通用性铁律"是这套 skill 里少见的、把"什么不该学"写死的边界）、confidence 三级语义完备、降级路径明确（解释器不可用 → 标 low 不假装 high）、生成自检 3 条可验。零死链、零术语违例。

**但它是全仓唯一"零守卫收口"的 skill，代价已经真实发生**：它的产出契约（`文风库/文风.md` 字段口径）与下游消费者（批 5 候选机检 `check-prose-candidates.js`）**字段口径不一致，且实测导致确定性误报 + 主指标失效**。这不是推断，是跑出来的（见 §六）。

## 二、阻断级：0 项

（说明：下述 S1 虽是确定性错误输出，但候选类机检结构上 `blocking_count` 恒 0、永不拦截流程，按本轮分级定义归需修级而非阻断级。）

## 三、需修级：2 项

### S1 文风产物与候选机检的字段口径错配：一个指标恒误报、两个指标恒失效

- **现象**：严格按 `moshu-style` 自己的模板生成 `文风库/文风.md`，交给 `check-prose-candidates.js --style` 后：
  1. **`avg_paragraph_chars` 恒误报**——解析器把模板里的「段落节奏：段落平均句数 **2.0**」抓成"段均字数基线 2-2"，而正文真实段均汉字 58.8，必然判为偏离；
  2. **`avg_sentence_len` 恒失效**——解析器要字面量 `平均句长`，模板产出的是「平均 **12 字**」，永不匹配；
  3. **`dialog_line_ratio` 无数据来源**——解析器要 `对话…N%`，而模板「对话技法」节只有定性描述（潜台词模式/标签习惯/语气区分），不产百分比。
- **证据（代码事实）**：
  - 解析器锚点：`skills/moshu-write/scripts/check-prose-candidates.js:66-69`（`/平均句长[^0-9]{0,10}(\d{1,3})/`、`/句长分布[^0-9]{0,20}平均句长…/`）、`:70-73`（`/段均字数…/`、`/段落节奏[^0-9]{0,15}(\d{1,4})/`）、`:74`（`/对话[^0-9]{0,10}(\d{1,3})\s*%/`）；语义在 `:107-117` 明确按 `han / paragraphs.length`（**汉字数/段**）比对。
  - 产出口径：`skills/moshu-style/SKILL.md:98`（`句长分布：{… / 平均 N 字}`）、`:102`（`段落节奏：{段落平均句数（统计）+ …}`）、`:112-116`（对话技法三项均为定性）；统计底座 `skills/moshu-style/references/style-learn-sop.md:53` 输出 `avg_len=…; para_avg_sents=…`，`:65` 明确 `para_avg_sents` 是**段落平均句数**。
- **实测（见 §六）**：模板口径 → `{"type":"style_drift","metric":"avg_paragraph_chars","actual":58.8,"baseline":"2-2"}`（假报）且无 `avg_sentence_len`；改成解析器口径 → 立刻产出 `avg_sentence_len actual 20.9 / baseline 12-12` 与 `dialog_line_ratio actual 18.2 / baseline 35-35`（能力本来存在）。
- **影响**：批 5「句式偏离基线」这一类候选在真实链路上**三个指标全不可用**：一个持续输出错误结论（污染作者判断——每章都说"段落远超基线"），两个静默不工作（作者以为在跑，其实没有）。这也解释了为什么此前无人发现：候选永不拦截 → 不会红 → 无守卫覆盖 → 无人核对。
- **建议修法（两侧同步，最小改动）**：
  1. **产出侧对齐（主）**：`moshu-style/SKILL.md` 模板「整体语感」三行改为解析器可读口径——`句长分布：… / 平均句长 N 字`、新增 `段均字数 N 字`、`段落节奏：段落平均句数 N`（保留原语义但与"段均字数"分离）；对话技法节增一行确定性字段 `对话行占比 N%`。同时 `style-learn-sop.md:53` 的统计脚本补两个输出字段：`avg_para_chars`（非空白汉字数/段）与 `dialog_ratio`（行首为引号的行占比，与解析器 `:90` 的判定一致）。
  2. **消费侧兜底（防存量文风文件继续误报）**：`check-prose-candidates.js:70-73` 的段落锚点加负向排除——`段落节奏` 后紧跟「句数」时不作为 `段均字数` 锚点（或把 `段落平均句数` 显式排除）。
  3. **加守卫（把契约变成可测不变量）**：`scripts/test-prose-candidates.js` 增一个用例——fixture 用**按 moshu-style 模板真实字段**写的文风文件，断言能解析出 `avg_sentence_len` 锚点且不产出 `avg_paragraph_chars` 假候选。这是本项唯一能防复发的手段。
- **预估改动量**：`moshu-style/SKILL.md` 约 4 行、`style-learn-sop.md` 约 3 行（脚本 print 串 + 字段语义各 1）、`check-prose-candidates.js` 约 3 行、`test-prose-candidates.js` 约 25 行（新用例）。共 4 文件。
- **验收**：`node scripts/test-prose-candidates.js` 绿（含新用例）；手工复跑 §六 两组实测——模板口径必须产出 `avg_sentence_len` 且**不再**出现 `avg_paragraph_chars` 假报。

### S2 `moshu-style` 在索引类文档缺席（与 G2 同源，此处记归属）

- **现象/证据/修法**：见 [审计-跨skill与仓库级.md](审计-跨skill与仓库级.md) **G2**（`README.md` / `README_EN.md` Skills 表、`CONTRIBUTING.md`、`docs/architecture.md` 四处缺席；路由表与 marketplace 已在位）。
- **本 skill 视角的额外影响**：`docs/architecture.md` §1 缺 `文风库 → 写作每章召回` 这条链路，而它在 `workflow-chapter.md` 写前准备 (d) 是**每章强制检查**项（缺失要 AskUserQuestion 交互提醒）——架构图漏掉的是一条热路径，不是边角功能。

## 四、候选级：2 项

### S3 零守卫收口（结构性盲区）

- **现象**：`moshu-style` 不出现在任何收口清单里。
- **证据**（逐文件 grep 实测，全部 `✗ 无`）：`scripts/behavior-contracts.json`、`scripts/doc-budget.json`、`scripts/shared-assets.json`、`scripts/current-contract.json`、`scripts/README.md`、`.github/workflows/cross-platform.yml`、`CONTRIBUTING.md`。
- **判定**：其中**合理的**——无脚本故不进 `shared-assets`/CI/`scripts/README`；SKILL.md 属冷路径（仅 `/moshu-style` 时加载）故不进 `doc-budget`（该文件 `:9` 明示"冷路径不登记"）。**不合理的**——产出契约（`文风可用：是`、锚点 ≥1 段、句长字段）被两个消费者依赖（`workflow-chapter.md` (d) 两级检查、`check-prose-candidates.js`），却无任何机读守卫，S1 正是这个盲区的产物。
- **修法**：不新增机制（`AGENTS.md` §5 决策树）——按 S1 第 3 条把契约挂进已有的 `test-prose-candidates.js`；如需更强，另在 `scripts/behavior-contracts.json` 加一条 `style-profile-fields`（`skills/moshu-style/SKILL.md` 必含 `平均句长` 与 `文风可用`）。改动量：1 文件 / 约 6 行。

### S4 链接抓取"暂不支持"的悬置声明

- **现象**：`SKILL.md:43` 写「链接抓取暂不支持（后续增强，复用 moshu-cdp）」——是**已知未实施**声明，非缺陷；但无对应 issue/规格锚点，属"未接线 vs 未实施"边界（总纲附录 D 雷区 #4 的邻居）。
- **修法**：保持现状即可（声明诚实、有替代路径）。若要收紧，可改为"仅支持本地文件/粘贴文本"的正向表述，去掉对未来能力的承诺。改动量：1 文件 / 1 行。**可不做**。

## 五、覆盖矩阵

| 维度 | 状态 |
|---|---|
| 引用图 | 死链 0 / 孤儿 0（`style-learn-sop.md` 被 `SKILL.md:61` 引用） |
| 术语表合规 | 违例 0 |
| 流程闭环 | Step 1-6 完整：确认对象 → 获取（含 GBK 转码）→ 轻量准备（标准档 5-6 章 / 最小档 2-3 章）→ 分析（4 项）→ 落盘（覆盖须 AskUserQuestion）→ 收尾衔接。**闭环成立** |
| 三层分工 | 遵守：句长/标点/段句数走确定性脚本（`style-learn-sop.md:33-55`），词频归纳明示"中文分词无轻量确定性方案，由 AI 完成"（`:72`），覆盖决策交作者 |
| 产物契约（内部一致性） | SKILL.md 模板 ↔ style-learn-sop 统计字段一致（`avg_len`→平均 N 字、`para_avg_sents`→段落平均句数） |
| 产物契约（跨 skill） | **不一致**（S1）——与 `check-prose-candidates.js` 口径错配 |
| 守卫覆盖 | **零**（S3） |
| 版本口径 | `SKILL.md` 1.0.0 == marketplace 1.0.0 ✓（10 个 skill 中唯一无漂移风险的新 skill） |

## 六、实测记录

| 检查 | 命令/方式 | 结果 |
|---|---|---|
| 引用图 + 术语 | 机械扫描（2 份 md） | 死链 0 / 孤儿 0 / 术语违例 0 |
| 守卫收口归属 | 7 份收口文件逐一 grep `moshu-style` | 全部无命中 |
| **S1 正向复现** | 按 `SKILL.md:88-131` 模板 + `style-learn-sop.md:53` 实测输出值造 `文风.md`，跑 `node skills/moshu-write/scripts/check-prose-candidates.js --prose evals/samples/prose-clean.md --style <该文件> --json` | exit 0；candidates 含 `{"type":"style_drift","metric":"avg_paragraph_chars","actual":58.8,"baseline":"2-2"}`（**假报**）；**无** `avg_sentence_len`；`degraded: ["gaps_not_provided"]` |
| **S1 对照组** | 同上，文风文件改为解析器口径（`平均句长 12 字` / `段均字数 60` / `对话占比 35%`） | exit 0；产出 `avg_sentence_len actual 20.9 baseline 12-12` 与 `dialog_line_ratio actual 18.2 baseline 35-35`——证明能力存在，只是口径对不上 |
| 版本比对 | UTF-8 安全解析 marketplace vs frontmatter | 1.0.0 == 1.0.0 |

（临时 fixture 位于 `.tmp/tests/audit-style/`，收尾删除。）

## 七、补充发现（子代理交叉审计，2026-08-21 第二轮）

独立子代理对同一 skill 做了第二轮深审，**印证了 S1/S2 并补出 4 条我漏掉的**，另修正了我一处措辞。以下为增量：

### S1 补强：这是**静默降级**，且有第二个消费方也要求「平均句长」

- `check-prose-candidates.js:82-85` 只在**三个锚点全失败**时才 push `style_baseline_unparsed`；部分失败**无任何标记** → 句长带丢失时脚本一声不响（`AGENTS.md` §4 反模式 #7「静默降级」明列禁止）。
- **第二个消费方**：`skills/moshu-setup/references/templates/agents/moshu-narrative-writer.md:207` 也按字面「平均句长」定位（"读取 `文风库/文风.md` 有数值的「句长分布」字段（…**平均句长**，`confidence: high`）"）——找不到就退到"以锚点片段语感为准"。**故一处 +3 字可同时修好两个消费方。**
- 子代理三组 fixture 实测（A 模板照抄 / B 脚本友好 / C 占位 stub）证明：A 无 `avg_sentence_len` 且无降级标记；B 改成「平均句长 26 字」后解析成功；C 全失败时 `style_baseline_unparsed` 确实出现——**反证 A 的"部分失败静默"是缺陷不是设计**。

### S2 补强：两个新细节

- `check-prose-candidates.js:90` 的 `dialogLines` 正则 `/^["“]/` **不认 `「`**，而 deslop 明确允许古言/日式保留「」（`deslop-workflow.md:316`）→ 中文网文常见引号风格下对话占比恒为 0%。
- **`--style` 在全仓流程文档中从无调用指示**：唯一调用点 `workflow-daily.md:130` 只写脚本名不带参数；`--style` 字样只出现在脚本自身（`:4/:185`）与 `docs/规格-V2/批5-候选类机检.md:36/:39`。→ 缺陷目前处于**休眠态**（没人被指示传 `--style`），属"脚本层建好、流程不指示"的接线缺口。
- 根因（有文档支撑）：`批5-候选类机检.md:39` 写"若 `--style` 提供且含可解析的**句长/段均字数**锚点"——规格按设想格式写，未对照 style 实际模板。

### S5 两级检查在手动路径与 explorer 快捷路径**语义不等价**（新增，需修级）

- 手动路径是**正查**：`moshu-write/references/workflow-chapter.md:39`「内容合规性（非空/非占位 stub、生成记录 `文风可用：是`、锚点 ≥1 段）」。
- 快捷路径是**反查**：`workflow-chapter.md:48` 把内容合规性委派给 explorer 的 `gaps.profile_degenerate`；而 `moshu-setup/references/templates/agents/moshu-explorer.md:174` 只判「`文风可用：否` → true」+「锚点片段全缺 → true」，**无正查、无"非空/非占位 stub"整体判定**。
- **后果**：缺少「生成记录」整段或缺 `文风可用` 那一行的 `文风.md`（生成中断的半成品）→ 手动路径判**不合规**、快捷路径判**合规**。而 `:43-48` 推荐走快捷路径。
- **修法**：`moshu-explorer.md:174` 改正查口径（"缺少 `文风可用：是`（含整段缺失/被截断）或写有 `否` → `profile_degenerate: true`"）。⚠️ 该文件是 agent 模板，按 `AGENTS.md` §3.3 需同步 bump `agents_version` 29→30 + 更新 `UPGRADING.md` → 改动量扩到 3 文件，**建议与其他 agent 模板改动合批**（setup 的 PM3 也改模板）。

### S6 守卫零覆盖的**直接后果已被定位**：`styleDriftCandidates` 全函数零测试（新增，需修级）

- `scripts/test-prose-candidates.js` 的三次 `run()` 调用（`:35/:60/:71`）**从未传 `--style`**，仅断言 `degraded` 含 `style_not_provided`（`:49/:65`）→ `check-prose-candidates.js:76-130` 整个 `styleDriftCandidates()`、`parseAnchor()` 与三组锚点正则**无任何正向或坏格式测试**。
- `scripts/README.md:53` 称该测试覆盖"降级（缺 style/gaps、坏格式）"——就 style 而言只覆盖了"缺 style"，**"坏格式 style"（`style_baseline_unparsed`）从未被测**。
- **这是 S1/S2 能长期潜伏的直接原因**，也是本项最高性价比的修法（见整改计划 S1-③）。

### 对我原文的一处修正（子代理指出，我采纳）

我在 S3 中写"V2 批 2 守卫扩面时它是否被漏掉"——**措辞不准**。`docs/规格-V2/批2-守卫扩面.md:9` 的目标是"叙述性 skill 计数进守卫 + 测试文件带守护对象声明 + 测试纪律成文"，§3 改动清单 8 行无一涉及具体 skill，**其范围本就不含 per-skill 覆盖**。准确说法是：**V2 九批中没有任何一批把 moshu-style 纳入守卫范围**，它自 CHANGELOG v1.1.2 拆出后一直未走 `AGENTS.md` §3.1 的"新增是否接入现有机制"自检。

### 另外三条候选（新增）

| 编号 | 发现 | 证据 | 修法 |
|---|---|---|---|
| S7 | `gaps.profile_stale` 由 explorer 产出但**无任何消费方** | `moshu-explorer.md:177/:178/:320` 产出；`workflow-daily.md:78-79` 只分支 `profile_missing`/`profile_degenerate`；全仓 `profile_stale` 仅这 3 处 | 删该字段，统一收敛到 `profile_degenerate`（与 S5 合批则无额外 agents_version 成本） |
| S8 | `文风库/_source.md` 未进资产协议表 | 生产侧 `SKILL.md:48`、`style-learn-sop.md:9/:34/:97`（`grep -F` 回查目标）；资产表 `moshu-write/references/artifact-protocols.md:98` 只登记 `文风库/文风.md` | 资产表 +1 行（该文件未进 doc-budget，无预算压力） |
| S9 | 《执行总纲V2》`:144` 声称该脚本吃"句长/**标点**基线"，脚本**零标点解析** | `check-prose-candidates.js:66-74` 三组锚点无标点；而 style 确定性产出 6 个标点占比（`SKILL.md:100`、`style-learn-sop.md:53/:66`）——即存在一个**低成本增强机会**（破折号/省略号占比漂移候选，与 deslop 硬安全线天然联动） | (a) 只改文档使其与实现对齐（推荐）；(b) 若认为增强值得做，另立一批 |

### 另一处正面发现（记录，非缺陷）

style 对"解释器不可用"有**正确的降级设计**：`style-learn-sop.md:68`（跳过确定性统计、句长段写"解释器不可用"、`confidence: low`）、`:114-115` 失败模式表、`SKILL.md:148` 生成自检"不假装 high"。

## 八、整改计划（含补充发现）

| 编号 | 级别 | 修法 | 改动量 | 依赖 | 验收命令 |
|---|---|---|---|---|---|
| **S1** | **阻断** | ①`moshu-style/SKILL.md:98` 「平均 N 字」→「**平均句长 N 字**」（一处修两个消费方）②`style-learn-sop.md:60` 加"字段名照模板逐字写（`平均句长` 是下游解析锚点）" ③**`test-prose-candidates.js` 增 style 正向 fixture**（照模板逐字造 `文风.md`，断言 `avg_sentence_len` 能解析）——这条同时永久锁住 S1 与 S2 | 3 文件 / ~25 行 | 无（style 未进 doc-budget） | `node scripts/test-prose-candidates.js` + 复跑 §六/§七 实测 |
| **S2** | 需修 | ①删 `:72` 的 `段落节奏` 兜底正则（缺字段就诚实走 `style_baseline_unparsed`）②`:74` 对话正则收紧为 `对话行占比`③`:90` 补 `「`④`workflow-daily.md:130` 补 `--style`/`--gaps` 参数示例 | 1 脚本 3 行 + 1 文档 1 行 | ④受 `workflow-daily.md` 余量 0 约束 → 依赖 G5 | `node scripts/test-prose-candidates.js` |
| **S5** | 需修 | `moshu-explorer.md:174` 改正查口径 + bump `agents_version` 29→30 + `UPGRADING.md` | 3 文件 / ~5 行 | 与 setup 的 PM3 合批（同为 agent 模板改动） | `check-agents-version-sync.sh` + `check-agent-template-rules.sh` |
| **S6** | 需修 | 见 S1-③（同一条测试同时覆盖） | — | — | — |
| S3 | 需修 | 见 [G2](审计-跨skill与仓库级.md)（索引补登记 4 处） | 见 G2 | — | `check-story-numbers.sh` |
| S4 | 候选 | 文风契约挂进 `behavior-contracts.json`（挂消费侧 `workflow-chapter.md` 的"唯一来源"比挂生产侧更能守住不变量）；另建议把 `moshu-style/SKILL.md` 登进 doc-budget（实测 3966，budget 4000） | 2 文件 / ~10 行 | S1 之后 | `check-behavior-contracts.sh` + `check-doc-budget.sh` |
| S7/S8/S9 | 候选 | 删 `profile_stale`（与 S5 合批）/ 资产表 +1 行 / 总纲 `:144` 与实现对齐 | ≤5 行 | S7 随 S5 | `static-check.sh` |
| S10 | 候选（可不做） | `SKILL.md:43`「链接抓取暂不支持」改正向表述 | 1 行 | 无 | `static-check.sh` |

# moshu-analyze 审计报告

- 审计日期：2026-08-21
- 对象：`skills/moshu-analyze/`（10 文件：SKILL.md + 6 references + `scripts/{chapter_boundary.py, check_chapter_summary.py, merge-chapter-summaries.js}`）
- 方式：委派深审（含临时 fixture 真实跑三个脚本）+ 本人复核 AM2

## 一、结论

**结构健康，无阻断级。** 三个确定性脚本实测全部按文档行为工作（含 fail-fast）；`_progress.md` 的 `progress_schema_version: 2` 契约与实现、守卫三方一致；`拆文库/{书名}/` 产物结构与写作侧消费方（`current-contract.json` 的 `primary_benchmark_artifacts` = `剧情/情绪模块.md` + `剧情/节奏.md`）严格对齐，缺主产物为 fail-fast 而非静默降级。零死链零孤儿、术语零违例、版本无滞后（1.1.1 == 1.1.1）。

**问题集中在"确定性未落到脚本"**（可数比值靠模型手算、模型自造置信度常数）与**一条三方互斥的流程死锁**（多卷重起书）。

## 二、阻断级：0 项

## 三、需修级：4 项

### AM1 多卷重起书（每卷「第一章」）三方互斥，形成死锁

- **现象**：合法多卷结构（每卷章号从「第一章」重起）无法通过任何被许可的路径产出章节边界表。
- **证据（本人复核脚本参数面）**：
  - `references/analyze-workflow.md:114`：「剔完仍有重复章号时不要自行取其一：多卷书每卷从「第一章」重起是合法结构…标题列保留卷号消歧、章号列按全书连续序号重编」；
  - `:112`：「**禁止临时手写解析脚本**」；
  - `scripts/chapter_boundary.py:170-174`：`if issue:` → `if not args.dry_run and args.outdir:` → 打印「问题未解决前不落盘边界表」并 `sys.exit(3)`；重复章号在 `:129-130` 即判为 issue。**本人 grep 确认 argparse 只有 `--input/--outdir/--book/--author/--encoding/--dry-run` 六个参数（`:74-79`），无任何重编号/放行选项**。
  - 子代理实测：目录块造成 `第一/二/三章` 重复 → `连续性: 重复章号: [1, 2, 3]`、**exit 3**、`_progress.md` 未生成。
- **影响**：三条路全堵——脚本拒绝落盘、文档禁手写脚本、文档要求的"章号重编"无执行载体。实际后果是 AI 要么违规手写脚本，要么手工誊写整本边界表（914 章级不可行），要么放弃拆解。
- **修法**：`chapter_boundary.py` 加 `--renumber-volumes`（仅在"重复章号且存在卷标记"时允许）：章号列按全书连续序号重编、标题列前置卷名消歧，stdout 打印重编映射表供人工核对；`analyze-workflow.md:114` 改为指向该选项；跳号仍 exit 3。
- **改动量**：脚本 +30~40 行；文档 1 处 2 行。

### AM2 情节点硬下限 10 已具备确定性条件，却被显式排除在机检外 ✅本人复核成立

- **证据（本人 grep 核对）**：`scripts/check_chapter_summary.py:62` `p_count = sum(1 for l in lines if P_LINE.match(l))` —— 数已算出；`:65-66` 只用它做"三者一致性"（`p_count == tone_count == desc_count`），**全文无 `p_count < 10` 判定**。文档侧 `analyze-workflow.md:251`「**硬检查就是上面 4 条，没有更多。**」而 `:242` 又把"情节点 < 10"列为触发 sonnet 升级重试的典型质量失败项；下限只靠 agent 自检（`moshu-chapter-extractor.md:296` + `:196`）。
- **影响**：违反三层分工宪法「脚本做确定性」（`docs/执行总纲V2.md:29`）。haiku 输出 6 个情节点、格式全对 → 脚本报 PASS → 主线程不触发 sonnet 重试 → 下游 Stage 3 拿到密度不足语料且无痕迹。
- **修法**：`check_file()` 加 `if p_count < 10: fails.append(...)`（上限 40 只作提示）；同步 `analyze-workflow.md:244-251`「4 条」→「5 条」。**改动量**：脚本 +3 行；文档 2 处。

### AM3 质量阈值的可数比值全靠模型手算；关系置信度是自造常数

- **证据**：`references/material-decomposition.md:402-406` 三个指标（置信度 ≥0.85 / 覆盖率 85-95% / 重叠率 ≤35%）定义全是除法；`:429`「覆盖率 =（总数 − 散落数）/ 总数 × 100%」；`:350-351`「通过第三方评价推断（置信度标 **0.7**）」「通过共同出现频率推断（置信度标 **0.6**）」；这些又驱动 `analyze-workflow.md:103` 的「置信度 ≥0.85 自动合并」。
- **影响**：确定性算术交给模型 = 三层分工越界且不可复算；0.7/0.6 属 `AGENTS.md` 反模式 #5「自造数字参数」，等于让模型估数决定自动合并。
- **修法（不新增脚本）**：`material-decomposition.md:396-408` 标明"本节比值为 AI 手算自检口径，非机检门限"；`:350-351` 的 0.7/0.6 改为定性档位（复用 `:419-421` 已有的强/中/弱三层表述）；`analyze-workflow.md:103` 同步改档位表述。**改动量**：~8 行 + 1 处同步。

### AM4 CI 三处同步缺一处：`test-merge-summaries.js` 不在 CONTRIBUTING 本地清单

- **证据**：`.github/workflows/cross-platform.yml:88` ✓、`scripts/README.md:46` ✓、`CONTRIBUTING.md:116-155` 本地命令块**无该行**（node 类仅 `:127/:128/:145`）。
- **影响**：违反 `AGENTS.md §2.5`；改 `merge-chapter-summaries.js` 的人本地一把梭跑绿 ≠ CI 会绿。
- **修法**：`CONTRIBUTING.md:128` 后补 1 行（与 scan 的 SM6 合并为同一次改动）。

## 四、候选级

| 编号 | 发现 | 证据 | 修法 |
|---|---|---|---|
| AC1 | `_progress.md` 骨架把 Stage 0 预写成 `done`，概要缺失无 fail-fast | `chapter_boundary.py:199` 硬编码 `\| 0 概要+章节边界 \| done \|`；恢复机制 `pipeline-ops.md:88-95` 只校验 schema 与边界表，不校验 `概要.md` 存在性 | 改 `partial` + 恢复步骤补核对；~3 行。**存疑**：也可能是作者有意把"脚本产出即 Stage 0 完成"当契约，需裁定 |
| AC2 | `--dry-run` 遇连续性问题仍 exit 0，不能当预检门 | `chapter_boundary.py:170-177`（exit 3 被 `not args.dry_run` 收窄） | dry-run 有 issue 也 exit 3；1 行 |
| AC3 | `behavior-contracts.json` 对 analyze 零覆盖 | 11 条全指 write。未守面：「拆解边界声明」不得以敏感拒绝整章（`SKILL.md:20`）、Stage 1 停靠点必须产出 `快速预览.md`（`analyze-workflow.md:125`）、`剧情/节奏.md`/`情绪模块.md` 为权威而 `拆文报告.md` 只作投影（`:88`） | 加 3 条 contract；JSON +18 行 |
| AC4 | 热路径预算余量 27 字（2273/2300），属守卫设计内的"锁死"非缺陷；附勘误 `doc-budget.json:75` why 写"约 2.2K"实测 2.27K | 与守卫同度量复算 | 随 G5；why 1 字符 |
| AC5 | 术语「对标书」单独指代主对标（**存疑**） | `deconstruction-notes.md:170` 标题 `## 对标书选择`（该节 `:178` 正文已用"1 本主对标"）、`output-templates.md:557`、`technique-summary-sop.md:40`。批 1 范围是"只统一机制名"（总纲 `:120`）且无守卫 | 或改标题为「主对标选择」，或在术语表把泛指边界写死；2~3 行。**需作者裁定** |
| AC6 | evals 无拆文场景剧本（e2e 空白） | `evals/scenarios/` 仅 3 份；唯一提及是 `开书/README.md:5` 的可选前置 | 加纯 `[机检]` 剧本（边界表行数 / `schema_version: 2` / `--deep` exit 0 / `最终状态 == paused_after_stage1`）+ 同步 `check-eval-scenarios.sh` 的"3 剧本"计数；1 文件 ~40 行 + 1 数字。**不引 LLM/联网** |
| AC7 | 仓库级：`behavior-contracts` 条数断言过期（`scripts/README.md:50`、`CONTRIBUTING.md:103` 写 10，实测 11） | 见总计划 **G7** | 与 G7 同批 |

## 五、覆盖矩阵

| 面 | 守卫 | 状态 |
|---|---|---|
| frontmatter/链接/锚点/references | `static-check.py` | ✅（6 references 全被引用，零死链零孤儿） |
| Phase/Stage 编号 | `skill-numbering.py check` | ✅（Phase 1-2 + Stage 0-6 无小数） |
| `schema_version: 2` 全仓锚点 | `check-current-skill-contracts.py:984-1020` | ✅ |
| 「章节边界」表/目录块剔除/落表前校验 | 同上 `:1052/:1138/:1139` | ✅ |
| 主产物 fail-fast、禁摘要替代 | 同上 `:554-609` | ✅ |
| SKILL.md 体积 | `check-doc-budget.sh` | ✅（余 27） |
| `merge-chapter-summaries.js` | `test-merge-summaries.js`（CI:88） | ✅（本地清单缺行 → AM4） |
| `check_chapter_summary.py` 4 检 + `--deep` | 无正式回归 | ⚠️ 未覆盖（临时手测符合文档） |
| `chapter_boundary.py` 解析/连续性/骨架 | 无正式回归 | ⚠️ 未覆盖（中文数字/BOM/卷段/exit 3 全无守护） |
| 情节点数下限 ≥10 | 无 | ❌（AM2） |
| 质量阈值三比值/置信度 | 无 | ❌（AM3，且模型手算） |
| 关键行为约束文本 | `behavior-contracts.json` | ❌ 零覆盖（AC3） |
| 管道 e2e | `evals/scenarios/` | ❌ 空白（AC6） |

## 六、实测记录（节选）

| 检查 | 结果 |
|---|---|
| **本人复核 AM2** | `p_count` 只用于三者一致性（`:65-66`），无下限判定 → 成立 |
| **本人复核 AM1** | argparse 六参数无重编号选项（`:74-79`）、`sys.exit(3)` 在 `:174` → 死锁成立 |
| `chapter_boundary.py`（重复章号） | `重复章号: [1,2,3]`、stderr「问题未解决前不落盘边界表」、**exit 3**、未落盘 |
| `chapter_boundary.py`（跳号 + 两卷 + 中文/阿拉伯混排） | `章号格式: cn、digit`、卷段识别正确、`1..103 跳号`、exit 3；「一百零三」正确解析为 103 |
| `chapter_boundary.py`（干净 3 章） | exit 0；骨架含 `- schema_version: 2`、Stage 0-6 恰好 7 行、边界表 4 列、字数为去空白精确整数 |
| `check_chapter_summary.py` | PASS/FAIL 均符合文档（半角 `基调:` 与空白描被如实捕获）；`--deep` 7 必含字段与 `output-templates.md:138-167` 一致 |
| `merge-chapter-summaries.js` | `已拼接 2 章（P 行 5，校验通过）`，无损校验按 `:54-57` 生效 |
| **本人补跑** | `test-merge-summaries.js` **PASS**（策略放开后，见 [基线-守卫全量.md](基线-守卫全量.md)） |

## 七、整改计划

| 编号 | 级别 | 修法 | 改动量 | 依赖 | 验收 |
|---|---|---|---|---|---|
| **AM1** | 需修 | `--renumber-volumes` + 文档指向 | 脚本 ~35 行 + 2 行 | 无 | 多卷 fixture 落盘成功 + 跳号仍 exit 3 |
| **AM2** | 需修 | `p_count < 10` 进硬检查 + 文档 4→5 条 | 脚本 3 行 + 2 处 | 无 | 6 情节点 fixture 必 FAIL |
| AM3 | 需修 | 比值标"AI 手算自检口径"；0.7/0.6 改档位 | ~8 行 | 无 | `static-check.sh` |
| AM4 | 需修 | CONTRIBUTING 补 `test-merge-summaries.js` | 1 行 | 与 SM6 合并 | 人工核对 |
| AC1-AC7 | 候选 | 见上表 | ≤50 行 | AC1/AC5 需作者裁定 | — |

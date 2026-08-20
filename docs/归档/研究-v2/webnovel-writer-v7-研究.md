# webnovel-writer-v7 研究档案（v2，源码级）

> 研究对象路径：`otherMaterials/referProject/webnovel-writer-v7/`
> 研究日期：2026-08-19（本档案为只读源码勘察，未跑测试/未装依赖/未动 git）
> 实际读过的关键文件（相对研究对象根目录）：
> - 入口/演化：`README.md`、`CHANGELOG.md`、`docs/README.md`、`docs/architecture/v7-design-discussion-notes-2026-06-11.md`、`docs/architecture/v7-implementation-plan.md`
> - v7 实现（重点）：`v7/skills/webnovel-writer/SKILL.md`、`v7/package.json`、`v7/src/mechanical-check/index.js`、`v7/src/retry-policy/index.js`、`v7/src/finalize/git.js`、`v7/src/finalize/index.js`、`v7/src/state-machine/{index,git-health,detectors}.js`、`v7/src/state-machine/flows/goto-chapter.js`、`v7/src/storage/{atomic,index}.js`、`v7/src/storage/adapters/ChapterWriter.js`、`v7/src/cache/{schema,rebuilder}.js`、`v7/src/health-check/{index,baseline}.js`、`v7/src/review/{index,schema}.js`、`v7/src/knowledge/{contract,index}.js`、`v7/src/style-stats/index.js`、`v7/src/commands/{mechanical-check,health-check}.js`、`v7/roles/{事实审查,编辑审}.md`、`v7/src/prep/book-status.js`、`v7/src/storage/parsers/book-config.js`
> - v6 实现（对比）：`webnovel-writer/scripts/backup_manager.py`、`webnovel-writer/scripts/data_modules/{chapter_commit_service,chapter_commit_schema,projection_log,doctor}.py`
>
> 路径约定：下文所有 `v7/...` 与 `webnovel-writer/...` 均为相对研究对象根目录的相对路径，可带行号。

## 1. 项目概况

**是什么**：跑在 Claude Code 上的长篇网文创作插件，核心卖点是"一致性系统"——让 AI 写到几百章仍记得设定、接得住伏笔。不是一次性生成器。

**形态（双轨并存，这是它最大的教材价值）**：
- **v6 市场版**（`master` 分支，`webnovel-writer/`，当前 6.2.0）：Python 3.10+ + pydantic + SQLite 双库 + RAG，8 个 skill，Story System（`.story-system/` 合同 + 章节提交 + 事件审计）+ 五路投影读模型。
- **v7 全量重写**（`v7` 分支，`v7/`，7.0.0-alpha）：Node ESM（engines `>=22.13.0`，`v7/package.json:7-9`）+ 文件即真相 + git 原子提交 + 可删缓存。唯一第三方依赖是 `js-yaml`（`v7/package.json:29-31`）。运行时架构推翻重来、保留项目资产（37 题材模板/审查维度/追读力体系）。

**规模**：约 1350 文件。v7 侧 `src/` 约 136 个 `.js`，`src/commands/` 精确 53 个命令（`Get-ChildItem` 计数，见 §2.9），`test/` 大量 `node:test` 用例；v6 侧约 200 个 `.py`（含 `data_modules/` 与 `tests/`）。

**维护状态**：v6.2.0 是市场现行版（`README.md:316`）；v7 里程碑 M0–M7 代码面均已标注达成（`v7-implementation-plan.md:167/178/185`），距 7.0.0 只差 beta 期活动（真写 50 章/≥3 真实 v6 迁移/npm 发版）。许可证 GPL-3.0。

## 2. 流程（重点问题清单逐题落代码）

### 2.1 v7 与 v6 的真实架构差异；commit 链为何被否决

**代码事实**：
- v6 的"commit 链 + 投影链"是**领域事件溯源**，不是 git commit。真源是 `.story-system/commits/chapter_NNN.commit.json`，五路投影 writer 从它派生出 `.webnovel/state.json`、`index.db`、`summaries/`、`memory_scratchpad.json`、`vectors.db`（`webnovel-writer/scripts/data_modules/chapter_commit_service.py:98-111` 的 `_projection_writers` 返回 state/index/summary/memory/vector 五 writer；`:55-89` 的 `projection_status` 同五键）。投影失败不阻断，走 `try/except`，状态 `done/skipped/failed`（`:113-162`）。
- v7 否决 commit 链的**真实原因写在设计纪要**，非 README 转述：`docs/architecture/v7-design-discussion-notes-2026-06-11.md:13-22` 列了 6 条病根并给 issue 编号互证——①用 prompt 驱动确定性状态机，模型不遵守（#91/#66/#87/#76）；②派生状态（SQLite/投影）与作者手改冲突，无解（#100/#77/#63/#67/#70/#71/#89）；③token/时间失控（每章 3 subagent + 4 份 JSON + 多道 gate，#58/#92/#106）；④安装门槛（Python + .env + RAG key，#90/#103/#69）；⑤禁词表治不了 AI 味（#94）；⑥连写缺失/质量漂移（#79/#95/#74）。第 22 行给出一句话结论：**"v6 信任流程、不信任模型和作者；v7 信任 markdown 和作者，把流程压到最薄。"**
- v7 替代方案（同文档 §3）：①状态外置、纯 markdown，作者可手改可 git diff，**没有 DB、没有向量库、没有投影**；②确定性活给代码（字数/复读/句式/一致性对账零 token）；③零依赖 Node 安装；④可靠性来自自愈不来自门禁；⑤手改是一等公民（未发布直接改+自动重入账、已发布只读、设定/大纲走影响分析）。
- 代码印证：v7 缓存只有 `.cache/index.db`（`node:sqlite` 六表 + meta，`v7/src/cache/schema.js:5-94`），且 `SCHEMA_VERSION` 变更即全量重建、无迁移（`:2`）；重建器是格式参考实现（`v7/src/cache/rebuilder.js:14-64`）。派生值查询时现算，见 `v7/src/prep/book-status.js:30-41`（连续弱钩/悬了太久都 SELECT 现算，不物化）。

### 2.2 机检"6 阻断 + 4 候选"与 6-gram 复读

**代码事实**：`v7/src/mechanical-check/index.js:39-48` 依次跑 10 项，阻断进 `issues`、候选进 `candidates`，**`pass = issues.length === 0`（`:50`），候选绝不参与 pass 判定**（这是"候选永不拦截"的代码依据）。

- **6 阻断**（`issues`，`blocking:true`）：
  1. 字数 `checkWordCount`（`:69-78`）：去空白字符计数，目标=book.yaml `每章目标字数`（默认 3000，`v7/src/storage/parsers/book-config.js:29`），容差 ±30%。
  2. 禁词 `checkBannedWords`（`:80-86`）：读 `文风/文风铁律.md` front matter `禁词`，`body.includes` 命中即阻断。
  3. 禁句式 `checkBannedPatterns`（`:88-99`）：front matter `禁句式` 当正则 `new RegExp(p).test(body)`，非法正则跳过不崩机检。
  4. 复读 `checkRepetition`（`:101-117`）：**字符级 6-gram**——`L=6`，`threshold=3`，去空白后滑动窗口计数，任一 6-gram 出现 ≥3 次即 push 一条阻断并 `break`（只报第一个命中）。
  5. front matter `checkFrontMatter`（`:178-189`）：`REQUIRED_FM = ['章号','标题','卷','字数','章定位','钩子','情绪定位']`（`:11`）缺任一非空字段即阻断。
  6. 条目变动形式检查 `checkThreadDeclarations`（`:193-231`）：只查形式（类型一致/开启类动词不撞已有编号/非开启类要求条目存在且状态=进行），零语义。
- **4 候选**（`candidates`，永不阻断）：
  1. 新专名 `checkNewProperNouns`（`:120-144`）：正则 `([一-龥]{2,3})(冷笑道|笑道|喝道|说道|问道|答道|道|说|喊|问)` 启发式抓疑似人名，比对名册 `entities`+`entity_aliases` 未登记则出候选。
  2. 信息差候选 `checkSecretKeywords`（`:146-176`）：查 `secrets WHERE reader_knows = 0` 的关键词，正文命中即出"疑似泄密候选（不拦截，请人工确认）"。
  3. 高频意象 `checkImageryHits`（`:234-253`）：消费体检缓存 `meta.imagery_top`，本章草稿命中出候选。
  4. 句式偏离 `checkStyleDeviation`（`:256-280`）：本章句长 vs 基线指纹，平均句长偏 ≥30% 或句长方差偏 ≥50% 出候选（阈值 `v7/src/style-stats/index.js:12-13`）。
- 命令层动作映射：`pass`→`continue-to-review`；`fail` 且 `remaining>0`→`revise-and-recheck`；`fail` 且 `remaining=0`→`hand-off-to-author`（`v7/src/commands/mechanical-check.js:83-87`）。

### 2.3 半提交探测 probeCommitAfterError（三件套判三态）

**代码事实**：`v7/src/finalize/git.js`。
- commit 前 `captureCommitExpectation`（`:178-193`）抓三件套：`parent = git.head()`（HEAD 指针）、`tree = git.writeTree()`（工作树内容哈希）、`message = normalizeCommitMessage(message)`（换行归一、去尾部空行）。
- commit 抛错后 `probeCommitAfterError`（`:195-234`）判**三态**：
  - `not-committed`：当前 HEAD 为空且期望 parent 为空，或 `current.hash === expected.parent`（HEAD 没动）。
  - `committed`：在 `expected.parent..HEAD` 的 rev-list 里找到一个候选，其 `parents` 数组严格等于 `[expected.parent]`、`tree` 相等、`message` 相等 → 返回该 hash（假失败真成功）。
  - `unknown`：其余（包括 read 失败/无法确定）。
- 消费方：`v7/src/finalize/index.js:271-289`——`committed` 则视为成功继续；`unknown` 则 `ok:false` 且**保留工作树与契约守卫、不误删已入档内容**，提示作者查仓库；`not-committed` 走正常抛错回滚。
- 判据依赖 `readCommitInfo` 用 `git show --format=%H%x00%P%x00%T%x00%B`（`:236-252`）。

### 2.4 每章备份机制（git commit + tag chNNNN / 前滚式恢复 / create-branch / 无 git 降级快照）

> 注意：这是 **v6** 的机制，实现在 `webnovel-writer/scripts/backup_manager.py`；v7 已废弃 tag（见 §2.4 末与 §11 勘误）。

**代码事实**（`webnovel-writer/scripts/backup_manager.py`）：
- `backup()`（`:231-292`）：`git add .` → `git commit -m "Chapter {N}: {title}"`（标题经 `sanitize_commit_message` 防注入，`:259`）→ **`git tag ch{chapter_num:04d}`**（即 `ch0045`，`:281`），旧 tag 先 `tag -d` 删。commit 无变更（"nothing to commit"）视为成功跳过。
- `rollback()`（`:294-340`）：**前滚式恢复**——`git checkout <tag> -- .`（只覆盖工作树）→ `git add -A` → `git commit -m "rollback: 恢复到 <tag> 备份点"`，在当前分支新建一个恢复提交、历史不丢。前置要求必须在一个分支上（`symbolic-ref --short HEAD`）。
- `create_branch()`（`:412-437`）：`git branch <branch_name> <tag_name>`，从章节 tag 分叉（"平行世界"）。
- `_local_backup()`（`:188-229`）：**无 git 降级快照**——git 不可用时，把 `正文/大纲/设定集` 三目录 `copytree` + `.webnovel/state.json` 复制到 `.webnovel/backups/snapshot_ch{NNNN}_{timestamp}/`，仅保留最近 10 个快照（`:214-219`）。
- CLI 参数（`:464-471`）：`--chapter`、`--chapter-title`、`--rollback N`、`--diff A B`、`--create-branch N --branch-name X`、`--list`、`--project-root`。

**v7 的替代实现**（代码事实）：
- 定稿提交消息是 `ch(${chapterNum}): ${title}` + 可选 `条目:`/`设定:` 行（`v7/src/finalize/index.js:392-399`），**不打 tag**；定位某章用 `git log --grep=ch(${n}):`（`v7/src/finalize/git.js:155-162`）。
- 回滚 `goto-chapter`：建救援 ref `refs/rescue/goto-{Date.now()}` 指向当前 HEAD → `reset --hard <该章提交>`（`v7/src/state-machine/flows/goto-chapter.js:66-81`），是**破坏式 reset + 救援 ref**（非前滚提交）；前置拒绝：有进行中批次、git 不健康、跟踪面有脏树（`:17-64`）。
- 章节文件级备份：写新章前把同章号旧文件 `rename` 成 `.wnwbackup.{pid}.{n}`（`v7/src/storage/adapters/ChapterWriter.js:13-32`），commit 成功后删、失败则还原（`finalize/index.js:291-297` 与 `:350-358`）。
- 无 git 的 v7 没有"快照降级"——git 是硬依赖，`.git` 损坏时 `checkGitHealth` 只给中文指引不自动动仓库（`v7/src/state-machine/git-health.js:42-49`）。

### 2.5 重试预算（2 轮上限 / sha256 幂等 / author-confirmed 记账 / fail-closed）

**代码事实**：`v7/src/retry-policy/index.js`，持久化到 `工作区/重试预算.json`（`:10`，schema v1，结构 `{schemaVersion, chapters:{<章号>:{mechanical:{attempts:[]},review:{attempts:[]}}}}`）。
- **2 轮上限**：`MAX_MECHANICAL_AUTO_REPAIRS = 2`（`:12`）、`MAX_AUTOMATIC_REVIEW_ATTEMPTS = 2`（`:13`）。机检自动修复 2 轮、两审自动轮次 2 轮（初审 + 1 自动重审）。
- **sha256 幂等**：`retryDraftHash`（`:74-77`）对整份草稿（**含 front matter**，换行归一 + trim）求 `sha256:`；同 hash 的机检/审稿返回 `idempotent:true`（`repeat-same-draft` / `repeat-same-review-input`），**不消耗预算**（`:125-136`、`:286-327`）。front matter 含入哈希的动机写在注释：只修 front matter 也算修复，必须换 hash 才记账。
- **author-confirmed 单独记账**：`reserveMechanicalAttempt` 里 `authorConfirmed === true` 直接走 `route:'author'`（`:154-165`），**先于自动上限判断、永不恢复自动额度**；两审侧 `authorApproved` 同理（`:345-363`，author 路由不 +1 自动计数）。机检期间草稿被改（before/after 哈希不等）→ 拒绝记账（`v7/src/commands/mechanical-check.js:67-70`）。
- **fail-closed**：`readRetryPolicy`（`:31-53`）——文件缺失=合法空态（`exists:false`），其余读失败/JSON 损坏/schema 校验失败一律 `ok:false` + "已停止自动流程"；校验器逐字段白名单（`:80-106`、`:463-534`），顶层/每章/每尝试字段必须精确匹配，多余字段即拒绝。
- **定稿清章**：finalize 成功后 `clearRetryPolicyChapters`（`v7/src/finalize/index.js:325-334`，失败只降 warning）。

### 2.6 状态系统投影链与 projection_log 定位不同步

**代码事实**（v6）：
- 主链 commit 经 `apply_projection_writers` 派发五 writer，每路独立 try/except 记 `done/skipped/failed`，不阻断主链（`chapter_commit_service.py:123-162`）。
- `projection_log.py`：每条 run 落 `.webnovel/projection_log.jsonl`（`:14`），含 `run_id`/`chapter`/`commit_path`/`commit_hash`/`commit_status`/`status`（overall `done/skipped/pending/failed`）/`writers`（每路 status）/`projection_status`（`:53-64`）。定位不同步：doctor 读 `latest_projection_run` 后判 `projection_run_failed`/`projection_run_pending`（`:85-99`），即"哪一路 writer 停在 failed/pending"。
- v7 无投影链：六表缓存重建器（`v7/src/cache/rebuilder.js`）+ 查询时现算（§2.1）。

### 2.7 事实审查/编辑审双角色、契约与 CHAPTER_COMMIT 格式

**代码事实**：
- 双角色任务书是单源 markdown（`v7/roles/事实审查.md`、`v7/roles/编辑审.md`），由生成器注入 `{{categories.factCheck}}`/`{{schema.example}}` 占位（角色正文 `:23/:27`）。
  - **事实审查** 9 维 category：setting/timeline/continuity/character/logic/requirement/leak/evidence/unregistered_thread（`v7/src/review/schema.js:6-9`）；并产出 `factChanges`（`事实审查.md:31`）。
  - **编辑审** 4 维 category：structure/pacing/commercial/motivation（`schema.js:10`）；评结构与商业性、情节决定权留给作者。
  - 阻断规则（`schema.js:78-81`）：`critical` 强制 `blocking=true`；`unregistered_thread` 强制 `blocking=false`（候选交作者）。
  - factChanges 选项必须显式布尔 `applyChange`，禁止按 optionId/文案猜（`事实审查.md:31`、`fact-changes.js` 校验）。
- **契约格式**（`v7/src/knowledge/contract.js`）：`作品契约/作品契约.md`，front matter 白名单 9 字段（类型/副题材/流派/创意约束/来源版本/契约版本/生效起章/更新原因/变更类型，`:37-47`）+ 8 个固定二级节（`CONTRACT_SECTIONS`，`:7-16`）。建书强制 `契约版本=1/生效起章=1/变更类型=建书`（`:212-216`）；更新强制版本 `+1` 且 `生效起章=下一未定稿章`（`:217-229`）。知识选择来源必须 `维度/文件.md@sha256:<64hex>` 或 `对谈共创/作者自定义`（`:51`、`:263-270`）。
- **CHAPTER_COMMIT 格式**（v6 `chapter_commit_schema.py` + `chapter_commit_service.py:55-89`）：`meta{schema_version,chapter,status}`、`contract_refs`、`provenance{write_fact_role,projection_role,legacy_state_role}`、`outline_snapshot{planned/covered/missed/extra_nodes}`、`review_result`、`fulfillment_result`、`disambiguation_result`、`extraction_result`、`projection_status`。**rejected = `review.blocking_count>0` 或 `fulfillment.missed_nodes` 非空 或 `disambiguation.pending` 非空**（`chapter_commit_service.py:45-48`）。四类 artifact 各是 pydantic 模型（`ReviewResult/FulfillmentResult/DisambiguationResult/ExtractionResult`）。

### 2.8 doctor/preflight 体检检查什么

**代码事实**：
- v6 `doctor.py`（`webnovel-writer/scripts/data_modules/doctor.py`）阶段感知，检查：preflight 转发、必需目录（`file.dir.*`）、必需文件（`file.required.*`）、目标章合同文件（`file.contract.*`）、JSON（`.webnovel/state.json` + `.story-system/MASTER_SETTING.json`，`:183-232`）、SQLite（`index.db` 的 chapters 表 + `vector.db` 的 vectors 表，`:252-289`）、RAG（embed/rerank 的 api_key 是否配置，`:292-311`）、投影日志（`:314+`）、Dashboard 产物。每条检查带 status/severity/message/impact/repair 五要素（`_check`，`:41-63`）。
- v7 `health-check`（`v7/src/health-check/index.js`）：零 token，报告落 `工作区/体检报告.md`（不入档），记 `meta.last_health_check_chapter`。含：全书近况 + 悬了太久 + 条目活跃率 + 连续弱钩 + 高频意象（4-8 gram Apriori，`v7/src/style-stats/index.js:78-159`）+ 句式 + 文体指纹漂移 + 缺时间锚点。状态机序 5 依据 `maxChapter - lastCheck >= 体检周期`（默认 50）触发（`v7/src/state-machine/index.js:107-111`）。

### 2.9 skill 与脚本分工（薄 skill 厚脚本）

**代码事实**：v7 只保留**一个**薄 skill（`v7/skills/webnovel-writer/SKILL.md`，全文 70 行），它只做：接话（"继续/写下一章/建书/回到第N章/吃书"）→ 调 `next --json` 拿状态机 DTO（序 0-6）→ 按序对话/组 JSON → 调对应命令。全部确定性逻辑下沉到 **53 个 CLI 命令**（`v7/src/commands/`，精确计数见 §1），skill 不读文件结构、不自己算字数/复读。铁律（SKILL.md:65-70）：事实变更只经定稿流程入 git；能数的交脚本、要判断的交两审；只吃 DTO；JSON 一律 `--file`/`--payload` 走文件（临时 JSON 放 `工作区/`，建书放工作目录根）——为规避 Windows 中文管道编码。
- 对照 v6：8 个 skill（init/plan/write/review/query/learn/dashboard/doctor，`webnovel-writer/skills/*/SKILL.md`），skill 更厚、且驱动 subagent。
- 状态机 7 态（序 0-6）：修复确认/建书/手改补登/断点续跑/卷复盘/体检/起草细纲（`v7/src/state-machine/index.js:16-129`），另有 `cache-error` 兜底态。

### 2.10 RAG/记忆检索的边界与成本

**代码事实**：
- v6 检索三层：`reference_search`（BM25 纯本地静态知识库）+ RAG 向量库（**必须外部 API**：`EMBED_BASE_URL=ModelScope Qwen3-Embedding-8B`、`RERANK_BASE_URL=Jina reranker-v3`，README:117-127；doctor 检查 embed/rerank api_key，`doctor.py:292-311`）。无 key 退 BM25。记忆三套：learn 经验（`project_memory.json`，全量注入不筛选）、结构化 `memory_scratchpad.json`（7 桶四态）、`vectors.db`。
- v7 **明确拒绝向量**（设计纪要 §3.1）。知识检索改为**纯本地 markdown**：`v7/references/` 按 10 维（题材/流派/创意约束/设定/人物/命名/节拍/场景/技法/追读）存 `.md`，`路由.csv` 只做题材/流派 canonical 归一（`v7/src/knowledge/index.js:92-117`），`queryKnowledge` 用关键词打分（名称精确命中 +100、查询含名称 +30、词项命中 +5~20，`:407-424`）+ 近期使用软降权 + **最多 3 候选**（`MAX_KNOWLEDGE_CANDIDATES=3`，`:9`）。来源版本 = `路径@sha256:<内容哈希>`（`:363-365`），供契约知识选择追溯。正文细节召回靠 Grep 正文原文（设计纪要 §3.1"正文本身就是无损数据库"）。

## 3. 架构（v6 vs v7 双轨对比）

| 维度 | v6（webnovel-writer/） | v7（v7/） |
|---|---|---|
| 真源 | `.story-system/` commit 链（领域事件） | 中文 markdown 文件（正文/大纲/设定/契约） |
| 派生 | 五路投影（state/index/summary/memory/vector） | 唯一可删 `.cache/index.db`（node:sqlite 六表） |
| 提交 | `chapter-commit` 事件 + 独立 git 备份（tag chNNNN） | 定稿=一次原子 git commit（无 tag） |
| 一致性 | 投影 + 门禁 + prompt 状态机 | git 原子性 + 查询时现算 + 自愈（宁停勿崩） |
| 运行时 | Python + pydantic + SQLite + RAG | Node ESM，零依赖（仅 js-yaml） |
| 检索 | BM25 + RAG（外部 API） | 纯本地 markdown + Grep |
| skill | 8 skill 厚提示 + subagent | 1 skill 薄编排 + 53 命令 |
| 手改 | 与派生状态冲突（无解） | 一等公民（序 2 检测 + relink 补登） |
| 审查 | reviewer 单 agent 多维 | 事实审查 9 维 / 编辑审 4 维双角色（可降级单审） |

**关键结论**：v6→v7 不是"加功能"，是**把"信任流程"换成"信任文件与作者"**，把复杂度从运行时（投影/DB/门禁）转移到格式法律文本（front matter/契约/声明制）+ 确定性脚本。

## 4. 思想

1. **文件即真相**：一切状态是中文 markdown，可手改、可 git diff，手改永不报错拒绝（`v7-design-discussion-notes:25-30`）。
2. **责任三分法**：能数的交脚本（零 token 机检/体检/重建），要判断的交 AI（两审），定稿归作者（SKILL 铁律）。
3. **可靠性来自自愈不来自门禁**：接受最终一致，每次写作前检测并修复（漏记/手改/崩溃统一收敛），宁停勿崩（设计纪要 §3.4）。
4. **git 隐身**：作者永不敲 git，健康检查全中文 fixed/guidance/rescued 输出（`git-health.js:12` 注释"作者永不直面 git 英文报错"）。
5. **诚实降级**：读取失败显式进 `degraded` 数组，AI 据此区分"没有数据"与"读取失败后的残缺数据"，不得静默断言无问题（`v7/src/review/index.js:241-243`、角色 `:10`）。
6. **文档先行铁律**：RFC 收口前只做格式不敏感地基，收口后格式层才开闸（`v7-implementation-plan.md:23-24`）。

## 5. 方法论

- **里程碑 + 出口判据**：M0-M7 每个有可验证出口（如"删 `.cache` 全量重建 CI 绿"提前在 M1 达成），不接受"做完了"（`v7-implementation-plan.md:26-27`）。
- **用例拆分脚本**：脚本层按 use case 拆（`prepareChapterMaterials/runMechanicalChecks/finalizeChapter/rebuildCache`），不做通用工具函数到处调用；跨层通信走稳定 DTO，不传半解析 YAML（`v7-implementation-plan.md:34-55`）。
- **小端口不搞上帝对象**：Storage 拆 `ChapterReader/ChapterWriter/ThreadLedgerReader/...` 小端口（`v7/src/storage/index.js` 全量导出 15 个小端口），每个 use case 只依赖需要的端口。
- **重建器即格式参考实现**：能全量重建缓存 = 格式自洽的 CI 验收项；`SCHEMA_VERSION` 变更即重建、无迁移。
- **确定性统计**：全部固定排序纯计数、无时间戳无随机（`style-stats/index.js:1-5`），删缓存重建后指纹不变。
- **`.trellis/` 工作流元数据**：任务目录 `task.json + prd.md + implement.jsonl + check.jsonl`（含 archive 历史），体现"先 spec/PRD → 再 implement → check 对账"的流程；`docs/architecture/` 是 v7 规格法律文本（PRD/story-repo-spec/multi-agent-spec 三位一体）。

## 6. 上下游设计

- **多宿主适配**：SKILL.md 是开放标准（30+ 工具支持），角色单源 markdown 构建时生成三平台壳（`v7/src/host-shells/generate.js` + `validator.js`，`v7/adapters/{claude-code,codex,opencode}/support.md`）；subagent 只做增强不依赖，skill 写降级路径（无 subagent 顺序自审 `mode=degraded`）。
- **安装器**：`npx webnovel-writer init/update` 检测环境拷 skills（`v7/src/installer/*`），解决 Python 门槛。
- **迁移**：`migrate <v6项目路径>` 源只读、失败自动回退、产出"迁移待校对-"前缀文件（`v7/src/migrate/*`）。
- **导出**：`export` 三形态（单章/范围/全书，去 front matter，落 `工作区/导出/`）。
- **自动模式**：`stage-chapter` 暂存 → `finalize-batch` 逐章原子入档，停止四件套（写满/收卷/卷纲耗尽/连续无条目变动/批次质检不过线），打回污染传播三态。

## 7. 可借鉴清单（分成本）

### 🟢 低成本（≤ 数百行，零依赖，直接抄）

1. **半提交探测 probeCommitAfterError**（`v7/src/finalize/git.js:178-234`）：parent/tree/message 三件套判 committed/not/unknown，防"假失败→重复提交"。**值得**：任何用 git 原子提交的流程都会遇到"commit 报错但实际成功"，~75 行解决。**mo-shu 落点**：若引入 git 备份，作为定稿提交前置。
2. **机检"阻断 vs 候选"分层 + 6-gram 复读**（`v7/src/mechanical-check/index.js`）：10 项零 token，候选永不拦。**值得**：确定性质量关与 AI 语义关分工清晰。**mo-shu 落点**：moshu-write 写后收尾加"字数/复读/禁词/front matter"可计数机检关，候选（新专名/泄密）只提示。
3. **重试预算模式**（`v7/src/retry-policy/index.js`）：sha256 幂等 + fail-closed + 按章持久化 + author-confirmed 单独记账。**值得**：防自动修复无限重跑，账目可审计。**mo-shu 落点**：机检/审稿自动轮次预算加幂等与持久化。
4. **git 人话化健康检查**（`v7/src/state-machine/git-health.js`）：陈旧锁 60s 阈值 + 删除前二次 stat 防 TOCTOU；网盘副本移动归档；半提交 stash；全中文输出。**值得**：作者永不直面 git 英文报错。**mo-shu 落点**：备份前置。
5. **degradation 显式标记**（`v7/src/util/degradation.js` + 各消费点 `ctx.degradation.report`）：读失败进 `dto.degraded`，AI 必须区分"没有数据"与"残缺数据"。**值得**：防静默缺料，成本极低。**mo-shu 落点**：各 Stage 流程读文件失败处加标记。
6. **审稿输入令牌**（`v7/src/review/input-binding.js` 的 sha256 全字段令牌 + 契约版本绑定）：两份报告 + 外层三重校验令牌逐字一致，防审稿上下文漂移。**值得**：低成本的契约防漂移。**mo-shu 落点**：moshu-review 契约。
7. **知识来源 @sha256 追溯**（`v7/src/knowledge/index.js:363-365`、`v7/src/knowledge/contract.js:51`）：知识条目引用必须带内容哈希，删改可验。**值得**：证据溯源纯增量。**mo-shu 落点**：对标资产/模板引用加 sha256。
8. **派生值查询时现算**（`v7/src/prep/book-status.js`）：悬久=当前章−最后推进章、连续弱钩倒序扫描，不物化。**值得**：避免投影漂移。**mo-shu 落点**：把可推导字段改为现算，不落盘。

### 🟡 中成本（值得做但要适配）

9. **六表缓存 + 全量重建器**（`v7/src/cache/{schema,rebuilder}.js`）：node:sqlite 六表 + meta，重建=格式参考实现，事务包裹防半库。**值得**：可删派生缓存 + 自愈。**mo-shu 落点**：若引入缓存索引，按此模式做"删了能重建"。
10. **契约（作品契约.md）版本守卫**（`v7/src/knowledge/contract.js` + `v7/src/staging/contract-invalidation.js`）：契约更新 → 影响章写失效记录 → 拒用旧工件定稿，版本严格 +1。**值得**：设定变更的传播防呆。**mo-shu 落点**：tracking state 加契约版本 + 影响传播（轻量版）。
11. **三类线索统一账本（伏笔/悬念/感情线）声明制**（`v7/src/util/thread-declarations.js` 的 VERBS/OPENING_VERBS + `ThreadLedgerWriter`）：章 front matter 声明"埋下 伏笔-031"，机检只查形式。**值得**：把"伏笔登记"变成可机检的形式约束。**mo-shu 落点**：事务/伏笔字段加声明校验。
12. **文体指纹漂移（4-8 gram Apriori + 窗口 TTR）**（`v7/src/style-stats/index.js`）：跨章高频意象、句长方差、段落分布、词汇丰富度基线对比。**值得**：零 token 逮 AI 味/桥段循环。**mo-shu 落点**：去 AI 味/文风漂移检测。
13. **断点续跑状态机（序 0-6）**（`v7/src/state-machine/{index,detectors}.js`）：按工作区现存工件最深优先推断"从哪继续"，不重写已可信完成的部分。**值得**：中断恢复体验。**mo-shu 落点**：拆文断点恢复已有雏形，可借鉴其"工件→续跑映射"表。
14. **事实转正 factChanges 裁决结构**（`v7/src/knowledge/fact-changes.js`）：difference/impact/options[{optionId,applyChange 显式布尔}]/resolution，作者裁决不猜。**值得**：把事实冲突的裁决从"猜"变成显式选项。

### 🔴 高成本（明确不抄/远期）

- 完整 git 备份体系（tag chNNNN + 前滚恢复 + 分支平行世界）：v6 全量方案对 mo-shu 过重，且 v7 自己都砍掉了 tag（见 §11）。
- 自动连写批次 + 污染传播三态（`v7/src/staging/index.js`）：状态机复杂度大，需作者挂机场景才值。
- 多宿主 shell 生成器 + registry 分级（`v7/src/host-shells/*`、`v7/src/installer/*`）：mo-shu 单宿主不需要。
- 契约知识治理三件套（`v7/docs/knowledge/` 维度宪章/策展规则/调用者字段矩阵）：单人项目偏重。

## 8. 不可借鉴清单

1. **"手改=破坏"→"手改一等公民"的直接平移**：v7 的 relink 补登依赖"真源就是 git 跟踪的 markdown"这一前提；mo-shu 真源是 `_tracking-state.json`（程序权威、check 逐字重渲染比对），若照搬"手改即真相"会破坏 mo-shu 的乐观锁与可验证重放。**只可借鉴"检测手改并显式呈报"，不可借鉴"手改自动成为真源"。**
2. **tag chNNNN 每章备份**：v7 已自证 tag 是多余负担（commit message grep + rescue ref 足够），且 v6 的 tag 与 `reset --hard` 语义冲突；mo-shu 若只做"定稿原子提交 + 提交消息定位"，不需要 tag。
3. **RAG 向量检索（外部 API）**：与 mo-shu 零外部依赖定位冲突，且中文召回质量差（设计纪要自身也弃用）。
4. **learn 式"只写不筛"经验记忆**：v6 的 `project_memory.json` 全量注入不筛选，旧文档已判"召回弱=死数据"；除非带细纲命中筛选，否则不抄。
5. **prompt 驱动的确定性状态机**：v6 病根之一（模型不遵守），v7 已改为"脚本判定 + AI 只做提议"。mo-shu 应坚持脚本权威、AI 只做语义。
6. **"已发布不可改"三档修改语义的完整落地**：网文铁律（发布后只读、生成"圆设定方案"）与 mo-shu 的"拆书/对标/可反复重渲染"定位不符，mo-shu 需要的是可重放 + check 校验，不是发布锁。

## 9. 与 mo-shu 差异定位

- **真源哲学相反但可互补**：v7 = markdown 真源 + git 权威 + 可删缓存；mo-shu = 程序权威 `_tracking-state.json` + 可重放渲染 + check 逐字比对。v7 用"git 原子性"保证不撕裂，mo-shu 用"可确定性重放"保证不漂移——后者恰好补上 v6 投影漂移的病灶，值得坚持。
- **共同点**：都把"确定性活给脚本、语义活给 AI、终审给作者"宪法化；都强调 fail-closed 与显式降级。
- **差距**：v7 有 53 命令精准读取面（非必要不全文读），mo-shu 目前靠 prompt 引导读文件；v7 有 git 隐身自愈，mo-shu 尚无自动备份。
- **mo-shu 独有而 v7 没有**：拆书/对标资产体系、作者真相/读者已知双视图、check 逐字可验证、字节硬预算、乐观并发 revision、扫榜选材、浏览器自动化。

## 10. 待验证问题

1. 旧文档"85 个降级点三分类"——源码中 `ctx.degradation.report(...)` 调用点确实遍布（review/prep/state-machine/readers），但"85"这个精确数无法在只读勘察下可靠计数，**存疑**。
2. 旧文档"733 测试实跑全绿"——`v7/test/` 目录用例大量存在，但"733 且全绿"是运行结果，本只读研究未跑测试，**存疑**（53 命令数与 `package.json` 一致属代码事实）。
3. "6-gram 复读"对中文是否过敏感（3 次即断）：`checkRepetition` 的去空白 6-gram 会把"他说道/林晚冷笑"这类常见搭配计数，阈值 3 可能偏高敏——属**推断**，需真实文本验证误报率。
4. v7 `node:sqlite` 门槛 ≥22.13.0 对作者的安装成本：设计自称"装 agent 工具的人必有 Node"，但版本门槛本身是新门槛——**推断**，需看安装器真实拒绝率。
5. 契约更新"生效起章=下一未定稿章"与批次并行的边界：`contract-invalidation.js` 的守卫与 `finalize-batch` 的证明文件复核链路较长，未逐条读透 `verifyPendingCommitProofFile` 的全部判定——**存疑**，若借鉴需再读。

## 11. 旧研究文档勘误

> 逐条对照旧文档 `docs/webnovel-writer-研究.md`（已于 2026-08-20 删除，本节为历史对照记录），只列与源码不符/过度解读/张冠李戴处。

1. **【硬错·张冠李戴】文体指纹"四维 delta（句长/句式/高频意象/高频开头）"不对**。旧文档 §3.3 末行称文体指纹 delta 四维是"句长/句式/高频意象/高频开头"，但源码 `v7/src/health-check/index.js:248-253` 的 delta 是 **平均句长、句长方差、平均段长、词汇丰富度** 四维（高频意象、高频开头只是 fingerprint_data 的内部字段，不参与漂移 delta）。旧文档把"指纹的组成字段"误当成"漂移对比的四个维度"。
2. **【硬错·v6/v7 混淆】"每章 commit + tag chNNNN、rollback/create-branch"是 v6 机制，不是 v7**。旧文档 §5 可借鉴清单 #5 写"自动 Git 备份（每章 commit + tag chNNNN，rollback/create-branch）"且未标注版本；实为 v6 `webnovel-writer/scripts/backup_manager.py` 的实现（tag `ch{NNNN}`、前滚式恢复、create-branch、无 git 降级快照）。**v7 已废弃 tag**：定稿提交消息是 `ch(N): title`（`v7/src/finalize/index.js:392`），定位靠 `git log --grep`，回滚用 `refs/rescue/goto-*` + `reset --hard`（非前滚提交）。若 mo-shu 照抄 #5 会抄到 v7 已淘汰的方案。
3. **【存疑·不可复现】"733 测试实跑全绿"与"85 个降级点"**：两者都是"实测/统计"性质结论，只读勘察无法复现精确数字（`v7/test/` 目录确有多文件、`degradation.report` 调用点确遍布，但精确计数存疑）。建议把这两条从"代码事实"降级为"未复核的旧档结论"。
4. **【轻·表述不准】"半提交探测 ~60 行"**：`probeCommitAfterError` 本体约 40 行，加上 `captureCommitExpectation`+`readCommitInfo` 共约 75 行（`v7/src/finalize/git.js:178-252`）；"~60 行精华"量级对、行数略偏，不影响结论。
5. **【轻·需补充语境】"v6 8 skill + 4 agent"**：8 个 skill 属实（`webnovel-writer/skills/*/SKILL.md` 恰好 8 个目录）；"4 agent"来自 README 的 context/reviewer/data/deconstruction 表述，但源码里 agent 是 subagent 定义、与 skill 不一一对应，旧文档把 skill 数与 agent 数并列易误读为"8+4 都是命令面"。属**过度概化**，非硬错。
6. **【核对无误·记录在案】**以下旧文档论断与源码一致，勘误时无需改：①"v7 拒绝向量"（设计纪要 §3.1）；②"6-gram 计数 ≥3"（`mechanical-check/index.js:101-117`）；③"新专名 `([一-龥]{2,3})(冷笑道|笑道|…)` + 名册排除"（`:131`）；④"高频意象 CJK 4-8 gram Apriori"（`style-stats/index.js:15-16、78-159`）；⑤"悬久≈10/10/30 章"（`book-config.js:33-35`）；⑥"缓存重建器=格式参考实现 / 指纹身份用(章段起,章段止)不带时间戳"（`cache/rebuilder.js`、`cache/schema.js:80-92`）；⑦"投影五 writer 独立 try/except 失败不阻断"（`chapter_commit_service.py:123-162`）。

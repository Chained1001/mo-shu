# mo-shu 代码现状盘点（研究-v3 / 04）

- 版本：v1（只读盘点档案）
- 日期：2026-08-20
- 盘点方式：直接读代码/结构 + 跑只读守卫；未读取研究-v2、实施总纲.md、规格、reference-review.md、moshu-style-plan.md、scan-analyze-v2-plan.md（按约定视为不存在；该 6 项当时位于 docs/ 顶层，已于 2026-08-20 归档至 docs/归档/）。docs/architecture.md 已读（结构性文档）。
- 证据格式：路径:行号 或 实测命令输出。所有「清单类数字」均实测。

---

## 1. 规模与结构总览

### 1.1 顶层结构

```
mo-shu/
├── AGENTS.md / CONTRIBUTING.md / LICENSE / README.md / README_EN.md / CHANGELOG.md
├── package.json（仅 dashboard 测试用，@playwright/test）
├── playwright.config.mjs
├── skills/（10 个 skill）
├── scripts/（37 个开发守卫/测试文件 + 5 个 JSON/md 配置）
├── tests/（dashboard 单测 + e2e + fixtures）
├── evals/（端到端正文质量评测，2 个样本）
├── docs/（architecture.md + 研究-v2/v3 + 规格等，按约定不读内容）
├── otherMaterials/（含只读参考项目，未动）
└── test-results/、node_modules/
```

### 1.2 skill 规模实测

命令：`find skills/<name> -type f | wc -l`、`find skills/<name> -type f | xargs wc -c | tail -1`

| skill | 文件数 | 总字节 | 版本(frontmatter) | 主要内容 |
|---|---|---|---|---|
| moshu | 6 | 107,729 | 1.1.1 | 路由入口 + Dashboard（dashboard-server.mjs 34.5KB + 前端资产 ~63KB）+ VERSION 文件(1.1.1) |
| moshu-write | 87 | 1,065,542 | 1.1.1 | 主写作引擎：49 个 references + 5 脚本 |
| moshu-setup | 94 | 860,137 | 1.2.11 | 部署器：7 agent 模板 + 10 hook 脚本 + 4 rules + agent-references 25+ |
| moshu-review | 18 | 391,332 | 1.1.5 | 多视角审查（full/lean/solo） |
| moshu-deslop | 8 | 188,290 | 1.1.1 | 去 AI 味 |
| moshu-analyze | 12 | 169,543 | 1.1.1 | 长篇拆文管道 |
| moshu-scan | 12 | 145,815 | 1.1.1 | 扫榜（4 平台 scraper + scan-analyze） |
| moshu-import | 8 | 137,128 | 1.1.1 | 逆向导入 |
| moshu-cdp | 2 | 48,238 | 1.1.1 | CDP 浏览器工具（setup-cdp-chrome.js 41KB） |
| moshu-style | 2 | 21,869 | 1.0.0 | 文风学习（无脚本，纯流程） |

合计 10 个 skill（`ls skills` 实测），总规模约 3.14MB。

### 1.3 scripts/ 清单（37 个 .sh/.py/.js + 配置）

实测 `ls scripts/ | grep -v __pycache__` = 37 个脚本 + README.md + 5 个配置（shared-assets.json、doc-budget.json、behavior-contracts.json、current-contract.json、__pycache__ 除外）。

- 静态守卫 12 个：static-check、skill-numbering、check-current-skill-contracts、check-shared-files、check-moshu-setup-deployment、check-doc-budget、check-hook-regex-sync、check-hook-locale-safety、check-python-invocation、check-claude-adapter、check-behavior-contracts、check-agents-version-sync（职责详表见 scripts/README.md:7-23，实测与文件一一对应）。
- 测试回归 19 个 `test-*`（scripts/README.md:26-47）+ `eval-prose-quality.sh`。
- 同步工具：`sync-shared-assets.py`（shared-assets.json 36 组，实测 `python -c json.load`）。

### 1.4 tests/ 与 package.json

- `tests/dashboard-server.test.mjs`、`tests/dashboard-trigger-contract.test.mjs`、`tests/e2e/dashboard.spec.mjs`（Playwright）+ helpers + fixtures（dashboard/scan/scan-empty）。
- package.json scripts：`test` = `test:dashboard`（node --test 两个单测文件）+ `test:dashboard:e2e`（playwright）。
- 实测 `npm run test:dashboard`：**31 tests，26 pass，0 fail，5 skipped**（skip 全部为平台能力探测：不可读目录/符号链接/POSIX 权限位，tests/dashboard-server.test.mjs:267,326,363,641,673,702）。e2e 未跑（会拉起浏览器，本轮不执行）。

### 1.5 守卫实测（本轮全部跑绿）

| 守卫 | 结果 |
|---|---|
| static-check.py | Total: 10 \| Pass: 10 \| Fail: 0 \| Warn: 0 |
| check-doc-budget.sh | 通过（附 3 条「比预算低可降 budget」提示，见 §5） |
| check-behavior-contracts.sh | 9 条约束在位 |
| check-shared-files.sh | Reference groups checked: 64 \| Mismatches: 0 |
| check-current-skill-contracts.sh | all passed |
| check-agents-version-sync.sh | agents_version 27 在所有 SKILL.md 一致 |

### 1.6 git 近况（git log --oneline -20，只作现状线索）

近 20 条提交全部是 docs/fix/feat 类：主题集中在大规模审查修复（全库逐 skill 审查、术语收敛、僵尸配置清理）、瘦身（style-craft 并入 writing-craft、删 ciweimao-rank-scraper）、doc-budget 反复救火（9229/9200 超支、CI 超支修复），以及最近 8 条全部是规划文档（研究/修改方案/产品文档）提交——代码本体近 8 次提交未动。

---

## 2. 各 skill 现状

### 2.1 moshu（路由 + Dashboard）
- 用途：模糊请求路由（skills/moshu/SKILL.md:11-28 路由表覆盖 10 个子 skill/入口）；本地 Dashboard（HTTP 服务浏览拆文库/项目/编辑文本）；多书切换；版本更新检查；spawn moshu-explorer（查故事资料）/moshu-researcher（查资料）。
- 输入输出：用户意图 → 路由；`/moshu dashboard` → 起 `scripts/dashboard-server.mjs`。
- 依赖：各子 skill；`.claude/agents/moshu-{explorer,researcher}.md`（部署产物）。
- 特殊：有 VERSION 文件（内容 `1.1.1`）与 frontmatter version 双轨。

### 2.2 moshu-write（核心写作引擎）
- 用途：从开书到日更的全流程（SKILL.md frontmatter description）。三层分工宪法在 SKILL.md:19（脚本做确定性/AI 做语义/作者做品味）。
- 核心资产：references/ 49 个文件（实测 ls）：workflow-{setup,daily,chapter,revision}.md（流程）、tracking-transaction.md（追踪契约）、volume-review.md（卷复盘）、recovery-protocol.md、recovery、reader-contract-and-progression.md、plot-*/character-*/hooks-*/genre-*/style-*/*-cards 等方法论库。
- 脚本：tracking_commit.py（1139 行，单权威追踪事务）、check-ai-patterns.js、check-degeneration.js、check-outline-copy.js、normalize-punctuation.js（后四者为共享副本，源在 deslop）。
- 状态机：架构级「下一步」状态机（docs/architecture.md:53-66，S0 未部署→…→S5 卷末→S6 下卷规划→回 S2）；追踪层为「单权威 state + 派生视图」模型（见 §3.1）。
- 衔接：读 拆文库/（moshu-analyze 产物）、对标/、文风库/文风.md（moshu-style 产物）；产出 正文/大纲/追踪/；审查交 moshu-review。

### 2.3 moshu-analyze（拆文管道）
- 用途：单一深度拆解管道 Stage 1-6（黄金三章→逐章摘要→聚合→设定关系→汇总报告→技法总结），产物落 `拆文库/{书名}/`（SKILL.md frontmatter + 正文）。
- 脚本：chapter_boundary.py（章节边界）、check_chapter_summary.py（摘要校验）、merge-chapter-summaries.js（自然序拼接）。
- 衔接：被 moshu-import 复用；产物被 moshu-write 主对标回退链消费（workflow-daily.md:9）；技法总结定位为纯作者学习材料，写书流程不读取（CHANGELOG v1.1.2 记录）。

### 2.4 moshu-import（逆向导入）
- 用途：已有小说→拆解（复用 analyze 管道到 拆文库/{导入书名}/）→迁移为标准项目结构；硬约束：不得把导入书登记为主对标（SKILL.md「名词与目录边界」）。
- 脚本：tracking_commit.py（共享副本），负责导入基线（imported_through_chapter 顶层字段）。
- references 7 个：import-workflow/structure-mapping-long/tracking-transaction/state-tracking/format-and-structure/character-state-reverse。

### 2.5 moshu-review（多视角审查）
- 用途：full（4 agent 并行）/lean（2 agent）/solo 三模式，降级链明确（SKILL.md:14-30）；「审查是找问题，不是验证正确性」铁律。
- 依赖：部署的 4 个 reviewer agent（architect/character-designer/narrative-writer/consistency-checker）；机检脚本 4 个共享副本（ai-patterns/degeneration/normalize-punctuation/tracking_commit）。
- references 12+ 个：review-workflow、plot-core-methods、character-relations、dialogue-mastery、reader-contract-and-progression、quality-checklist、tracking-transaction 等。

### 2.6 moshu-deslop（去 AI 味）
- 用途：检测+清除 AI 写作痕迹；「改味优先/改最少效果最大/过度去 AI 味保护（不得整段删除正文）」（SKILL.md:20-33）。
- 脚本（多为唯一源）：check-ai-patterns.js（70.9KB，最大脚本）、check-degeneration.js、normalize-punctuation.js；check-outline-copy.js 为共享副本。
- references：anti-ai-writing.md（38KB）、deslop-workflow.md、banned-words.md。

### 2.7 moshu-scan（扫榜）
- 用途：多平台榜单分析→题材候选/风险阈值/验证动作；「跨样本重复模式才算信号」。
- 脚本：4 个 scraper（qidian/fanqie/jjwxc/qimao）+ cdp-utils.js + scan-analyze.js（4 平台通用提取，--dup 跨平台聚合）。ciweimao scraper 已删（CHANGELOG v1.1.2）。
- 依赖 moshu-cdp（浏览器登录态）。
- references 5 个：scan-output-format/genre-trends/topic-decision/publishing-guide/reader-profiling。

### 2.8 moshu-setup（部署器）
- 用途：向 Claude Code 项目部署 hooks/agents/rules/CLAUDE.md；「不覆盖用户已有配置，合并而非替换」铁律；agents_version 升降级语义（SKILL.md:18-22）。
- 部署物：7 个 agent 模板（architect/chapter-extractor/character-designer/consistency-checker/explorer/narrative-writer/researcher，位于 `references/templates/agents/moshu-*.md`，实测 ls；本行初版误写为 `templates/agents/`，已订正）、10 个 hook 脚本（`references/templates/hooks/`：session-start/end、pre/post-compact、check-prose-after-write、detect-story-gaps、guard-outline-before-prose、validate-story-commit、story_hook_core.js 51.9KB + story_hook_cli.js + lib）、4 个 rules、CLAUDE.md.tmpl、`references/agent-references/`（共享方法论副本 25+ 个）。
- 脚本：deploy.py（24KB 源，主部署逻辑）、merge-claude-settings.py（settings 合并）。
- UPGRADING.md：agents_version 权威（27），历史 10 个版本段。

### 2.9 moshu-style（文风学习）
- 用途：任意量原文→文风库/文风.md（句长/标点/段落节奏/对话技法/锚点片段）；明确「表达层提取、题材层排除」边界与与 analyze 技法总结的分工（SKILL.md「范围声明/提取边界」）。
- 无脚本，纯 SOP（references/style-learn-sop.md 12KB）。产物被 moshu-write 每章文风召回消费。

### 2.10 moshu-cdp（浏览器工具）
- 用途：CDP 控制 Chrome 复用登录态；--detect-only 无副作用探测；「首次启动会 kill 常规 Chrome，须先征求同意」（SKILL.md:15）。
- 单文件 setup-cdp-chrome.js（41KB）。被 moshu-scan 依赖；标注 Windows 实验性。

---

## 3. 机制盘点

### 3.1 追踪 schema / 状态系统（代码事实）

权威定义：`skills/moshu-write/scripts/tracking_commit.py`（三副本字节同步，shared-assets 组 story-tracking-transaction）。

- 版本常量（:25-26）：`INPUT_SCHEMA_VERSION = 1`、`TRACKING_SCHEMA_VERSION = 4`。
- 字节护栏（:27-33）：delta 1536/3072、context 8192/12288、snapshot 4096/8192（target/max）。
- 续写状态卡固定 7 栏（:35-43）：当前位置/长期约束/核心角色状态/活跃伏笔/近三章速记/下一章承诺/连贯性风险（workflow-daily.md:46 同口径）。
- 枚举（:44-48）：伏笔状态 已埋/已回收/已过期/放弃；揭示 未揭示/部分揭示/已揭示；ID 格式 F\d{3,}/E\d{3,}。
- 退役路径清单（:60-67）：_tracking-meta.json、阶段摘要.md、角色状态.md、时间线.md 等→`_旧追踪存档`。
- 模型：单写者串行事务，`_tracking-state.json` 最后原子写为唯一提交点（文件 docstring :1-5）；派生视图（逐章增量/角色快照/伏笔视图/作者读者时间线/状态卡）全部由工具确定性生成（workflow-daily.md:48）。
- 修订号协议：`expected_state_revision` 乐观锁（workflow-daily.md:54）。
- current-contract.json：`progress_schema_version: 2`、`agents_version: 27`、`setup_skill_version: "1.2.11"`、required_outline_sections 8 项——细纲契约的机读权威。

### 3.2 机检（确定性检测器）

四类共享检测器 + 追踪事务（shared-assets.json 36 组实测，前 5 组为脚本副本）：
- check-ai-patterns.js（AI 句式，源 deslop，3 副本）、check-degeneration.js（退化/占位符，3 副本）、normalize-punctuation.js（3 副本）、check-outline-copy.js（细纲照搬，源 write，2 副本）、tracking_commit.py（3 副本）。
- 部署后由 hooks 触发：check-prose-after-write.sh、detect-story-gaps.sh（伏笔状态检测，check-hook-regex-sync.sh 守卫其行为）、guard-outline-before-prose.sh、validate-story-commit.sh。

### 3.3 shared-assets 同步

- shared-assets.json 36 组：source→targets 字节级同步；`sync-shared-assets.py sync/check`；check-shared-files.sh 在其上再扫同名 reference 文件（实测 64 组 0 mismatch）。忽略/分叉白名单（check-shared-files.sh:13-36）：output-templates 等 5 个 basename 忽略、双男主.md（genre-styles 分叉）、emotional-methods.md（moshu-write 长篇专属分叉）。

### 3.4 文档体积预算

- doc-budget.json：12 个热路径文件 budget（去空白字数）；check-doc-budget.sh 守卫 + `_comment` 记录历次显式调预算理由（40600→40900→43300→43600 组预算链）。超支处理顺序：先删等量旧文本，删不动才显式调高。

### 3.5 行为契约守卫

- behavior-contracts.json：9 条 must_contain 约束（裸调用停靠/细纲优先/S1S2 过桥/日更事务/串行不并发等），check-behavior-contracts.py 静态验证 + 正反 fixture 回归。

### 3.6 版本一致性

- agents_version=27：8 处 SKILL.md 声明 + UPGRADING.md + current-contract.json，check-agents-version-sync.sh 守卫（实测通过）。
- skill 版本：write/analyze/import/scan/deslop/moshu/cdp=1.1.1、review=1.1.5、setup=1.2.11、style=1.0.0（实测 frontmatter）。

### 3.7 CI

- `.github/workflows/`（scripts/README.md:5 提及 cross-platform.yml 等；本盘点未逐个读 yml——存疑：CI 配置详情未验证）。

---

## 4. 缺陷与不一致清单

| # | 严重度 | 类型 | 内容 | 证据 |
|---|---|---|---|---|
| 1 | 中 | 文档数字过期 | scripts/README.md 称 check-claude-adapter 守卫「Claude marketplace 与 **9 个 skill** 的一一映射」，实际 skill 数为 10（static-check 实测 Total: 10）；adapter 脚本本身已是动态枚举（check-claude-adapter.sh:37 `glob("*/SKILL.md")`），仅索引文档数字未随 moshu-style 加入更新 | scripts/README.md:21 vs `ls skills` |
| 2 | 中 | 版本发布状态漂移 | CHANGELOG 顶版本为「v1.1.2（2026-08-18，**未发布**）」且含大量已合入改动（瘦身/删 ciweimao/审查修复），但 moshu/VERSION=1.1.1、README.md:19 仍写「最近更新（v1.1.1）」、各 skill frontmatter 停在 1.1.1/1.1.5/1.2.11——发布版本三处（VERSION/README/frontmatter）与 CHANGELOG 不同步 | CHANGELOG.md:5、skills/moshu/VERSION、README.md:19 |
| 3 | 低 | README 覆盖面不全 | README.md:5 概括为「覆盖扫榜、拆文、写作、去AI味的全流程」，未提 审查/导入/文风（三个已存在 skill）；后文目录树有文风库说明（:176-177），首段口径滞后 | README.md:5 |
| 4 | 低 | 预算松弛提示未处理 | check-doc-budget 输出 **4 条**「比预算低可降 budget 锁住精简」（终检复核补全）：moshu-review/SKILL.md 低 1101 字、moshu-import/SKILL.md 低 991 字、moshu-deslop/SKILL.md 低 1229 字、moshu-analyze/SKILL.md 低 1227 字——预算未随精简收紧，后续膨胀空间敞口（初版漏记 review 一条，已订正） | check-doc-budget.sh 实测输出 |
| 5 | 低 | 测试断言弱/跳过 | dashboard 单测 5/31 skipped（平台能力探测：不可读目录/符号链接/POSIX 权限位），Windows 上权限类断言实际未执行 | tests/dashboard-server.test.mjs:267,326,363,641,673,702 |
| 6 | 低 | 磁盘卫生 | skills/{analyze,review,write,setup}/scripts/__pycache__/*.pyc 存在于工作区（最大 64KB）；git ls-files 实测 0 个被跟踪——非污染，但目录树盘点与字节统计被抬高（本表 1.2 的字节数含 .pyc） | find skills -name '*.pyc'；git ls-files \| grep -c pycache → 0 |
| 7 | 低 | 双轨版本载体 | moshu skill 同时有 frontmatter `version: 1.1.1` 与独立 VERSION 文件（内容 1.1.1）；两处需人工同步，无守卫覆盖 VERSION 文件（check-agents-version-sync 只管 agents_version） | skills/moshu/SKILL.md:3、skills/moshu/VERSION |
| 8 | 低 | 双名称机制 | 「续写状态卡/上下文.md/_tracking-state.json 检查点」三种称呼指同一物（workflow-daily.md:44-46 三段内并用）；「主对标/对标书/对标」混用（workflow-daily.md:9）；无统一术语表 | skills/moshu-write/references/workflow-daily.md:44-54 |
| 9 | 低 | 白名单腐化注释 | check-shared-files.sh IGNORE_NAMES 中 5 项里至少 3 项自述为 no-op（AGENTS.md.tmpl/hooks.json/genre-writing-techniques.md 已不存在），注释已声明是有意保留，但长期会掩盖真实忽略需求 | check-shared-files.sh:13-22 |
| 10 | 低 | evals 样本极薄 | evals/samples 仅 2 个样本（prose-ai-flavored/prose-clean 各 1），端到端质量回归对单一主题文本对的依赖度高 | ls evals/samples |
| 11 | 低 | （推断）文档引用守卫盲区 | static-check 校验 Markdown 相对链接，但 scripts/README.md:21 的「9 个 skill」这类叙述性数字不在任何守卫覆盖内（check-current-skill-contracts 只管 manifest 固定值）——属机制空白而非单点 bug | scripts/README.md vs current-contract.json |

TODO/FIXME 汇总：grep 全仓 skills/scripts 代码（排除检测器正则）**0 个真实 TODO/FIXME**（仅 check-degeneration.js:42、story_hook_core.js:753 中把 "TODO" 作为被检测的占位符模式）。注释掉的代码块未发现（static-check 0 warn）。

---

## 5. 能力空白清单（长篇网文写作系统视角）

| # | 空白 | 代码证据（未发现） |
|---|---|---|
| 1 | **一致性追踪无信息差/读者知识状态维度** | tracking_commit.py 枚举仅伏笔/揭示/事件（:44-48）；无 reader-knowledge/信息差结构。REVEAL_STATUSES 是单条揭示状态，不是「某角色/读者各自知道什么」矩阵 |
| 2 | **伏笔无悬置时长自动预警的机检落点** | 「悬了太久预警」仅出现在 volume-review.md:14 的复盘口径（AI 语义判断）；detect-story-gaps.sh 有伏笔状态检测但未见按章距计算的预警（check-hook-regex-sync.sh 守卫的是状态正则）——（推断，hook 内部细节未逐行验证） |
| 3 | **审查闭环不完整：review 产出→修改→复审的工单化流转缺失** | moshu-review SKILL.md/review-workflow.md 有 findings 输出，但全仓 grep 无 fix_ticket/工单/复审判定结构；review 与 write 的 revision 流程（workflow-revision.md）之间无确定性衔接产物 |
| 4 | **卷复盘为纯冷路径文档流程，无任何确定性支持** | volume-review.md 四步全部 AI 执行；伏笔清账读 追踪/伏笔.md 人工归类，tracking_commit.py 无卷范围查询子命令（argparse 子命令实测以 init/commit/check 为主） |
| 5 | **无进度持久化的机读「下一步」判定** | architecture.md:53 的 S0-S6 状态机是路由层示意，未见任何脚本计算/落盘该状态；判断散落在各 SKILL.md 的条件分支里 |
| 6 | **文风仅有静态基准，无正文与文风基准的偏差度量** | moshu-style 产 文风.md（表达层特征）；check-* 检测器无「文风漂移」维度的确定性检测（check-ai-patterns 是通用 AI 味） |
| 7 | **无跨章/跨卷节奏与字数曲线的确定性分析** | 机检仅字数下限/句式；无逐章字数/事件密度序列的分析脚本（dashboard 只做浏览编辑，dashboard-server.mjs 定位） |
| 8 | **多书管理仅是目录约定** | moshu/SKILL.md「多书切换」为 .active-book 文件 + 目录扫描；无书级元数据/进度汇总结构 |
| 9 | **evals 无 LLM-judge/主观维度** | evals/README.md「边界（诚实声明）」自认：情绪交付、节奏、爽点等主观维度不在评测范围，且客观侧也只有 1 对样本 |
| 10 | **e2e 仅覆盖 dashboard** | tests/e2e 只有 dashboard.spec.mjs；写作/拆文/导入等核心管道无端到端自动化（依赖真人无头走查，CHANGELOG v1.1.0 述） |
| 11 | **CDP/scraper 依赖外部站点结构，无契约测试外的防变化监控** | 4 个 scraper 硬编码选择器（如 jjwxc-rank-scraper.js 17KB）；test-scan-runtime 只测 argv/JSON 契约与无副作用 import，不验证站点改版 |

---

## 6. 测试与守卫现状小结

- 守卫体系（12 check + 19 test + 1 eval）设计上互为正反 fixture（行为契约/版本同步/shared-assets 均有「反向必须失败」用例），本轮实测 6 项守卫全绿、dashboard 单测 26/31 过 0 fail。
- 强项：字节级共享资产同步、agents_version 全链一致、热路径预算硬约束、schema 版本常量三副本一致（INPUT=1/TRACKING=4，tracking_commit.py:25-26 三处 grep 相同）。
- 弱项：叙述性数字无守卫（缺陷 #1/#11）；e2e 覆盖窄；evals 样本薄；CI yml 本轮未核（存疑）。

## 7. 待验证问题

1. CI workflow（.github/workflows/*.yml）实际跑哪些守卫、分支/矩阵配置——本轮未读。
2. moshu-setup 部署回归 check-moshu-setup-deployment.sh（>2min）未跑；deploy.py 在 Windows GBK 环境的实际行为仅由静态守卫保证。
3. e2e（playwright）未跑，浏览器依赖未知。
4. detect-story-gaps.sh 内部是否有伏笔悬置时长计算（空白 #2 的推断部分）。
5. moshu-review「AI 模式计数 10→12」（CHANGELOG）与当前代码的检测器规则数是否对齐——未逐条数 check-ai-patterns.js 规则。

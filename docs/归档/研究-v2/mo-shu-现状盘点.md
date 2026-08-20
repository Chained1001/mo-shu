# mo-shu 现状盘点（源码级）

> 盘点日期：2026-08-20（基于工作区当前工作树）
> 盘点方式：只读（read/grep/glob/pwsh 只读命令），未改动任何项目文件，未跑构建/安装。
>
> 实际读过的关键文件（代表性，非穷尽）：`README.md`、`README_EN.md`、`docs/architecture.md`、`docs/实施总纲.md`、`CHANGELOG.md`、`package.json`、`playwright.config.mjs`、`.claude-plugin/marketplace.json`、10 个 `skills/*/SKILL.md`、`skills/moshu-setup/references/templates/agents/*`（7）、`skills/moshu-setup/references/templates/hooks/*`（8+lib）、`skills/moshu-write/scripts/tracking_commit.py`、`scripts/behavior-contracts.json`、`scripts/shared-assets.json`、`scripts/doc-budget.json`、`scripts/current-contract.json`、`scripts/README.md`、`scripts/check-claude-adapter.sh`、`scripts/check-shared-files.sh`、`tests/*`（3）、`.github/workflows/*`（3）、`evals/README.md`。

> 关键结论先说：本项目工程质量较高（多层守卫 + 三平台 CI + 单一权威追踪事务），当前工作树处于 **CHANGELOG v1.1.2「未发布」的中途态**（moshu-style 已拆出、marketplace 已 10 插件，但 README/architecture/scripts-README 的「9 个 skill」等数字尚未同步）。最严重问题集中在：**文档层事实漂移（9 vs 10 skill）** 与 **`docs/实施总纲.md` 白纸黑字自认的 8 项架构缺陷（P1-P8）仍未实施**。

---

## 1. 总体结构（目录树 + 各层职责）

```
mo-shu/                        # 长篇网文写作 skill 包（Claude Code 单端）
├── skills/                    # 10 个 skill（1 路由中枢 + 9 功能 skill）
│   ├── moshu/                 # 路由中枢 + Dashboard（assets/ + scripts/dashboard-server.mjs）
│   ├── moshu-setup/           # 部署（agents/hooks/rules/CLAUDE.md/agent-references 模板源）
│   ├── moshu-write/           # 写作（最大，Phase1-5 + 追踪事务）
│   ├── moshu-analyze/         # 拆文
│   ├── moshu-scan/            # 扫榜（4 平台 scraper）
│   ├── moshu-deslop/          # 去 AI 味
│   ├── moshu-import/          # 逆向导入
│   ├── moshu-review/          # 多视角审查
│   ├── moshu-style/           # 文风学习（v1.1.2 新拆出）
│   └── moshu-cdp/             # 浏览器 CDP（基础组件）
├── scripts/                   # 仓库开发守卫/测试/代码生成（42 文件：37 脚本 + 4 JSON + README）
├── tests/                     # dashboard node:test 单测 + Playwright E2E + fixtures/helpers
├── docs/                      # 架构图 + 三参考项目研究 + 实施总纲（规划）
├── .github/workflows/         # 3 个 CI（cross-platform / dashboard / cli-compat）
├── .claude-plugin/            # marketplace.json（10 个 plugin 声明）
└── evals/                     # 正文质量评测基准（2 样本 + README）
```

**各层职责**（对应 `docs/architecture.md` §4 分层）：
- **会话层**：`moshu` 路由（SKILL.md 内 11 行意图表 + 9 序状态机）分发到 9 子 skill，按需 spawn 7 agent。
- **确定性脚本层**：`check-ai-patterns.js` / `check-degeneration.js` / `check-outline-copy.js` / `tracking_commit.py` / `dashboard-server.mjs` / 榜单 scraper / `deploy.py`。
- **Hook 层**：8 个 shell hook（见 §4）。
- **文件系统数据层**：拆文库 / 写作项目（设定·大纲·正文·对标·追踪）。

**规模数字（本次实测）**：10 skill；skills 下运行时脚本 27 个；`scripts/` 37 个脚本；全仓 `references/*.md` 精确 **187** 个文件；`shared-assets.json` 36 组（51 target + 36 source = 87 副本）；`tests/` 3 个测试文件（合计约 1451 行）。

---

## 2. Skill 体系

### 2.1 总表

| Skill | 版本 | 触发 | 核心职责（一句话） | references 数* | scripts | 依赖/路由到 |
|---|---|---|---|---|---|---|
| moshu | 1.1.1 | `/moshu` `/网文` | 路由中枢 + Dashboard | 0 | 1 | spawn explorer/researcher；路由 9 子 skill |
| moshu-setup | 1.2.11 | `/moshu-setup` | 一键部署 hooks/agents/rules/CLAUDE.md | ~89 | 2 | 写 `.story-deployed` sentinel |
| moshu-write | 1.1.1 | `/moshu-write` | 长篇写作（开书→日更→修订）+ 追踪事务 | ~81 | 5 | 消费 analyze/import/style 产物 |
| moshu-analyze | 1.1.1 | `/moshu-analyze` | 拆文（黄金三章/节奏/技法总结） | 6 | 3 | 产 `拆文库/`；被 import 复用管道 |
| moshu-scan | 1.1.1 | `/moshu-scan` | 扫榜（4 平台市场趋势/选题） | 5 | 6 | 复用 cdp-utils |
| moshu-deslop | 1.1.1 | `/moshu-deslop` | 去 AI 味（检测+清除） | 3 | 4 | 复用 write 的检测器 |
| moshu-import | 1.1.1 | `/moshu-import` | 逆向导入（旧书→标准结构） | 6 | 1 | 驱动 analyze 管道；产追踪状态 |
| moshu-review | 1.1.5 | `/moshu-review` | 多视角对抗审查（full/lean/solo） | 12 | 4 | spawn 4 reviewer agent |
| moshu-style | 1.0.0 | `/moshu-style` | 文风学习（→`文风库/文风.md`） | 1 | 0 | 产物供 write 每章召回 |
| moshu-cdp | 1.1.1 | `/moshu-cdp` | 浏览器 CDP 自动化（基础组件） | 0 | 1 | 被 scan/researcher 复用 |

\* 数字为约数（setup/write 含 genre-prose-cards 与 templates 子目录，口径见 §2.3）。

### 2.2 各 skill 要点（入口/热路径/差异）

- **moshu**（路由中枢，131 行）：`frontmatter` 无 model；路由表 11 行 + 「状态判定」9 序（未部署→无书→未完成拆文→开书→补纲→写章→卷复盘→未完成审查→询问），判定全来自文件系统证据（`.story-deployed` / `拆文库/*/_progress.md` / 细纲章号 vs `last_committed_chapter`）。显式声明 `agents_version: 27`，spawn explorer/researcher 前做轻量可用性检查，不可用降级 `Fallback: ... -> direct lookup`。Dashboard 起 `scripts/dashboard-server.mjs`（只监听 127.0.0.1，防暴露）。
- **moshu-write**（221 行，最大功能 skill）：热路径 = `SKILL.md` + `workflow-daily.md` + `workflow-chapter.md`（合计 ~35KB 去空白，受 doc-budget 约束）。`agents_version: 27`。references 81 文件分「大纲/人物/钩子/情绪/风格/技法/去 AI/质量/追踪」等簇，按需加载。
- **moshu-setup**（189 行）：部署态 skill，`deploy.py`（365 行，deploy/verify 子命令）+ `merge-claude-settings.py`（139 行，仅 hooks 幂等合并）。agent-references 63 个 .md（31 方法论 + 32 genre-prose-cards）。
- **moshu-analyze / moshu-import / moshu-review / moshu-deslop**：v1.0.1 起「入口骨架化」——SKILL.md 从 29-36KB 瘦到 4.6-7KB，流程下沉 `references/*-workflow.md`（CHANGELOG v1.0.1），每个入口设 doc-budget 防再膨胀。
- **moshu-scan**（349 行，SKILL.md 最长）：4 个 scraper（`qidian/fanqie/jjwxc/qimao-rank-scraper.js`）+ `scan-analyze.js`（4 平台通用提取）+ `cdp-utils.js`。**无 agents_version 声明**（存疑：是否有意省略）。
- **moshu-style**（v1.1.2 新拆，版本 1.0.0）：单 reference `style-learn-sop.md`，无 scripts，无 agents 机制。是「文风」从 analyze Stage 拆出的独立技能。
- **moshu-cdp**：基础组件，无 references、无 agents_version。static-check 规则「除 moshu-cdp 外禁止跨 skill 文件引用」印证其 base 地位。

### 2.3 跨 skill 重复（设计模式 + 维护成本）

- **references 字节重复**：`genre-prose-cards`（32 张）在 write 与 setup 完整重复；`anti-ai-writing.md`/`banned-words.md` 跨 4 处（write/deslop/review/setup）；`character-relations/dialogue-mastery/plot-core-methods/quality-checklist/reader-contract-and-progression` 跨 3 处（write/review/setup）；`tracking-transaction.md` 跨 3 处（write/import/review）。
- **scripts 字节重复**：`check-ai-patterns.js`/`check-degeneration.js`/`normalize-punctuation.js` 跨 3 处（write/deslop/review）；`tracking_commit.py` 跨 3 处（write/import/review，SHA256 三份完全一致）；`check-outline-copy.js` 跨 2 处（write/deslop）。
- 以上由 `shared-assets.json`（36 组）+ `check-shared-files.sh` 守护字节一致，属「部署自包含」设计（skill 独立分发需自带副本），非缺陷；但大块方法论（如 genre-prose-cards 32 张 ×2）维护成本高、改一处需 sync。

---

## 3. Agent 体系（7 个）

**模板位置**：`skills/moshu-setup/references/templates/agents/`（7 个 .md）。**部署方式**：`deploy.py` 将 7 个 .md `shutil.copy2` 原样复制到项目 `.claude/agents/`；**模型/tools 不注入**——已写在每个 .md 的 frontmatter，由 Claude Code 运行时读取。`agents_version` **不在 agent frontmatter**，而在部署层（`deploy.py` `DEFAULT_AGENTS_VERSION='27'`，写入 `.story-deployed` sentinel；`scripts/current-contract.json` 也记 `agents_version: 27`）。版本门禁：禁止降级覆盖。

| Agent | 模型 | tools（disallowed） | memory/maxTurns | 职责一句话 | 引 references |
|---|---|---|---|---|---|
| moshu-architect | **opus** | Read,Glob,Grep,Write,Edit | project/30 | 宏观架构：题材/世界观/大纲/钩子/反转/情绪弧线 | hooks-chapter、hooks-suspense、emotional-arc-design、reversal-toolkit、outline-*、genre-*、opening-design、quality-checklist |
| moshu-character-designer | **sonnet** | Read,Glob,Grep,Write,Edit | project/25 | 角色档案/语言风格/动机链/弧线/对话 | character-basics、character-design-methods、character-relations、dialogue-mastery |
| moshu-narrative-writer | **sonnet** | Read,Glob,Grep,Write,Edit,**Bash** | project/30；`skills:[moshu-deslop]` | 正文写作 + 去AI味(7 Gate) + 格式合规 + 字数实测 | writing-craft、format-and-structure、genre-*、anti-ai-writing、banned-words、quality-checklist、dialogue-mastery、文风.md(外部) |
| moshu-consistency-checker | **haiku** | Read,Glob,Grep（**禁** Write,Edit,Bash） | **无 memory**/15 | 事实一致性 grep-first 检查，输出 S1-S4 | 仅 quality-checklist |
| moshu-researcher | **sonnet** | Read,Glob,Grep,Bash,Write（禁 Edit） | project/20 | 外部资料研究，CDP 优先 WebSearch 兜底 | 无（用 CDP/WebSearch） |
| moshu-explorer | **haiku** | Read,Glob,Grep（禁 Write,Edit,Bash） | 无 memory/15 | 项目结构化只读查询，返回 JSON | 无（纯文件系统） |
| moshu-chapter-extractor | **haiku** | Read,Glob,Grep（禁 Write,Edit,Bash） | 无 memory/12 | 章节→情节点/摘要/角色提取（并行拆文核心） | 无（自带输出格式） |

**模型绑定规律**：创作类最强（architect=opus）；执笔/设计/研究=sonnet；只读查询类=haiku（consistency/explorer/extractor）。两个纯只读 agent（consistency-checker/explorer）故意**不设 `memory: project`**（注释说明会隐启 Write/Edit 与 disallowedTools 矛盾）。

**prompt 结构**：
- 三个「创作+审查」agent（architect/writer/designer）同构：参考路径规则（含 canonical 路径 `{项目根}/.claude/skills/moshu-setup/references/agent-references/` + 「包内路由表边界」防跨 skill 读）→ 参考体系表 → 创作能力 → 审查能力（对抗性）→ 禁止事项 → 职责边界 → 被调用协议。
- consistency-checker：三步流程（术语→冲突扫描→推理型审查）+ S1-S4 分级。
- explorer：11 种 query_type 逐条流程 + 纯 JSON 输出（必须 `JSON.parse` 可解析、禁 code fence）。
- chapter-extractor：「材料合法性→客观白描铁律→输出格式(OUTPUT_MODE:json)→提取规则→12 条质量自检」。

---

## 4. Hooks（8 个）

**模板位置**：`skills/moshu-setup/references/templates/hooks/`（8 个 .sh + `lib/common.sh` + `lib/sentinel.sh` + `story_hook_cli.js` + `story_hook_core.js`）。**触发配置**：`skills/moshu-setup/references/templates/settings-hooks.json`。`merge-claude-settings.py` 幂等合并（`MANAGED_HOOK_SCRIPTS` 8 个 .sh 文件名集合）。

**8 个 hook 在 settings-hooks.json 里各注册恰好一次，无缺配、无孤儿**（实测核对）。实际配置 3 个 matcher 块（PreToolUse×2 + PostToolUse×1），其余 5 个走事件级（无 matcher）。

| Hook | 触发时机 | 功能 | 阻断? | 依赖 |
|---|---|---|---|---|
| session-start.sh | SessionStart | 重启确认、部署自检、进度/上下文摘要、版本检查 | 否（纯信息） | common+sentinel |
| session-end.sh | SessionEnd | 仅 `STORY_SESSION_LOG=1` 时追加日志 | 否 | common |
| detect-story-gaps.sh | SessionStart | 6 项缺口检测（设定少/伏笔异常/大纲缺/拆文未完/连续性） | 否（WARN） | common(+node continuity) |
| pre-compact.sh | PreCompact | 输出上下文路径行数 + git 变更计数 | 否 | common |
| post-compact.sh | PostCompact | 提醒读 `追踪/上下文.md` 恢复上下文 | 否 | common |
| validate-story-commit.sh | PreToolUse matcher `Bash`+`if: Bash(git commit*)` | 提交时查正文硬编码属性/角色卡缺字段 | 否（**advisory，恒 exit 0**） | common+node |
| guard-outline-before-prose.sh | PreToolUse matcher `Bash\|Write\|Edit\|MultiEdit` | 写正文前：缺细纲/追踪检查点/毒句式欠账 | **是（BLOCKING，exit 2）** | common+node |
| check-prose-after-write.sh | PostToolUse matcher `Write\|Edit\|MultiEdit` | 正文落盘后轻量确定性网（截断/拒绝语/工程词/复读/毒句式/字数） | 否（advisory，exit 0） | common+node |

**实现共性**（编码健壮性）：全 hook `export LC_ALL=C`（字节匹配抗 Windows GBK）；全角冒号 `(：|:)` 交替；`printf '%s'` 防转义；`NL=$'\n'` 真实换行；`HOOK_INPUT` 不 export（防 E2BIG）；Windows 盘符归一正斜杠；git diff `-z` null 分隔。`lib/common.sh` 提供项目根/活跃书发现/拆文未完检测；`lib/sentinel.sh` 解析 `.story-deployed` YAML sentinel。

---

## 5. 脚本与守卫体系

### 5.1 分类清单（`scripts/` 共 42 文件 = 37 脚本 + 4 JSON + README；与 `scripts/README.md` 1:1 吻合，无死脚本/未登记脚本）

- **静态守卫（check-*，13 个）**：`static-check.py/.sh`（frontmatter/路径/锚点/Agent 引用/references 可达性，禁跨 skill 引用）、`skill-numbering.py`（Step 编号策略+小数守卫）、`check-current-skill-contracts.sh/.py`（manifest 校验版本/Phase/schema/主产物/细纲契约）、`check-shared-files.sh`（runtime 副本 + reference 字节一致）、`check-moshu-setup-deployment.sh`（部署回归，>2min）、`check-doc-budget.sh`（热路径字数预算）、`check-hook-regex-sync.sh`、`check-hook-locale-safety.sh`（GBK 字节安全）、`check-python-invocation.sh`（禁裸 `python3`）、`check-claude-adapter.sh`（marketplace↔skill 精确映射 + 可选真实 CLI）、`check-behavior-contracts.sh/.py`、`check-agents-version-sync.sh/.py`。
- **测试回归（test-*，17 个）**：检测器回归（ai-patterns/outline-copy/degeneration/normalize-punctuation）、hook 回归（prose-backstop/story-continuity/hook-encoding/charcount）、扫描/分析回归（scan-runtime/scan-analyze/merge-summaries）、契约回归（static-check/current-skill-contracts/shared-assets/behavior-contracts/agents-version-sync/skill-numbering）、**追踪回归（tracking-commit/tracking-workflow-contracts）**、端到端评测（eval-prose-quality）。
- **代码生成**：`sync-shared-assets.py`（sync/check 子命令）。

### 5.2 四个 JSON 机制（防漂移/防膨胀）

1. **`behavior-contracts.json`**（9 条契约）：关键写作约束的**文本存在性守卫**——每条 `must_contain` 子串必须存在于指定文档，防止 skill 迭代删掉关键约束（裸调用停靠/细纲优先/S1-S2 过桥/追踪事务/三层分工等）。`check-behavior-contracts.py` 逐条校验。
2. **`shared-assets.json`**（36 组 = 5 脚本组 + 31 reference 组；51 target + 36 source = 87 副本）：唯一 source→targets 映射，`sync-shared-assets.py` 保证字节+mode 一致，防跨 skill 共享副本漂移。
3. **`doc-budget.json`**（12 文件预算 + 3 路径组上限 35400/22750/43600）：热路径文本「去空白字数」上限，超了要么删旧文本要么显式调高（带 why）。度量=去空白字符数。
4. **`current-contract.json`**（manifest）：`setup_skill_version 1.2.11` / `agents_version 27` / `topic_decision_phase 5` / `progress_schema_version 2` / 2 主产物（剧情/情绪模块.md + 剧情/节奏.md）/ 8 细纲节。防版本降级与主产物静默替代。

---

## 6. 数据层（追踪系统）

**实现文件**：`skills/moshu-write/scripts/tracking_commit.py`（1139 行，权威；write/import/review 三份 SHA256 字节一致）。

**唯一权威 + 事务模型**：`追踪/_tracking-state.json` 是唯一结构化权威（`TRACKING_SCHEMA_VERSION=4`，`INPUT_SCHEMA_VERSION=1`）。三个子命令 `init`/`commit`/`check`。

- **schema 顶层 8 域**：`schema_version`、`book_title`、`last_committed_chapter`、`imported_through_chapter`、`state_revision`、`context`（position/long_term_constraints≤6/active_character_names≤6/continuity_risks≤5/recent_chapters≤3/next_chapter_commitments≤5）、`characters`（identity/location/goal/state/abilities_resources/relationships/knowledge/open_threads）、`foreshadow`（status∈已埋/已回收/已过期/放弃；importance 高/中/低；伏笔/悬念/感情线/债务共用 summary 前缀区分，零 schema 变更）、`timeline`（story_time/objective_fact/reader_knowledge/reveal_status∈未揭示/部分揭示/已揭示/reveal_chapter/characters/first_recorded_chapter/updated_chapter）。
- **派生视图**（由 `render_views` 整份重生成）：`上下文.md`（7 栏续写状态卡）、`伏笔.md`、`时间线/作者真相.md`、`时间线/读者已知.md`、`角色状态/{名}.md`、`逐章记录/第NNN章.md`。字节预算（target/max）：delta 1536/3072、上下文 8192/12288、角色快照 4096/8192。
- **check 逐字比对**：`check_project()`（行 1070-1099）从 `_tracking-state.json` 重新 `render_views`，对每个派生视图 `path.read_text() == expected` **逐字比较**；并校验逐章记录连续性（`imported_through_chapter+1` 起连续覆盖）、规范文件名、体积、角色快照文件集合。
- **事务协议**：`mode=append` 要求 `chapter == last+1`；`mode=revision` 要求 `chapter <= last`（重算该章记录）；两类退役只允许 append；`expected_state_revision` 乐观并发（构造前 check 取 revision，提交不等即拒 stale）。**落盘顺序**：先写逐章记录 → 派生视图 → 最后 `atomic_write_text`（mkstemp+fsync+os.replace）原子替换权威 JSON。
- **无锁/无哨兵**：docstring 明言 "one serial writer; concurrent commits are intentionally unsupported"，`expected_state_revision` 是顺序校验**不是并发锁**（`tracking-transaction.md` 明示）。行为契约第 7 条「不得多章并发写」背书串行假设。
- **作者/读者时间线隔离**：`作者真相.md`（objective_fact+reveal_status+实际揭示章）vs `读者已知.md`（只呈现 reader_knowledge，不泄露作者侧真相）——防未来剧情泄漏的核心机制。
- **导入反向重建**：`moshu-import/references/character-state-reverse.md`（只从落盘拆书产物反推 8 字段截至最后完整章；残稿不提前生效）；`state-tracking.md` write/import 两侧逐字相同。

---

## 7. 测试与 CI 现状

### 7.1 测试

- **`tests/dashboard-server.test.mjs`**（804 行，node:test）：工作区扫描/路径边界/HTTP API（懒加载、原子保存、外部改动 409、跨源删除 403、8 并发 PUT 仅 1 成功、token 鉴权）。
- **`tests/dashboard-trigger-contract.test.mjs`**（52 行）：契约测试——`/moshu dashboard` 触发词、127.0.0.1、不主动 `--allow-network`、marketplace 发布、5 bundle 文件在位。
- **`tests/e2e/dashboard.spec.mjs`**（595 行，Playwright）：UI 端到端（浏览/搜索/编辑/XSS 净化/删除确认/保存竞态/CRLF 保真/深目录/分页/mobile）。
- **数据层测试在 `scripts/` 而非 `tests/`**：`test-tracking-commit.py` + `test-tracking-workflow-contracts.py`（追踪事务/契约回归），CI 三端均跑。
- **`evals/`**：端到端正文质量基准（`prose-ai-flavored.md` vs `prose-clean.md`，缺陷样本命中必须 > 干净样本），`eval-prose-quality.sh` 驱动。README 诚实声明：只覆盖确定性可检测维度，主观维度需 LLM-judge。
- **fixtures**（`tests/fixtures/`）：`dashboard/`（拆文库《盘龙》+ 长篇《让你管账号…》）、`scan/`（4 平台榜单 md）。

### 7.2 CI（`.github/workflows/`）

| Workflow | 触发 | 覆盖 |
|---|---|---|
| `cross-platform.yml` | push/PR（**无 path filter，全量**） | 5 job：static-guards（ubuntu 全部 check-*）、runtime-regressions（ubuntu 全部 test-* 含追踪回归+评测）、deploy-check、windows（Node20 Git Bash 模拟 Claude Code + GBK locale + cdp/chrome）、macos（Bash3） |
| `dashboard.yml` | push(main)/PR，**path-filtered**（moshu 资产/tests/marketplace 等） | api 矩阵 3 OS + e2e（仅 ubuntu Playwright） |
| `cli-compat.yml` | push/PR path-filter + **每周一 09:23 cron** + workflow_dispatch | 装最新 `@anthropic-ai/claude-code`，`CLAUDE_REAL_CHECK=1` 真实 CLI strict validate |

**覆盖盲区**：`dashboard.yml` path-filter 不含 `skills/moshu-write`/`tracking_commit.py`，追踪改动只能靠 `cross-platform.yml`（全量）兜底；追踪工具是 Python，`tests/` 目录（node:test+Playwright）不直接覆盖，由 `scripts/` 下 Python 回归承担。

---

## 8. 现状问题清单

### P0（事实错误/断链/死代码）

1. **「9 个 skill」vs 实际 10 个（事实错误，三处权威文档）**：`README.md` Skills 表只列 9 行（缺 moshu-style）；`docs/architecture.md`「9 个 Skill 入口」；`scripts/README.md`「check-claude-adapter … 9 个 skill」。而实际 `skills/` 有 10 个、`.claude-plugin/marketplace.json` 有 10 个 plugin、`check-claude-adapter.sh` 已改为动态派生（实测断言 marketplace↔skills 两边均 10 且一致）。根因：moshu-style 在 CHANGELOG v1.1.2（未发布）拆出，文档未同步。
2. **README「适用平台」仍列刺猬猫（5 平台），代码已删其 scraper（事实错误）**：`README.md:225` 列「起点·番茄·晋江·七猫·刺猬猫」；但 `skills/moshu-scan/scripts/` 只剩 4 个 scraper（qidian/fanqie/jjwxc/qimao），`CHANGELOG.md`（v1.1.2）明言「删除 ciweimao-rank-scraper.js（刺猬猫已排除）」。
3. **断链/死代码未发现硬证据（存疑）**：未运行 `static-check.py`（本次只读约束）；`CHANGELOG.md`（v1.1.2）自述「0 断链 0 孤儿」+「5 个子代理并行 + 确定性扫描」。此处标注「未验证」。

### P1（架构缺陷/职责混乱/重复实现）

1. **审查不闭环（实施总纲自认 P1）**：review/consistency-checker 结论不持久化，`.moshu-review/` 是会话态，下章不一定消费。证据：`docs/实施总纲.md` 附录 A.3「P1 审查不闭环」。
2. **写审合一（P2）**：narrative-writer 写后自审（7 Gate 去 AI 味内嵌写作 agent），自己审自己会自我辩护。证据：`skills/moshu-setup/references/templates/agents/moshu-narrative-writer.md` 7 Gate + 实施总纲 P2。
3. **上下文注入无场景过滤（P3）**：写前召回追踪状态不按目标章过滤，未来剧情可能泄漏。证据：实施总纲 P3 + U4「渲染只注入 ≤N 章」未落地。
4. **moshu-write 职责过宽（P8/D.2）**：创作设计(Phase1-3)+执行生产(Phase4-5)耦合，references 81 文件全仓最大。实施总纲 D.2 自认「应拆 moshu-plan + moshu-write」（U10，未实施）。
5. **guard-outline-before-prose.sh 阻断语义 fail-open（架构缺陷）**：README 声称「阻断」，但追踪检查点/毒句式/Bash 正文目标识别均依赖 node，node 缺席时**放行**（仅细纲门纯 bash 可拦）——native 无 node 环境下 BLOCKING 强度下降。证据：hook 实现注释 + 依赖链。
6. **追踪唯一写入口无并发锁**：仅 `expected_state_revision` 乐观校验，协议明文「不支持并发」（设计取舍；若未来多 Agent 并行写有 TOCTOU 窗口）。证据：`tracking_commit.py` docstring + `tracking-transaction.md`。
7. **大块方法论跨 skill 字节重复**：genre-prose-cards 32 张 ×2、anti-ai/banned-words ×4、tracking_commit.py ×3、3 个 JS 检测器 ×3。属「部署自包含」设计（shared-assets 36 组守护），但维护成本高。

### P2（体验/文档问题）

1. **`scripts/README.md`「64 组共享 reference」陈旧**：实际 `shared-assets.json` 36 组/51 份；`check-shared-files.sh` 动态计算、不硬编码。证据：`scripts/README.md:15` vs `shared-assets.json` 实测 36 组。`docs/architecture.md:129`「36 组」正确。
2. **`scripts/README.md`「5 个 scraper」陈旧**：实际 4 个（ciweimao 已删）。证据：`scripts/README.md:41`。
3. **README「全仓 references 189 份」vs 实际 187**（差 2）。证据：`README.md:127` vs 实测 `references/*.md` = 187。
4. **`doc-budget.json` 组上限 < 成员和**：正文 agent 组 43600 < 成员和 43650（banned-words 4200 的 +200 未同步进组）；开书组 22750 < 成员和 22800。潜在 CI 假失败风险。
5. **模型绑定用代号（opus/sonnet/haiku）非具体版本号**：绑定强度依赖 Claude Code 对别名的解析，换 CLI/换模型可能失效（存疑）。
6. **版本矩阵分散 + 处于 v1.1.2 未发布中途态**：`VERSION`=1.1.1、`marketplace.json` metadata=1.1.1、但 CHANGELOG 已有 v1.1.2（未发布）、moshu-style=1.0.0、setup=1.2.11、review=1.1.5——工作树是「已部分完成 v1.1.2 但未发布」的中间态。

---

## 9. 能力空白（对照「长篇一致性系统」目标）

> 全部来自 `docs/实施总纲.md`（状态「方案定稿 · 待实施」）——即项目自己规划的、尚未落地的一致性能力。**当前代码里均不存在对应实现。**

| # | 缺失能力 | 规划单元 | 现状 |
|---|---|---|---|
| 1 | 审查工单闭环（审完不丢、写前注入、复审关闭） | U3 quality_tickets | `.moshu-review/` 会话态，不持久化 |
| 2 | 写评分离（写作/审查两模式） | U5 | narrative-writer 写后自审 |
| 3 | 上下文场景过滤（防未来剧情泄漏注入） | U4 | 写前召回无目标章过滤 |
| 4 | 细纲伏笔引用可机检（setup_refs/payoff_refs） | U9 | 细纲只有信息留白，无机器可查引用 |
| 5 | 日更进度持久化（断点续写） | U8 `_write-progress.json` | 靠人工读追踪判断 |
| 6 | 文风负向约束（作者回避清单） | U6 | 文风库只有正面统计 |
| 7 | 每章 Git 备份/回滚/半提交探测 | U1 | 无备份脚本，写废无法回滚 |
| 8 | 机检「6 阻断+4 候选」分层/重试预算/实体名册/文件门禁 | U2 | 现机检较简单（字数/禁词/禁句式/复读等），无分层候选/预算/名册 |
| 9 | schema 升级（工单/经验/债务/追读力/evidence 域） | U3 | 现 schema v4，无这些域 |
| 10 | 章后对照 observer/arbiter + 世界事实裁决 | U4 | 章后对照仅主会话粗查，无独立裁决 agent |
| 11 | 本地 BM25 检索 / 五段任务书 / 候选制 / degradation | U7 | explorer 仅 grep，任务书未落地 |
| 12 | 团队化拆分 moshu-plan（含设定守护） | U10 | moshu-write 仍耦合规划+执笔 |

**结论**：mo-shu 现有「单一权威追踪 + check 逐字校验 + 8 hook + 7 agent」是**已落地**的强底座；但「审查闭环」「场景过滤」「可回滚」「机检分层」等长篇一致性核心能力**尚在规划文档、未进入代码**。实施总纲 §3.2 明确这些分布在 v1.1.3（U1-U2）→ v1.2（U3-U4）→ v1.3（U5-U9）→ v2.0（U10）。

---

## 10. 与三个参考项目的初步差距表

> 只列「从 mo-shu 本项目代码/规划文档能确认」的差距；参考项目细节由其他研究档案负责。来源 = `docs/实施总纲.md` 附录 A（L=webnovel-writer、S=SparkArc、P/B=自审/笔枢）与 §4 U 单元。

| 参考项目 | 借鉴点 | mo-shu 现状 | 差距确认 |
|---|---|---|---|
| webnovel-writer v7 | 每章 Git 备份/半提交探测（L1-L3） | 无备份脚本 | **缺**（U1 规划） |
| | 机检「阻断 vs 候选」分层+重试预算（L4-L5） | 现机检无分层/无预算 | **缺**（U2） |
| | 实体名册+别名反查（L11） | 无 `追踪/名册.md` | **缺**（U2） |
| | 追读力四维标注 / evidence 溯源（L6-L7） | 无 reading_power/evidence 域 | **缺**（U3） |
| | 经验库带筛选注入（L13） | 无 learned_patterns | **缺**（U3） |
| SparkArc Studio | 质量工单闭环（S5，最高价值） | 审查不闭环 | **缺**（U3） |
| | 落盘回执协议（S1） | 无「必须落盘+字数实测」契约 | **缺**（U5） |
| | 写评分离两模式（S3/S6） | 写审合一 | **缺**（U5） |
| | 三圈记忆+场景时间点过滤（S7） | 无场景过滤 | **缺**（U4） |
| | 文风作者回避负面清单（S11） | 文风库只有正面 | **缺**（U6） |
| DeterminFlow-Plugins(笔枢) | 章后对照 observer/arbiter 分离（B1） | 无独立 observer/arbiter | **缺**（U4） |
| | 叙事债务 debts 域（B2） | 无 debts 域 | **缺**（U3） |
| | 文件门禁 prepare/checkpoint（B3） | 无 `check --gate` | **缺**（U2） |
| | 命名卡/场景卡/节拍卡（已学） | 已落地（CHANGELOG v1.1.0） | ✅ 已实现 |

**已落地的跨项目能力**（mo-shu 已从参考项目吸收并进入代码）：三层分工宪法、单一权威 + check 逐字校验、反 AI 20+ 模式、钩子 14 式章尾、命名卡/场景卡/节拍卡、事实查证纪律、设定包减法加载、卷复盘机制——证据：`CHANGELOG.md` v1.1.0/v1.1.2 与对应 `references/` 文件。

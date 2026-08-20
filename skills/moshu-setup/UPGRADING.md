# 升级指南

## 当前版本

- `setup_skill_version: 1.3.0`
- `agents_version: 30`

`.story-deployed` 缺失任一字段，或 `agents_version` 缺失 / 非整数 / 小于 `30`，都视为待更新部署。直接重新运行 `/moshu-setup`；不在运行时逐级兼容历史模板。如项目 `agents_version` 大于 `30`，说明本地 moshu-setup 比项目旧：先更新 mo-shu，不得用 v30 降级覆盖。历史版本改动见仓库根目录 `CHANGELOG.md`。

**v29 → v30 变更**：moshu-explorer 模板的文风两级检查改为正查口径（合规必须见到 `文风可用：是`；「生成记录」整段缺失/被截断/占位 stub 一律 `profile_degenerate`，与主会话手动路径等价）——agent 模板变化，重跑 `/moshu-setup` 并新开会话后生效。

**v28 → v29 变更**：agent 模板产出纪律收敛为共享 base 段 `agent-references/shared-output-discipline.md`（纯 JSON 无围栏 / ASCII 直引号 / 换行转义 / 禁尾随逗号 / 先落临时文件再 --input / 输出前自检三问）——moshu-explorer 与 moshu-chapter-extractor 的散落纪律句改为锚点引用，并新增 `check-agent-template-rules` 守卫（禁互引 / 挂载点存在 / 单副本）——agent 模板与 agent-references 变化，重跑 `/moshu-setup` 并新开会话后生效。

**v27 → v28 变更**：4 个 reviewer agent 模板（moshu-architect / moshu-character-designer / moshu-consistency-checker / moshu-narrative-writer）新增「审稿令牌」段——输入首行带 8 位令牌、报告首行必须逐字回传（防 subagent 未读输入编造报告），主会话用 `review_tickets.py verify-token` 校验后采纳——agent 模板变化，重跑 `/moshu-setup` 并新开会话后生效。

**v26 → v27 变更**：agent-references 内容更新（反 AI 10 条硬约束并入、命名卡 5 张、钩子 11 类补全、场景卡 6 张、技法卡 6 张、群像反应确定性检测、beat-cards 增补等）——agent 参考文件变化，重跑 `/moshu-setup` 并新开会话后生效。

**v25 → v26 变更**：agent-references 内容更新（角色深层动机与信念、核心梗定调句、quality-checklist 统一、信息生态检查项、reader-contract 补齐等）——agent 参考文件变化，重跑 `/moshu-setup` 并新开会话后生效。

## 升级策略

| 策略 | 适用场景 | 行为 |
|------|----------|------|
| 覆盖部署 | 全新项目 | 写入当前 agents/hooks/rules/reference bundle |
| 合并部署 | 已有项目 | 替换 moshu-setup 管理文件，合并用户维护文件 |
| 手动更新 | 只更新特定文件 | 仅建议熟悉部署契约的维护者使用 |

推荐始终重新运行 moshu-setup，让部署器按 owner class 处理文件。

## 文件所有权

### moshu-setup 管理，可替换

这些文件由 moshu-setup 管理，不含用户自定义内容：
- `.claude/hooks/` — 所有 hook 脚本与 `lib/` 辅助库
- `.claude/agents/` — 所有 agent 定义
- `.claude/rules/` — 所有 path-scoped 规则
- `.claude/skills/moshu-setup/references/agent-references/` — Agent 参考资料副本

### 用户与 moshu-setup 共同维护，只合并管理块

这些文件可能含用户自定义内容：
- `CLAUDE.md` — 按 marker/section 合并，用户独有 section 保留
- `.claude/settings.local.json` — 按 command 识别 moshu hooks；已存在的受管 command 会迁移到当前模板的 event/matcher/timeout/if（例如 v26 的 Bash 正文 pre-guard），其他用户 hook 与配置保留

### 用户状态，不覆盖

- `{书名}/正文/`
- `{书名}/设定/`、`大纲/`、`追踪/`
- `.active-book`

## v27 当前契约

- agent-references 内容更新：anti-ai-writing 扩至 20+ 模式（笔枢 10 条硬约束：名词性独语句/可追问测试/最低信息量/禁命名情绪/拆物化结尾/禁群像反应/禁"了一下"/禁破折号滥用/禁元叙事/标记词每千字限额）、naming-cards 5 张、hooks-chapter 钩子 11 类、scene-cards 6 张、craft-cards 6 张、beat-cards 增补、群像反应确定性检测（check-ai-patterns.js 三副本同步）。
- v26 的部署行为契约全部保留：正文 Bash 前置守卫、书目录 4 层发现、narrative-writer 工具白名单与细纲消费两分法、复沓锚句字段。

## v26 当前契约

- Claude Code 的正文前置守卫现在也注册到 Bash：常见的重定向、`tee`、`touch`、`cp`、`mv`、`install` 写入正文时复用共享 JS 核识别目标并执行大纲/追踪门；只读命令里的引号示例与 heredoc 正文提及不拦，并按 hook `cwd` 解析相对路径。该面是**静态 best-effort 识别，不是 shell 沙箱**：环境变量间接路径、运行时生成命令与未列出的任意写文件程序无法可靠静态判定；这类写入应改用 Write/Edit。Bash 命令面依赖 node，node/共享核异常时显式告警后 fail-open；Write/Edit/MultiEdit 的纯 bash 兜底不受影响。
- 共享 JS 的书目录发现统一限制为项目下 4 层，并剪枝隐藏目录、`node_modules`，避免 SessionStart/Stop 无界扫描。
- moshu-narrative-writer 与部署 reference 增加“普通名词不用引号强调”的 Gate B；合法对话、直接引用、书名/代号和场内系统载体原文保留。
- moshu-narrative-writer 的工具白名单加入 `Bash`：字数统计、句长分布、`check-ai-patterns.js` 与 `check-outline-copy.js` 复扫都要确定性数值，缺工具时这几条规则整条空转。字数与句长必须报实测值，探测不到 Python / node 时如实声明“未完成机器验证”，不得声称已统计或已运行脚本。
- moshu-narrative-writer 的细纲消费规则拆成两条并列：内容层（每项独立落地、不许漏、不许两项并一句）与形状层（落地位置、顺序、断段自定，可打散重排，不要一项一段平推）。形状半边同步进 `moshu-write` 的 spawn 清单。
- 细纲「情节细化」新增**复沓锚句**字段：必须一字不差进正文的原话逐行列出并注明落点，没有写“无”。存量细纲缺该字段时按“无锚句”处理，行为与此前一致，不必回头补。

重新部署后需**新开会话**，custom agent 与 hooks 才会重新注册。

## v24 当前契约

- `.claude/rules/story-narrative.md` 删掉「禁止 AI 腔」红线块。该块只在 `拆文库/` `对标/` `设定/` 三个 path 下加载，正文目录根本不命中，五条规则也已由 moshu-narrative-writer 的 7 Gate / 禁止事项与 `check-ai-patterns.js` 的 blocking 规则覆盖。
- `.claude/rules/story-format.md` 的对话标签规则从「禁止「他说」「她道」」改为「避免对话标签机械化」：高频或公式化标签用动作/上下文替代，普通「说」低频使用可保留。此前该文件是全仓唯一把普通「说」判为违规的地方，与 `format-and-structure.md` 等 11 处口径冲突，且它正好在 `正文/` path 上加载。
- `.claude/agents/moshu-narrative-writer.md` 精简约 19%：删除与 7 Gate / 禁止事项重复的审查清单（moshu-review spawn 时会内联完整 rubric）、正文写作阶段的具体字数表达校验（移到审查侧）、以及 `……`/`——`、段间空行、章节元信息正则的重复陈述。写作规则本身未放宽，Gate A-G 与禁止事项口径不变。
- `.claude/hooks/guard-outline-before-prose.sh` 补上追踪检查点门：追踪状态缺失、schema 不是 4、续写状态卡修订号与 state 不一致、首建新章时上一章事务未提交，都拦下写正文。细纲/大纲门只在首建时判，追踪门对首建与续写都判。判定经 `.claude/hooks/story_hook_cli.js` 的 `tracking-checkpoint` 子命令调共享核；需要解析 JSON，故 node 不在场时这道门放行（大纲/细纲门仍是纯 bash，无 node 也拦得住）。
  - **对已部署项目的影响**：v0.7.3 起就该迁移的旧追踪项目，此前在 Claude Code 上还能继续写，现在会被拦下。按提示走 `/moshu-import` 的「旧追踪项目迁移」重建 `追踪/` 即可，不必重跑全书拆解。

重新部署后需**新开会话**，custom agent 才会重新注册。

## v23 当前契约

- `moshu-import` 只把作者已有小说重建为写作工程：`拆文库/{导入书名}/` 迁移到正文/设定/大纲/追踪，不再自动登记成主/副对标，也不再复制到项目 `对标/`。只有用户明确选择、且来源为独立 `拆文库/{对标书名}/` 的外部作品才同步到 `对标/{对标书名}/`。
- 无外部对标时只跳过对标模块与节奏召回（情绪/节奏目标改从本书细纲/卷纲/题材定位等内部材料取）；**文风召回独立于对标**——`文风库/文风.md` 由 moshu-style 产出，无对标也照常按写前准备 (d) 检查执行。项目题材卡仍从本书题材信息生成，不再被对标分支误伤。对标主产物缺失继续 fail-fast，只有单个可选模块卡未命中时才局部跳过。
- 所有可能 spawn 项目 agent 的 Skill 都先读取 `.story-deployed.agents_version`：与 v23 不一致时**照常 spawn**，只在报告里提示版本不匹配、建议重跑 `/moshu-setup` 并新开会话。版本不匹配不阻断并行——bump 常常源于别的部署物变化而 agent 模板未动。真正降级 solo/direct 的信号是 agent 文件缺失或运行时不暴露 custom agent。
- 写作与导入只接受当前拆文产物：`剧情/情绪模块.md` 与 `剧情/节奏.md` 缺失时 fail-fast，并给出重跑 Stage 3+ / 重新导入的修复动作。
- 新建、补建、改纲的细纲只接受完整章节蓝图：缺少阶段位置、结构公式、禁止提前释放、内容概括、情节安排、人物关系、情节细化或结尾设定时，先补齐再写。旧版细纲缺这些字段不阻塞日更，回退消费旧字段（核心事件、情节点序列、目标情绪、章首/章尾钩子、字数目标）。
- 细纲字段是本章「要发生什么」的内容规格，不规定正文形状：各字段都要在正文里兑现，但正文可合并、穿插、重排情节点，不按条目顺序一条一段平推。细纲「结尾 / 结尾设定」写本章最后落在什么动作、画面或台词上，不写状态判词。
- 每个 agent 只读取本目标的 canonical reference 路径：Claude `.claude/skills/`。
- `_progress.md` 恢复只接受 `schema_version: 2` 与章节边界表，不再执行隐式历史迁移。
- 定制 hook 如果调用了已删除的 `discover_book_dir()`，请改为 `discover_active_book()`。当前版不再保留该兼容别名。
- `拆文库/` 的「未完成拆文」提醒按 `_progress.md` 的「最终状态」取值过滤：`completed` / `completed_with_errors` 不计入，其余取值与字段缺失、空文件、不可读一律按未完成上报。判定收在 `lib/common.sh` 的 `discover_incomplete_analyses()`。
- 被动版本更新提醒按 24h 节流提示本身；取不到 GitHub 时写入负缓存，同一窗口内不重复请求。

## 升级步骤

1. 在项目根目录重新运行 moshu-setup。
2. 确认 `.story-deployed` 写入 `agents_version: 30` 与 `setup_skill_version: 1.3.0`。
3. 确认目标 CLI 的 agents、hooks/rules 和 reference bundle 都通过安装验证。
4. 新开会话，使 custom agents 与 hooks 按当前文件重新注册。
5. **长篇在写项目必做**：检查每本书的 `追踪/_tracking-state.json` 是否存在。不存在就是旧追踪结构，按下方「追踪模型迁移」重建，否则写下一章会被拦。
6. 若已有拆文库或细纲不满足当前契约，先重新拆解/导入或补齐细纲，再继续写作。

## 导入项目的自对标清理（v23）

旧版 `moshu-import` 可能把作者自己的导入书误建成 `对标/{当前书名}/`，甚至把本书设定登记成“主对标”。升级不会自动删除用户文件，按以下边界人工核对：

1. 保留 `拆文库/{导入书名}/`；它是本书导入分析和重建工程的数据源，不是错误目录。
2. 以项目根 `设定/` 为本书正式设定。若 `对标/{当前书名}/` 的内容确认只是从本书 `设定/` 或 `拆文库/{导入书名}/` 复制而来，且没有人工补充，再删除这个误建目录。
3. 清理 `设定/题材定位.md` 中把当前书登记为主对标的字段；真实外部对标登记不动。
4. 若某个 `对标/{外部书名}/` 目录名看似外部作品，但内容实际来自当前书，删除这份错误视图，再从真正的 `拆文库/{对标书名}/` 重新同步；不要改名冒充修复。
5. 重新运行 `/moshu-setup` 并新开会话，使 v23 的 agent 模板生效；在此之前 spawn 照常工作，只会多一条版本不匹配提示。

## 追踪模型迁移（v0.7.2 及更早的长篇项目必读）

长篇追踪从「模型自由写多个 Markdown」改成 **`追踪/_tracking-state.json` 单一结构化权威 + `scripts/tracking_commit.py` 事务写入**。所有 Markdown（续写状态卡、逐章记录、角色快照、伏笔表、时间线双视图）都是由工具整份生成的派生视图，不再手写。

判断与后果：

| 情况 | 表现 |
|------|------|
| `追踪/_tracking-state.json` 存在且 `check` 通过 | 正常，无需处理 |
| 缺 `_tracking-state.json` 但已有正文 | 日更停止；Claude Code 上写正文被 hook 直接拦截 |
| 存在但派生视图被手改 | `check` 报 `derived view differs from _tracking-state.json` |

迁移**不需要重跑全书拆解**：正文、`设定/`、`大纲/`、`拆文库/` 都不受影响，只重建 `追踪/`。执行 `/moshu-import` 的「旧追踪项目迁移」——数出最后完整章号 `N`，从旧追踪文件与最近几章正文重建当前状态，构造 `last_chapter=N` 的初始化事务跑 `tracking_commit.py init`。旧追踪结构会被按受管清单移入 `追踪/_旧追踪存档/`，不删除、不参与解析。

退役结构：`_tracking-meta.json`、`时间线/事件库.json` 及更早追踪文件不再被解析，`commit` 与 `check` 遇到会直接拒绝。

日常写作的两条硬约束：所有追踪写入都走 `tracking_commit.py`；派生视图被改动后用该章的 `mode=revision` 事务整份重建，不手改。

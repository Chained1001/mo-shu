# 升级指南

## 当前版本

- `setup_skill_version: 1.5.1`
- `agents_version: 49`

> **别名注记（版本地图乱点②处置）**：sentinel 字段 `setup_skill_version` 与 moshu-setup SKILL.md frontmatter `version` 是**同一版本号的两个名字**（别名关系，值恒等）——`bump-agents-version.py --setup-version` 唯一合法修改；deploy.py verify 校验 sentinel 写入值 == 常量、TS10 校验 frontmatter == current-contract，双向一致。

`.story-deployed` 缺失任一字段，或 `agents_version` 缺失 / 非整数 / 小于 `49`，都视为待更新部署。直接重新运行 `/moshu-setup`；不在运行时逐级兼容历史模板。如项目 `agents_version` 大于 `49`，说明本地 moshu-setup 比项目旧：先更新 mo-shu，不得用 v49 降级覆盖。历史版本改动见仓库根目录 `CHANGELOG.md`。

**v48 → v49 变更**：B107 大纲流程施工批——evaluator 模板**新增 panel 型**（三评委面板：读者/编辑/作家三视角+关注面+判据内置[reader-contract/outline-structure-theory/plot-frameworks/genre-core-mechanics/reversal-toolkit]+结构化输出；moshu-outline 打磨阶段 spawn 用）；researcher 模板**新增采风专用模式节**（type=caifeng/survey 四域检查单+九段/八节产物 schema+源优先级内嵌——spawn 只传对象+模式）。agent 模板变更，重跑 `/moshu-setup` 并新开会话后生效。

**v47 → v48 变更**：B103 大纲阶段重构——evaluator 模板新增「故事核心设计/草稿验收」对象行+「大纲打磨（5.2 质量审）」质量面行+benchmark_path 改 `设定/基本设定.md`（旧书回退题材定位.md）；researcher 模板改分层引用（内嵌六节骨架→指向 caifeng-outline.md schema）+产物路径三路（设定/参考/{书}.md+设定/采风/CF-*.md+设定/资料/{专题}.md）。agent 模板变更，重跑 `/moshu-setup` 并新开会话后生效。

**v46 → v47 变更**：B95 写作模式重构——4 个 agent 模板引用改指（包内路由边界注记 workflow-chapter→workflow-daily）+narrative-writer `skills:[moshu-deslop]`→`skills:[]`（deslop 技能已删除收编）；agents_version 46→47+指纹重登记。agent 模板变更，重跑 `/moshu-setup` 并新开会话后生效。

**v45 → v46 变更**：B94 标尺合并——evaluator 模板三档参照改两档（删 virtual_benchmark_path，benchmark_path=设定/题材定位.md 成品标尺节；理想书评/虚拟对标收口）；agents_version 45→46+指纹重登记。agent 模板变更，重跑 `/moshu-setup` 并新开会话后生效。

**v44 → v45 变更**：agent-references 死库存清理（B87 全仓瘦身）——7 个零模板引用副本删除（craft-cards/literary-techniques/scene-cards/style-combat-face/naming-cards/plot-core-methods/genre-writing-formulas），shared-assets 组同步（4 组删条目+3 组删 target）；agents_version 44→45。部署物变更（删除文件），重跑 `/moshu-setup` 并新开会话后生效。

**v43 → v44 变更**：moshu-researcher 模板扩展融合模式（B81 采风融合智能体）——新增「融合模式（caifeng-fusion）」节（type: caifeng-fusion 触发；输入 caifeng_product/story_files/design_need；融合四步=结构对照→功能位借用→本土转译→方法论验证；输出 JSON 含 fusion_strategy/borrowed_positions/translated_elements/verification/token_echo；纪律=只出策略不改文件+防抄红线+功能位清单必含可审计）。agent 模板变更，重跑 `/moshu-setup` 并新开会话后生效。

**v42 → v43 变更**：moshu-evaluator 模板按人类角色合并重写（B77 写审配对补全）——eval_type 枚举 7→2（structure 责编/reader 读者评委：structure 吸收 outline/unit/final/detail-batch/settings/revision+新增人物设计/场景表/卷末体检对象，reader 吸收 full+新增融合产物/防撞对照/完结清账对象）；两型按评审对象索引的清单模块表（判据逐条标注方法论来源，零发明）；score 规则迁移 full→reader（structure 型不填）；新增 optional 参数 related_paths（跨产物审查材料清单，structure 型跨稿核对义务）；shadow mode 声明（两型报告只呈报永不拦截）。agent 模板变更，重跑 `/moshu-setup` 并新开会话后生效。

**v41 → v42 变更**：B76 遗留称谓变更补 bump（B76.5 整改 R2）——moshu-architect/moshu-evaluator 两模板的调用方称谓随 build 拆分改「moshu-volume」（B76d 修改模板漏 bump，本条目补登记）；agents_version 41→42+指纹重登记（83f6eeff4aba）。agent 模板变更，重跑 `/moshu-setup` 并新开会话后生效。

**v40 → v41 变更**：moshu-narrative-writer 模板两级装配模板侧（B75，LLM 专家视角「只改一处」立项）——新增「流程规则承接」节（三遍法结构/细纲优先边界/禁止提前释放+🔒 剧透锁/格式硬约束/场景路由映射/一进一出判据/语声对照七条稳定判据摘要，完整规则见已部署 chapter-core，摘要引用非全文复制）——spawn prompt 后续只传本章增量、规则由模板承接（spawn 侧瘦身随 B75b 启用）。agent 模板变更，重跑 `/moshu-setup` 并新开会话后生效。

**v39 → v40 变更**：moshu-evaluator 评审对象扩展三型（B69 写-审配对补全）——eval_type 加 detail-batch（细纲批评审：写正文前最后一道语义闸，钩子链连贯/预算分布/场景表与卷纲单元对照/一进一出呼吸）、settings（设定包评审：一致性+题材卡置信度复核+防撞三维独立复核[B65 流程不变，只复核不接管]+信息量超载）、revision（修订包评审：影响面复核/最小改动/契约影响——只供参考，不构成裁决依据）；三型不填 score（评分仅 full 型）；被调用协议加三型 target/context 参数说明。agent 模板变更，重跑 `/moshu-setup` 并新开会话后生效。

**v38 → v39 变更**：moshu-narrative-writer spawn 材料清单加两项引用（出场角色语声锚文件路径 `追踪/角色状态/{名}.md` 近作台词节 + 点名清单出场称谓行）；tracking_commit 追踪域增强（voice_samples 滚动 5 条/address_book 称谓域，schema 6→7 migrate 带备份）——agent 模板与脚本变更，重跑 `/moshu-setup` 并新开会话后生效。

**v37 → v38 变更**：moshu-evaluator 评审准则三维度改三档优先级对照（benchmark_book_paths 对标拆文 > virtual_benchmark_path 虚拟对标 > benchmark_path 理想书评——有对标路线 Phase B 补齐，精确参照接入打磨环）；协议加 benchmark_book_paths 参数（仅有主对标时传入，传入时省略 virtual_benchmark_path）。重跑 `/moshu-setup` 并新开会话后生效。

**v36 → v37 变更**：moshu-evaluator 模板全面增强——eval_type 加 full（Phase B 全局评审）、评审准则三维度加对照虚拟对标/理想书评指令、JSON 输出加 score/research_needed/summary/recommendation 四字段、similar_examples 幻觉防护（不确定标"存疑"禁编造）、maxTurns 10→15、协议加 virtual_benchmark_path 参数。重跑 `/moshu-setup` 并新开会话后生效。

**v35 → v36 变更**：architect 模板称谓修正（「被 moshu-write（Stage 1-3）调用」→「被 moshu-build（cold-path 卷级辅助）与 moshu-write（细纲批）调用」）与「契约摘要承接」段新增（六项摘要说明+使用方式）；evaluator 模板 eval_type 清单收紧（character 移除——Stage 3 为自动步无评审，合法值收为 outline/unit/final）——agent 模板变更，重跑 `/moshu-setup` 并新开会话后生效。

**v34 → v35 变更**：agent-references 方法论内容修订（outline 系去编号化/outline-rhythm/genre-writing-formulas 等）与 CLAUDE.md 模板路由表触发词对齐（/准备写书→「部署墨枢写作环境」、/导入→「导入小说」）——agent 参考文件与 CLAUDE.md 模板变化，重跑 `/moshu-setup` 并新开会话后生效。

**v33 → v34 变更**：新增 moshu-evaluator 评审 agent 模板（三维度评审[编辑·商业/作者·新鲜度/读者·留存]·只读[禁 Write/Edit/Bash]·审稿令牌回传·JSON 输出；被 moshu-build 停靠屏调用，形成创作→评审→采风→融合→再评闭环）——agent 模板新增，重跑 `/moshu-setup` 并新开会话后生效。

**v32 → v33 变更**：outline-methods agent-references 副本更新（B22「舞台与规则设计」节经 shared-assets 同步进 agent-references）——agent 参考文件变化，重跑 `/moshu-setup` 并新开会话后生效。

**v31 → v32 变更**：moshu-researcher 模板新增采风研究段（五类型[结构/角色/设定机制/情节/情绪]+源七类+采风专属纪律[小说正文不取/来源 URL 防编造/专名清单占比/转译三问初答]；maxTurns 20→30 采风多源交叉场景上调）——agent 模板变化，重跑 `/moshu-setup` 并新开会话后生效。

**v30 → v31 变更**：agent-references 内容更新（B17 三书逆向萃取三节——势力场设计/升级绑弧光/叙事装置，经 shared-assets 同步进 agent-references；题材公式降级头注定位）——agent 参考文件变化，重跑 `/moshu-setup` 并新开会话后生效。

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

> **清空重建警示**：重部署为清空重建（replace 语义）——上述目录先清空再写入当前模板，旧版本残留文件（如已移除的 hook/agent/规则）会被清除，不会留在项目里。请勿把自定义内容放进这些目录（自定义 hooks/rules 请用自有目录或 settings 用户注册）。

### 用户与 moshu-setup 共同维护，只合并管理块

这些文件可能含用户自定义内容：
- `CLAUDE.md` — 按 marker/section 合并，用户独有 section 保留
- `.claude/settings.local.json` — 按 command 识别 moshu hooks；已存在的受管 command 会迁移到当前模板的 event/matcher/timeout/if（例如 v26 的 Bash 正文 pre-guard），其他用户 hook 与配置保留

### 用户状态，不覆盖

- `正文/`
- `设定/`、`大纲/`、`追踪/`
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
2. 确认 `.story-deployed` 写入 `agents_version: 49` 与 `setup_skill_version: 1.5.1`。
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

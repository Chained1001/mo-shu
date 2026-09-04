# 01·awesome-novel-studio 研究（开源强化）

## 0 元信息

- 仓库 URL：https://github.com/MJbae/awesome-novel-studio
- 本地路径：`C:/Users/1/Desktop/skillDev/mo-shu/.tmp/tests/开源强化研究/awesome-novel-studio`（只读快照）
- SHA：`bb720652a3ef0aadebe731309a4bc8d21a686aa4`（本地 git log 实测，单 commit 快照；作者 MJbae，韩国）
- 星数：144★（2026-08-27 抓取）；license：Apache-2.0（`LICENSE`）
- 活跃度：最近 push 2026-04-14（版本 1.1.0，`README.md:2`、`.claude-plugin/plugin.json:3`）；本地快照仅 1 个 commit 无法看提交频率（代码事实），此后约 4 个月无 push（据抓取元数据）
- 一句话定位：Claude Code 插件形态的**韩语网文端到端自动生产流水线**——18 个专业 agent + 10 个 skill，覆盖 propose → design(big/small) → create → polish → rewrite，主打"300 话/150 万字长篇不崩"的三堵墙工程化（`README.md:75-84`）
- 与 mo-shu 关系：同形态竞品（同为 Claude Code 上的网文生产系统），但哲学相反——它是"全自动化流水线"，mo-shu 是"作者主权 + 三层分工"。全仓 **0 个脚本**（实测：`find *.py/*.js/*.sh/*.mjs` 无结果），纯 prompt 工程：所谓确定性检查全部由 agent 用内置 Grep/Read 工具执行，只有编排器自己跑 `wc -m` 数字数（`skills/create/SKILL.md:251`）
- 规模实测：18 个 agent 文件（`ls agents/ | wc -l` = 18）、10 个 skill 目录、agent 正文共约 2,400 行、skill+references 共约 4,800 行；主语言标 HTML 是因为 `index.html`（770 行 GitHub Pages 营销落地页，`index.html:1-30`）

## 1 机制清单

### M0 全景：管线与文件产物

- 证据：`README.md:63-71`（管线图，文档宣称）；`skills/create/SKILL.md:13-22`（create 四 agent 流水线图，代码事实）；`README.md:129-148`（目录结构，文档宣称）
- 机制：`/propose`（domain-researcher R1/R2/R5 联网调研 → proposal-generator 出 3 案 → 用户选 1）→ `/design-big`（概念/角色/情节三 agent 出 bootstrap/角色表/plot-hook 指南三件套，自动生成 `novel-config.md`）→ `/design-small`（25 话单位细设计：细角色表+细情节指南）→ `/create`（每话 4 agent：设计图+连续性并行 → 写作 → 裁剪 → 验证，PASS 才进下一话）→ `/polish`（每话 4 诊断 agent 并行 + 执行 + 复核）→ `/rewrite`（设定改动后自动算影响面重写）。产物区：`design/`、`episode/ep{NNN}.md`、`revision/`（fix_plan/learnings/alive-tracker）、`_workspace/`（agent 间交接报告）
- mo-shu 映射：对应我们 build（A 快速生成 + B 打磨环）+ write（日更）+ review 的合体；`novel-config.md` ≈ 我们的 skill 配置 + `追踪/` 的混合体；`_workspace/` 编号报告 ≈ 我们的 agent 交接产物
- 结论：**理念可学**（阶段化 + 每阶段产物落盘），实现不抄（其为韩语场景 + 全 prompt 化）

### M1 18 agent 清单与分工（重点问题 1）

- 证据：`agents/` 目录 18 个文件（实测）；README:205-219 的四组分类（文档宣称，与文件实测一致）
- 代码事实清单（每个 agent 的职责取自各文件 frontmatter/正文）：

| # | Agent | 组 | 职责 | 文件 |
|---|---|---|---|---|
| 1 | proposal-generator | 设计 | 调研输入出 3 个差异化轻量企划案（基调/主角站位/叙事结构三轴变奏），落 `_workspace/01_proposals.md` | `agents/proposal-generator.md`（122 行） |
| 2 | concept-builder | 设计 | bootstrap 设计：世界观、叙事起点、核心能力模块（范围/极限/消耗条件）、平台策略 | `agents/concept-builder.md`（48 行） |
| 3 | character-architect | 设计 | 角色表：主角/助力者/反派层级/关系网/成长弧 + 声音速查卡 | `agents/character-architect.md`（50 行） |
| 4 | plot-hook-engineer | 设计 | 情节钩子指南：全书弧、50 话单位 arc、爽感节奏、付费转化策略 | `agents/plot-hook-engineer.md`（53 行） |
| 5 | domain-researcher | 设计 | 8 类联网调研 R1-R8（WebSearch/WebFetch），带 HIGH/MEDIUM/LOW 可信度评分 | `agents/domain-researcher.md`（212 行） |
| 6 | episode-architect | 创作 | 从设定文档提取单话设计图：情节 beat/子 beat、确定数值、时间线锁、情绪曲线、钩子策略 | `agents/episode-architect.md`（137 行） |
| 7 | continuity-bridge | 创作 | 读前 2 话提取：时间/地点、时间线检查点、数值检查点、关系状态、未解伏笔、上话悬念原文 500 字、非语言动作重复记忆 | `agents/continuity-bridge.md`（89 行） |
| 8 | episode-creator | 创作 | 写正文：声音卡/对话 DNA/惊讶校准/爽点密度/字数自检（Grep 数"있었다"等 3 词） | `agents/episode-creator.md`（197 行） |
| 9 | quality-verifier | 创作+重写共用 | 双模式验收（CREATE 8 轴 / REWRITE 6 QA+立体度），PASS/REWRITE 二值判定，最多 2 次重试 | `agents/quality-verifier.md`（447 行，全仓最大 agent） |
| 10 | rule-checker | 打磨 | 5 轴诊断：BANNED/VOICE/TITLE/SILENCE/TRANS（grep 先行+精读去误报） | `agents/rule-checker.md`（120 行） |
| 11 | story-analyst | 打磨 | 3 轴诊断：SCENE/LOGIC(TIMELINE+NUMBER+PLAUSIBILITY)/UNIFORM，强制 3 步数值时间线交叉验证协议 | `agents/story-analyst.md`（188 行） |
| 12 | platform-optimizer | 打磨 | 4 轴：HOOK(末 500 字)/OPENING(首 1000 字)/MOBILE/SUMMARY + 韩国平台特化清单 | `agents/platform-optimizer.md`（130 行） |
| 13 | alive-enhancer | 打磨 | ALIVE-1~4：回声对话、沉默→非语言、配角张力点、关系曲线；维护 alive-tracker | `agents/alive-enhancer.md`（149 行） |
| 14 | revision-executor | 打磨 | 汇总 4 份诊断报告按 15 级优先级直接 Edit 正文；数值时间线类必须回头 grep 前 2 话定正本 | `agents/revision-executor.md`（147 行） |
| 15 | revision-reviewer | 打磨 | 7 项复核：过改/新错/TIMELINE 残留/自定义轴/保全护栏/钩子/字数±15%，PASS/REVISE | `agents/revision-reviewer.md`（154 行） |
| 16 | revision-analyst | 重写 | 设定文档↔正文落差分析（PLOT/NUMBER/TIMELINE/FUND/SETTING/CUSTOM），出重写设计书 | `agents/revision-analyst.md`（118 行） |
| 17 | character-sculptor | 重写 | 角色立体度 7 维诊断（VOICE/NONVERBAL/INNER/RELATION/ASTONISHMENT/CATHARSIS/DIALOGUE），0-10 打分 | `agents/character-sculptor.md`（167 行） |
| 18 | episode-rewriter | 重写 | 按两份分析报告整话重写（先写结尾 500 字再写开头 1000 字） | `agents/episode-rewriter.md`（152 行） |

- mo-shu 映射：episode-architect+continuity-bridge ≈ 我们 write A 段 13 项准备；quality-verifier ≈ C 段机检链的 LLM 版；rule-checker+story-analyst ≈ review 四 reviewer；本仓无 scan/deslop/style/import 对应物
- 结论：**理念可学**（诊断/执行/复核三权分立的 agent 编队设计；每个 agent 文件自带输入输出协议+错误处理小节，是很好的 agent 模板纪律）

### M2 16-axis 检查轴体系（重点问题 1）

- 证据：`skills/polish/references/12-axes.md:1-346`（12 轴权威定义）；`agents/alive-enhancer.md:20-56`（ALIVE 4 轴）；`README.md:184-203`（16 轴表=12+A1-A4，文档宣称与代码一致）
- 机制：12 轴分两组——Part A 违规必改 5 轴（BANNED 禁语/VOICE 声音表对照/TITLE 称谓三重核/SILENCE 沉默≤4 次每话/TRANS 翻译腔三子类：形态翻译腔+AITONE 韩语 AI 腔+SEMANTIC 语义直译腔）+ Part B 改进 7 轴（SCENE 场景锚点/LOGIC 数值时间线合理性/SUMMARY 报告腔/UNIFORM 开场模式单一化/HOOK 钩子强度 1-5/OPENING/手机可读性定量阈值）+ ALIVE 4 轴（A1 回声对话/A2 沉默转非语言/A3 配角张力点/A4 关系距离曲线）。每轴定义：检测方法（grep 关键词表）、等级（CRITICAL/MAJOR/MINOR）、修改方向。**16 轴之外还有 custom_axes**：`novel-config.md` 可注册项目自定义轴（如 PASTLIFE 前世设定一致性），带正本/检测关键词/VIOLATION-ALLOWED 边界三要素（`skills/polish/references/project-config-template.md:174-226`）
- mo-shu 映射：我们机检是确定性脚本（阻断/候选两列），他们是 LLM 分轴诊断。我们的 deslop 去 AI 味 ≈ TRANS 轴；TITLE 称谓 ≈ 我们没有的维度；MOBILE 定量阈值（段落≤3-5 句、句≤40 字、对话占比≥40%）≈ 我们的网文规范类
- 结论：**理念可学+部分可移植**——(1) "轴"作为机检组织的单位：每轴=检测器+等级+修法，比我们散的 check-*.js 更体系化；(2) AITONE/SEMANTIC 的韩语 AI 腔关键词表对 deslop 的中文 AI 腔词典是直接方法论参照（转述机制不抄词表）；(3) custom_axes 的"正本+检测关键词+判定边界"三要素定义法可以用于我们的候选类检查注册

### M3 数值/时间线 3 步交叉验证协议（重点问题 3）

- 证据：`skills/polish/references/12-axes.md:181-254`；`agents/story-analyst.md:47-96`；`agents/quality-verifier.md:78-88`
- 机制：**Step1 提取**（本话+前 2 话所有时间标记：显式日期/相对时间/季节/流逝时长，相对时间按场景显式日期换算绝对日期）；**Step2 交叉对照**（同一事件/同一对象的数值与时间在话间矛盾→[TIMELINE]/[NUMBER] CRITICAL）；**Step3 强制输出提取表**（"没有问题也要输出空表，禁止用'没问题'跳过验证"——`agents/story-analyst.md:179`）。**数值正本优先级**四级：①细情节指南 EP 确定值 ②bootstrap 宏观数值 ③验证记录 ④前话，统一成文 `skills/polish/references/numeric-source-priority.md:1-55`（角色年龄恒=当前年份-出生年，出生年从角色核心文档算）
- mo-shu 映射：我们的追踪事务+`伏笔.md`/`角色状态` 是"登记派"，他们是"每话重提取派"（不维护长期 state，靠前 2 话滑动窗口+设定文档正本）。两者互补：他们解决了"state 文件本身会过期/漏记"的问题，代价是每话重复全文扫描
- 结论：**理念可学**——"强制输出空表"反偷懒纪律、"数值正本优先级成文"与我们追踪派生视图的权威链是同构问题；他们没有我们的单权威 state，长程（>2 话前）矛盾只能靠设定文档兜底，说明纯滑窗不够——反证我们追踪事务方向的必要性

### M4 alive-tracker 滚动窗口（重点问题 3，直击 mo-shu 已知缺口）

- 证据：`agents/alive-enhancer.md:59-90`
- 机制：关系事件追踪文件 `alive-tracker.md` 只保留**最近 20 话为活跃区**，更早的移入"归档"节且每角色压成 1 行终态摘要；50 话（细设计边界）时整理归档；读取者（continuity-bridge/alive-enhancer/episode-rewriter）**只读活跃区**，查特定角色历史时才翻归档（`agents/continuity-bridge.md:88`）
- mo-shu 映射：直击我们已知缺口"追踪派生视图全量读入、无按需注入"。我们的 `上下文.md`/`伏笔.md` 是每章全量派生；他们是"活跃窗口+归档摘要"两层
- 结论：**可移植（改造）**——不必照搬文件形态，但"派生视图分活跃/归档两区、注入时只取活跃区+按需查归档"的原则可以进我们的追踪事务派生策略（如 `伏笔.md` 按悬置章距分活跃/沉寂区，`上下文.md` 按最近 N 章滚动）

### M5 `.design-hashes` 设定变更指纹 → 重写影响面自动计算（重点问题 2/4）

- 证据：`skills/create/SKILL.md:384-392`（create 收尾写 SHA256 基线）；`skills/rewrite/SKILL.md:94-145`（变更分级 CRITICAL/MAJOR/MINOR→影响 EP 范围自动产出→用户确认）
- 机制：create 完成时把 `design/` 下所有设定文档的 SHA256+时间戳写入 `.design-hashes`；`/rewrite` 启动时 git diff（书仓是 git 时）或 hash 对比检测哪些设定文档变了，按变更类型分级映射影响范围（角色核心设定变更→该角色登场 EP 起全量；数值/时间线变更→首次提及 EP 起全量；字词润色→不需重写），给出建议重写区间请用户确认，然后逐话跑 重写流水线，完成后**自动重置 fix_plan.md 中被重写话的打磨状态**（`skills/rewrite/SKILL.md:66-82`）
- mo-shu 映射：我们 review 有工单，但"设定文档改动→哪些章需要重查"的影响面计算缺失；我们也没有"重写后自动失效下游打磨状态"的传播机制
- 结论：**可移植（脚本化）**——完全符合我们三层分工：hash 指纹+变更分级→影响 EP 区间是确定性逻辑，应做成脚本（对比我们的 `_tracking-state.json` 与设定文档指纹），不照搬其"每次让 LLM 分级"的做法；"下游状态失效传播"理念同效于我们兼容四原则

### M6 断点恢复与状态管理（重点问题 2）

- 证据：`skills/polish/SKILL.md:55-80`（自循环+断点续跑）；`skills/create/SKILL.md:147-153`（create-plan.md）；`skills/rewrite/SKILL.md:419-444`（rewrite-plan.md）
- 机制：每个长流程有一份 checkbox 计划文件（create-plan.md / fix_plan.md / rewrite-plan.md），逐话勾选；`/polish` 无参数重启时从"最上方未完成项"续跑（`skills/polish/SKILL.md:80`"중단 시 재개"）。每话完成还更新 learnings.md（新模式发现时才写）——**经验回灌**：诊断 agent 后续话会参考已发现的坏模式。另有 verdict 缓存失效纪律：REWRITE 重跑前**必须删除旧 verdict 文件**，防止 quality-verifier 复读旧结论（`skills/create/SKILL.md:371-373`）
- mo-shu 映射：我们的 next_step.py S0-S6 判定同角色；learnings.md ≈ 我们没有的"机检/审查发现模式沉淀"文件（类似把 review 工单的共性沉淀回创作约束）
- 结论：**可学两条**——(1) verdict/派生报告的"重算前先删旧文件"防缓存污染纪律（我们机检是脚本重跑天然无此问题，但 review 工单类 LLM 产物有）；(2) learnings.md 作为"审查发现→创作预防"的回流通道，可挂在我们 review 技能工单之后（注意勿演化为任务板，见 §3）

### M7 create 内部质量闭环：过量写作→裁剪门→验证→双保险（重点问题 2/5）

- 证据：`skills/create/SKILL.md:243-288`（Step 2.5 裁剪门）、`skills/create/SKILL.md:326-364`（PASS 后编排器亲自 Grep/wc 复核 + 轻违规编排器直接改/重违规打回）、`skills/create/SKILL.md:371-375`（REWRITE 最多 2 次，第 3 次起标 [△] 部分通过放行）
- 机制：写作 agent 按 6000-10000 字写，编排器 `wc -m` 实测后裁剪到 5000-8000（"写多再删比凑字质量高"，`skills/create/SKILL.md:118-121`）；quality-verifier 判 PASS 后**编排器不信任，亲自 Grep 数"있었다/고 있었다/것이었다"三词 + wc -m 复核**，不一致则改判 REWRITE；MINOR 超限≤3 处且纯文本替换时编排器自己 Edit（时态保守替换表），否则走 REWRITE。重试 2 次仍不过→[△] 部分通过，进下一话并在计划文件留痕
- mo-shu 映射：这是我们"脚本做确定性"角色的 LLM 替身——他们用"验证 agent + 编排器双保险"逼近确定性，我们直接用 tracking_commit.py/check-*.js。**[△] 部分通过 ≈ 我们"候选永不拦截"的降级出口**，但他们缺"候选只呈报作者"一层——放行是系统决定而非作者决定
- 结论：**理念可学**——(1) "写超再裁"的初稿量策略可试于我们 write B 段；(2) 双保险交叉复核（生成侧自检+独立侧复检）模式可用于我们 write 技能未完整走查的自检设计；判定门与重试上限的显式数值（2 次）是他们自定参数，若移植需按我们反模式 #5 命名常量+可覆盖

### M8 agent 失败处理与耦合方式（重点问题 5）

- 证据：`skills/create/SKILL.md:406-415`（错误处理表：agent 失败→重试 1 次→仍败标 [!] 跳下一话）；`skills/propose/SKILL.md:172-181`、`skills/design-big/SKILL.md:359-370`（每个 skill 尾部错误处理表：重试 1 次→**leader（编排器主线程）亲自代写**该产物并声明"自动生成-建议人工复核"）；`skills/create/SKILL.md:159-167`（Phase1 等待纪律：禁 TaskOutput、禁 sleep 轮询、靠系统完成通知）
- 机制：每个 agent 都是无状态 general-purpose subagent，spawn 时 prompt 里塞：①agent 定义文件路径（agent 自读）②白名单文件路径（**路径硬约束**："只许读列出的文件，禁止 Glob 探索 design/"，`agents/episode-architect.md:32-38`、`skills/create/SKILL.md:189-200`）③输出路径。失败统一"1 次重试→主线程接管"，与我们"fallback 主线程"纪律同构但无 agents_version/契约摘要/部署物成本概念——18 个 agent 全裸放 `agents/`，靠 skill prompt 显式传 `${CLAUDE_PLUGIN_ROOT}/agents/xxx.md` 路径加载
- **（推断）关键疑点**：design-big/design-small 的编排伪码用 `TeamCreate/SendMessage/TaskCreate`（`skills/design-big/SKILL.md:133-211`）——这些**不是 Claude Code 的标准工具名**（Claude Code 是 Agent/Task 工具）；结合 README:221-223 致谢 revfactory/harness，推断 design 系列是对着另一套 harness 的 API 写的，在标准 Claude Code 上大概率跑不通或需改造；而 create/polish/rewrite 用的是标准 Agent 工具（`subagent_type: general-purpose`，`skills/create/SKILL.md:170`），是可执行的。同仓两套编排范式并存
- mo-shu 映射：我们的 spawn 协议（模板+fallback+契约+agents_version）比他们完整；他们的"路径白名单硬约束"是我们没有显式成文的——对防 agent 乱读很有效，值得吸收进我们 agent 模板的 spawn 协议
- 结论：**理念可学（路径白名单）+ 镜鉴**：无契约、无版本、双范式并存正是我们 AGENTS.md 部署物全套成本纪律要防的病

### M9 平台/商业化维度（重点问题 4：mo-shu 缺的能力维度）

- 证据：`agents/domain-researcher.md:30-53`（R2 平台策略调研：付费转化时机/曝光算法/连载模式/KPI）；`agents/platform-optimizer.md:44-79`（付费转化点钩子强制 4+）；`agents/plot-hook-engineer.md:23`（"付费转化点±3 话集中最高笔力"）；`skills/create/references/creation-principles.md:132-155`（手机可读性定量、爽/虐平衡每话至少 1 爽点、point scene 每话 2-3 个防 3500 字滑动态）
- 机制：把"读者留存经济学"做成一等公民设计约束——付费墙前后话数是显式设计参数进 plot 指南，每话验收含 HOOK 强度与付费点特检；韩国 6 平台白名单（문피아/네이버시리즈/카카오페이지/리디/조아라/노벨피아）贯穿所有入口的校验门（`skills/propose/SKILL.md:21-42` 别名归一化表）
- mo-shu 映射：我们 scan 扫榜选题覆盖"选什么写"，但**发布平台经济学（付费墙位置、追读节奏、存稿节奏）完全没有**。他们也没有数据回流（README 宣称的 2500 日浏览是营销数字，无回流机制，文档宣称）
- 结论：**理念可学**——"付费转化点"作为细纲/卷纲的一个显式字段（我们细纲六值可评估加"钩子强度/付费点标记"）；平台白名单+别名归一化的入口校验门模式可挂在 scan/构建。具体数值（±3 话、4+ 强度）是他们自定参数，移植时按反模式 #5 处理

### M10 三层角色资产：voice 速查卡 + 非语言动作库 + 对话 DNA（重点问题 4：风格管理）

- 证据：`agents/episode-architect.md:96-100`（声音速查卡：语尾/句长/口头禅/专属非语言≤3 个/5 级惊讶方式）；`agents/character-sculptor.md:11-29`（核心/细节/对话 DNA 三层文档体系）；`skills/rewrite/references/character-dialogue-dna.md:10-77`（"非语言是身体的调色板，对话 DNA 是说话的调色板"；思考模式/信息处理/说服方式/情境变体矩阵/禁忌模式五要素）；`skills/rewrite/references/character-embodiment-rubric.md`（7 维 0-10 分评分细则，主角 7 维平均、重要配角 4 维、龙套只测 VOICE）
- 机制：角色防串味有三层资产+三道防线——设计期（速查卡入每话设计图）、写作期（"换人读不别扭=失败"的自检）、验收期（立体度 rubric 打分，主角<7 分即 REWRITE）。惊讶 5 级强度变奏（第 5 级"专属动作反而不出现"用反差传震撼）是防"角色反应模板化"的具体技法
- mo-shu 映射：我们 style 技能管文风、追踪管角色状态，但**"对话不可交换性"这个可测判据和三层角色资产结构**是我们缺的；我们的对标拆文产物（moshu-analyze）可产出这类 DNA 卡
- 结论：**可移植（模板化）**——把"角色对话 DNA 卡（五要素）+非语言库+惊讶分级"做成 build Phase A 的角色资产模板，从主对标拆文产物自动填充；rubric 打分可作为 review 的角色维度 checklist（LLM 语义判定，符合我们三层分工）

### M11 韩国 AI 腔检测（AITONE/SEMANTIC）与 deslop 对位（重点问题 4）

- 证据：`skills/polish/references/12-axes.md:105-147`（AITONE 12 类模式：情感形容词堆叠/"不是 X 而是 Y 且是 Z"双重定义/双重否定/情绪名词作主语/总括句等；SEMANTIC 9 类：情境主语/所有格滥用/抽象名词主语/连接词开头等）；`skills/rewrite/SKILL.md:527-543`（大台词 3 步法+变奏规则）；`agents/revision-executor.md:69-80`（**修文 agent 自检 AI 腔**——"修正者本身是 AI，改翻译腔时可能注入 AI 腔"，修正句必须比原文更短更干更具体）；`agents/revision-reviewer.md:38-47`（复核者专门检查"修正引入的新 AITONE≥3 处→REVISE"）
- 机制：AI 腔不只是检测对象，还是**修正过程的副产物风险**——闭环里每个环节都设了"AI 腔再感染"检查位
- mo-shu 映射：deslop 的直接对位；"修正引入 AI 腔"的回路意识是我们 deslop/review 没有显式覆盖的（我们 review 改稿后没有专门的"改动是否引入新 AI 味"复核轴）
- 结论：**理念可学**——给 review 工单的整改回执加一条"修正文本自检去 AI 味"；AITONE/SEMANTIC 的模式分类学（形式层/文风层/语义层三分）可指导 deslop 中文词典的组织

### M12 novel-config.md：单文件项目契约（重点问题 2）

- 证据：`README.md:150-182`（文档宣称）；权威模板 `skills/polish/references/project-config-template.md:1-337`；三个执行 skill 都有"必需字段校验门"（`skills/create/SKILL.md:49-92`：缺字段报错终止；platform 白名单校验；EP 范围表重叠检测告警）
- 机制：一个 markdown 承载：项目基本盘（平台/目录）、设定文档映射（公共文档+**EP 范围→细分指南/细分角色表路由表**）、保全护栏（改稿不可破坏项）、数值正本优先级、自定义轴、沉默例外角色、核心数值速查。所有 skill Step 0 先过校验门。EP 路由表实现"第 100 话自动选用第 3 幕的细指南+该区间角色表"——**按需注入的文献路由**
- mo-shu 映射：我们多卷并发管理缺口的解法同构——"EP/章区间→适用卷纲/角色表"的映射表；我们 skill 配置无此路由层
- 结论：**可移植（改造）**——映射表+启动校验门+范围重叠检测都是确定性逻辑，适合做进我们 setup/build 的配置校验脚本；护栏清单 ≈ 我们机检的作者自定义阻断项注册口

## 2 与 mo-shu 差异对照

| 维度 | awesome-novel-studio | mo-shu |
|---|---|---|
| 定位 | 韩语网文全自动流水线（harness 自称） | 中文网文作者主权工具箱 |
| 确定性层 | **无脚本**，检查全靠 agent 用 Grep/Read + 编排器双保险 | 脚本做确定性（追踪事务/机检/守卫），AI 只做语义 |
| 追踪 | 无长期 state：前 2 话滑窗重提取 + 设定文档四级正本 + alive-tracker 20 话滚动窗 | 单权威 `_tracking-state.json` + 派生视图，每章结构化提交 |
| 断点恢复 | checkbox 计划文件（fix_plan/create-plan/rewrite-plan）+ 无参重跑续传 | next_step.py S0-S6 文件证据判定 |
| 审查独立性 | 诊断/执行/复核分 agent，但全部自动执行修订 | review 四 reviewer+工单；**候选永不拦截，作者定夺** |
| 作者介入点 | 选企划案、确认概念、确认重写范围；**创作/打磨每话不等作者**（"사용자 입력을 기다리지 않는다"，`skills/polish/SKILL.md:78`） | A 段 13 项准备到 D 段追踪事务，作者品味贯穿 |
| 设定变更 | `.design-hashes` 指纹→自动影响面→重写→下游打磨状态自动失效 | review 工单人工驱动，无影响面计算 |
| 角色管理 | 三层资产（voice 卡/非语言库/对话 DNA）+ 立体度 rubric 7 维打分 | 角色/关系入追踪派生视图，无对话 DNA 资产 |
| 商业维度 | 平台经济学一等公民（付费点/钩子强度/追读指标/6 平台白名单） | scan 扫榜止于选题，无发布经济学 |
| agent 纪律 | 18 agent 裸文件+skill prompt 传路径加载；错误处理表齐但无版本/契约 | spawn 协议+fallback 主线程+agents_version+全套部署物成本 |
| 语言/市场 | 韩语+韩国平台；AI 腔检测（AITONE）针对韩语 | 中文+中文站点；deslop 对位 |
| 规模宣称 | "300 话/150 万字不崩"三堵墙叙事；1 部作品签出版约（文档宣称） | 百万字后期一致性是已知缺口（待解） |

## 3 不学清单冲突核查（只列相关项+判定）

| 条目 | 触点 | 判定 |
|---|---|---|
| 自动连写污染传播（无暂存无作者定稿的连写） | polish/create/rewrite 三 skill 均为**自循环连跑**且明确"不等用户输入"（`skills/polish/SKILL.md:75-80`），单话内部虽有验证闭环但话与话之间无作者定稿闸门 | **不学其连跑编排**；单话内部"诊断→修正→复核→放行/降级"闭环可学；若吸收任何自动推进，必须保留我们"作者定稿才 commit 追踪事务"的闸门 |
| LLM 导演黑盒自治（水平 agent 通信） | design-big 让 concept-builder 与 character-architect **peer-to-peer SendMessage** 协调（`skills/design-big/SKILL.md:215-227`）；且该 API 非 Claude Code 标准（见 M8 推断） | **不学**（且疑似跑不通）；对照 design-small 的"leader 中介交接"（`skills/design-small/SKILL.md:209-230`）更接近我们模式，仍以我们主线程编排为准 |
| work_tracker 任务板 | fix_plan.md/create-plan.md/rewrite-plan.md 是 checkbox 进度文件 | **不触发**（判定：轻量断点状态文件非任务板系统；但吸收时警惕不演化成看板/任务系统） |
| Dashboard 常驻服务化 | `index.html` 是 770 行 GitHub Pages 静态营销页 | **不触发**（纯落地页，非服务） |
| RAG/向量检索；数据库后端；外部 AI 检测器；每章全量快照；git 书仓托管；npx 分发；PreToolUse 拦截；「文件即真相」重构；知识治理三件套；多宿主适配 | 均无对应物（实测 0 脚本、0 DB、检测全内嵌 prompt、状态为增量文件、无书仓托管/安装器/hook 门禁） | **不涉及** |

## 4 （推断）与存疑

1. **（推断）design-big/design-small 的 TeamCreate/SendMessage/TaskCreate 非 Claude Code 标准工具**（Claude Code 为 Agent/Task 工具），推断设计期编排在该插件当前形态下不可直接运行或依赖 revfactory/harness 环境；create/polish/rewrite 用标准 Agent 工具应为可执行。未实际安装运行验证——存疑，需上机验证才可定论。
2. **（推断）quality-verifier 的 CREATE 轴表内部不一致**：agent 定义文件列 8 轴为 DESIGN/NUMBER/TIMELINE/VOICE/HOOK/PLAUSIBILITY/PLATFORM/KOREAN（`agents/quality-verifier.md:99-207`），而 create skill 下发的 8 轴为 PLOT_BEAT/TIMELINE/NUMBER/GUARDRAIL/CONTINUITY/HOOK/CHAR_VOICE/CUSTOM（`skills/create/SKILL.md:296-306`）——同一 agent 两套轴表，README 未提；推断是版本演进残留，提示"清单类断言最易过期"在我们仓库同样成立。
3. **（推断）全 prompt 检查的实际拦截力存疑**：Grep 计数类（있었다≤5 等）可复现，但 HOOK 强度 1-5、立体度 0-10 等评分轴无 ground truth，"PASS 比率过高要复查基线"（`agents/revision-reviewer.md:148`）是作者自己承认的漂移风险——这正是我们用确定性机检的理由。
4. **（推断）前 2 话滑窗 + 设定文档正本能覆盖的矛盾半径有限**：2 话之前的伏笔/数值矛盾只能靠正本文件兜底，长程一致性弱于结构化追踪事务（推断依据：`skills/create/SKILL.md:108-116` continuity_lookback 默认 2，可配但未见长窗实践）。
5. **（存疑）生产实证**：README"签约出版/日浏览 2500+"为文档宣称，无数据回流机制佐证。
6. **（推断）活跃度**：本地快照单 commit、GitHub 最后 push 2026-04-14，之后 4 个月无更新，144★；项目可能已进入维护停滞——引用其机制时注意其未经过长期社区检验。

---
*研究方法：全量精读 18 agent + 10 skill + 9 references + 配置/落地页（约 7,900 行），git/文件数实测；未运行被研究项目。完成于 2026-08-27。*

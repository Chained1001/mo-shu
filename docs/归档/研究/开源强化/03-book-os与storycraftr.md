# 03·book-os 与 storycraftr 研究（开源强化）

> 研究单元：book-os（Novel-OS）+ storycraftr + storycraftr-example 三仓合并。
> 纪律：每条论断标证据（`相对路径:行号`，注明所属仓）；「（推断）」显式标注；README 宣称标注「（文档宣称）」。
> 本地副本均在 `.tmp/tests/开源强化研究/` 下，属临时验证产物区，引用路径以各仓根为基准。

## 0 元信息

| 项 | book-os（Novel-OS） | storycraftr | storycraftr-example |
|---|---|---|---|
| URL | github.com/forsonny/book-os | github.com/raestrada/storycraftr | github.com/raestrada/storycraftr-example |
| 本地 | `.tmp/tests/开源强化研究/book-os` | `.tmp/tests/开源强化研究/storycraftr` | `.tmp/tests/开源强化研究/storycraftr-example` |
| SHA | `bf15599`（git log 实测，单提交 "Add files via upload"） | `73a7709`（本地 git log 末次提交 2025-11-06；任务简报称 push 2026-03-06，本地无该提交，存疑见 §4） | `b8b6f1f`（2024-10-25） |
| 星 | 63（2026-08-27，任务简报口径） | 162（同上） | —（示例仓） |
| License | MIT（`LICENSE`） | MIT（`LICENSE`） | CC BY-NC-SA 4.0（`README.md`、chapters 内页均声明；书内容非 MIT） |
| 活跃度 | **停更约一年**：CHANGELOG 唯一版本 1.0.0=2025-08-18（`CHANGELOG.md:9`），此后零提交。所有结论**基于停更前版本** | beta 迭代中（v0.12.0-beta10，`README.md:16`），有 CI（pytest/pre-commit workflows） | 2024-10 产物仓，冻结 |
| 语言/形态 | Shell 安装器 + 纯 Markdown 提示工程（无应用代码） | Python CLI（click+rich+LangChain+Chroma）+ VSCode 扩展 | 纯产物 |
| 定位 | 给 AI 结构化写作上下文的工作流系统，Claude Code/Cursor 集成（`README.md:14`） | AI 小说 CLI：worldbuilding/outline/chapters/iterate/publish 全命令面（`README.md:6`） | 用 storycraftr 生成的示例书（`README.md:3`） |

与 mo-shu 关系：book-os 是**同宿主近亲**（Claude Code slash commands + subagents 机制，与我们技能包形态同构），其三层上下文与「追踪事务+派生视图」是同一问题的不同解法；storycraftr 是**管道化对照**——build/write/review 三环都做但全走 CLI+RAG，其生成器链对标我们 build Stage 1 四轮交互；storycraftr-example 展示该类无结构化追踪管线的产出上限。

## 1 机制清单

### M1 三层上下文 + lite 双版本（book-os）
- 证据：`README.md:66-107`（文档宣称）；`instructions/core/write-scenes.md:54-77`；`instructions/core/plan-novel.md:300-337,122-130`（代码事实：模板定义处）
- 机制：三层 = Standards（`~/.novel-os/standards/`，全局文风/类型指南）→ Novel（项目 `.novel-os/novel/`：premise/writing-plan/decisions）→ Manuscripts（`.novel-os/manuscripts/YYYY-MM-DD-story/`：story-outline/sub-specs/tasks）。关键设计：每份重文档配一份 `-lite.md` 压缩版（premise-lite=电梯陈述+1-3 句；story-outline-lite=1-3 句故事总纲），**装配上下文时只读 lite 版**，全文版留给人看与深查。
- mo-shu 映射：我们 A 段按「本章涉及设定」清单减法加载 ≈ 同一问题的清单法；lite 双版本 ≈ 续写状态卡（`追踪/上下文.md`）之外再给每份设定/大纲配机器友好压缩版——**我们目前只有追踪视图一族，设定/大纲侧无 lite 层**（已知缺口「追踪视图无按需注入」的相邻面）。
- 结论：**理念可学**（lite 双版本 + 装配用 lite、全文备查）。

### M2 context-researcher：专职检索子代理（book-os）
- 证据：`claude-code/agents/context-researcher.md:16-27,59-71`；`instructions/core/write-scene.md:84-139`（step 3/4 以 subagent 属性强制调用）
- 机制：输入=主代理的检索请求（如"取本章出场角色的对话风格"）→ 处理=先查是否已在主上下文（已在则只回 `✓ Already in context`），否则 grep 定位→**只抽取相关段落**回传 → 输出=最小增量信息。约束：只读、不改文件、keep responses concise。
- mo-shu 映射：这是把「按需注入」从流程文字变成**专职 agent 职责**的做法。我们 write 流程的上下文装配目前靠 SKILL.md 指令驱动主代理自取；已知缺口「追踪视图无按需注入」可借其形态：定义一个只读检索 agent 契约（输入=涉及清单，输出=蒸馏段落）。我们 agent 使用判据 §「上下文隔离的重型阅读」已覆盖此模式。
- 结论：**理念可学**（检索职责收口为只读 agent 契约；注意我们须配 fallback 主线程纪律）。

### M3 conditional loading 决策规则（book-os）
- 证据：`instructions/core/write-scenes.md:68-77`（essential_docs vs conditional_docs）；`instructions/core/create-outline.md:62-76,270-275,440-463`
- 机制：每个步骤显式列出必读文档（tasks.md 恒读）与条件文档（premise-lite/story-outline-lite/character-profiles——**仅当不在上下文才读**）；写场景前先做里程碑判定，明确不达标则整步跳过。最极端一条：**decisions.md「NEVER load into context」**（`create-outline.md:460-462`）——决策日志只写不读，靠结构化条目（DEC-XXX）在需要时定点查。
- mo-shu 映射：与我们「只吃判定结果」同源但更细：他们把「读什么/何时跳过」写进每步的 XML 属性。我们的 next_step.py 是全局路由级判定，章节内装配级无对应物。
- 结论：**理念可学**（每步 essential/conditional 两列 + 禁读清单——补 write 走查时的装配纪律）。

### M4 decisions.md 创作决策日志（book-os）
- 证据：`instructions/core/plan-novel.md:389-448`（schema：date/ID/status(proposed|accepted|rejected|superseded)/category/stakeholders + 决策/背景/备选/理由/后果五段模板）；`plan-novel.md:400-402`（头部声明「Override Priority: Highest——本文件指令覆盖用户 CLAUDE memories/Cursor rules 的冲突项」）；`create-outline.md:436-512`（只有显著偏离 premise/plan 且**用户批准**才写新条目）
- 机制：输入=一次显著创作决策 → 处理=五段模板落 `decisions.md`（append，不覆写）→ 输出=带编号的审计轨迹；后续流程以它为最高优先级覆盖源。
- mo-shu 映射：我们追踪事务记录的是**客观状态**（登场人物/伏笔/信息差变动），没有「为什么这样改」的决策卡产物。build 的四轮交互产物含设计理由，但 write 阶段的中途改道无登记位。
- 结论：**理念可学**（写作中途的「决策卡」append-only 日志；注意其 Override 声明是宿主提示词层面的优先级 hack，不必照搬）。

### M5 六专职 subagent 分工 + date-checker（book-os）
- 证据：`setup-claude-code.sh:178`（六 agent 名单）；`claude-code/agents/date-checker.md:12-31`（用 `touch` 临时文件读文件系统时间戳取当前日期，校验 `^\d{4}-\d{2}-\d{2}$`、年份 2024-2030）；`claude-code/agents/prose-reviewer.md:22-26`（审查者 never attempt edits）；`claude-code/agents/continuity-checker.md:121-147`（severity 三级：Critical/Minor/Suggestions）
- 机制：写作（manuscript-creator）/检索（context-researcher）/版本（writing-workflow）/审文（prose-reviewer）/审连戏（continuity-checker）/取日期（date-checker）六职分离，全部只读或受控写。date-checker 解「LLM 系统日期不可信」：文件系统 mtime 是确定性来源——**用脚本级确定性补 LLM 盲区**，与我们三层分工同哲学。
- mo-shu 映射：审查隔离（review 的 reviewer 分身防自审）我们已有；date-checker 思路=我们的确定性脚本思路（moshu 侧日期均取自文件/事务时间戳）。continuity-checker 的「只查事实性不一致，不评判创作选择」（`continuity-checker.md:128`）≈ 我们机检「阻断/候选」两列的代理版。
- 结论：date-checker **可移植**（若我们任何流程需要"今天"且宿主不给，文件 mtime 法可用）；其余我们已有等价物，不新增。

### M6 setup 安装器对 Claude Code 环境的改造（book-os）
- 证据：`setup-claude-code.sh:150-198`（mkdir `~/.claude/{commands,agents,output-styles}`；下载 4 命令 + 6 agents + 1 output-style）；`setup-claude-code.sh:110-148`（CLAUDE.md 配置：先备份 `CLAUDE.md.backup-<时间戳>`，再 grep 幂等检测已含配置则跳过，再探测 `~/.agent-os` 存在与否选「组合模板/纯小说模板」）；`setup.sh:103-146`（基础安装到 `~/.novel-os/`，已有文件默认跳过、`--overwrite-*` 显式开关）
- 机制：命令文件是**薄壳**——`commands/plan-novel.md` 只含 12 行引导（`echo $USERPROFILE` 解析 home → 读 `~/.novel-os/instructions/core/plan-novel.md` 执行真工作流），逻辑体全部留在全局安装区。**无任何 hooks**（全仓 grep 无 hooks 目录/设置；这是与 mo-shu 宪法「hooks 只提醒不拦截」和平共存的形态）。
- mo-shu 映射：moshu-setup 同为安装器，但我们是技能包分发（marketplace），无需 home 区下载。其「薄命令壳 + 全局逻辑体」两段式可借鉴于：把高频重逻辑放 references、命令面只留路由（我们事实上已如此）。
- 结论：**理念可学**（幂等+备份+共存探测三件套是安装器好范式）；形态不必移植。

### M7 write-scenes/write-scene 两层循环 + 阻塞协议（book-os）
- 证据：`instructions/core/write-scenes.md:136-184`（编排层：load write-scene.md ONCE → for each scene 执行→更新 tasks.md）；`instructions/core/write-scene.md:35-273`（单场景 7 步：理解任务→选择性读大纲→查文风→查角色声线→写→单场景质检→更新状态）；`write-scene.md:246-273`（tasks.md 勾选格式 `[x]`/`[ ]`/`⚠️ Creative block`，**最多尝试 3 种写法后标记阻塞并上报**）；`write-scenes.md:298-313`（完成后 `afplay` 系统提示音——macOS 专属，跨平台断裂证据）
- 机制：输入=任务清单中的下一场 → 处理=七步流水（其中 2/3/4 步都是减法装配）→ 输出=正文+tasks.md 状态翻转。创作阻塞被显式建模为状态而非异常。
- mo-shu 映射：我们的写章流程 A/B 段 + 追踪事务提交 ≈ 更强的版本（状态在 JSON 而非勾选框）。「3 次尝试→标记阻塞→求人」的**创作阻塞协议**我们没有显式条款——write 走查时可补一句同类纪律。
- 结论：**理念可学**（阻塞三试协议）；其余我们更强。

### M8 章节目录日期命名与版本语义（book-os）
- 证据：`instructions/core/create-outline.md:126-149`（`manuscripts/YYYY-MM-DD-story-name/`，kebab-case，≤5 词）；`claude-code/agents/writing-workflow.md:22-33`（版本名 `mystery-novel-v1.0`，语义化 draft/revision/final）
- 机制：每次 create-outline 产生一个带日期的故事目录，多稿并存；版本号由 agent 按里程碑建议递增——**纯提示语约束，无脚本强制**。
- mo-shu 映射：我们单权威 state + 每章事务原子写 ≈ 严格更强（他们同名冲突、日期取错、版本号漂移均无守卫）。
- 结论：**不学**（弱于现有机制；多卷并发缺口也轮不到它来补）。

### M9 storycraftr 生成器链：一句话种子 → 固定文件矩阵（storycraftr）
- 证据：`storycraftr/templates/folder_story.py:1-71`（init 创建 13 个固定文件：chapters 4 + outline 4 + worldbuilding 5）；`storycraftr/agent/story/outline.py:47-56` 与 `agent/story/worldbuilding.py:47-56`（**NEW/REFINE 双态判定：目标文件存在且 >3 行 → REFINE prompt，否则 NEW prompt**）；`storycraftr/utils/core.py:203-222`（`file_has_more_than_three_lines` 实现）；prompt 全文见 `prompts/story/outline.py:1-45`、`prompts/story/worldbuilding.py:1-41`（每条仅 1-3 句，把丰富度完全交给检索上下文与 behavior 契约）
- 机制：输入=一句话 prompt（如"概述一个反乌托邦科幻的总纲"）→ 处理=超薄模板 prompt + behavior.txt 系统契约 + 参考作者人设 + RAG 检索全书既有 md（k=6）→ 输出=落盘对应 md（旧文件转 `.back`）。**从最小输入生成丰富设定的方法=行为契约（见 M11）×参考作者人设（见 M12）×分维度逐文件生成（5 个 worldbuilding 维度各自独立成文件再互为检索语料）**。
- mo-shu 映射：对标 build Stage 1 四轮交互。差异：我们是**交互展开**（核心概念→故事承诺→卷骨架→读者契约，人盯四轮），他们是**一次一句话+静默生成**，丰富度靠先验契约而不是当轮追问。他们的「分维度文件矩阵 + 后生成文件成为先生成文件的检索语料」与我们 build 产物分层（设定/大纲）同构。
- 结论：**理念可学**（最省输入的杠杆是 behavior 契约与分维度矩阵；四轮交互换丰富度 vs 一句话+好契约换速度，是可选档位）。

### M10 全书知识库管道：md → Chroma 向量库（storycraftr）
- 证据：`storycraftr/agent/agents.py:55-125`（`ensure_vector_store`：`RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)`，`as_retriever(search_kwargs={"k": 6})`）；`agents.py:144-175`（`load_markdown_documents`：全项目 `**/*.md`、跳过 ≤3 行文件与 vector_store 目录）；`agents.py:312-329`（`update_agent_files`：**每次生成后 force 全量重建**向量库并作废全部线程）；`storycraftr/graph/assistant_graph.py:41-88`（检索片段以 `Source: <相对路径>` 拼进 system prompt 的 Context 段）
- 机制：输入=项目全部 md → 处理=切块/嵌入/入库，每命令后重建 → 输出=每次问答自动带 6 个最相关块。
- mo-shu 映射：这正是宪法 §6「RAG/向量检索」条目。它解决的「百万字一致性」问题与我们的「派生视图+按需注入」同题，但其解法每命令全量重嵌入的成本随书厚线性涨，且检索无审计。
- 结论：**不学**（触 §6 RAG/向量检索——显式红线）。

### M11 behavior.txt 作者契约（storycraftr）
- 证据：`storycraftr/cli.py:135`（`--behavior` 为 init **必填**项）；`storycraftr/agent/agents.py:194-217`（读 `behaviors/default.txt`，无则内置兜底文案；behavior.strip() 作为 system_prompt 首段）；示例实体：`storycraftr-example/behaviors/default.txt`（一份完整反派视角写作契约：基调/叙事焦点/情节结构/人物动力/世界观/主题六节，英文，约 40 行）
- 机制：输入=作者在 init 时提供的自由文本契约 → 处理=原样进 system prompt 顶部 → 输出=全书所有生成共享同一先验。
- mo-shu 映射：对标我们 style skill 的文风样本 + build 的读者契约。差异：他们把「基调+题材焦点+主题」打包为一个必填文件，作为**最省 token 的人格锚**；我们读者契约在 build 产物里，write 阶段注入多少取决于 A 段清单。
- 结论：**理念可学**（必填 behavior 契约是「最小输入生成丰富设定」的第一杠杆；与 moshu-style 可互补）。

### M12 参考作者人设注入（storycraftr）
- 证据：`storycraftr/prompts/story/core.py:1-6`（FORMAT_OUTPUT："You are {reference_author} writing a new engaging book."）；配置实体 `storycraftr-example/storycraftr.json`（`"reference_author": "Brandon Sanderson"`）
- 机制：init 配置里的对标作者名 → 每次生成的系统提示首句人设化。
- mo-shu 映射：我们「主对标」登记的是具体书目录并按清单取用其拆解产物；他们只注入一个名字当风格压缩锚。（推断）名字锚的稳定性弱于结构化拆解样本，但 token 成本近零。
- 结论：**理念可学**（零成本风格锚可作为我们主对标机制的补充提示语，不是替代）。

### M13 iterate 全书重写命令族（storycraftr）
- 证据：`storycraftr/agent/agents.py:332-399`（`process_chapters`：遍历 chapters/outline/worldbuilding **全部 md**（排除 cover/back-cover），逐文件喂 LLM 重写后覆写）；`storycraftr/cmd/story/iterate.py:26-240`（CLI 面：`check-names`/`fix-name <旧> <新>`/`refine-motivation <角色> <语境>`/`strengthen-argument <论点>`/`insert-chapter <位置> <prompt>`/`add-flashback`/`split-chapter`/`check-consistency`）；`storycraftr/prompts/story/iterate.py:3-97`（FIX_NAME_PROMPT 处理昵称/变体；INSERT_CHAPTER_PROMPT 声明后续章自动重编号）；备份：`storycraftr/utils/markdown.py:28-63`（覆写前 `shutil.copyfile` → `<原名>.md.back`，示例仓中 `outline/*.md.back` 与 `worldbuilding/*.md.back` 是实跑痕迹）
- 机制：输入=一条意图（如改人名）→ 处理=对全书每文件跑同一条 prompt（含该文件旧全文）→ 输出=全部覆写 + 单跳 .back 备份。rewrite 粒度是**全书**而非选段。
- mo-shu 映射：这是「无作者定稿的批量重写」，是宪法 §6「自动连写污染传播」的近亲变体（重写版）：一条意图未经作者逐章确认就改写全书。我们 review 产工单、作者定稿后才落地，方向相反。可取的只有两点碎片：`.back` 单跳备份（我们迁移带备份同源，已覆盖）；`fix_name` 的**昵称/变体替换语义**值得在工单 prompt 里借鉴。
- 结论：**不学**（自动连写污染传播边缘 + 每文件全量重写成本失控）；碎片「变体名替换语义」理念可学。

### M14 insert_chapter 确定性重编号（storycraftr）
- 证据：`storycraftr/agent/story/iterate.py:145-249`（Python 纯脚本：按 `chapter-<n>.md` 解析数字排序，从尾到头 `rename` 递增，然后才调 LLM 生成新章，最后重写前后邻章缝合）
- 机制：文件重排这类**确定性操作由脚本完成**，LLM 只写新内容——与我们「脚本做确定性、AI 做语义」同一条宪法的实例。
- mo-shu 映射：我们脚本层已有同等能力（追踪事务/派生视图脚本），且我们的章文件管理走单权威 state。此条作为「同哲学互证」记录。
- 结论：**理念可学**（互证：他们把重编号从 LLM prompt 里拿出来写成代码，正是我们反模式清单 #5 的反面教材的正确解）。

### M15 prompts.yaml 生成日志 + 随机日期短语（storycraftr）
- 证据：`storycraftr/utils/core.py:18-38`（每次 LLM 调用：随机选一条日期格式短语拼在 prompt 头 + 完整 prompt 追加进项目根 `prompts.yaml`）；`storycraftr/prompts/permute.py:1-40+`（40+ 条同义日期短语池）；实例：`storycraftr-example/prompts.yaml`（首条 2024-10-23，完整含 FORMAT_OUTPUT 全文）
- 机制：输入=原始 prompt → 处理=加随机化日期前缀 → 输出=可复放的 prompt 存档。（推断）随机前缀疑似用于绕过 provider 端 prompt 缓存/防模式化，仓库未说明用途——存疑。
- mo-shu 映射：我们「AI 产出先落文件」+ 研究纪律「实测数字可复现」同源；他们的 prompts.yaml 让每次生成**可审计可复放**，这是我们 write 阶段没有的产物（我们的等价物是追踪事务 JSON，但不含 prompt 全文——宪法 §8 明确不测 prompt 全文，方向不同但审计价值可参考）。
- 结论：**理念可学**（生成调用留痕落盘；随机前缀部分存疑不学）。

### M16 示例仓产物结构与质量（storycraftr-example）
- 证据：文件树（实测）：`chapters/`（chapter-1..18.md + cover.md/back-cover.md/epilogue.md + cover.png/template.tex）、`outline/`（general_outline/character_summary/plot_points/chapter_synopsis 四件 + 各自 `.md.back`）、`worldbuilding/`（culture/geography/history/magic_system/technology 五件 + `.back`）、`behaviors/default.txt`、`prompts.yaml`、`storycraftr.json`、`books/libro_completo.md|.pdf`（西语）与 `_en` 版、`storycraftr/{chat,getting_started,iterate}.md`（工具文档拷贝）
- 数字（实测 `wc -w`）：18 章各 853-1202 词（西语），整书 19,587 词；`books/libro_completo_en.md` 1,054 行
- 质量粗评（文档宣称+抽样）：README 自述"许多 prompt 已丢失未备份"（`README.md:5`）——过程记录不完整；抽样 `chapters/chapter-1.md` 正文连贯、画面感成立、反派视角纪律执行到位；但 `worldbuilding/magic_system.md` 残留 OpenAI 旧版 file_search 引用标记 `【4:9†source】`（第 9/17/19 行等）——**引用幻觉/泄漏进正文**的直接证据，且该文件双标题（"# Magic/Science System" + "# Sistema Mágico/Científico"）显示生成拼接痕迹。上限判断：一句话种子 → 2 万词可读中短篇成立；无结构化追踪下的一致性依赖 RAG 命中率，未提供任何百万字级证据。
- mo-shu 映射：这是我们「百万字一致性」缺口的反面参照：无追踪事务的管线在 18 章规模就出现引用残留与结构瑕疵。
- 结论：**不学**（作为上限证据收录）。

## 2 与 mo-shu 差异对照

| 维度 | mo-shu | book-os（Novel-OS） | storycraftr |
|---|---|---|---|
| 宿主形态 | Claude Code 技能包（11 skill + marketplace） | Claude Code/Cursor 全局安装（slash 命令+agents+output-style，**无 hooks**） | 独立 Python CLI + VSCode 扩展（自带 LLM 调用） |
| 上下文装配 | A 段「本章涉及设定」减法清单（缺口：追踪视图无按需注入） | lite 双版本 + context-researcher 专职检索 agent + 每步 essential/conditional 清单 | RAG：全项目 md 向量化 k=6 自动注入（不学） |
| 状态/追踪 | 追踪事务（每章 JSON 提交）+ 单权威 state + 派生视图 + 续写状态卡 | tasks.md 勾选框 + writing-plan 里程碑（全提示语约束，无脚本守卫） | 无追踪层；一致性=检索命中率；决策无登记 |
| 决策留痕 | 追踪事务记客观变动；build 产物含设计理由 | decisions.md：DEC-XXX 五段决策卡，只写不读，最高覆盖优先级 | 无（prompts.yaml 只记 prompt 不记决策） |
| 版本安全 | 迁移带备份；state 原子写 | 提示语级「备份/版本号」+ 安装器真备份 CLAUDE.md | `.md.back` 单跳备份（每个覆写点，实测有效） |
| 确定性边界 | 脚本做确定性（宪法） | 几乎无脚本（date-checker 用 mtime 是唯一亮点） | insert_chapter 重编号=脚本；其余（含一致性检查）全 LLM |
| 作者控制点 | 作者做品味：定稿门、机检候选只呈报 | 显式确认门多处：plan-novel 输入阻断校验；create-outline 第 10 步用户审阅→第 13 步"是否开写 Task 1"；write-scenes 场景选择确认+环境确认；决策入库须批准 | 命令即生成，**无门禁**；仅 `cleanup` 有 confirm（`cli.py:354-360`）；iterate 全书重写一把梭 |
| 生成入口档位 | build 四轮交互（丰富度优先） | /plan-novel 一轮问答产 5 文件 | 一句话种子 + behavior 契约（速度优先） |
| 审查 | moshu-review 四 reviewer + 工单 + 机检阻断/候选 | prose-reviewer/continuity-checker 只读代理，三级严重度 | iterate check-consistency（=全书逐文件 LLM 重写，检改合一无呈报） |
| 测试/CI | 守卫+回归测试体系 | 无 | 有 pytest/pre-commit CI |
| 活跃度 | v1.5.0 后治理中 | 停更约一年 | beta 迭代 |

## 3 不学清单冲突核查

| §6 条目 | book-os | storycraftr | 判定 |
|---|---|---|---|
| RAG/向量检索 | 未用（grep+子代理检索） | **核心依赖**（Chroma+k=6，`agents.py:55-125`） | storycraftr 该层**不学**；其余机制不受污染 |
| LLM 导演黑盒自治 | 否（工作流编排，人确认点密集） | 否（命令由人发起；但 iterate 全书重写无确认） | 均不直接触发 |
| 「文件即真相」整体重构 | 否 | 否（文件即语料但非真相重构） | 不触发 |
| 每章全量快照 | 否 | `.back` 单跳备份非快照 | 不触发 |
| work_tracker 任务板 | 否（tasks.md 是场景清单非任务板系统） | 否 | 不触发 |
| 自动连写污染传播 | 否（无暂存定稿概念但也无自动连写） | **边缘触碰**：iterate 族=无作者定稿的全书批量重写（M13） | 该自动化程度**不学** |
| 知识治理重三件套 | 否 | 否 | 不触发 |
| 多宿主适配 | 其双宿主（Claude/Cursor）是**它们**的形态 | 独立 CLI 天然多宿主 | mo-shu 自身仍不做多宿主 |
| 数据库后端 | 无 | Chroma 本地向量库（属 RAG 条款涵盖） | 不学（并入 RAG 条） |
| Dashboard 常驻服务化 | 无 | 无 | 不触发 |
| 外部 AI 检测器 | 无 | 无 | 不触发 |
| git 书仓托管 | 无（版本是提示语） | 无 | 不触发 |
| npx 安装器/插件市场 | curl 安装器（非 npx） | pipx 安装 | 不触发（也不学其 curl-管道-安装形态） |
| PreToolUse hook 拦截门禁 | **无 hooks**（实测） | 不适用 | 不触发 |

## 4 （推断）与存疑

1. **（推断）book-os 实际执行强度存疑**：全部工作流是给 LLM 的 XML 指令，无任何脚本验证步骤是否被执行（如「conditional loading」全凭 LLM 自觉）。其 63 星/零 issue 演进的社区验证度未知。我们的结论只针对**设计文本**，不对其运行效果背书。
2. **（推断）storycraftr `push 2026-03-06` 与本地不符**：本地 git log 末次提交 2025-11-06（`73a7709`）。可能远端有分支/后续推送未收入本副本——以其 GitHub 页面为准，本研究一律以本地 SHA 为证据基线。
3. **（推断）随机日期短语用途**：`prompts/permute.py` 的 40+ 条同义日期前缀，仓库无注释说明；（推断）为绕过 provider prompt 缓存或降低模式化，无证据，不学。
4. **（推断）example 仓引用残留成因**：`magic_system.md` 的 `【4:9†source】` 是 OpenAI Assistants file_search 引用格式，而当前代码已是 LangChain+Chroma 重构版——（推断）示例书产自 2024-10 的旧版 Assistant API 管线，现行代码不复现该标记；同时说明「引用泄漏进正文」是该类管线的历史真实风险。
5. **（推断）lite 文件的维护成本**：book-os 让 LLM 在 plan-novel/create-outline 时同步产出 lite 版，但无机制保证 lite 与全文随后续修改保持一致——（推断）长期会漂移；若 mo-shu 借鉴，lite 应像派生视图一样**由脚本或事务从全文确定性派生**，而非双写。
6. **存疑**：book-os 星数 63、storycraftr 星数 162 均引自任务简报（2026-08-27 口径），未独立复核。
7. **（推断）storycraftr 命令粒度启示**：其 CLI 面把「改人名/强化论点/插章/拆章」做成一等命令，说明作者心智里**修书动词**与「写书动词」同级；mo-shu 若补 write 走查，可审视工单→修文动词是否覆盖同级粒度（此为需求侧信号，非移植建议）。

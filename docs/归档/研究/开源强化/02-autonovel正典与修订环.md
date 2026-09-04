# 02·autonovel 正典与修订环研究（开源强化）

## 0 元信息

### 0.1 仓 A：NousResearch/autonovel

- URL：https://github.com/NousResearch/autonovel
- 本地：`.tmp/tests/开源强化研究/autonovel`（只读检出，master）
- SHA：`d165f26`（最后提交 2026-03-20，实测 `git log -1`）
- 星：1526（2026-08-27，任务书给定，未实测）
- license：**无**（仓内无 LICENSE 文件，实测 `ls | grep -i licen` 无结果）——本报告只转述机制，不抄代码/prompt 原文
- 语言/规模：Python；根目录实测 27 个 `.py`（README.md:62 宣称 "27 Python scripts"，数字相符；其中 `main.py` 是 hello-world 桩，实测 1-5 行）
- 定位：自主小说管线——种子到成品（写作/修订/排版/插图/有声）一条龙，"modify-evaluate-keep/discard" 循环套用到小说（README.md:3-8）
- 与 mo-shu 关系：**机制参照**（修订环防劣化、正典生长、评分门禁的反面教训）；其全自治形态与作者品味宪法相反，只学零件不学形态。

### 0.2 仓 B：DukeTwoCan/autonovel-agent-skills

- URL：https://github.com/DukeTwoCan/autonovel-agent-skills
- 本地：`.tmp/tests/开源强化研究/autonovel-agent-skills`（只读检出）
- SHA：`aac4df4`（最后提交 2026-07-15，实测）
- 星：2（2026-08-27，任务书给定）
- license：MIT（LICENSE 文件在仓根）
- 语言/规模：Python（标准库，dependency-light）+ 9 个 Agent Skills；`skills/creative/autonovel/lib` 实测 15 个模块（各阶段 skill 另有镜像子集：drafting 9 个、revision 8 个、foundation 6 个、grade 6 个、export 4 个、consistency-pass 2 个、prose-review 1 个）；`tests/` 48 个文件；类型包 53 个 manifest.json（实测 `find -name manifest.json | wc -l`）
- 定位：仓 A 的 Agent Skills 移植，**协作优先**、可全自动（README.md:3-9）；测试于 Codex 与 Hermes Agent（README.md:11-14）
- 与 mo-shu 关系：**同形态参照**（也是 skill 包 + 脚本做确定性 + LLM 做语义 + 每章一次落盘提交）；其 story_state 事实账本直接命中 mo-shu「追踪视图无按需注入」「百万字后期一致性」两个已知缺口。

> 证据标注约定：`仓A:` 前缀 = autonovel 本地仓相对路径；`仓B:` 前缀 = 移植版本地仓相对路径（skills/ 下省略 `skills/creative/`）。README/文档来源的数字与宣称均标（文档宣称）。

## 1 机制清单

### M1 五层协同演化与传播债（仓 A）

- 证据：`仓A:program.md:16-23`（层栈定义）、`仓A:program.md:113-127`（传播规则+债 JSON）、`仓A:README.md:157-171`（"Changes propagate both down … and up"）、`仓A:run_pipeline.py:73`（state 里仅初始化 `debts: []`）
- 机制：五层 = Layer 5 `voice.md`（怎么写）→ Layer 4 `world.md`（有什么）→ Layer 3 `characters.md`（谁行动）→ Layer 2 `outline.md`（发生什么）→ Layer 1 `chapters/ch_NN.md`（正文），横切层 `canon.md`（什么是真的）。演化规则：
  - 向下传播：上层文档改动须检查下游（voice 变→全书重估 voice_adherence；world 变→查全部章节 lore 一致性；outline 变→重估受影响章节 beat 覆盖；章节变→查伏笔账本与相邻章）（program.md:115-120）。
  - 向上传播：写作中发现设定缺口/矛盾，在 state.json 记一笔"债"：`{"trigger": "ch_07: …", "affected": ["world.md","ch_03.md"], "status": "pending"}`（program.md:122-127）。
  - **代码事实**：`debts` 在全部 27 个脚本中只在 `run_pipeline.py:73` 作为默认值出现，无任何脚本读/清它——传播债是 program.md 对 agent 的纯 prompt 约定，README.md:171 "The pipeline tracks propagation debts in state.json" 属**文档宣称超出代码事实**。
- mo-shu 映射：对标我们的 设定/ → 大纲/（卷纲+剧情单元卡+细纲）→ 正文/ → 追踪/ 分层。双向传播里"向上记债"对应我们把写作中发现的矛盾登记进追踪；mo-shu 的优势是追踪事务是结构化 JSON + 单权威 state，A 仓的债只是自由文本约定。
- 结论：**理念可学**——「层间变更必须检查下游」可以成为 mo-shu 大纲/设定变更时的检查清单语义（写入施工或 review 流程文档即可，无需新机制）；债队列本身 A 仓证明了纯 prompt 约定不可靠，不学。

### M2 正典提取与随章生长（gen_canon.py + canon.md，仓 A）

- 证据：`仓A:gen_canon.py:40-42`（输入）、`:44-91`（prompt）、`:86-88`（条数与差异规则）、`仓A:canon.md:3-16`（使用规则）、`:19-68`（七类结构）；消费方：`仓A:draft_chapter.py:75`（起草注入）、`仓A:evaluate.py:558-560`（"CANON … violations are bugs"）、`:633-635`（canon_compliance 维度：一处重大违例封顶 6 分）、`:663`（eval 输出 `new_canon_entries`）；生长：`仓A:program.md:76-79`（每章评估后把新事实补进 canon.md）
- 机制：
  - 输入：seed.txt + world.md + characters.md 全文，低温度（0.2）单次提取。
  - "hard fact"判据（prompt 转述）：写作者不可矛盾的一切——名字、年龄、日期、外貌、魔法规则、地理、关系、已发生事件；一事一条、短、可检验；每条尾部括注来源（world.md / characters.md / ch_NN）；两文档细节冲突时**显式记录差异**；不发明事实；目标 80-120 条起步。
  - 输出结构：canon.md 七类——Geography / Timeline / Magic System Rules / Character Facts / Political/Factional / Cultural / **Established In-Story**（已发生且不可撤销的事件，模板明确"Kael killed the messenger in ch_03. This cannot be undone"，canon.md:63-68）。
  - 消费链：起草（全文注入）→ 章评（canon_compliance 违例=bug + 产出 new_canon_entries）→ 人工/agent 把新事实追加回 canon.md（**推断**：追加步骤无脚本自动化，靠 program.md 指令驱动）。
- mo-shu 映射：对标单权威 `_tracking-state.json` + 派生视图。方向相反：A 仓是「markdown 即数据库、无 schema、注入全文」；mo-shu 是「JSON 权威、视图派生」。可学的三点：①"一事一条 + 来源标注 + 可证伪"的条目纪律（对应追踪事务字段语义）；②**Established In-Story 的不可逆事件类**——mo-shu 追踪里"既成事实"与"状态"应分开登记；③"两源冲突时记录差异"= 机检候选列的天然候选来源。
- 结论：**理念可学**（条目纪律 + 不可逆事件类 + 冲突记录）；canon.md 的 md 无 schema、全文注入不做 token 预算的做法不学（百万字下不可扩展）。

### M3 三阶段管线与阶段门禁（WORKFLOW/PIPELINE，仓 A）

- 证据：`仓A:PIPELINE.md:117-146`（Phase 1）、`:148-184`（Phase 2）、`:186-359`（Phase 3 含 3b）、`:361-372`（Phase 4）；`仓A:run_pipeline.py:39-45`（常量：FOUNDATION_THRESHOLD 7.5 / CHAPTER_THRESHOLD 6.0 / MAX_FOUNDATION_ITERS 20 / MAX_CHAPTER_ATTEMPTS 5 / MIN·MAX_REVISION_CYCLES 3·6 / PLATEAU_DELTA 0.3）；`仓A:program.md:45-51`（lore 权重 40%）；`仓A:evaluate.py:508`（lore 40% / character 30% / structure 20% / craft 10%）
- 机制：
  - **阶段 1 建设（无正文）**：gen_world → gen_characters → gen_outline（part1 节拍）→ gen_outline_part2（伏笔账本）→ 声纹发现（5 段试写选 register）→ MYSTERY.md → gen_canon → `evaluate.py --phase=foundation`。**门禁**：foundation_score > 7.5 且 lore_score > 7.0 才准进 drafting（program.md:34, 62-63；PIPELINE.md:122 宣称 canon 应 400+ 条才出地基，文档宣称）。产物 = 五文档 + MYSTERY + canon。
  - **阶段 2 逐章起草**：每章注入 voice/world/characters/本章大纲条目/前章尾部约 1000-2000 词/下章大纲前 10 行（draft_chapter.py:71-87, program.md:69-72），评后 keep（≥6.0）/discard（<6.0，最多 5 次尝试；5 次全败则保留最好的一次硬着头皮前进，run_pipeline.py:373-385）。**门禁**：章分 ≥ 6.0（"Forward progress over perfection"，program.md:203-205）。
  - **阶段 3 自动修订环**（见 M4/M5）+ **阶段 3b Opus 审查环**（见 M7 停止条件）。
  - **阶段 4 导出**：重建 outline/arc_summary → manuscript.md → LaTeX → tectonic PDF。
- mo-shu 映射：build（构建环）≈ 阶段 1；write 日更（A 13 项准备→B 三遍→C 机检链→D 追踪事务）≈ 阶段 2 但 mo-shu 每章有作者定稿、A 仓只有评分门；review/deslop ≈ 阶段 3。差异本质：A 仓所有门禁都是 LLM 评分门（见 M11 反面教训）。
- 结论：**理念可学**——「阶段门禁 + 常量集中定义 + CLI 可覆盖」与 mo-shu 宪法 §4.5（常量命名+CLI 可覆盖+验收可测）同构，A 仓这点做得对；评分当门不学。

### M4 修订环防劣化三件套：评分对比回滚、高原检测、审查停止条件（仓 A）

- 证据：`仓A:run_pipeline.py:519-575`（pre_score/post_score 对比，变差即 `git_reset_hard("HEAD")` 回滚）、`:600-604`（plateau：cycle≥3 且 |Δ|<0.3 停）、`仓A:review.py:185-205`（should_stop）、`仓A:PIPELINE.md:402-410`（危险模式清单）
- 机制（怎么防止越改越坏）：
  1. **keep/discard 语义**：每次修改先评后比，分数不升即回滚（git reset --hard），所有实验记入 results.tsv（run_pipeline.py:87-96）。
  2. **高原检测**：≥3 轮后全书分变化 <0.3 视为平台期，停止修订（PLATEAU_DELTA=0.3）。
  3. **审查停止条件**（review.py:198-204）：★≥4.5 且无 major 未限定项；或 ★≥4 且过半条目是 qualified/hedged（"individually fine / costs of ambition" 类措辞，review.py:151-155 检测）；或只剩 ≤2 条。核心认知："审稿人永远能找出问题，停止条件看严重度与限定性，不是零缺陷"（PIPELINE.md:349-351）。
  4. **经验性护栏**（PIPELINE.md:402-410，生产复盘）：压缩勿低于 1800 词（甜区 2200-3000）；gen_revision 实际会比任务书多写约 30%（expansion bloat）；追"最弱章"是打地鼠，轮换 2 次即停；修一个分常掉另一个分。
- mo-shu 映射：对标 build Phase B evaluator 打磨环与 review 技能。mo-shu 的对应物是「作者定稿 + 机检候选不拦截」——A 仓的回滚/停止条件是**无人值守下的劣化防线**，mo-shu 有人工定稿天然免疫大部分，但"高原检测（连续 N 轮无显著改善即停）"与"审稿停止条件（严重度分级而非零缺陷）"对 review 技能的工单分诊有直接参考价值。
- 结论：**理念可学**（停止条件语义 + 高原检测常量化）；git 回滚本身触「git 书仓托管」不学（见 §4），其"一次验收一个提交点"的语义 mo-shu 已由追踪事务承担。

### M5 对抗式删减 + 四读者面板 + 共识解析（仓 A）

- 证据：`仓A:adversarial_edit.py:1-8`（docstring："cut 500 words…The cut list IS the revision plan"）、`:90-131`（10-20 处引文级删改清单，六型分类 FAT/REDUNDANT/OVER-EXPLAIN/GENERIC/TELL/STRUCTURAL，另要求给 tightest_passage"永不碰"与 loosest_passage）；`仓A:reader_panel.py:24-77`（四人格 system prompt：编辑/类型读者/作家/第一读者）、`:79-111`（全书级 10 问）、`:155-184`（find_disagreements：按"Ch N"正则提取各读者点名章节，部分点名部分未点名=分歧=编辑决策点）；`仓A:run_pipeline.py:403-464`（parse_panel_consensus：分歧项+点名计数合并排序取前 5）；`仓A:apply_cuts.py:43-76`（引文精确匹配→空白归一正则，多重匹配拒删保安全）
- 机制：对抗编辑把"删哪里"变成结构化 JSON（引文+理由+型+动作）；读者面板读 arc_summary（非全文）按 10 问作答，**分歧而非一致**被当作编辑决策入口；两者喂给 gen_brief（M6）。
- mo-shu 映射：对标 review 四 reviewer 隔离 + 工单。同构点惊人：①多 reviewer 人格隔离防自审；②产出结构化工单而非自由文本；③"tightest passage 保留清单"≈ 工单里应含"保留项"避免越改越坏。差异：A 仓面板基于摘要视图（arc_summary ≈ 派生视图），mo-shu review 直接读正文多章。
- 结论：**可移植**（机制层面）——「面板分歧=决策点」「工单含保留清单」两个设计可直接吸收进 moshu-review 的工单 schema 设计；四人格 prompt 不抄（无 license），自拟中文人格即可。

### M6 修订任务书（brief）结构化生成（仓 A gen_brief.py）

- 证据：`仓A:gen_brief.py:186-196`（按主负面反馈定型 COMPRESS/DRAMATIZE/TIGHTEN/REVISE）、`:316-327`（字数目标随型定：COMPRESS×0.55 / TIGHTEN×0.85 / DRAMATIZE 持平）、`:330-342`（五段结构 PROBLEM / WHAT TO KEEP / WHAT TO CHANGE / VOICE RULES / TARGET）、`:606-784`（--auto：取全书 eval 的 weakest_chapter，交叉并入章评/面板/删减三源）；`仓A:gen_revision.py:46-96`（重写时注入 brief + 旧稿全文"keep what works" + 前章尾/后章头）
- 机制：把三源反馈（面板 JSON / eval JSON / 对抗删减 JSON）机械汇成一份带保留清单、字数目标、声纹规则的任务书，重写模型只对任务书负责。
- mo-shu 映射：对标 moshu-review 工单（tickets_{时间戳}.json）。可直接对照的字段设计：工单应含「保留项（防误删好句）」「目标字数/幅度（压缩型×0.55、收紧型×0.85 这种显式系数）」「变更项逐条编号」。
- 结论：**可移植**（工单字段语义，非代码）。

### M7 事实账本 story_state 与 STORY STATE 按需注入（仓 B，核心）

- 证据：`仓B:autonovel/lib/story_state.py:31-41`（九谓词 + 排他作用域）、`:43-45`（账本形状）、`:52-60`（原子写：tmp + os.replace）、`:71-119`（add_fact：幂等去重、同域开放事实自动闭合、乱序 ValueError、同章取代留 [N,N) 瞬态区间）、`:130-143`（end_fact 显式结束：转移=一 end+一 fact）、`:146-167`（current_facts 的 N-1 约定）、`:170-188`（query_block：STORY STATE 行 + 事实行 `[since chN]` + FORESHADOW DUE + TIMELINE 最近锚点）、`:191-215`（伏笔 add/due/unpaid/payoff）；填充协议 `仓B:autonovel-drafting/references/fact-extraction.md:17-52`（提取 JSON 元素：fact/ends/new_entity/foreshadow/payoff/story_time；只提取**变化**不复述存量）、`:67-108`（解析失败重试一次；未知谓词重提一次后丢弃该条不阻断整批；乱序记 needs_attention 跳过）、`:132-151`（初始化：从 characters.md/world.md 播种实体）、`:153-159`（"What this replaces"：**账本查询替代为找事实而重读旧章**；前章尾 1000 词仍读，但只为文风衔接不为事实）；注入预算 `仓B:autonovel-drafting/SKILL.md:80-94`（每章起草前 `story_state.py query <facts.json> N <本章出场角色>`，STORY STATE 块 ≤1.5k token，超了先缩角色面再丢次要角色事实并注明）
- 机制：每章接受后一次结构化提取（AI 做语义）→ 谓词封闭集 + 章戳有效区间的事实账本（脚本做确定性）→ 下一章起草按需查询注入（token 预算受控）。九谓词：located_in / possesses / knows / believes / feels_toward / injured / allied_with / alive / owes；排他作用域分 per-subject（located_in、alive）与 per-pair（feels_toward 等）。一致性审查第 N 章用 `current_facts(N-1)`（入章状态）而非 N（避免把本章自身的状态变迁误判为矛盾）。
- mo-shu 映射：**直接命中两个已知缺口**——「追踪视图无按需注入」：query_block(chapter, subjects) 就是按需注入的实现范式（按本章出场角色过滤 + token 预算 + 超限降级规则），可挂在 write A 段准备步骤查询 `_tracking-state.json` 派生视图；「百万字后期一致性」：章戳区间 + 自动闭合使账本规模只随"状态数"而非"章数"增长，闭式谓词集保证查询确定性。与追踪事务的同构：每章一次提交、AI 提语义、脚本管权威与原子写。差异：mo-shu 追踪事务已有单权威 state + 派生视图，缺的只是「查询命令 + 预算 + 降级序」这一层接口语义。
- 结论：**可移植**（接口范式：按需查询块 + 角色过滤 + ≤N token 预算 + 缩面降级 + N-1 审查约定）。谓词集需为网文另设计（境界/身份/功法/契约等），"封闭谓词集 + 排他作用域 + 章戳区间"三件套模式照搬。

### M8 滚动摘要 + 窗口化一致性走查（仓 B）

- 证据：`仓B:autonovel-consistency-pass/SKILL.md:3-4`（"27B/65k 本地模型包络——绝不一次载入全书"）、`:35-52`（滚动摘要：起草时已逐章活追加到 consistency_state/rolling_summary.md，走查只补缺不重建）、`:54-69`（4 章一窗，chunk_by_chapters）、`:92-122`（每窗注入 STORY STATE ENTERING THE WINDOW（as of end of ch a-1）≤1.5k token，超限先缩角色再丢次要事实并注明"绝不注入无预算账本"）、`:124-136`（六类发现：人物声线漂移/情节矛盾/重复短语（双引）/世界规则违反/档案矛盾（引 fact id + 章:行））、`:138-177`（合并去重 + 内容标签全书覆盖检查 + 每幕边界出 Mermaid 关系图给**人**看、"never injected into any prompt"）、`:183-185`（硬上限 2 轮防无限打磨）；摘要模板活追加 `仓B:autonovel-drafting/references/fact-extraction.md:117-130`（~200 token/章，与章文件同一次 commit）
- 机制：一致性不靠全书一次喂入，靠「滚动摘要（一次构建复用）+ 4 章窗 + 入窗状态块 + 六类结构化发现 + 窗间去重合并」。
- mo-shu 映射：对标 review 技能的多章审查与「百万字后期一致性」缺口。可直接吸收：①审查窗+滚动摘要的组合使审查成本 O(窗口) 而非 O(全书)；②**N-1 约定**（审第 N 章对着入章状态，本章自身的状态变迁不算矛盾）——这是 mo-shu 机检链里"状态连续性检查"极需要的语义；③关系图给人不给 prompt（作者品味层的可视化，不进机器链路）。
- 结论：**可移植**（窗口走查 + N-1 约定 + 摘要活追加）。

### M9 五门验收 + 外科式重写 + 原子补丁（仓 B）

- 证据：`仓B:autonovel-drafting/references/surgical-rewrite.md:1-5`（"Never regenerate a whole chapter to fix slop — on a 27B that just rolls new slop"）、`:33-40`（每章预算：两轮批量重写 + 一轮确定性删并，不随 span 数量放大）、`:44-55`（重写单元=完整句子而非正则命中片段）、`:56-70`（批量重写协议：编号句子→整句替换/KEEP/DELETE，拒绝整章重写）、`:71-97`（补丁 JSON 带 expected_sha256 + 事实保全校验——替换若改变任何事实/数字/时距/因果/身份则整批拒绝，hash 不符/锚点歧义整批拒绝不改文件）、`:118-177`（五门：①机械扫描，分层 ZERO-TOLERANCE / BOUNDED / SCORE-ONLY，warning 永不阻断；②全书重复短语仅 error 级阻断且须命中本章；③句子评级门 ≤15% WEAK、0 CUT；④画像合规；⑤揭示预算合规）；候选区与门后替换 `仓B:autonovel-revision/SKILL.md:140-174`（重写产物先落 critique/candidates/cycle_N/，五门全过才原子替换正章；"an improved 1-10 score never overrides a failed gate"；门失败只走 span 级外科重写不再生成整章）；设计动机 `仓B:docs/superpowers/specs/2026-07-13-autonovel-quality-gates-design.md:19-30`（五起真实事故：校验崩溃后 agent 谎报通过并改 phase、大纲字段全缺、契约回声、第 1 章抄声纹例文 96.1% 相似度、重复门无界重写循环）
- 机制：验收=全部门通过（确定性），分数只记趋势；修 slop 只修被标记的句子，整章重生成被明令禁止（会滚动出新 slop）；补丁带内容 hash 与事实保全断言，失败整批回退。
- mo-shu 映射：与 mo-shu 机检「阻断/候选两列」高度同构（ZERO-TOLERANCE+BOUNDED 超限 ↔ 阻断；warning/domain ↔ 候选永不拦截）；「deslop 只做句级手术不做整段重写」对标 deslop 技能；sha256+事实保全校验对标追踪事务的原子写纪律。**新增可学**：「整章重生成禁令」与「每章固定重写预算（两轮+一刀）」直接防"越改越坏"。
- 结论：**可移植**（外科式重写预算 + 补丁事实保全校验 + 门禁优先于分数）。

### M10 揭示预算与 MYSTERY.md 作者专属层（仓 A + 仓 B）

- 证据：`仓A:MYSTERY.md:1-2`（"Author's Eyes Only — Not for AI agent context during drafting"，起草期不注入）；但 `仓A:gen_outline_part2.py:38-49` 大纲生成时读 MYSTERY.md（作者层信息进入大纲规划，不进正文起草）。仓 B 升级为门禁：`仓B:autonovel-foundation/references/outline-prompt.md:126`（每章字段 "Reveal budget: May reveal: [facts spendable now]; Must withhold: [facts reserved for later]"）+ 场景卡表格含 Reveal 列（:119-123）；`仓B:surgical-rewrite.md:169-175`（Gate 5：逐条枚举本章首次披露的新事实，**必须引用确切的 May reveal 条款或场景卡 Reveal 单元格**作为授权，"the chapter follows the outline" 这类泛称不算证据；未授权事实与 Must withhold 披露=阻断）
- 机制：信息差被物化为大纲字段 + 逐条授权审计，"泄密"从语义判断变成可核对的引用检查。
- mo-shu 映射：对标 `追踪/信息差.md`（知情人×读者已知登记）与伏笔悬置章距。mo-shu 的信息差是**登记表**（作者看），仓 B 把同类信息变成了**起草门禁**（逐条引用授权）。这正好补「信息差只登记不拦截」的缝——可在 write C 段机检链里加一条候选级检查：本章新披露事实是否在细纲的"可揭示"清单内（候选不阻断，呈报作者）。
- 结论：**理念可学**（揭示预算进细纲字段 + 机检候选级核对；保持 mo-shu 候选不拦截宪法，不做仓 B 的阻断门）。

### M11 自适应阈值：分数只做趋势，验收由门决定（仓 B）

- 证据：`仓B:autonovel/lib/state.py:5-10`（公式 threshold = max(floor, min(ceiling, recent_max - margin))，前 3 次warmup 用 floor）、`:18-25`（WARMUP 3 / WINDOW 10 / 各维 floor-ceiling）、`仓B:autonovel-drafting/SKILL.md:188-191`（"compute the 1-10 trend score ONCE … acceptance is gate-based"，SKILL.md frontmatter "thresholds are trend signals only"）；`仓B:autonovel/SKILL.md:93-94`（"state.py — adaptive threshold computation (thresholds are trend signals only; acceptance is gate-based)"）
- 机制：滑窗内最高分减 margin 得动态阈值，防"单次弱开场把杆永久钉死在地板"；同时把 LLM/机械评分整体降级为趋势信号，验收完全由确定性门决定。这是仓 A「评分当门（6.0/7.5 硬阈）」在 27B 本地模型上的失败教训转化（对照 design doc 五事故）。
- mo-shu 映射：build Phase B evaluator 打磨环可用此思想——评分只用于决定"继续磨还是收敛"，不作为接受/拒绝单章的门；接受由作者定稿 + 机检阻断列决定。
- 结论：**理念可学**（趋势信号化）；其动机（本地 27B 不可复现）对 mo-shu 不成立但哲学一致：不可复现的信号不做门。

### M12 声纹双层结构 + 定量指纹（仓 A）

- 证据：`仓A:voice.md:1-16`（Part 1 护栏=全声线通用永久；Part 2 本书声线=地基期发现生成）；发现流程 `仓A:program.md:169-179`（写 5 段不同 register 试笔→评估→选优→范例+反例）；`仓A:voice_fingerprint.py:1-8`（"Measures the things the voice doc says SHOULD be true and checks if they ARE"）、`:21-52`（三大词汇井：musical/trade/body，逐章统计）；消费 `仓A:gen_brief.py:64-85`（brief 内嵌声纹规则节）
- 机制：护栏与书声分离（护栏不随书变）；声线不是描述性文档而是可对照检验的断言集（词汇井命中率、句长 CV 等逐章量化）。
- mo-shu 映射：对标 style（文风样本/拆书）与 deslop。可学：①「声纹文档=可检验断言」——style 技能的文风卡若带词汇井/句式断言，机检可量化对照；②范例+反例成对出现。
- 结论：**理念可学**（声纹断言化 + 词汇井量化；具体词表自建不抄）。

### M13 可组合类型包与故事契约（仓 B）

- 证据：`仓B:autonovel/SKILL.md:115-126`（genre_context/resolved.json + compiled/ 任务包 + patterns.json）；53 个 manifest（实测）；故事契约 `仓B:autonovel-foundation/SKILL.md:53-101`（七节结构的 create-once 决策记录：主类型与主引擎/副包及角色/读者承诺/组合方式/必需回报/受众约束/明确拒绝的方向；**硬上限 1500 估算 token，超限重生成不截断**；常规迭代复用不重建）；确定性解析 `仓B:autonovel/lib/genre_resolver.py`（1026 行，指纹缓存）；包边界纪律 `仓B:docs/superpowers/specs/2026-07-13-autonovel-quality-gates-design.md`（"No validator may contain a production pack ID or genre-specific plot rule"）
- 机制：类型知识=内容包（manifest 声明、无代码），按 profile 确定性解析编译成每任务的有限上下文包；故事契约是"本书要什么/不要什么"的一次性决策记录，所有后续阶段引用。
- mo-shu 映射：对标拆文库（analyze 产物）与文风样本的引用方式。可学：①「参考包=纯内容+manifest，校验器不含包 ID」的边界纪律（对标 shared-assets 单副本与锚点引用）；②故事契约 ≈ 开书时的「主对标+承诺/排除」登记，1500 token 硬上限是很好的预算先例。
- 结论：**理念可学**（决策记录带 token 硬上限 + 内容包与校验器分离）。

## 2 DukeTwoCan 移植对照

原版（仓 A）机制 → 移植版（仓 B）保留/丢失/升级，及对 skill 形态的启示：

| 原版机制 | 移植版处置 | 细节证据 |
|---|---|---|
| run_pipeline.py 常驻编排器（顺序调用各脚本） | **丢失**——无编排进程；改为入口 skill 读 state.json `phase` 分发到阶段 skill | `仓B:autonovel/SKILL.md:56-64`；对照 `仓A:run_pipeline.py` |
| evaluate.py LLM judge 当门（6.0/7.5 硬阈） | **降级**——LLM 评分仅趋势信号，验收改为五门（确定性+语义门） | `仓B:state.py:5-10`；`仓B:surgical-rewrite.md:118-177`；`仓B:design doc:19-30`（五事故） |
| keep/discard：git commit/reset 硬回滚 | **升级**——候选目录 + 五门全过才原子替换 + 原稿留在 git 历史；门失败走 span 级手术而非再生成 | `仓B:autonovel-revision/SKILL.md:140-174` |
| canon.md（md 无 schema，全文注入） | **保留 canon.md + 新增** story_state/facts.json 事实账本（九谓词/章戳区间/伏笔注册表）与 ≤1.5k token 查询块 | `仓B:story_state.py:31-188`；`仓B:drafting/SKILL.md:80-94` |
| state.json + debts 传播债（纯 prompt 约定） | debts **丢失**；被 needs_attention 队列替代（验证器独占写入，3+ 章连停升为系统性条目） | `仓B:state.py:44-49`；`仓B:autonovel-grade/SKILL.md:44-56` |
| adversarial_edit.py / reader_panel.py / gen_brief.py 独立脚本 | **保留为 references prompt**，由 agent 在 skill 内执行；产物落 critique/（adversarial_NN / reader_panel_NN / brief_NN） | `仓B:autonovel-revision/SKILL.md:65-131` |
| apply_cuts.py 引号匹配删句 | **升级**——chapter_patch.py：sha256 锁版本 + 事实/数字/因果保全校验 + 整批原子应用 | `仓B:surgical-rewrite.md:71-97` |
| review.py Opus 双人格审查环（星级停止条件） | **未移植**——无对应物；以 consistency-pass（窗口走查）+ prose-review（人触发行级）替代 | 全仓 grep 无 review 环对应；`仓B:README.md:125-138` 技能表 |
| compare_chapters.py Elo 对战 | **未移植** | 技能表无对应 |
| gen_revision.py 整章重写 | **收缩**——整章重写仅修订阶段且过五门；slop 修复明令禁整章重写 | `仓B:surgical-rewrite.md:1-5` |
| voice.md 双层 + voice_fingerprint.py | **保留结构**，声纹例文加回声检测（防抄例文，96.1% 事故） | `仓B:validation.py`（914 行）；design doc 事故 4 |
| seed.py / MYSTERY.md / 分支隔离（branch per novel） | seed 改由入口 skill 问用户；MYSTERY 未见显式对应（揭示预算取代其大部分职能）；分支改为 workspace 每书一目录 + 目录内 git | `仓B:autonovel/SKILL.md:38-52`；`仓B:outline-prompt.md:126` |
| 外部服务：fal.ai 图 / ElevenLabs 有声 | **丢失**，改本地开源链：XeLaTeX 容器 PDF、ePub、F5-TTS 文本分块（可跳过） | `仓B:README.md:145-218` |
| 无测试 | **新增** 48 个测试文件 + evals/cases.json | 实测 `tests/` 48 项 |
| 无类型体系 | **新增** 53 类型包 + resolver + 故事契约 | 实测 manifest 数 |

**对 skill 形态被证明是「必需最小集」的机制**（对我们最有参考价值）：

1. **落盘状态机 + 入口分发**：skill 形态没有常驻进程，进度必须全落 state.json，由入口 skill 按 phase 只读分发（仓 B 用 SKILL.md 文字路由；mo-shu 用 next_step.py 只读判定——后者更符合我们"脚本做确定性"宪法）。
2. **确定性门禁取代 LLM 评分门**：移植版最大教训转化——评分只做趋势，验收靠门（阻断/候选两列与 mo-shu 机检同构）。
3. **修订产物先进候选区、过门后原子替换**：防越改越坏的最小实现，不需要 git 书仓。
4. **事实一致性最小三件套**：结构化事实账本 + 按需查询块（token 预算）+ 滚动摘要；不需要 RAG/向量/数据库。
5. **每章一次原子 checkpoint + needs_attention 队列**：与 mo-shu 追踪事务惊人同构（一章一提交、失败不阻断只登记呈报）。

## 3 与 mo-shu 差异对照

| 维度 | mo-shu | autonovel（仓 A） | 移植版（仓 B） |
|---|---|---|---|
| 定位 | 作者品味宪法：作者做品味 | 全自主（"NEVER STOP"，program.md:202） | 协作优先、可全自动（README.md:3-9） |
| 作者控制点 | 每章作者定稿；候选永不拦截 | 无作者位；评分即门；git 回滚代替品味 | grade/prose-review 人触发；主线仍可无人跑 |
| 一致性机制 | 追踪事务（每章结构化 JSON）→ 单权威 state + 派生视图；伏笔悬置章距；信息差登记 | canon.md（md、全文注入、eval canon_compliance）+ 前章尾 3000 词 + 债（无代码） | facts.json 账本（谓词/区间/幂等/原子写）+ STORY STATE ≤1.5k token 注入 + 滚动摘要 + 4 章窗走查 |
| 按需注入 | **缺口**：追踪视图无按需注入 | 无（全文注入） | **有**：query_block(chapter, subjects) + 缩面降级序 |
| 修订环 | build Phase B 打磨环（成文时）+ review 工单 | 全书完稿后 3-6 轮自动修订 + Opus 审查环 | 修订 skill 3-6 轮 + 一致性环（上限 2 轮）+ 语法终检 |
| 防劣化 | 作者定稿 + 机检阻断列 | 评分对比回滚 + 高原检测 + 审查停止条件 + 经验护栏（1800 词下限等） | 五门验收 + 候选区 + sha256/事实保全校验 + 每章两轮重写预算 + "分数不凌驾门" |
| 门禁语义 | 机检阻断/候选两列 | LLM 评分硬阈 + 机械 slop 扣分（evaluate.py:703-708 评分减扣分） | ZERO-TOL/BOUNDED/SCORE-ONLY 三层 + warning 永不阻断（同构于阻断/候选） |
| 信息管控 | 信息差.md 登记（作者视角） | MYSTERY.md 作者专属（起草不注入） | 每章揭示预算字段 + Gate 5 逐条引用授权（阻断） |
| 文风 | style/deslop 技能 | voice.md 双层 + 声纹发现 + 定量指纹 | voice 结构保留 + 例文回声检测 |
| 三层分工 | 脚本确定性/AI 语义/作者品味 | 脚本编排 + LLM 写评（模型分离防自夸，evaluate.py:32-34） | "Python owns schema validation…Markdown remains creative model output"（design doc） |
| 写作对象 | 中文网文日更（连续连载） | 英文单本成书（19-24 章后整书修订） | 同左（benchmark 20 章大纲/3 章成稿） |
| 部署 | Claude marketplace 技能包 | uv + API 脚本仓 | 手动复制 9 目录；Codex/Hermes 双栖 |

## 4 不学清单冲突核查（宪法 §6）

| 不学条目 | 冲突情况 | 判定 |
|---|---|---|
| 自动连写污染传播（无暂存无作者定稿连写） | **正面冲突**：仓 A Phase 2/3 无人值守连写+自动改稿+git 自动回滚，正是该条反模式；仓 B 主线亦可全自动 | **不学**其自治连写形态；其防劣化零件（停止条件/外科重写预算）按 mo-shu 作者定稿宪法吸收 |
| LLM 导演黑盒自治（水平 agent 通信） | 仓 A 是"确定性脚本编排 LLM"，无水平 agent 通信；仓 B 是 skill 文字路由 | 不触列；但"NEVER STOP"自治哲学不学 |
| git 书仓托管与 git 隐身 | 两仓都以 git 管小说（A 分支隔离、B 每书一 repo 每章一 commit） | **不学**；keep/discard 语义 mo-shu 已由追踪事务承担，不引入书仓管辖 |
| 多宿主适配 | 仓 B 明确 runtime-portable（Codex/Hermes/其他），手动复制分发 | **不学**（宪法列明）；其 skill 内部结构（状态机/门禁）与宿主无关，可学 |
| 外部 AI 检测器进主链路 | 仓 B LanguageTool 为外部服务（可本地容器、不可用时跳过并告警、明确禁用 LLM 语法 pass）；仓 A 依赖 Anthropic/fal.ai/ElevenLabs 付费 API | **不学**外部服务依赖；「可跳过的本地语法终检」理念可记，落地须零外部依赖（守卫纪律） |
| RAG/向量检索 | 无——事实账本用封闭谓词+token 预算查询 | 不冲突，且是反例佐证（不需要 RAG 也能做长程一致） |
| 数据库后端 | 无——纯 JSON 文件 + 原子写 | 不冲突 |
| 每章全量快照 | 无——滚动摘要 ~200 token/章 + 头尾采样 | 不冲突 |
| work_tracker 任务板 | 无——state.json 是管线状态非任务板；needs_attention 是呈报队列 | 不冲突（needs_attention ≈ mo-shu 候选呈报语义） |
| 知识治理重三件套 / 文件即真相整体重构 / Dashboard 常驻 / npx 安装器 / PreToolUse 拦截门禁 | 均无对应物 | 不冲突 |

## 5 （推断）与存疑

1. **「30 章一致」宣称未找到文本证据（存疑）**：两仓 grep 无 "30 chapter/thirty" 宣称。实测可查的宣称为：仓 A README.md:10-12 "19 chapters, 79,456 words"（bells 分支，文档宣称，未检出该分支验证）；仓 B benchmark "20-chapter outline, 3 drafted chapters, state honestly `drafting` 3 of 20"（examples/01-dying-star-expedition/sol-high/BENCHMARK_SUMMARY.md:5-8）。任务书所述「30 章一致」疑为讹传或指未检出的 bells 生产分支——按纪律记存疑，不采信。
2. **仓 A master 非干净框架（代码事实）**：多个脚本残留故事专属内容未参数化——gen_canon.py:69-70 prompt 写死 "Tonal Law / Cass's gift"；gen_revision.py:61 标题写死 "The Second Son of the House of Bells"；gen_outline_part2.py:38 读 `/tmp/outline_output.md` 且写死 17/24 章剧情；adversarial_edit.py:155 章数硬编码 1-24；build_arc_summary.py:56 硬编码 1-20、reader_panel.py:84 写死 "72,422 words across 24 chapters"。启示：框架/故事分离需要专门清理批次，mo-shu 的 shared-assets 同步纪律是对的做法。
3. **传播债无代码消费（代码事实）**：见 M1——README 的 "tracks propagation debts" 属文档宣称。
4. **（推断）**仓 A 章评的 `new_canon_entries`（evaluate.py:663）→ 追加进 canon.md 无脚本自动化，靠 agent 按 program.md:76-79 执行；可靠性等同于 prompt 约定。
5. **（推断）**仓 B 九谓词集对中文网文不够用（境界/修为/身份/契约/阵营归属等），需扩谓词；但封闭谓词集+排他作用域+章戳区间的**模式**可迁移，且扩谓词必须保持封闭（校验器才能拒绝未知谓词，story_state.py:89-90）。
6. **仓 B 一致性宣称的上限（存疑）**：窗口走查+账本机制只在其 benchmark（3 章）上验证过，20 章以上一致性无仓内实证；其设计针对 "27B/65k 包络"（consistency-pass/SKILL.md:3），对大上下文模型的必要性需另行评估——mo-shu 采纳时应以 token 预算与确定性收益为由，而非照搬其模型约束。
7. 仓 A 无 license：本报告全部为机制转述与自拟归纳，未复制其代码或 prompt 原文；仓 B 为 MIT，亦只转述机制。

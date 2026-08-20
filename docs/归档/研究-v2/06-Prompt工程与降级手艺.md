# Prompt 工程与降级手艺（补充研究 06）

> 编写方式说明：本文档由主会话综合三份源码级研究档案（R1 `DeterminFlow-Plugins-研究.md`、R2 `spark-arc-studio-研究.md`、R3 `webnovel-writer-v7-研究.md`）与 mo-shu 现状盘点（R5）整理而成。**证据等级**：标"档案转述"=研究子代理已逐行核实并带行号，原始行号见对应档案；标"综合判断"=主会话基于档案事实的落地建议。原深读子代理运行超时被终止，其范围已由本综合版覆盖。
> 研究日期：2026-08-20

---

## 1. Prompt 手艺清单（目标 ≥6 项，实收 10 项）

| # | 手艺 | 参考写法（摘录/转述） | 证据 | mo-shu 落点 |
|---|---|---|---|---|
| 1 | **section 式组装** | 笔枢 prompts.json 每个 agent 由 `sections[]` 组成，每段带 `name/content/token_estimate/cache_break/enabled/workflow_only/order`——可按段做 token 预算、启停、缓存 | R1 档案 §5.2（档案转述） | mo-shu agent 模板改"分节+每节标注预算"；大模板（architect/writer）优先 |
| 2 | **共享段复用** | `nw_importent`（"重要写作约束"，原文拼写）被多个写手 agent 复用；15 条中文禁令块 `custom_1781186638389` 与 `custom_1780919570646` 逐字相同 | R1 档案 §5.2（档案转述） | mo-shu 3 个创作 agent 重复的"参考路径规则/创作能力/禁止事项"抽共享段（F.2 已裁决方向，批 5 落实） |
| 3 | **JSON 完整性铁律** | 自审/裁决器等产出 section 末尾统一附"🔴 JSON 完整性铁律"：ASCII 直引号、不转义换行、无尾逗号、无围栏——把坏 JSON 风险前移到 prompt 约束层 | R1 档案 §5.2（档案转述） | mo-shu 所有要求 JSON 输出的 agent（explorer/extractor/observer）模板加同款铁律段 |
| 4 | **参数化占位 + 首条消息注入** | `{{变量}}` 贯穿 first_message 与 file 变量默认值；agent prompt 不硬编码任何文件路径，全部"首条消息注入"（file_structure 段反复强调"无需自行读取文件"） | R1 档案 §5.2（档案转述） | mo-shu 模板的路径一律用 `{项目根}` 等占位（现状已部分如此），禁止硬编码绝对路径 |
| 5 | **base 占位符展平** | SparkArc `agent_utils.py` 把 yaml 顶层 `base` 递归展平为 `base.xxx` 注入（不覆盖用户显式传值），多轮替换（max 5 轮）支持二级展开；各模态用 `{base.identity}` 等引用共享片段 | R2 档案 Q1（档案转述） | mo-shu 模板共享段用"命名锚点"引用（如 base.参考路径规则），单点维护 |
| 6 | **tool reference 自动注入** | 有落盘工具的 agent 重写 `_get_tool_prompt_references()` 把产出规范挂到落盘工具的 yaml system 字段；运行时拼"当你决定调用工具 xxx 时，必须复用以下规范…" | R2 档案 Q1（档案转述）；Muse bug 教训见 05 档案错误 9 | mo-shu 无工具门面层，等价形态=**产出规范单文件+多模板引用**（批 5 的 B4 双向复用+模板单源化即是） |
| 7 | **归一化层** | SparkArc `_normalize_review_result`/`_normalize_grade`/`_clean_json_block`：等级别名容错、0-100 数字分换算、去围栏/智能引号/尾逗号——把脆弱解析隔离在薄层 | R2 档案 Q3 + 主会话 grep 闭合（`agent_critic.py:40-162,207,271`） | 批 5 已排"所有解析 LLM JSON 的脚本走归一化层"；mo-shu 落点=check_chapter_summary 等脚本共享一个 parse_llm_json 函数 |
| 8 | **边界铁律写法** | 笔枢 director"回答发生了什么为什么，不回答怎么写"；settler"永远给意图，永远不给清单，每条 ≤60 汉字"；story-planner"只定义力的性质规律，不定义在哪章落地" | R1 档案 §4.3（档案转述） | mo-shu explorer/checker 边界写死（批 6）参照此句式："你只做 X，不做 Y" |
| 9 | **模型参数按职能** | 规划/创意 temp 0.8-0.9；维护/观察/裁决 0.3；自审 0.4+top_p 0.7；整合写手 thinking_budget 4000；distributor/trimmer 关 thinking | R1 档案 §3.4（档案转述） | 已落批 4 observer（temp 0.3 关 thinking）；其余 agent 按宿主支持度列可选 |
| 10 | **同一规则双向复用** | 15 条中文禁令在写手侧=遵守清单、自审侧=15 个枚举标签（nsc_output 标签表 ↔ custom_* 规则块逐字同源） | R1 档案 §4.4（档案转述） | 批 5 的 quality-rules-shared.md 单一真源+标签版检测即此形态 |

## 2. mo-shu 3 个 agent 模板改造建议（基于 R5 模板盘点）

### 2.1 moshu-narrative-writer（现状：写+自审合一，7 Gate 内嵌）
- **改造**：批 5 两模态拆分后，按手艺 1/2/8 重排——写作模式段保持"五段输入→落盘回执→字数实测"；审查模式段引用 quality-rules-shared.md 的**标签版**（非复制全文）；共同段（身份/格式规范/禁词纪律）抽"base 锚点"。
- **依据**：手艺 10（双向复用）+ R5 §3（模板同构重复）+ SparkArc 两模态互斥（R2 Q1）。

### 2.2 moshu-consistency-checker（现状：grep-first 三步流程，只读 haiku）
- **改造**：①加"JSON 完整性铁律"输出段（手艺 3）②加 degraded 纪律段（"degraded 板块一律视为无法核实，不得断言无问题"——批 6 已排入收尾规范，此处在 agent 模板同步）③边界写死段（"你只做推理核对，不做自由检索"——批 6 已排）。
- **依据**：R5 §3（checker 输出 S1-S4 结构化）+ v7 事实审查.md degraded 纪律（R3 档案 §2.7，档案转述）。

### 2.3 moshu-explorer（现状：11 种 query_type 纯 JSON 输出，只读 haiku）
- **改造**：①边界写死段（"你只做检索"）②JSON 铁律段（已有"必须 JSON.parse 可解析、禁 code fence"，对照手艺 3 补"无尾逗号/ASCII 直引号"）③关键词打分检索优先级说明（批 6 已排：名称精确 +100/含名称 +30/词项 +5~20/软降权）。
- **依据**：R5 §3（explorer 现状）+ v7 queryKnowledge 打分（R3 档案 §2.10，档案转述）。

## 3. 异常降级三分类与 degraded 纪律

**v7 三分类**（R3 档案 §3.2，档案转述）：85 个降级点分三类——**有损**（数据缺失影响结论，进 `dto.degraded` 并先呈报）/ **良性**（可回退等价物，静默）/ **合理吞错**（预期内的非关键失败）。

**degraded 纪律原文**（v7 `roles/事实审查.md:10`，R3 档案 §2.7 转述）："若有 `degraded` 数组：该处材料读取失败过、数据可能残缺——degraded 涉及的板块一律视为「无法核实」而非「确认无问题」，不得据此断言一致。"

**mo-shu recovery-protocol.md 升级方案**（综合判断）：
- 现状 A 环境/B 状态/C 主产物/D 模型四类失败分类保留；
- 新增"读取失败≠没有数据"纪律：所有读文件失败的路径必须产出 `degraded` 标记（批 6 已排），消费方模板同步该纪律（2.2/2.3）；
- 降级点登记：mo-shu 各 skill 的读文件点按"有损/良性/合理吞错"三分法在 recovery-protocol 中列表登记（不追求 85 点全量，按热点路径优先）。

## 4. 待验证问题

1. 笔枢 `token_estimate` 字段是否被 Core 引擎真实消费（R1 待验证）——mo-shu 若做分段预算，需自定度量口径（现有 doc-budget 去空白字数即可）。
2. SparkArc 三模态的"互斥选择"对 mo-shu 的两模态拆分的映射边界：mo-shu 无聊天模态入口，两模态是否够用（批 5 已裁决够用；若未来加聊天场景需回访）。
3. mo-shu 现有 7 模板中 architect/character-designer 是否也值得 section 化——需先看其当前行数（R5 未给行数，flash 实施批 5 时实测再定）。

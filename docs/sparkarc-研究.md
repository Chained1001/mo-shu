# SparkArc Studio 研究存档

> 研究对象：[SparkArc Studio 引火AI创作台](https://github.com/lingfengQAQ/spark-arc-studio)（Agent 自主智能集群驱动的网文创作平台，Python FastAPI + LangGraph + React + 演出端）。
> 研究日期：2026-08-19。方法：3 轮并行子代理（agent 设置/创作流程/质量保障），全部机制实读代码确认。
> 本地副本：`otherMaterials/referProject/spark-arc-studio/`。
> 与 webnovel-writer 研究的定位差异：webnovel 教"工程化与防呆"（确定性机检/预算/备份），SparkArc 教"闭环与协议"（审稿工单/落盘回执/写评分离）。两者互补。

---

## 0. 项目概览

**定位**：Agent 自主集群驱动的创作平台，打通"灵感→设定→节奏→大纲→写文→校验→发布→分享→演出"全链路。核心产品理念："灵感与情感是人类创作不可剥夺的核心尊严"——三模式（你我共舞/我说你写/我写你修）由用户决定 AI 介入程度。

**架构**：8 个注册 Agent（导演/文案策划/执笔编剧/评审专家/灵感种子/设定专家/文风克隆/系统工具），LangGraph Supervisor 图编排，`.arc` 场景文件格式（文件名内嵌机器身份），StoryMemory 运行期记忆池，风格克隆集群，MCP 集成。

**与 mo-shu 的本质差异**：
- SparkArc = **机器状态机**（上下文自动组装/落盘自动校验/进度自动持久化，人只负责触发确认）+ 聊天平台架构
- mo-shu = **人肉状态机**（确定性由脚本承担、品味由作者拍板、AI 只做语义）+ Claude Code skill 架构
- 失控防护答案不同：mo-shu 用停靠点+机检守卫，SparkArc 用落盘护栏（不落盘不算完成）+状态机+预算保护

---

## 1. Agent 设置（8 个）

| Agent | 职责 | 关键机制 |
|---|---|---|
| 导演 | 唯一总入口与协调中枢，**不做内容生产**——读状态+拆任务+委派+汇总；路由决策由 LLM 工具调用自主做出（取代规则式意图识别） | LangGraph 双节点图（director/sub_agent）+ delegate_task 哨兵 + baton 接力棒 + completion_mode 三值（report_to_user/return_to_director/silent_continue）+ 团队能力概览动态注入 |
| 文案策划 Showrunner | 梗概→节拍表→大纲（Markup 文本），不写正文 | Beat 序列（pre_state/trigger/choice/post_state/reveal/knowledge_change） |
| 执笔编剧 Scriptwriter | 唯一的"笔"：正文/对话/续写/改写，.arc/novel 双态 | PreWrite 工具循环（≤4 次模型请求：调查→判断→落盘）；**落盘回执**（只输出草稿=未完成打回） |
| 评审专家 Critic | 只读审稿，无落盘工具 | 五维（structure/language/dialogue AI 味 + literary_flatness + logic_and_character），S/A/B/C/D 分级 + hits 证据化 + fix_tickets（target/edit_goal/must_keep/operations） |
| 灵感种子 Muse | 灵感碎片扩展为创意种子 | 草稿绝不进 prompt，只注入已绑定项目的灵感 |
| 设定专家 Lorebook | 世界观/角色档案/人物关系生成与维护 | `canon_boundary` 强制边界（长期 canon 归世界观/角色，最近状态归记忆池）；反注入（拒收网页/代码误输出自动重试）；关系只写长期稳定（作者确认） |
| 文风克隆 Style | 风格档案生产 + 风格问答 | UnifiedStyleAnalyzer 串行分块（30k token/块 + 块间摘要传递 + 末块合成）；风格执行卡 + 作者回避负面清单 |
| 系统工具 Utility | 内部基建：长上下文结构化压缩/附件解析 | 创作型摘要 schema（保留否决方案/未确认假设/原话锚点） |

**编排要点**：专家全部经导演中转（星型拓扑，水平自主通信是预留能力——主流模型还不具备多轮多角色长交互）；work_tracker 任务板（每 Agent 一个 JSON，协议强制：回交结果且任务板未清 → 必须先更新再委派）；三模态提示词（system 专有工作模式/chat_system 交互/pipeline_system 导演委派，工具 reference 自动注入防漂移）。

## 2. 流程架构（全链路）

**写前三圈记忆**（`build_scene_context`）：圈 1 章内最近 3 场全文（硬）→ 圈 2 前 2 章章末锚点（跨章情感）→ 圈 3 梗概+节拍表（全局线）；前置**按场景时间点过滤**的实时状态事实包（登场角色状态卡/关系/开放线索/矛盾风险/未关闭修订工单/最近 2 场摘要）。

**大纲场景契约**（细纲场景级字段）：`knowledge_before/after`（知情边界）、`forbidden_setup`（禁止提前发生）、`causal_dependencies`、`setup_refs/payoff_refs`（伏笔引用，机器可检查）。

**写后零等待记忆**：保存后确定性快照立即可见（不依赖 LLM），LLM 结构化抽取异步执行，带**来源哈希防旧结果覆盖**（`require_current_source_hash`）；同场景重写先撤销旧贡献再合并。

**上下文省钱**：prompt cache 稳定前缀（system 固定/尾部动态）+ 预算分区裁剪（protected 区块永不裁：当前场景事实包/契约/指导；按比例裁：世界观 2200 下限/大纲 2600/角色 3600/前文 5200）+ checkpoint 幂等压缩（成功才落盘）+ 工具循环后 rebudget。实测缓存命中率 ~94.5%。

**ARC 格式**：场景文件内嵌机器身份（`__spark__chap=001.scene=001.order=001001`）；`<conception>` AI 构思区（先想后写，解析器剥离不污染正文）；`[角色名]` 说话人；`<choice>` 分支逻辑。

## 3. 质量保障

**记忆池分层**：lorebook（长期 canon：世界观 Markdown/角色 XML/作者确认关系图）+ StoryMemory（运行期 8 类状态：scenes/character_states/relationships/threads/events/fact_claims/conflict_risks/quality_memory，均带 scene_id + evidence 回链）。

**审稿闭环**（最强机制）：Critic 评审 → fix_tickets 持久化为 quality_memory 工单（ticket_id/open/target 三元定位/must_keep/operations/evidence）→ **写前 compose_scene_task_pack 自动注入 open 工单** → 复审通过（PASS 且无新 ticket）时关闭同目标工单。**审稿默认关闭**（auto_review 默认 false，手动保存绝不隐式触发 Critic）。

**风格克隆 vs mo-shu 文风库**：
- SparkArc 优势：学"你自己/任一作者"的作品（比外部对标书通用）；提取深度到认知层（叙述者姿态/联想路径/情绪处理策略）；稳态 vs 高潮态语体档位；作者回避负面清单与正面特征同源产出
- SparkArc 劣势：无确定性验证（validator 未接线）、无锚点回查（脱敏短例不可溯源）、全靠 LLM 自觉
- mo-shu 优势：句长/标点数值化可验证（confidence high）、锚点逐字切片可 grep 回查、反 AI 腔与文风解耦（deslop 机器化复扫 + Gate 硬门槛）
- mo-shu 劣势：特征偏表层统计、学不了"自己作品/非对标书"

**AI 腔检测对比**：SparkArc 全部 LLM 判断（critic 五维 + validator 未接线），**无确定性 AI 腔脚本**；mo-shu 有 check-ai-patterns.js 确定性检测（blocking/advisory）+ deslop 7 Gate——mo-shu 机器化、可复扫，更优。

## 4. 与 mo-shu 的角色对比结论

**SparkArc 有而 mo-shu 缺的角色**：导演（LLM 总控——**mo-shu 不需要**，主会话确定性路由更稳）、设定管理（lorebook——学其持续性/输出纯度/关系纪律，不必然加 agent）、灵感（muse——idea-seed.md 已有对应）、文风问答（不需要）。

**mo-shu 独有**：explorer（查询）、researcher（资料）、chapter-extractor（拆书）——SparkArc 用工具面替代。

**mo-shu 角色重叠/可合并**：explorer/consistency-checker 边界漂移史（保留两个、边界写死）；architect 职责过宽（题材+世界观+大纲+钩子+弧线，对应 SparkArc 的 showrunner+lorebook 两个角色——**团队化拆分候选**）。

## 5. 可借鉴点索引（详见 `docs/学习规划.md` 第二部分 S1-S13）

S1 落盘回执协议 / S2 机器可消费修改单 / S3 三模态提示词 / S4 文风分块分析 / S5 质量工单闭环（最高价值）/ S6 写评分离 / S7 三圈记忆+场景过滤 / S8 大纲场景契约字段 / S9 任务板进度持久化 / S10 结构 stale 传播 / S11 风格执行卡+作者回避 / S12 脱敏短例 / S13 最终可见正文验收口径。

**总体结论**：SparkArc 最强的一点是**把"写前核设定→写中推逻辑→写后验质量"从人工 checklist 变成自动管道**，并用"稳定前缀保缓存命中、protected 区块保关键、成功才落盘"把上下文全面性与成本统一起来；对 mo-shu 最有价值的是**审稿工单闭环（S5）与写评分离（S6）**——补上"审完不丢、写审分离"两块拼图。

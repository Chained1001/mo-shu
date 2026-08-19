# webnovel-writer 研究存档

> 研究对象：[lingfengQAQ/webnovel-writer](https://github.com/lingfengQAQ/webnovel-writer)（Claude Code 长篇网文创作插件）。
> 研究日期：2026-08-19。研究方法：四轮并行子代理（v6 架构/v6 流程/v6 记忆检索/v7 设计文档）+ 一轮实测子代理（v7 分支 7.0.0-alpha 实际代码，733 测试实跑全绿）。
> 本地副本：`otherMaterials/referProject/webnovel-writer/`（v6 快照）、`otherMaterials/referProject/webnovel-writer-v7/`（v7 分支 clone）。

---

## 0. 项目概览与最大价值

**定位**：一套面向长篇连载的一致性系统——"让 AI 写到几百章依然记得住设定、接得住伏笔、守得住大纲"。

**双轨并存**（这是它最独特的教材价值）：
- **v6 市场版**（6.2.0）：Python + SQLite + RAG，commit 链 + 多投影读模型 + 8 skill + 4 agent
- **v7 全量重写**（7.0.0-alpha 已过 M7）：Node ESM + 文件即真相 + git 原子提交 + 可删缓存，53 命令全落地

**核心教训（v6 → v7 的自我否定）**：v6 的"commit 链 + 投影读模型"因**投影漂移**被作者自己否决（goto 回退后 next 用旧章号起草错章）；v7 转向"文件即真相 + git 原子性 + 查询时现算"。v6 病根：prompt 驱动确定性状态机模型不遵守、SQLite 派生与作者手改冲突、每章 3 subagent + 4 JSON + 多 gate 的 token 失控、Python+env+RAG 安装门槛。

**v7 宪法级产品原则**（PRD）：
1. 文件即真相（一切状态是中文 Markdown，可手改可 git diff，手改永不报错拒绝）
2. 脚本能做的归脚本、做不到的归 AI 语义判断（禁止正则硬凑语义）
3. git 隐身铁律（作者永不敲 git）
4. 可靠性来自自愈不来自门禁（宁停勿崩）
5. 精准读取、非必要不全文读
6. 作者界面零机器味
7. **定稿永远由作者敲定，系统没有任何不经作者确认就写入定稿区的路径**

---

## 1. 架构核心

### 1.1 v6 提交链（已弃用，教训价值）
`chapter-commit` → pydantic 校验 → `.story-system/commits/chapter_NNN.commit.json`（contract_refs/provenance/outline_snapshot/review_result/fulfillment/extraction/projection_status）。accepted = blocking_count>0 或 missed_nodes 非空则 rejected。五投影 writer（State/Index/Summary/Memory/Vector）独立 try/except，失败不阻断，可 retry/replay。

### 1.2 v7 文件即真相
- 定稿 = 一次原子 git commit（无中间态）；`.cache/index.db`（node:sqlite 六表）是唯一可删派生缓存
- 派生值一律查询时现算（悬久 = max_chapter − last_advanced；蓄积 = max − registered），不物化
- 缓存重建器 = 格式的参考实现（能完整重建 = 格式自洽的 CI 验收项）
- 指纹身份用 (章段起, 章段止) 不带时间戳（删缓存后确定性重算一致）

### 1.3 三类线索统一引擎（v7）
伏笔（埋下→推进→回收/放弃，悬久≈10章）/ 悬念（设下→推进→揭晓/放弃，≈10章）/ 感情线（开启→推进→修成正果/无疾而终，≈30章）。每条目一个 md（front matter + 履历 + 收尾计划）；**声明制**（章 front matter 声明"埋下 伏笔-031"，机检只查形式）；悬久预警"是提醒不是错误"。

### 1.4 信息差管理（v7）
每条一文件（知情人/读者已知/关键词）；蓄积章数报表 = "装逼打脸库存"；机检出泄密**候选清单不拦截**，两审判真伪。

### 1.5 机检/两审分工
机检只做可计数项（零 token），AI 只做语义判断；问题清单结构化 severity/category/blocking；ReviewInput 确定性 sha256 令牌防审稿漂移。

---

## 2. 流程（v6 实测 + v7 设计）

### 2.1 写章流水线（v6 六步，v7 简化）
v6：预检→刷新合同树→备上下文（context-agent 五段任务书）→起草→审查（reviewer 只返 JSON）→润色（Anti-AI 终检）→提交（data-agent 三 artifact + write-gate 三道闸 + chapter-commit 自动判定）→备份（git commit + tag chNNNN，可回滚/对比/分支）。
v7：备料（prepare-chapter）→ 起草 → 机检（mechanical-check 10 项）→ 两审（事实审查九维/编辑审四维，独立新鲜上下文，只读 ReviewInput）→ finalize（原子定稿，作者确认）。

### 2.2 审查闭环（v6 数据驱动 vs mo-shu 人工仲裁）
v6 审查嵌在写章 Step 3（强制闸门），指标落库（review_metrics）并**自动回灌下一章任务书**（"近 5 章 S1 频发维度"）。mo-shu 是写作后独立对抗流程 + S1/S2 显式过桥 + review-log 文本回灌。

### 2.3 追读力 taxonomy（v7 保留，v6 扩展）
钩子五型（危机/悬念/渴望/情绪/选择）+ 强度分级；爽点模式 8 种；微兑现 7 类；Hard Invariants（HARD-001~004 不可申诉）+ Soft Guidance（可申诉但记债务，rationale_type 7 种）。

### 2.4 记忆（v6 三套并存）
- learn 经验记忆（project_memory.json，手动沉淀，**召回弱**——只全量注入不筛选，教训）
- 结构化记忆（memory_scratchpad.json，7 桶，commit 投影自动写入，active/outdated/contradicted/tentative 四态）
- 检索（reference_search BM25 静态知识库 + RAG 向量库——v7 已明确拒绝向量）

---

## 3. v7 实际实现（7.0.0-alpha 实测）

### 3.1 完成度
53 命令全部落地（22 精准读取 + 2 写章 + 11 宿主通道 + 6 安装多书 + 6 状态机/例外 + 6 自动模式）；733 测试实跑全绿；M0-M7 台账全达成；源码几乎无 TODO。距 7.0.0 只差 beta 期活动（真模型 smoke/写 50 章/真实迁移/npm 发布）。

### 3.2 防呆与自愈（设计外新增的安全层）
- **半提交探测**：commit 失败后 `probeCommitAfterError` 用 parent/tree/message 三件套遍历 rev-list 判三态（committed/not/unknown），防"假失败→重复提交"（~60 行精华）
- **commit 成功后才清工作区**；commit 前中断逐文件回滚；commit 后收尾失败只降 warning
- git-health：陈旧锁 60s 阈值 + 删除前二次 stat 防 TOCTOU；.git 损坏只指引；网盘副本移动归档非删除；全中文输出
- **重试预算**：机检自动修复 2 轮 + 两审 2 轮；草稿 sha256 幂等；author-confirmed 单独记账；严格 schema fail-closed；定稿清章
- **契约失效传播**：契约更新 → 影响章写失效记录 → 拒用旧工件定稿
- **DTO 降级显式标记**：85 个降级点三分类（有损/良性/合理吞错），有损事件进 dto.degraded，SKILL 要求先呈报缺料
- 审稿输入令牌（ReviewInput sha256 + 契约版本绑定）、payload 路径白名单（P0 安全）、writeAtomicBatch 多文件原子写、知识来源 @sha256 追溯

### 3.3 零依赖中文统计（绕开分词难题）
- 复读：字符级 6-gram 计数 ≥3
- 新专名：`([一-龥]{2,3})(冷笑道|笑道|…)` 对话提示词启发式 + 名册排除
- 高频意象：CJK 段内 4-8 gram Apriori 分层（前 n-1 层不频繁则不数 n 层，内存有界）
- 句长：`[。！？；…]+[”』」]?` 标点分句
- 文体指纹：基线区间（闭区间齐全才建基线）+ 四维 delta（句长/句式/高频意象/高频开头）

---

## 4. 与 mo-shu 的对比

### 4.1 哲学级差异

| 维度 | mo-shu | webnovel-writer v7 |
|---|---|---|
| 真源 | `_tracking-state.json`（程序权威），Markdown 派生，手改=破坏 | 中文 Markdown，手改一等公民（relink 补登） |
| 正确性 | 乐观锁 + check 逐字重渲染比对 + 字节硬预算 | git 原子性 + 格式法律文本 + fail-closed |
| 职责 | 三层分工（脚本/AI/作者） | 责任三分法宪法化（零 token 机检/AI 语义/作者定稿） |
| 读取 | 固定 7 栏状态卡 + explorer 定点查询 | 53 命令精准读取，非必要不全文读 |
| 材料 | 具体对标书资产 + 引用视图 | 通用知识库 + 候选制（≤3 条）+ 对谈共创降级 |

### 4.2 各自独有

**webnovel-writer 有而 mo-shu 没有**：自动 Git 备份（回滚/分支）、追读力量化闭环、learn 经验记忆、章档案 front matter、线索/信息差逐条账本、机检零 token 关、契约版本守卫、缓存重建器、文体指纹漂移检测、多宿主适配。

**mo-shu 有而它没有**：拆书/对标资产体系（它无具体对标书维度）、作者真相/读者已知双视图时间线、check 逐字可验证性（它只能重建不能比对）、字节硬预算、乐观并发 revision 模式、拆文断点恢复、扫榜选材、浏览器自动化、文风独立库、去 AI 味。

### 4.3 关键结论
mo-shu 的"单一权威 + 可重放渲染 + check 校验"在形态上接近 v6 的"commit 链 + 投影"，但**恰好补上了 v6 投影漂移的缺陷**（可确定性重放 = 不会漂移），值得坚持。真正差距：作者手改可检测可补登（mo-shu 手改即破坏）、精准读取命令面（mo-shu 靠 prompt 引导读文件）。

---

## 5. 可借鉴清单

### 🟢 第一梯队（低成本高价值，建议做）

| # | 机制 | 借鉴位置 | 成本 |
|---|---|---|---|
| 1 | **半提交探测**（probeCommitAfterError，~60 行） | 每章 Git 备份的前置 | 低 |
| 2 | **机检"阻断 vs 候选"分层**（10 项字符级零依赖） | moshu-write 写后收尾前置机检关 | 低-中（~300 行） |
| 3 | **重试预算模式**（草稿 sha256 幂等 + fail-closed + 按章持久化） | 机检修复预算补幂等+持久化 | 低 |
| 4 | **git 人话化 + 健康检查**（陈旧锁双 stat 防 TOCTOU） | 备份前置 | 低 |
| 5 | **自动 Git 备份**（每章 commit + tag chNNNN，rollback/create-branch） | workflow-chapter 步骤 12 后 | 低 |
| 6 | **追读力四维标注**（hook/爽点/微兑现/硬约束） | 事务 delta 加 reading_power 字段 | 低-中 |
| 7 | **evidence 溯源链**（事务带 evidence: ["chapter:12:event"]） | 事务字段扩展（纯增不改） | 低 |
| 8 | **outline 相关性筛选**（渲染上下文.md 时细纲子串命中优先） | tracking_commit 渲染函数 | 低 |
| 9 | **实体名册 + 别名反查** | 追踪/ 名册表，commit 校验新专名 | 低 |
| 10 | **章间"悬了太久"预警**（mo-shu 已有 10/10/30 阈值） | report 轻量脚本 | 低 |
| 11 | **"候选是材料不是答案"**（建议 ≤3 条 + 未命中如实降级） | 拆书模板/技法库统一候选制 | 低 |
| 12 | **degradation 显式标记**（读文件失败防静默缺料） | 各 Stage 流程 | 低 |
| 13 | **作者友好三段式报告**（总状态/产生的文件/问题与下一步） | 各 skill 收尾 | 低 |

### 🟡 第二梯队（中成本，值得做）

| # | 机制 | 借鉴位置 | 成本 |
|---|---|---|---|
| 14 | 审查指标落库 + 趋势回灌 | moshu-review 收尾落轻量 JSON + 写前读取 | 中 |
| 15 | 信息差逐条登记 + 蓄积报表 | 时间线双视图之上加 secrets 域 | 中 |
| 16 | 本地 BM25 检索（纯本地，无 API） | moshu-explorer 增强 | 中 |
| 17 | 写前五段任务书 | workflow-chapter 步骤 3 升级 | 中 |
| 18 | 审稿令牌防漂移 | moshu-review 契约 | 中 |
| 19 | 章档案 front matter | 正文文件头（需存量迁移规则） | 中 |
| 20 | 契约失效传播（轻量版：contract_version 校验） | tracking state 加版本字段 | 中 |

### 🔴 明确不建议 / 远期

- RAG/向量检索（外部 API + 中文召回质量差，与 mo-shu 零外部依赖定位冲突）
- learn 式经验记忆（原项目自身召回弱——只写不筛=死数据；除非带细纲命中筛选）
- 自动连写污染传播（状态机复杂度大，远期）
- 知识治理三件套（单人项目偏重，可只留准入五项轻量版）
- 宿主 registry 多 CLI 适配（当下不需要）

---

## 6. 对 mo-shu 的总体启示

1. **确定性纪律是最强护城河**：能数的交脚本（零 token）、要判断的交 AI、定稿归作者——mo-shu 已有雏形，可补"机检关 + 重试预算 + 半提交探测"三块工程拼图（合计 ~400 行，零依赖）。
2. **作者手改的方向**：mo-shu 的"手改派生=破坏"与 v6 病灶同源，值得朝"手改可检测、可补登（relink）"演进（但保留 check 逐字校验作为安全网）。
3. **精准读取命令面**：把"读一段/读当前行/现算派生值"脚本化，减少 prompt 引导读文件的 token 成本。
4. **量化闭环**：追读力/审查指标落库 + 趋势回灌，让"这章写得好不好"变成可累计的数据流（但避免过度量化，S1-S4 已够用，趋势只提示不裁决）。

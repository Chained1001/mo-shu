# 规格 · 批 B21：采风 agent 化——扩展 moshu-researcher + 技能改壳

- 版本：v1.4（2026-08-24，作者裁决"采风做成 agent"）+产物数据模型+CF需求票据+五类维度+七类源+来源质量优先级+未消费机检+任务量评估+融合锚定+检索效率）
- 前置依赖：B19 已合入（技能与调用点在位）；无其他依赖。
- 依据：作者架构直觉 + 规划侧复核算错更正——采风的网页摄入为全文进上下文（5 部作品×多页面≈5-15 万 token），**命中 AGENTS.md §5 判据 2（上下文隔离的重型阅读）**；且项目初始快照即有 `moshu-researcher` agent（事实查证/素材采集/灵感搜集，CDP 优先+WebSearch 兜底，被 moshu 路由/write/review 调用），其"体系构建——参考同类作品设定"场景已是采风原始形态。**B19 现状事实核漏查了该 agent 的存在**（grep"采风"零命中即结论"无联网环节"，未查 agent 模板既有检索能力）——规划侧研究盲区，本批一并记档修正。

---

## 一、现状事实（施工前逐条复核）

1. `ls skills/moshu-setup/references/templates/agents/`——7 个模板，含 `moshu-researcher.md`（初始快照 8dfbeb8 引入）：三场景表（事实查证/素材采集/灵感搜集）、被调用协议（query/type/context/project_dir/cdp_port → JSON status + `参考资料/{topic}.md`）、model sonnet/maxTurns 20。
2. researcher 调用接线：`skills/moshu/SKILL.md:29/:89/:92`（查资料路由+查询降级）、`moshu-review/references/review-workflow.md:317`（事实核查条件 spawn）、`moshu-write/references/artifact-protocols.md:87`（参考资料产物）。
3. `skills/moshu-research/`（B19 产物）：SKILL.md + references/caifeng-methods.md——检索/提取当前在**主线程内联执行**（无 agent spawn）。
4. `skills/moshu-build/references/workflow-build.md` 三处 `/moshu-research` 调用点（:208/:312/:376 区域）。
5. agents_version=31（UPGRADING.md 权威；9 文件字面量，v31 bump 先例在 B 发版 commit）。
6. 守卫：`check-agent-template-rules`（禁互引/挂载存在/单副本）、`check-agents-version-sync`（全 skills 一致）。

## 一·五、采风产物数据模型与生命周期（v1.1 补强）

- **文件（CF 需求票据制，v1.2）**：`设定/采风-CF{NNN}-{类型}-{主题}.md`——**一文件一需求**；CF 编号在需求产生时登记台账「采风需求」行（CF-{NNN}｜需求描述｜状态：进行中→已回→已消费/已取代），spawn prompt 携带、文件名自带、元数据头记录——**并发采风按 CF 对号入座**；重采=新 CF（台账标「取代 CF-XXX·原因」）。编号递增：ls 设定/采风-CF* 取 max+1。
- **六节结构**：①元数据头（类型/主题/**触发需求**[哪一步·喂哪个字段]/本书语境[spawn context 原文]/日期/执行者[agent 或 fallback]/**版本/状态**[未消费｜已消费｜已被 vN 取代]）②来源清单（作品/媒介/URL/访问日期/占比）③要素表（类型专属字段）④来源专有名词清单 ⑤转译三问初答（机制类）⑥**融合与消费记录（主线回写）**：融合四步结论/消费去向[喂了哪个产物哪个字段]/作者过目[角色类必填]。
- **类型（五类，v1.2）**：结构/角色/设定机制/**情节**（桥段·名场面·情节装置——如「主角突破反俗套」）/**情绪**（情绪节拍·催泪燃点设计）。边界：文笔归 moshu-style；场景描写归 researcher 既有素材采集场景（写作期）。
- **源（七类，v1.2）**：网文/名著经典/影视剧情/漫画·动漫剧情/游戏/真实事件/历史事实。**真实事件采风需改编脱敏**（借结构与冲突模式，真实人物细节必须改编）；历史事实与事实查证分界：采风借事件结构，查证管内容准确性。
- **来源质量优先级（v1.3）**：要素断言可信度按来源分级——**专业分析/创作方法论（编剧课/写作技法文/文学评论）> 权威百科/官方资料 > 平台页面/榜单 > 个人评论/读后感**；要素表高优先级来源的关键发现可在占比披露旁标注来源级别；**名著源的结构分析走文学评论/解读文章**（名著无榜单书评生态，搜索加「解读/分析/文学评论」关键词）。
- **取代关系**：需求级（台账 CF 行标注），文件不覆盖不追加。
- **下游消费映射**：build 步骤读元数据.触发需求+融合记录（判断时效性）+要素表；融合四步读要素表；check_outline 读专名清单（通配全文件）；作者过目读全文件（角色类强制）；台账记采风完成+消费回写附注。
- **融合锚定表（v1.4，字段锚定融合）**：采风类型×验证方法论×大纲落点三方锚定——结构→势力场设计/中点假胜败/八节点→骨架表八列/势力场总览/暗线层次表；角色→九维/三层标签反差/升级绑弧光/主题卡→四件套/角色一页/弧线六阶段；机制→转译三问+代价边界→力量体系/核心设定表；情节→beat-cards/单元卡章功能→剧情单元卡；情绪→情绪引擎/弧线六阶段/期待感管理→每卷情绪基调/情绪引擎段。
- **融合时点双模式（v1.4）**：写前取材（设计字段前读要素表，pull）与写后校验（字段写完用要素表反扫功能位缺口，check）均合法——caifeng-methods 融合四步注明两种入口。
- **功能位清单回写（v1.4）**：消费记录的融合结论必含「借鉴功能位清单」——借了哪几个功能位、各自转译成了什么（融合可审计）。
- **检索效率四件套（v1.4，移植 gpt-researcher 架构模式，模式级借用不引代码）**：①检索计划先行——需求分解 2-4 个角度查询再动手（防单查询失败）；②两段式——广度找候选源（只看标题摘要）→top 3-5 深度抓取；③源去重——同作品的多视图（百科/词条/书评）算一个源；④引用强制（已有：无来源 URL 丢弃）。落 caifeng-methods「检索策略」节并标注来源。
- **明确不做**：过期自动判定不做脚本（无确定性判据）——触发需求字段供 AI/人工判断；采风是项目快照不是资产库。

## 二、设计总纲

**技能做壳，agent 做芯**：moshu-research 保留交互门（consent/类型确认/作者过目）+ 融合四步（主线消费报告）；检索+蒸馏下沉给扩展后的 moshu-researcher（采风任务类型）；**现内联路径降级为 fallback**（agent 不可用时主线程执行，一行不废）。

## 三、文件级改动清单

### A. `skills/moshu-setup/references/templates/agents/moshu-researcher.md`（扩展）

1. **新增「采风研究」场景段**（置于既有三场景表后，自包含）：
   - 五类型表：`结构采风`（输入题材关键词+本书方向；检索同题材热门 3-5 部的百科/词条/目录标题/书评——只取元数据层）/`角色采风`（输入角色需求描述；检索类似角色词条/人设分析——只学结构功能位）/`设定机制采风`（输入机制需求；机制解析文章+同类设定比较）/`情节采风`（输入桥段需求如「主角突破反俗套」；名场面/桥段手法/情节装置分析）/`情绪采风`（输入情绪目标如「让读者哭的情节组合」；催泪/燃点/憋屈节拍设计分析）；**源七类**（网文/名著/影视/漫画动漫/游戏/真实事件/历史事实——真实事件需改编脱敏）；
   - **采风专属纪律（加粗，区别于事实查证的"可取正文"）**：①**小说正文不取不复述**（事实查证可引制度/历史正文内容，小说类作品的正文/章节内容一律不取——只取简介/标签/百科/目录标题/书评/解析文章）；②**每个要素标注来源 URL**（无来源的要素丢弃——防编造，blocking 纪律）；③产出含**来源专有名词清单**与**各来源占比披露**；④设定机制类附**转译三问初答**（动力源/获取方式/社会结构适配）；
   - **产物落盘**：`{project_dir}/设定/采风-{结构|角色|机制}-{主题}.md`（区别于事实查证的 `参考资料/`）；文件含要素表+来源清单+专名清单+占比+转译初答；
   - 输出 JSON 扩展：采风任务时 `research_file` 指向采风产物，`type` 取 `caifeng-structure|caifeng-character|caifeng-mechanism|caifeng-plot|caifeng-emotion`。
   - **frontmatter 任务量评估（v1.3）**：既有 `maxTurns: 20` 为单查询事实查证所调；采风为多源交叉（3-5 源×多页），施工时将模板 maxTurns 提至 **30** 并在头注注明「采风多源交叉场景上调」；`model: sonnet` 维持（施工后如实测不足再议）。

### B. `skills/moshu-research/SKILL.md` + `references/caifeng-methods.md`（改壳）

2. SKILL.md 入口流程改写：交互门（不变）→ **spawn moshu-researcher**（部署检查 `.claude/agents/moshu-researcher.md` 存在 + 非子代理上下文）→ 读回采风产物 → 主线执行**融合四步** → 角色类**作者过目停靠**；
3. **spawn 契约成文**（SKILL.md 调用协议段）：prompt 必含 `type`（caifeng-*）、`query`（检索需求：题材关键词/角色需求描述/机制需求）、`context`（**本书语境一段摘要**：题材+主角+当前步骤+要喂给哪个字段）、`project_dir`；产出去向与融合衔接；
4. **fallback 成文**：agent 不可用（未部署/子代理上下文/spawn 失败/联网缺失）→ 主线程按 caifeng-methods 内联执行原检索流程（标注 `Fallback: researcher unavailable -> inline`），降级声明照旧；
5. caifeng-methods.md 头注更新：检索执行的权威路径是 researcher agent（本文件定义方法本体，agent 与主线 fallback 共用）；融合四步归主线。

### C. 版本与部署

6. **agents_version 31→32**：UPGRADING.md 版本头 + v31→v32 变更条目（moshu-researcher 模板新增采风研究段）；9 文件字面量同步（历史条目不动，v31 bump 同款操作）；deploy-manual.md 字面量同步。
7. moshu-research SKILL.md 版本 1.0.0→1.1.0（行为变化：检索转 agent+fallback）；moshu-setup 1.4.1→1.5.0（模板扩展）；marketplace.json 两处同步。
8. workflow-build 三调用点**不动**（壳接口不变，调用方无感知）。
9. **产物模板落位**：caifeng-methods.md 增加「采风产物六节模板」（§一·五 的文件结构原文）；researcher 模板采风段的产物落盘说明指向该结构（模板内自含六节骨架精简版）。
10. **主线回写指令**：SKILL.md 融合四步之后加"融合结论/消费去向/作者过目结果回写采风文件「融合与消费记录」节，元数据状态改已消费"；重采流程一句（同需求重采＝新 CF，台账标取代关系）。
11. **caifeng-methods 双节增强（v1.4）**：「融合四步」节并入锚定表+双模式时点+功能位清单回写；「检索策略」节并入效率四件套（标注"移植 gpt-researcher 架构模式"）。
12. **check_outline.py 候选扩展（v1.3）**：新增 candidate——扫描 `设定/采风-CF*.md` 元数据，存在状态「已回未消费」的采风产物 → 提示「有 N 份采风产物未消费（CF-XXX…）」（candidate 永不拦截，沿用 B18 纪律；版本兼容：无采风文件时跳过）；`scripts/test-check-outline.py` 补 fixture 一组（含未消费采风 fixture → candidate 出现且 exit 0）。

## 四、禁止事项

1. agent **不做融合**（融合四步留主线）、不写构建产物（只写 `设定/采风-*.md`）。
2. 模板采风段**自包含**（禁互引其他 agent 模板——check-agent-template-rules）；不把 caifeng-methods.md 登记进 agent-references（模板内自含采风方法要点，避免 shared-assets 新组）。
3. 正文红线在模板内**与事实查证模式显式区分**（事实查证可引资料正文，采风不得取小说正文）。
4. fallback 主线路径保留不删；无来源 URL 的要素不得输出（防编造，blocking）。
5. 不动 moshu 路由/review/write 对 researcher 的既有调用（它们用的是事实查证场景，互不干扰）。
6. 实测验证归下轮（本批不做联网走查断言——守卫零外部依赖，反模式 #8）。

## 五、验收命令

```bash
grep -c "采风研究" skills/moshu-setup/references/templates/agents/moshu-researcher.md          # ≥1
grep -c "小说正文不取" skills/moshu-setup/references/templates/agents/moshu-researcher.md     # ≥1（红线）
grep -c "caifeng-structure" skills/moshu-research/SKILL.md skills/moshu-setup/references/templates/agents/moshu-researcher.md  # 各 ≥1（契约对齐）
grep -c "Fallback: researcher unavailable" skills/moshu-research/SKILL.md                     # ≥1（降级成文）
grep -c "触发需求" skills/moshu-research/references/caifeng-methods.md                        # ≥1（元数据头）
grep -c "融合与消费记录" skills/moshu-research/references/caifeng-methods.md skills/moshu-research/SKILL.md  # 各 ≥1（回写闭环）
grep -c "来源质量优先级\|专业分析" skills/moshu-research/references/caifeng-methods.md                 # ≥1
python scripts/test-check-outline.py                                                                  # 全绿（含未消费采风 candidate 新用例）
grep -c "maxTurns: 30" skills/moshu-setup/references/templates/agents/moshu-researcher.md             # 1
grep -c "融合锚定\|借鉴功能位清单" skills/moshu-research/references/caifeng-methods.md                  # ≥2
grep -c "检索计划先行\|两段式\|gpt-researcher" skills/moshu-research/references/caifeng-methods.md     # ≥2
python scripts/check-agents-version-sync.py                                                   # 32 全一致
bash scripts/check-agent-template-rules.sh                                                    # 绿
bash scripts/static-check.sh && bash scripts/check-claude-adapter.sh && bash scripts/check-story-numbers.sh && bash scripts/check-doc-budget.sh && bash scripts/check-behavior-contracts.sh  # 全绿（research 1.1.0 / setup 1.5.0 四轨同步）
```

场景走查（人工，下轮实测覆盖）：联网环境 `/moshu-research 结构采风` → spawn researcher → 产物含来源 URL 清单+专名清单+占比 → 主线融合四步照常；模拟 agent 未部署 → 主线内联执行 + Fallback 标注。

## 六、提交规范

`feat(moshu-research): 采风 agent 化——扩展 moshu-researcher 模板新增采风研究段（三类型+正文红线+来源URL防编造+转译三问初答）、技能改壳（spawn 契约+融合四步留主线+fallback 内联降级）、agents_version 31→32、research 1.1.0 / setup 1.5.0（作者架构裁决；修正 B19 研究盲区）`

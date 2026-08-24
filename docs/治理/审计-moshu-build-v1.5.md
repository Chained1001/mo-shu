# 审计报告 · moshu-build 全面审计（审计法 v1.5 首次应用）

- 审计对象：`skills/moshu-build/`（SKILL.md + 30 references + 3 scripts + 28 题材卡）
- 方法：`docs/审计法.md` v1.5 六步流程（基线 / 结构盘点 / 机制链与产消 / 一致性 / 历史回归 / 分级汇总）+ `docs/开发标准.md` v1.1 合规检查（2d）
- 纪律：**只查不改**——本报告是唯一写入；问题只呈报，修复走后续规格批次
- 日期：2026-08-24（批 B27）
- 依据：`docs/规格/批B27-moshu-build全面审计v1.4.md`；输出文件名按作者指示用 v1.5（规格 §四 写 v1.4，作者口头指示 v1.5 为准）

---

## 一、基线（Step 1）

**守卫矩阵**（9 个 python 守卫，全部 exit 0）：

| 守卫 | 结果 |
|---|---|
| static-check.py | 12/12 通过，Warn 0 |
| check-behavior-contracts.py | 15 契约通过 |
| check-capability-wiring.py | 13 能力 / 35 检查点通过 |
| check-reference-closure.py | 114 引用闭合通过 |
| check-story-numbers.py | 12 项数字口径通过 |
| check-route-write.py | 4 行路由通过 |
| check-agents-version-sync.py | agents_version=33 全仓一致 |
| check-current-skill-contracts.py | 通过 |
| check-agent-template-rules.py | 7 项规则通过 |

**回归测试**：`scripts/test-*.py` 共 16 个全部 exit 0（含 test-check-outline 八列 COMPLIANT/各 blocking 分支、test-impact-scan 正反向、test-bump-agents-version 四例含回滚、test-tracking-commit 等）。

**平台假红排除**：bash 守卫（check-doc-budget.sh / check-shared-files.sh / check-claude-adapter.sh / check-eval-scenarios.sh / check-moshu-setup-deployment.sh 等）在 Windows 沙箱被拦截（Cygwin 信号管道 Win32 error 5，非守卫本身失败）——以等价验证替代：doc-budget 用 python 逐文件非空白字符核算（见 §二）、shared-files 此前会话已全绿（76 组/111 副本）、claude-adapter 人工核对 12 插件 OK。`test-skill-numbering` 初跑 exit 2 经判因为 bash wrapper 误调（等价 `skill-numbering` 检查绿），非真红。

**预算核对**（复现命令：`python -c "import pathlib; [print(f,(pathlib.Path(f).read_text(encoding='utf-8').count(' '))) ...]"` 的非空白变体，实测）：

| 文件 | 非空白字符 | 预算 | 状态 |
|---|---|---|---|
| SKILL.md | 1659 | 1800 | ✅ 未超 |
| workflow-build.md | **24169** | 24700 | ✅ 未超（B20 预算条目记 23488，B21/B22 增量 681 未登记 _comment——见 §七 候选 13） |
| revision-workflow.md | 2239 | 2350 | ✅ 未超 |

基线结论：**全绿**，无真红。

---

## 二、结构盘点（Step 2a）

**文件清单与体量**（`skills/moshu-build/`，61 文件）：

- **入口**：SKILL.md（37 行 / 3.6 KB）
- **references**（30 个 .md，含 28 个题材卡）：
  - workflow 热路径：workflow-build.md（740 行 / 57.6 KB）、revision-workflow.md（70 行 / 5.1 KB）
  - 冷路径：cold-path.md（46 行，开新卷+Agent 调用，刻意薄）
  - 方法论 5 个：plot-frameworks.md（711 行 / 27.1 KB）、plot-special-topics.md（637 行 / 25.9 KB）、character-design-methods.md（573 行 / 27.9 KB）、plot-core-methods.md（522 行 / 19.8 KB）、outline-methods.md（362 行 / 17.5 KB）
  - 主题参考 16 个：emotional-methods（209）/ emotional-arc-design（426）/ outline-structure-theory（326）/ outline-rhythm（389）/ outline-conflict（457）/ outline-workflow（115）/ character-basics（447）/ character-relations（385）/ plot-emotion-system（368）/ opening-design（360）/ genre-core-mechanics（423）/ genre-readers（235）/ genre-writing-formulas（117）/ genre-prose-cards（91）/ beat-cards（94）/ reader-contract-and-progression（109）/ reversal-toolkit（348）/ style-genre-modules（510）/ tracking-transaction（205）/ idea-seed（75）/ naming-cards（52）等
  - 题材卡 28 个（`genre-prose-cards/`，各 ~51-53 行）
- **scripts**（3 个）：check_outline.py（363 行，机检）、impact_scan.py（152 行，修订影响分析）、tracking_commit.py（1799 行，追踪事务，shared-assets 共享）

**doc-budget 登记核对**：三入口文件均已登记（SKILL 1800 / workflow-build 24700 / revision-workflow 2350），budget=_comment 逐批记录调高理由，符合"触发即全量"判据。

**安全面轻扫**：
- `check_outline.py:97-101`：`--project` 默认 "."，`resolve()` 后 `project/"大纲"/"大纲.md"`、`project/"大纲"/"整合记录.md"`（:226）、`project/"设定"`（:305）——全部限定在项目子树内，无 `../` 穿越面【事实】
- `impact_scan.py:109-119`：`--project` required + `resolve()`，读 `追踪/_tracking-state.json`、`大纲/`、`正文/`——同限子树【事实】
- 输入解析失败三分类：`check_outline.py:33-42` `read_text` 明示 缺（文件不存在）/ 坏（UnicodeDecodeError/OSError）/ 空（空文件），读失败 exit 2 带报文明示【事实】；`impact_scan.py` 退出码 0=分析完成（空命中仍 0，非判定器）/ 2=追踪未初始化或参数/读文件错误（revision-workflow.md:21）【文档宣称→代码事实】

**冷热分离检查**（workflow-build.md 逐节引用计数，<2 次标记冷路径下沉候选——见 §八 提案 1）：

| 节 | 行范围 | 主流程引用次数 | 处置 |
|---|---|---|---|
| 交互模态规则 | 13-18 | 全流程隐含 | 热 |
| 构建台账与进入规则 | 20-77 | 三入口必读 | 热 |
| 方法论副本索引 | 79-96 | 0 显式（承载 static-check 可达图 Warn 0） | **冷候选**（含 0 引用，但有守卫耦合） |
| 流程总览/六步定义 | 100-165 | 全流程 | 热 |
| Stage 1-6 | 169-649 | 全流程 | 热 |
| 自动步的打断与恢复 | 653-660 | 1（流程规则 3 隐含） | **冷候选** |
| 停靠选项的级联说明 | 662-673 | 1（:319 显式） | **冷候选** |
| 开新卷 | 675-677 | 冷路径指针（已下沉） | ✅ 已冷 |
| 卡片按需加载清单 | 679-691 | 1（:540 显式） | 边缘 |
| 浮现记录机制 | 695-708 | ≥2（:76/:460） | 热 |
| 定稿与 artifact 创建 | 712-721 | 1（:579 显式）+ 操作关键 | 边缘（不可下沉，操作核心） |
| Agent 调用 | 727-729 | 冷路径指针（已下沉） | ✅ 已冷 |
| 与现有机制的关系 | 730-740 | 0 显式 | **冷候选** |

---

## 三、引用内容抽检（Step 2b）

**热消费深读**（outline-methods.md / character-design-methods.md / plot-emotion-system.md，子代理深读 + 本人抽验）：

1. **旧 Phase 称谓矛盾（4 处，本三文件）**：
   - outline-methods.md:3「Phase 3 建大纲时加载」→ v3.0 应为 Stage 2/6【事实】
   - outline-methods.md:11「开书 Phase 1 前置收敛」→ 应为 Stage 1 前置【事实】
   - character-design-methods.md:365「开书 Phase 1 后、角色建档时」→ 应为 Stage 3【事实】
   - character-design-methods.md:396「Phase 3 卷级大纲/卷纲定人物弧线时」→ 应为 Stage 3/6【事实】
   （全 references 层面共 ~15 处/8 文件，见 §七 候选 3）
2. **引用不可达（2 处，closure 守卫静默放过的盲区）**：
   - outline-methods.md:29 引用 `artifact-protocols.md`——build 侧 `references/` 不存在，仅 `skills/moshu-write/references/` 有【事实】
   - outline-methods.md:30 引用 `volume-review.md`——同上，build 侧裸名解析失败【事实】
   （closure 的"非资产宇宙忽略"规则会静默放过此类提及——审计法 v1.5 明列的 CI 盲区，只有人查能抓）
3. **苏格拉底格式**：
   - 完整符合（范例节）：舞台与规则设计（outline-methods.md:341-362，5 问 ≤5 + 「答不出说明设计未完成」:345 + 反面清单:358-362）、升级绑弧光（character-design-methods.md:552-573，3 问 + :558 + 反面清单 :564/:570-573）【事实】
   - 部分符合：势力场设计（outline-methods.md:323-340，主体为清单式"三条设计法":327-331，仅一条问句⑥:333-334 且编号从⑥孤立——①-⑤在 B16 总览表）【事实】
   - 不完整：情绪低压电路（plot-emotion-system.md:41，有调剂密度问句 :51 但无「答不出」等价措辞、无反面清单）【事实】
   - 覆盖统计：5 个方法论文件中仅 outline-methods（4 处）/ character-design-methods（3 处）含苏式句；emotional-methods（11 问句 0 苏式）/ plot-core-methods（9 问句 0 苏式）/ plot-frameworks（5 问句 0 苏式）【事实，本人复跑】
4. **模板填空式**：三文件均无 `{____}` 填空模板（多为已填充表格/清单）——与 workflow-build 的填空式（骨架表 :302 中点列、卷末跃迁列）互补，方法论文件本身以问句/清单承载，不构成缺陷【事实】
5. **体量与重复**：
   - 跨文件重复（反模式 #4 风险）：六种爽点类型（outline-methods.md:298 vs plot-emotion-system.md:130-139）、倒推法（outline-methods.md:294-298 vs plot-emotion-system.md:141-146）【事实，子代理发现、本人抽查确认行号】
   - 同文件概念相近：plot-emotion-system 误解卡（:232-235）vs 误会制造拉扯法（:281-298）【事实】
   - 体量异常：plot-frameworks 711 行（>700 候选瘦身）；cold-path.md 46 行（冷路径刻意薄，非空壳）；其余无 <50 行异常【事实】

**通用性四问**（对三节逆向萃取 + 身份行为论抽检，子代理 + 本人复核）：

| 节 | 定位 | 四问 | 苏格拉底有效性 | 回退路径 |
|---|---|---|---|---|
| 势力场设计 | outline-methods.md:323-340 | **未过**（①过，③临界，②④不过——无势力场题材用不上且无豁免） | 强制（:333-334 借力桥段落位问，答不出单元卡编号=非设计） | **无显式豁免**（对比舞台节 :343 有「整节可跳过」） |
| 升级绑弧光 | character-design-methods.md:552-573 | **基本过**（②临界，弱绑定回退兜底） | 强制（:562 升阶后新行为，反标签括号） | 有（:566-568 弱绑定回退） |
| 舞台与规则设计 | outline-methods.md:341-362 | **基本过**（③临界） | 强制（:348 具体限制，反"有挑战"标签） | 有（:343 整节可跳过） |
| 身份行为论 | plot-special-topics.md:341-379 | **未过**（①过，②③④临界） | **不够强制**（:349「主角等级够不够格」二元门闩，2 字可答） | 有条件（:374/:361-368），无整节豁免 |

**过时信号全扫**（`workflow-setup|Phase [123]|旧版|已废弃`）：命中全部为上述 Phase 称谓残留（§七 候选 3）与 workflow-build:5 的 v3.0 重构历史注记（合理用法）【事实】。

**苏格拉底问句有效性抽检（workflow-build 指引块，本人模拟回答）**：
- 主题论证问句（:305）「这一卷对主题主张是辩护还是质问？」→ 模拟回答「辩护」（2 字标签可答）→ 不够强制（候选·低；该问句语义是强迫二选一表态，设计决策本身即标签，深度依赖后续「质问也是推进」语境）
- 暗线层次问句（:307）「我的暗线选哪几层、各层何时揭」→ 模拟回答「外部阴谋」（4 字标签可答前半，但层次表揭示卷列强制后半）→ 部分强制（候选·低）

**标签消费检查**（2b/3b 交叉）：停靠 1/2/3 的 卷行总览（workflow-build:476-479/:609-613）明确「只展示不落盘——改字段回源文件」「AI 语义拼装不写脚本」——展示层有真相源纪律，未发现标签消费（填"直面共鸣"四字而无实质）型缺口【事实】；观察 011（test2-4 实测）「十批建设全部字段被正确消费，零空转」互证【文档宣称，test2-4 实测记录】。

---

## 四、机制链表（Step 3a）

### 链 1：开书构建 Stage 1→6 —— **闭合**
- 正常：SKILL.md:23 入口 → workflow-build 开书构建；进入规则先读台账（:20-26，缺台账开书→轮 4 创建最小台账 :25）；四轮式开场（:201-243）→ Stage 1 核心设定落盘（:178-179）→ Stage 2 骨架+停靠 1（:280-372）→ Stage 3 自动（:376-418）→ Stage 4 单元+停靠 2（:422-509）→ Stage 5 自动（:513-562）→ Stage 6 定稿+停靠 3（:566-649）→ 定稿与 artifact（:712-721）→ tracking init【事实】
- 异常降级：缺台账 ✓（:25-26）；**缺理想书评无显式降级路径**（轮 3 必做 :178/:227-233，停靠 1/2/3 对照依赖 :362/:463/:636，流程未写明缺失处置，check_outline REQUIRED_SECTIONS 亦不含理想书评）→ (推断) 候选 11；中途关窗 ✓（流程规则 3 收尾必结 :74 + 自动步打断恢复 :653-660，台账纯 Markdown 快照幂等可恢复）【事实】
- 人机分工点：档位选定（:165）、停靠 1/2/3 主选择（:367/:504/:642）、理想书评作者改定（:178）——齐备【事实】
- 交互模态一致性：13 个交互点逐一核对（轮 1 定调对话 :204-207 / 参考书弹窗 :208-212 / 采风默认执行+跳过 :213-218 / 轮 2 批弹窗 :220-226 / 轮 3 对话 :227-233 / 轮 4 弹窗 :235-240 / 停靠 1/2/3 弹窗 / 修订裁决弹窗 revision-workflow:25 / 开新卷候选弹窗 cold-path:26）——行为全部符合三规则【事实】；**但交互模态规则节（:13-18）仅列 4 条，缺「过程性→默认执行+跳过」规则陈述**（行为已实现于 :213，规则节未收口）→ 需修 1

### 链 2：采风→researcher→融合→Stage 2 —— **闭合**
- 正常：轮 1 采风默认执行（workflow-build:213-218，声明+可跳过+spawn+过目+融合四步本 Stage 内执行）→ moshu-research SKILL.md:20-30（入口流程：交互门→spawn→融合→过目；融合四步 :30）→ 产物 `设定/采风-机制-*.md`（:321）/ `采风-角色-*.md`（:386）/ CF 票据 → check_outline B19/B21 candidate 比对（check_outline.py:304-333）【事实】
- 异常降级：用户跳过→降级声明进台账（:215）；agent 不可用→主线程 fallback（cold-path.md:39）【事实】
- 判定：闭合（含双降级路径）

### 链 3：修订→impact_scan→裁决→落盘→stale→消化→构建态 —— **闭合**
- 正常：SKILL.md:34 → revision-workflow.md 五步（① impact_scan 三清单 :15-21 → ② 作者裁决 AskUserQuestion + 红线三条显式确认 :25-28 → ③ 变更日志 append-only :32-39 → ④ stale 级联标记 :43-51 → ⑤ stale 消化闭环翻回定稿 :55）【事实】
- 回流入口：审查工单 review_tickets.py list + 追踪连贯性风险/信息差冲突（:57-64，不新开管线）【事实】
- 异常降级：impact_scan exit 2 追踪未初始化明示（:21）；缺台账→提示先创建（workflow-build:26）【事实】
- 字段级吻合：三清单（未写细纲章号 > last_committed_chapter / 已写正文 ≤ / 追踪四域）与追踪 state 字段对齐（impact_scan.py:119）【事实】
- 判定：闭合

### 链 4：开新卷（cold-path）—— **闭合**
- 正常：SKILL.md:25 → cold-path.md 开新卷（:9-30）：卷复盘输入→候选弹窗→Stage 4 起增量→停靠 2/3→构建态 开卷中→定稿【事实】
- 异常降级：无复盘文件→询问作者直接常规开卷（:25）；首批细纲归 write（:28 边界）【事实】
- 判定：闭合

### 链 5：Stage 6 定稿→tracking init→context JSON→write 消费 —— **闭合（1 存疑）**
- 正常：停靠 3 确认（workflow-build:643）→ `tracking_commit.py init`（:719）→ 续写状态卡 7 栏 + 伏笔/时间线视图 + `next_chapter_commitments` 从单元卡「单元承诺」映射（:719）→ write 侧消费（追踪/上下文.md、chapter-core.md:211 消费变更日志）【事实】
- 字段级：next_chapter_commitments 上游字段（单元卡单元承诺，:437）真实产出 ✓
- 存疑：**tracking init 重复执行（已存在 state 时）行为未实测**——覆盖/拒绝/报错未实证 → 存疑 16

### 链 6：check_outline 机检→blocking 修→candidate 附屏 —— **闭合**
- 正常：停靠 1/2/3 呈报前必跑（workflow-build:331/:467/:601）→ check_outline.py blocking/candidate 两列（:108-109）→ blocking 先修再呈报、candidate 附屏（:331）【事实】
- 异常：读失败三分类 exit 2（:9/:33-42）；旧结构整体降级一条 candidate（:111-135）；B24 格式容错（括号注释 :184-185 / 中文量词 :195-196 / bullet 前缀 :211-212 / 括号后缀 :297）；candidate 永不拦截（:5）【事实】
- 覆盖面：必备节 a / 八列表头+非空 b-c / 中点假胜假败 d / 卷数字数 e / 四阶段占比 f / 台阶算术 g / 终局底牌 h / 整合记录伏笔闭合 i / 暗线支线 B20 / 势力场互引 j / 采风专名 k / CF 未消费 B21 / 常驻压力 l / 反转覆盖 m / 配角高光表头 B22【事实】
- 判定：闭合

---

## 五、产消对账表（Step 3b）

### 正向（产出侧，逐项 grep 全仓消费点）

| 产出物 | 消费方（证据） | 定级 |
|---|---|---|
| 理想书评（落盘 `设定/`） | moshu-write/references/idea-seed.md:33,37；workflow-build 停靠 1/2/3 对照 :362/:463/:636 | 显式消费 ✓ |
| 题材定位.md | moshu-analyze/references/deconstruction-notes.md:178；moshu-import/import-workflow.md:345 | 显式消费 ✓ |
| 关系.md | moshu-analyze/analyze-workflow.md:67；output-templates.md:521；moshu-import/character-state-reverse.md:12 | 显式消费 ✓ |
| 题材正文提示卡.md | moshu-setup/references/agent-references/genre-prose-cards.md:9,21 | 显式消费 ✓ |
| 构建台账 | moshu-research/SKILL.md:55；caifeng-methods.md:125 | 显式消费 ✓ |
| 大纲/大纲.md | moshu-import/import-workflow.md:247,250,397 | 显式消费 ✓ |
| 角色弧线 | moshu-import/import-workflow.md:260；moshu-setup/agents/moshu-architect.md:188 | 显式消费 ✓ |
| 世界观 | moshu/SKILL.md:14；moshu-analyze/analyze-workflow.md:76 | 显式消费 ✓ |
| 单元卡 | moshu-import/structure-mapping-long.md:234；moshu-research/caifeng-methods.md:112 | 显式消费 ✓ |
| 整合记录.md | check_outline.py:226-236（机检）；workflow-build:479/:613 真相源 | 显式消费 ✓ |
| 卷纲_第X卷.md | moshu/SKILL.md:14,50 | 显式消费 ✓ |
| 变更日志.md | moshu-write/references/chapter-core.md:211 | 显式消费 ✓ |

**零悬空、零标签消费**（全部达显式消费级；观察 011「十批建设全部字段被正确消费」互证【文档宣称】）。

### 反向（输入侧）

| 必需输入 | 产出方（证据） | 字段级吻合 |
|---|---|---|
| `.story-deployed` | moshu-setup/scripts/deploy.py:242-243（sentinel 写入）；消费：SKILL.md:9 入口门 + session-start.sh:64 | ✓（build 只查存在性，版本比对在 session-start） |
| 采风产物（设定/采风-*.md） | moshu-research（SKILL.md:20-30 入口流程） | ✓（workflow-build:321/:386 + check_outline:304-333 消费） |
| 卷复盘_第X卷.md | write 侧（cold-path.md:25 消费；缺复盘→降级路径） | ✓ |
| 审查工单 | moshu-review（review_tickets.py，revision-workflow:61 消费） | ✓ |
| 追踪 state（last_committed_chapter 等） | write 侧追踪事务（impact_scan.py:119 消费；build 只读） | ✓ |

反向无断裂（必需输入全部有产出方且字段吻合）。

### capability-wiring 对账

- 登记面：3 行（story-construction / build-revision / build-ledger），checks 全部命中（SKILL.md 含 workflow-build ✓、workflow-build 含 tracking_commit.py init ✓、revision-workflow 含 impact_scan+变更日志 ✓、台账行含 构建台账 ✓）——**无假登记**【事实】
- **漏登记候选**：开新卷冷路径（cold-path.md）与 check_outline 机检无 capability 行；story-construction producer 描述仍写「Phase 1 选题/对标 → Phase 2 核心设定 → Phase 3 卷级大纲」（旧称谓）→ 候选 9【事实】

### 向后兼容核对（v1.3）

- 大纲旧结构：check_outline.py:111-135 八列表头缺失时新节 blocking 整体降级为一条 candidate——存量旧项目零误伤 ✓
- 台账/卷纲纯 Markdown 无 schema 迁移面 ✓；追踪 init 幂等未实证（存疑 16）

---

## 六、填充测试结果（Step 2c）

**数据源**：大奉打更人 弧1（税银案，第 1-40 章），章节标题实证（`otherMaterials/referFile/《大奉打更人》.txt` 第 1-42 章标题）；剧情层为（推断/常识），标题层为【事实】。

### 八列骨架表（卷 1）

| 列 | 填充 | 判定 |
|---|---|---|
| 一句话（主角中心） | 穿越者许七安为救被税银案牵连的许家，用现代知识破案自证、跻身打更人（主语=主角 ✓，案件作宾语 ✓） | 填顺 |
| 主要对手（+私人纠缠） | 明面=刑部（章法层），暗面=税银案幕后主使（未露面）；纠缠=主角翻案即动其利益（附着元素 ✓） | 填顺 |
| 危机/赌注 | 实质死亡：许家满门问斩/流放——如果失败，二叔许平志与全家遭殃（死亡三类型可指认 ✓） | 填顺 |
| 中点 | 假胜：主角以诗才名动京城（第 20 章半阙七律惊大儒）以为凭才名可保家人，读者已知刑部缉拿在即（第 23 章标题实证） | 填顺（读者先知型 ✓） |
| 高潮定死 | 打更人出手「拍死我这只蝼蚁」（第 28 章标题实证）——主角获体制力量顶住提人 | 填顺 |
| 卷末跃迁 | 阶下囚→打更人：现在能做以前做不到的事——合法查案、调动打更人资源追查税银案 | 填顺 |
| 字数 | 40 章 | 填顺 |

### 势力场总览（≥3 势力成网，可借力矛盾）

许家（罪眷）↔刑部（追缉）；县衙（推理舞台，从属刑部）；打更人（救场→收编，与刑部职权博弈=**可被主角借力**）；幕后主使（利用刑部）；妖物/术士势力（第 2-5 章引入，世界真相线）——5 势力互关联成网 ✓

### 中点假胜败 / 常驻压力 / 暗线层次

- 中点假胜败：假胜（第 20 章诗才成名 → 第 23 章缉拿升级为真败前奏）✓
- 常驻压力：家族存亡（税银案追查进程=每卷结算的慢性危机：入狱→洗冤→再缉拿→打更人庇护逐级升级）+ 副压力穿越身份暴露风险（第 16 章「许七安的日记」标题实证）✓
- 暗线层次：外部阴谋（税银案幕后，读者先知=悬念）/ 主角自我认知（穿越身份，第 1 章即示，主角先知=期待）/ 世界真相（妖物背景）——四类类型学覆盖 ✓

### 残差（填不顺处，三缺分类）

- **R1（深度缺·推断·候选）**：中点填空式 `{假胜/假败：主角此时错误地相信____，但读者已经知道____}`（workflow-build:302）只支持**读者先知**语义——主角先知型中点（读者与主角同步/后知）会填出别扭内容；大奉弧1 恰好是读者先知型故填顺。查库存：outline-methods「八节点故事结构」节无独立「主角先知型中点」变体 → 属**深度缺**（充实填空式双态），非库存缺/接线缺
- **R2（深度缺·推断·候选）**：常驻压力模板例句偏个人代价型（阴德账/折寿累积，workflow-build:296），家族存亡型/身份型压力无示例；死亡三类型（:287）可覆盖家族存亡=实质死亡 → **深度缺**（示例扩展），非库存缺
- **无库存缺**（grep 方法论库未发现缺失节）；**无接线缺**（流程引用行均在位）

**结论**：五项核心模板对成功作品全部填顺——B16 骨架六要素/B20 暗线层次模板覆盖良好（正面发现）；2 处深度缺候选为充实方向。

---

## 七、一致性轻扫（Step 4）

- **版本散射专项（工具化）**：`python scripts/bump-agents-version.py 34`（dry-run）——40 处出现点全部一致（当前 33，预览 34→逐条 `33 → 34`），覆盖 8 个 SKILL.md（反引号+无反引号两格式）/ current-contract.json / session-start.sh（-lt/-gt）/ deploy-manual.md / deploy.py（DEFAULT+usage）/ UPGRADING.md——exit 0。**一致性通过**（SOP 禁止手工 grep 为唯一验证，此处用确定性工具）【事实】
- **术语表违例**：扫描命中仅「对标书」泛指用法（AGENTS.md 术语表明确允许），无违例【事实】
- **悬空引用**：closure 114 闭合（基线）——但 outline-methods:29-30 裸名引用（artifact-protocols/volume-review）不在资产宇宙内被静默放过（见 §三 发现 2，候选 4）【事实】
- **数字口径**：story-numbers 12 项通过（基线）【事实】
- **doc-budget**：三文件均未超（§一）；B21/B22 增量 681 非空白字符未登记 _comment（候选 13）【事实】
- **路由与判定表一致性**：SKILL.md:21-25 三入口表 ↔ workflow-build/revision-workflow/cold-path 三节对齐 ✓；收尾边界（:644 只提示转 /moshu-write，不即兴建议）✓

---

## 八、历史回归（Step 5）

| 已修项 | 复验 | 结果 |
|---|---|---|
| deploy.py DEFAULT 常量（观察 007/008） | deploy.py:54 `DEFAULT_AGENTS_VERSION='33'`、:55 `DEFAULT_SETUP_VERSION='1.5.1'`；bump34 dry-run 显示 deploy.py:12/:54 现已被 bump 脚本覆盖 | ✅ 无回潮 |
| session-start.sh 版本守卫 | :71 `-lt 33`、:74 `-gt 33` 在位 | ✅ 无回潮 |
| check_outline 版本兼容降级 | :7-8/:25/:111-135 OLD_STRUCTURE_CANDIDATE 整体降级逻辑在位 | ✅ 无回潮 |
| 苏格拉底问句（B25） | 舞台与规则设计/升级绑弧光 完整在位；覆盖不全归候选 7（存量未转化，非回潮） | ✅ 无回潮 |
| Stage 命名（B26「步 N」禁止） | 节头全为 Stage 1-6 ✓；但台账步列 0-5 + 「步 N」汇报口径 4 处残留（:72/:479/:613/:657）——B26 偏差 3 自记「不改列结构」+ 验收口径 `步 [0-5]` 漏字母用法 → 需修 2（**迁移残留，非回潮**） | ⚠️ 迁移残留 |
| check_outline 格式容错（观察 010，B24 修） | 括号注释 :184-185 / 中文量词 :195-196 / bullet 前缀 :211-212 / 括号后缀 :297 全部在位 | ✅ 无回潮 |
| 步 0 问句措辞/档位重复（test2-1 观察 003/004） | 四轮式开场（:201-243）替代五问式；轮 4 档位唯一化 + 方法论声明仅档位一行（:180） | ✅ 无回潮 |
| 采风默认执行（B25/观察） | workflow-build:213-218 声明+可跳过+降级进台账 | ✅ 无回潮 |

---

## 九、分级清单（Step 6）

### 阻断
**无**。

### 需修（2）

1. **交互模态规则节缺「过程性→默认执行+跳过」规则陈述**【事实】——workflow-build.md:13-18 列 4 条（封闭→弹窗/开放→对话/合批一屏/弹窗带推荐），缺 开发标准.md:87-90 三规则的第 3 条；行为已实现（采风默认执行 :213-218）但规则节未收口。修法方向：交互模态规则节补第 3 条规则陈述（与 §2.5 对齐）。
2. **0 基「步 0-5」编号违反开发标准 2.1b（禁止 0 起编号/禁「步 N」旧称）**【事实】——workflow-build.md:40-47（台账六步状态表 步列 0-5，名称列 Stage 1-6 →「步 0」=Stage 1 的 0 基映射）、:121-128（六步流程定义表 步 0-5）、:72（流程规则 1「你在步 N·XX」）、:479/:613（「待步 N 产出」）、:657（自动步打断恢复「你在步 {N}·{名称}」）；revision-workflow.md:11 同口径。节头 Stage 1-6 正确。注：**B26 迁移不完整**——B26 偏差 3 记录「台账模板六步状态表只改名称行（Stage 制）不改列结构」（步列 0-5 有意保留），且 B26 验收口径 `grep "步 [0-5]"` 漏掉「步 N」字母用法（:72/:479/:613/:657）；非回潮，属迁移残留。建议台账步列改 Stage 1-6（或删除步列）、汇报口径改「Stage N·XX」。

### 候选（13）

3. **旧 Phase 称谓残留 ~15 处/8 文件**（2b 过时信号）【事实】——outline-methods:3,11；character-design-methods:365,396；idea-seed:3,11,39,43,53；opening-design:96；outline-conflict:3；outline-rhythm:3；outline-workflow:19；genre-prose-cards:21；style-genre-modules:33,40。与 Stage 1-6 矛盾（workflow-build:5 的历史注记与 :175 moshu-scan Phase 5 为合理用法，不计）。
4. **outline-methods.md:29-30 引用不可达**【事实】——`artifact-protocols.md`/`volume-review.md` 仅 write 侧存在，build 侧裸名解析失败；closure 静默放过。修法方向：改跨 skill 路径或改注「write 侧文件」。
5. **势力场设计未过通用性四问**（②④不过）【事实】——outline-methods.md:323-340 无「无势力/单一冲突题材可整节跳过」豁免（同文件舞台节 :343 有）→ 案例残留候选；补豁免注记为优先修法。
6. **身份行为论未过四问 + 问句不够强制**【事实】——plot-special-topics.md:341-379；:349「主角等级够不够格」可 2 字二元回答 → 案例残留候选（弱）。
7. **苏格拉底格式覆盖不全**（存量未转化）【事实】——5 方法论文件中仅 2 个有苏式句（outline-methods 4 处/character-design-methods 3 处）；emotional-methods（11 问 0 苏式）/plot-core-methods（9 问 0 苏式）/plot-frameworks（5 问 0 苏式）；势力场设计部分符合（问句⑥编号孤立）；情绪低压电路不完整（无「答不出」/反面清单）。
8. **跨文件内容重复（反模式 #4 风险）**【事实】——六种爽点类型（outline-methods:298 vs plot-emotion-system:130-139）、倒推法（outline-methods:294-298 vs plot-emotion-system:141-146）双份维护会漂移；plot-emotion-system 误解卡（:232-235）vs 误会制造拉扯法（:281-298）概念相近。
9. **capability-wiring 漏登记 + 旧称谓**【事实】——开新卷冷路径/check_outline 机检无 capability 行；story-construction producer 描述用「Phase 1/2/3」。
10. **苏格拉底问句标签可答（workflow-build 指引块）**（推断）——主题论证问句（:305）「辩护/质问」2 字、暗线层次问句（:307）「外部阴谋」4 字可答；设计语义本身为强迫表态，层次表揭示卷列兜底 → 候选（低）。
11. **缺理想书评无显式降级路径**（推断）——流程必做轮 3（:178）但未写明缺失处置；停靠 1/2/3 对照依赖 :362/:463/:636；机检不含该检查。
12. **hooks-suspense 卡片待评估遗留**【事实】——workflow-build:687 ⚠️待评估。
13. **doc-budget _comment 未登记 B21/B22 增量**【事实】——workflow-build 非空白 24169（B20 条目记 23488，+681 无批注）；预算内无红，但 _comment 与实测口径脱节。

### 存疑（2）

14. **tracking init 幂等性未实证**——重复 init（已存在 state）行为（覆盖/拒绝/报错）未实测；审计不替代实测，建议实测补证。
15. **按节精读执行率未实测**——方法论副本索引纪律句（:81）与指引块节名锚点是否真的让 AI 节级加载而非整文件读入，需 test2-4 Read 日志实测评估（归 §九 提案 4 待办）。

---

## 十、性能优化与瘦身提案（只提案不施工——走后续规格批次）

### P1. workflow-build.md 瘦身（热路径 24169 非空白 / 预算 24700，余量仅 531）
冷热分离候选节（合计约 45-50 行）：
- **自动步的打断与恢复**（:653-660）——主流程仅 1 次显式引用，可下沉 cold-path.md
- **停靠选项的级联说明**（:662-673）——仅 :319 显式引用，可下沉 cold-path.md
- **与现有机制的关系**（:730-740）——0 显式引用，可下沉或压缩为一行指针
- **方法论副本索引**（:79-96）——0 显式引用，但**承载 static-check 链接可达图 Warn 0**（B4 决策），下沉需另法维持可达性（如保留链接清单但移到文件尾）
- 预期收益：下沉 45-50 行 ≈ 1500-2500 非空白字符（6-10%），预算可回降

### P2. 方法论大文件瘦身
- **plot-frameworks.md（711 行，>700 候选）**：与 plot-core-methods（522 行）/ plot-special-topics（637 行）逐节去重（§七 候选 8 已发现跨文件重复先例）；建议按节引用计数标记低频节
- **plot-special-topics.md（637 行）/ character-design-methods.md（573 行）**：同法评估

### P3. tracking_commit.py 瘦身（1799 行）
开发标准 v1.1 §5.3 已知候选（>1500 行共享脚本→拆子命令）——按 init/commit/check/query 子命令拆模块或提取共享工具函数；**待性能优化批处理**（开发标准原文即标注）。

### P4. 按节精读执行率评估（存疑 15）
方法论副本索引纪律句（:81）+ 指引块节名锚点齐备；但实际执行率需 test2-4 Read 日志实测——若节级加载执行到位，单次会话热路径加载可降至 ~10-15K 非空白；若整文件读入，24169 全量付 token 是浪费主项。**审计不替代实测**，此提案附实测任务。

### P5. shared-surface 瘦身
shared-assets 76 组/111 副本（90% references 共享）——候选评估：build 侧是否持有 write 侧才用的文件完整版（如 reader-contract-and-progression.md 为 write 权威，build 仅引用）；共享面瘦身须同步 write 侧消费点，走专门批。

### P6. 版本散射面固化（已工具化，无需新施工）
bump-agents-version.py 40 处覆盖已完备（含 deploy.py），后续只增不改机制——本项为确认性结论，不构成提案。

---

## 十一、自我推翻记录

1. **test-skill-numbering exit 2 初判真红 → 推翻为命令形态误用**：复核为 bash wrapper 误调（Windows 沙箱拦截），等价 `skill-numbering` 检查绿——非真红，不属三类已知假红，单列。
2. **「苏格拉底句覆盖 2/4 文件」初判缺陷 → 复核降级为候选（存量未转化）**：emotional-methods/plot-core-methods/plot-frameworks 的问句密度存在但无苏式句；经子代理逐节深读确认这些文件多为清单式/卡表式节（非 B25 转化目标节），属存量未转化而非 B25 后回潮——降为候选 7。
3. **填充测试初判「可能填不顺」→ 实测全部填顺**：大奉弧1 反填八列骨架/势力场/中点/常驻压力/暗线层次五项全顺，推翻初判——正面发现（模板覆盖良好），仅 2 处深度缺候选。
4. **「势力场设计」初判仅苏格拉底编号异常 → 复核升级为四问未过**：子代理复跑确认该节 ②④ 双失（无豁免/无回退），对比舞台节 :343 不对称——定级案例残留候选（候选 5）。
5. **「停靠屏标签可答」初判需修 → 复核降级候选（低）**：停靠 1 对照检查问句（:366）可 ≤5 字标签回答，但停靠本身是作者裁决点（展示内容+填空式模板已强制具体），标签回答不会空转——按 SOP「苏格拉底问句不够强制归候选级」定级候选。

---

*报告完。本审计只查不改；修复建议见 §九/§十，走作者发起的新规格批次。*

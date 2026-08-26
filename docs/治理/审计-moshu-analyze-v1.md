# moshu-analyze 技能审计报告 v1

> 依据 `docs/治理/审计法.md` v1.8 六步 + 产品文档 Ⅲ.19 维度 9/10（性能/优化）专项。对象：`skills/moshu-analyze/` 全部（SKILL.md + references×6 + scripts×3 + 新测试×2）。
> 基线：提交 `069663b`（analyze 走查修复批 C1-C8+M1）后工作区干净；守卫矩阵绿（shared-files 71 组 0 失配 / static-check 11/11 / audit-guards 50 守卫 50 在 CI 0 未接 / test-chapter-boundary 10 用例 / test-chapter-summary 10 用例 / test-merge-summaries OK）。
> 方法注记：2b 引用抽检由探查子代理深读五份 references 完成（结论经本人抽查行号核实）；2c 以 C4 行为回归（先红后绿）+ 产物消费链核验替代填充测试（管道型基建技能）。

## 一、结构与引用（2a/2b）

**体量**：SKILL.md 65 行（薄入口达成 ✓）｜references 六份 1826 行（output-templates 562 / material-decomposition 533 / analyze-workflow 300 / deconstruction-notes 270 / pipeline-ops 93 / technique-summary-sop 68，去空白字符 14.7K/12.7K/13.7K/4.2K/2.5K/2.5K）｜scripts：chapter_boundary.py 265 / check_chapter_summary.py 184 / merge-chapter-summaries.js 100（+测试×2 已迁 scripts/）。

**封闭性【事实】**：六份 references 全仓零外部引用（仅 skill 内互引）——其他 skill 只消费**落盘产物**（节奏.md/情绪模块.md=写作权威、剧情单元清单→write 对标检索、拆文报告→选题回填/import 同步）。封装优秀，无跨域耦合。

**doc-budget 注册口径不一致（→需修 N3）【事实】**：analyze-workflow.md（管道会话触发即全量加载，14.7K）**未登记预算**（json 中命中仅为 SKILL.md 条目 why 注释）；同类 import-workflow/deslop-workflow 亦未登记；对照 build 侧 workflow-build（26.7K）已登记。C1-C8 修复批对该文件的文本增量（+约 300 字符）即处于无膨胀守卫状态。修法：登记 analyze-workflow≈15500（或补口径声明「拆解会话一次性加载、小时级摊薄，不登记」——二选一须作者裁决，现状是不一致）。

**2b 抽检要点（子代理深读+本人抽查）**：五份文件角色清晰、五阶段↔管道映射一致（C3 修复后）、阈值体系自洽（AI 自检口径声明三处一致）；发现四类问题——①**Stage 2-3 P 行格式四份维护**（output-templates L195-244 / agent 模板 L120-176/289-304 / spawn prompt 压缩版 workflow:203 / 密度公式 material-decomposition:187-198——枚举已有脚本权威缓解，**样例与白描铁律仍是三份手工同步**，反模式 #4 最大活体）；②**material-decomposition L529-533 跨会话恢复节过时**（无 schema_version: 2 门槛、与 pipeline-ops:86-93 恢复步骤矛盾——照做会绕过断点续跑的 schema 门槛，→需修 N1）；③SKILL.md:56「material-decomposition 何时加载：Stage 2-5」**偏窄**（实际 2-3 语料/2-4 阈值/2-4~2-6 分块多点引用，→需修 N2）；④小双份清单（散落兜底×2 / 拆文报告清单×2 / 抽象对抗路由×2 / confidence 档位×2 / 白描铁律×3 / 阶段列举口径 L442 不一 / output-templates:332 相对路径风格）。

## 二、机制链与产消（3a/3b）

| 链 | 判定 |
|---|---|
| 管道 2-1→2-7（边界表唯一真值→黄金三章→停靠→并行摘要→聚合→设定→报告→技法） | **闭合**（C2 修复后切片消费者口径一致；停靠一问两答；断点只认 schema_version: 2） |
| agent 降级链（extractor 缺→串行；执行失败 haiku 重试→sonnet 升级→标跳过不阻断） | **闭合** |
| 硬检查门（check_chapter_summary 4 硬+1 提示；C8 后 boundary 任何模式 issue=exit 3——行为实测过） | **闭合** |
| 产消对账 | 产物全有消费方（快速预览→停靠决策物；拆文报告→2-7 前置+选题回填+import；深度拆解→--deep+2-7；节奏/情绪→write 权威）**零悬空零标签消费**【事实】 |
| import 复用管道 | 文字协议复用（不脚本耦合）——既定取舍，维持 |

## 三、历史回归（5）

B33/B34 称谓（全文件 Stage 2-x ✓）；C1-C8+M1 修复在位（本批基线即含）；爽点枚举 6v5（f49894f ✓）；agent 4 走查发现（边界表真值/检查点/停靠交互）无回潮。**无回潮**。

## 四、分级清单（6）

### 阻断：无。
### 需修（3，均小文档修）
1. **N1** material-decomposition.md:529-533「跨会话恢复」节过时且与 pipeline-ops 恢复步骤矛盾（无 schema 门槛、泛言恢复）——删该节改一行指针「恢复操作唯一权威=[pipeline-ops.md](pipeline-ops.md)」。
2. **N2** SKILL.md:56 加载指引偏窄——「何时加载：Stage 2-5」→「Stage 2-3~2-6（语料读取/质量阈值/分块策略按节加载）」。
3. **N3** doc-budget 注册口径（见 §一）——登记 analyze-workflow 或补不登记口径声明，二选一待作者裁决。
### 候选（7）
4. **C-a** P 行格式收敛：样例+白描铁律以 agent 模板为单权威（spawn 必读位），output-templates/workflow 改指针+差异注记——净减约 80-120 行双份文本（最大反模式活体，专项小批）。
5. C-b 散落情节兜底双份→output-templates 模板版改指针。
6. C-c material-decomposition:442 阶段列举口径统一（2-1/2-2/2-4/2-5/2-6 vs 2-4~2-6）。
7. C-d 小双份指针化批（拆文报告清单/抽象对抗路由→output-templates「爽点分析」/confidence 档位）。（勘误 2026-08-26：原文误写「指针到 material-decomposition」——grep 实证抽象对抗该文件 0 命中，权威在 output-templates:170，施工侧纠正、旗舰复核确认）
8. C-e output-templates:332 相对路径风格统一。
9. C-f SKILL.md description 触发与操作说明混杂偏长——触发面收紧供作者裁决（对照 setup 两触发先例）。
10. C-g 阶段 1「识别章节分隔符」节已被脚本化——加一句「已由 chapter_boundary.py 承担，本节为背景说明」定位注记。
### 存疑（1）
11. ~~check_chapter_summary 是否子进程 grep 模式~~——**已销案（2026-08-26 P-A 实测+旗舰亲验）**：单遍 Python 正则实现（read_text 一次读入+四正则遍历，subprocess/Popen 零命中），无子进程开销，不改造。

## 五、优化四维评估（专项）

**性能**：文本加载非瓶颈（管道会话一次性 14.7K+按节加载，小时级摊薄合理）。真瓶颈候选：**P-A——check_chapter_summary 若为子进程 grep 模式，改单遍 Python 正则可把千章校验从分钟级降秒级**（先实测确认实现，收益随书厚线性）；并行 5-8/批与 checkpoint 已在最优区间；merge O(n) 无优化面。
**设计**：停靠一问两答/边界表唯一真值/copy-on-consume 对标复制=三个好设计。候选：Stage 2-4~2-6「硬事实 grep 回原文」自检的半机械化辅助（candidate 级脚本，与 build 输入体检候选同类——攒一类再评估，B48 减法纪律下不单独立项）。
**架构**：封闭性优秀无需动。候选 A-2：material-decomposition「方法论域（5 阶段）」与「运维域（执行指引/分块 96 行）」混装——拆分后方法论可被未来 skill 复用且不带运维包袱（成本=一次搬迁+引用同步，收益中，低优先）。
**瘦身**：S-1 output-templates 说明文本 47%（其中约半为跨文件重复，C-a/b/d 落地即净减）；S-2 material-decomposition 冷节 60-80 行（含 N1 删除项）；S-3 deconstruction-notes 冷知识节（影视拉片/经典拆解等 ~50 行）属 B6 式定位声明资产，**建议保留加定位注记不删**。总潜力 150-200 行，非急需（按节加载模式决定瘦身收益低于 build 热路径）。

**优先级**：需修 N1/N2（随下一小批）→ N3（作者裁决）→ C-a 专项 → P-A 实测 → C-c/d/e 攒批 → A-2/S-1/2 低优先 → C-f 作者裁决。

## 六、自我推翻记录
1. 「analyze-workflow 未登记预算」初判源于 raw-text grep True——复核为 json why 注释命中，条目实不存在（grep 命中≠注册在案，又一格式变体教训）。
2. 初拟「测试位置偏差」复核时发现施工侧已按 P1 条件迁移 scripts/ 并提交（069663b）——基线核实推翻待办状态。
3. 审计报告 C-d② 初稿误写「指针到 material-decomposition」——子代理报告本正确（output-templates↔workflow 双份），本人转录失真；施工侧 grep 实证纠正后旗舰复核确认（转录类错误首例，教训：转述子代理结论时保留其行号证据链）。

*报告完。只查不改；修复建议走下一批。产物已入库本文件。*

# moshu-build 技能审计报告 v2

> 依据 `docs/治理/审计法.md` v1.8 + 产品文档 Ⅲ.19 标准。对象：`skills/moshu-build/` 全部（SKILL.md + scripts×3 + references 30 md + 题材卡 32）。前史：`审计-moshu-build-v1.5.md`（B27 时代）。
> 基线：工作区干净；static-check 11/11、shared-files 71 组 0 失配、doc-budget 绿（workflow-build 26641/26700 余量 59）。
> 方法：三探查子代理分域深读（流程权威组/大纲剧情族/人物情绪题材族）+ 旗舰抽验载荷主张 4 条（3 坐实 1 推翻）。

## 一、结构与引用（2a/2b）

**体量**：SKILL.md 37 行（全仓最薄 ✓）｜scripts：check_outline 363 / impact_scan 152 / **tracking_commit ~1799（B27 P3 拆分候选仍悬置）**｜references 30 份共 ~9700 行：workflow-build 818（热路径）> plot-frameworks 711 > plot-special-topics 636 > character-design-methods 572 > plot-core-methods 522 > style-genre-modules 510 > outline-conflict 457 > character-basics 447 > emotional-arc-design 426 > genre-core-mechanics 423…｜题材卡 32 张（抽 3 张结构完全一致 ✓）。

**副本纪律【事实，正面】**：抽查的 24 份方法论文件 build/write/setup 三方字节全一致（shared-assets 守卫有效）；BC-001~012/SC-001~006/NC-001~005 编号体系与消费方（含 write chapter-core B1 按 BC-ID 铺场景）对齐无断档；outline-workflow 双副本**已登记**（`outline-workflow-reference` 组——子代理误报未登记，旗舰抽验推翻）。

**冷热与预算**：B27 P1 的冷热下沉**已执行**（打断恢复/停靠级联/机制关系均在 cold-path，workflow-build 原位只剩指针）——历史候选闭环 ✓。但 workflow-build 818 行/26641 字符余量仅 59，预算三连调趋势（26500→26600→26700）持续；本轮修复批增量将再触预算——**收敛批（见 §四批②）是预算的真正解法**。

**挂账⑤终裁证据（architect 契约摘要）**：「契约摘要」全仓仅三处命中——cold-path:40（要求附带）/:43（定义六项内容）与 outline-workflow:113（双副本）；**architect 模板全文无任何承接段**（被调用协议仅 任务描述/文件路径/上下文摘要 三项）。判定：PRD Ⅲ.11「契约摘要随 spawn 附带」＝**要求侧事实、模板侧虚构**——单向要求未接线。另 architect 模板:6「被 moshu-write（Stage 1-3）调用」为过时称谓（Stage 1-3 现归 build）。

## 二、发现清单（分级）

### 阻断：无。
### 需修（9）
1. **N1 采风产物名断链**：workflow-build:348/:434 写「采风-机制-*.md」「采风-角色-*.md」，caifeng-methods:25 强制命名「采风-CF{NNN}-{类型}-{主题}.md」——glob 对不上；类型名三摇摆（机制/结构/设定机制，台账 :64-66 与 caifeng:76 又漏"类型"列）。**旗舰抽验坐实**。
2. **N2 同文件降级矛盾**：workflow-build:773 冷表「genre-writing-formulas｜Stage 2+4｜骨架定方向+单元按公式填｜✅纳入」vs :475/:513 及文件自身降级头注（离线兜底、禁排卷结构）。**坐实**。
3. **N3 一级/二级结构三套定义打架**：outline-methods:34-40 vs outline-structure-theory:27-44 vs plot-special-topics:276-284——三个热路径可能同载的文件对同一术语各执一套。
4. **N4 引用断锚**：workflow-build:509 引「emotional-methods.md 情绪交替模式」——双侧文件「情绪交替」**0 命中**（按节精读纪律下断锚）。**坐实**。
5. **N5 冲突裁决序分歧**：style-genre-modules:36（细纲>题材卡>文风>通用）vs genre-prose-cards:14（多"情绪/节奏权威召回"一档）——分歧随四方副本复制。
6. **N6 口径统一**：workflow-build:5/:127-136「三子节（故事/人物/对标）」vs 正文 Stage 2-5 实际五面（+设定/情绪）；:148-173 双路设计与档位表仍用「步 0-5」编号与 Stage 1-6 并存。
7. **N7 B25 残留**：outline-methods:335-336 借力桥问句「⑥」孤编号（前无①-⑤）；:296/:298 节名锚「倒推法」「爽点类型」在 plot-emotion-system 中不存在（实际「设计爽点的倒推法」「六种爽点类型」）。
8. **N8 architect 模板:6 过时称谓**（「被 moshu-write（Stage 1-3）调用」）——**agent 模板变更，修则触发 agents_version 35→36**（决策点 A）。
9. **N9 挂账⑤修法二选一**（决策点 B）：模板加契约摘要承接段（改部署物，又触发 bump）or cold-path:43 改措辞「摘要作为普通上下文供给，模板无需承接」+ PRD Ⅲ.11 行修正。

### 候选（15）
10. 双份重复 cross-ref 化批：plot-frameworks:424-487（故事本质/五幕/六幕 vs structure-theory，~64 行）、:400-421（桥段四章 vs outline-rhythm，~22）、:173-205（三层抽象三重冗余，~33）、提炼层级表（outline-rhythm:83-101 vs emotion-system）、改编法（special-topics:427-438 vs rhythm:352-357）、噱头三类型表、高潮节奏铁律——五幕已做 cross-ref 的模式推广。
11. 瘦身批（B27 P2 名单刷新）：plot-frameworks ~100 行（至 ~610）、plot-special-topics ~90-100、style-genre-modules ~145（题材卡召回规则双源 :29-75 + 市场定位重复 :395-444 + 元素拼接内部冗余 :404/:437 + 开篇重叠 :457-495）、character-basics ~90-110（反派两节合并 :74-148/:383-399 + 清单与 cdm 重叠）。
12. 苏格拉底下轮（B25 存量）：outline-rhythm（0 苏式）/plot-frameworks（0）/reversal-toolkit（0）/outline-structure-theory（0，末尾 13 项清单）/outline-conflict（1/18）。
13. 三停靠块 ~90 行同构模板抽取（workflow-build:358-413/522-578/684-746——token 成本，预算解法之一）。
14. evaluator 模板:29「character｜Stage 3 产物」类型从未被触发（Stage 3 是自动步）。
15. tracking-transaction 实为四副本（build/write/import/review），「三副本」叙事不一致。
16. outline-workflow:84 补纲「向卷纲卷尾追加单元卡」与 :5 头注「修改既有构建资产转 build」字面冲突，缺显式豁免句。
17. genre-prose-cards.md:27「九件事」与实际 12 节卡 schema 不同步。
18. emotional-methods:207-209 章节五段口径与 write 侧 writing-craft:286 现行五段名脱锚。
19. genre-core-mechanics:5/genre-readers:5 配合行未随 genre-writing-formulas 降级更新。
20. workflow-build:776 冷表「genre-prose-cards ❌不进 build」未区分 .md 索引（:187 在用）与卡片目录。
21. workflow-build:104 副本索引含 write 域 outline-workflow——与 closure 白名单「免持副本」设计意图相悖（改文本提及可撤副本，需评估可达图）。
22. 停靠块与 evaluator 模板协议**完全一致**（token/eval_type/…一一对应）——正面确认；副本索引 14 项不含 outline-methods 等 4 文件（正文可达，逃检候选）。
23. 杂项：都市高武.md:11 双「的」错字；genre-readers:100 表格疑似损坏；emotional-arc-design:69 vs :59 顶点区间轻微错位；write 侧 artifact-protocols:354「五种反转」实 7 类。

## 三、历史回归（5）

B27 P1 冷热下沉已执行 ✓；B25 苏格拉底（outline-methods/character-design-methods 在位，⑥孤编号为新残留）；B26 Stage 制（正文全 Stage，:148-173 步号残留为新发现）；B30 采风段/评审块在位 ✓；B45 称谓（references 内 Phase 零残留 ✓）。**v1.5 审计的 13 候选终态**：P1 闭环/P2 名单刷新/P3 仍悬/P6 已工具化/其余多被 B28-B30 与本轮吸收。

## 四、组批建议

- **批① build 需修批**：N1-N7（纯文档修，约 15 处）+ 视决策并入 N8/N9。预算注意：增量先内部对冲（N6 步号统一与 N7 锚修正可净减）。
- **批② 收敛与瘦身批**：候选 10+11（双份 cross-ref + 四文件 ~400 行）——workflow-build 预算的根本解法；量最大，独立批。
- **批③ 苏格拉底下轮**：候选 12（五文件方法论改造）——可与批②串行。
- 候选 13-23 攒批或随批①顺手（杂项一行级）。
- tracking_commit 拆分（B27 P3）仍悬，单独排期。

## 五、自我推翻记录
1. 子代理「outline-workflow 双副本未登记」——旗舰抽验推翻（`outline-workflow-reference` 组在位）；本会话子代理虚报第三例（64 组/抽象对抗/本次），抽验纪律持续必要。
2. N1 初判「类型名设定机制 vs 机制摇摆」——抽验发现实为「机制 vs 结构」更深摇摆（workflow-build 写"机制"、caifeng 命名写"结构"），比子代理报告更糟。

*报告完。只查不改；修复走批①起。产物已入库本文件。*

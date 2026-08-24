# 规格 · 批 B46：采风收编 build（消 moshu-research 技能壳）

- 版本：v1.1（2026-08-25 同日修订：清单新增 genre-writing-formulas 双副本项——/moshu-research 无斜杠引用为 v1.0 grep 面盲区，旗舰审核核验发现；验收 5 同步强化；同日批号 B45→B46——审核闭环批先行占用 B45）
- 版本：v1.2（2026-08-25 推送后复核修订：锚点行号实测未漂移（workflow-build :221/:224）；evals 与 doc-budget 零 research/caifeng 引用（补查面）；导读实测无技能计数字面——清单 10 相应简化；doc-budget 无 research 条目——清单 11 改为实测复核；发版顺序调整为 B46 先行——CHANGELOG 由「不动」改为随批加 Unreleased 一条）
- 依据：作者 2026-08-25 裁决。架构一致性：moshu-researcher 是 8 个 agent 中唯一被技能壳包裹的（其余全部由各 workflow 直呼）；四方消费方（build/write/review/moshu）实测无一经技能壳；技能壳独立入口为断头路（采风产物喂构建字段，写作中途改设定应走 build 修订流 impact_scan）。触发词面（采风/找参照/找类似角色）随壳移除，README 注明采风为 build 内嵌环节——作者指示「按合理的方式做」即采此口径。
- 性质：架构收编（技能删除 + 手册迁移 + 引用面收口）。**零 agent 变更、零部署物变更**（setup 侧全不动，agents_version 不 bump）。

## 一、现状事实（grep 实测；行号可能因前序批次漂移，以文字描述 + grep 结果为准）

1. `skills/moshu-research/` 仅 2 文件：`SKILL.md`（55 行）/ `references/caifeng-methods.md`（133 行）。
2. **researcher 直呼先例四方**（无一经技能壳）：`skills/moshu-build/references/workflow-build.md` Stage 1 采风段（:224 附近「spawn moshu-researcher（结构采风，CF 票据登记）」）、`skills/moshu-write/references/chapter-core.md:64`（事实查证）、`skills/moshu-review/references/review-workflow.md:317`（事实核查）、`skills/moshu/SKILL.md`（:29/:89 查资料意图）。**四方向均保留不动**。
3. `caifeng-methods.md` 活区引用仅 2 处：`moshu-research/SKILL.md`（随壳删）、`scripts/current-contract.json` artifact_contracts「采风-CF 记录」条目 anchor_docs（:84 附近）。
4. 契约条目（:73-86 附近）：`producer: "moshu-research"`、`consumer: "moshu-build"`、`fields: [CF/需求描述/状态]`、anchor_docs 两项（workflow-build.md + moshu-research 路径的 caifeng-methods.md）。
5. **build 侧零字面引用**：workflow-build / cold-path 均无 `caifeng-methods`、`moshu-research` 字样（融合四步已内联 workflow-build :226 与 :253-262 分语境表）。
6. shared-assets 无任何 research/caifeng 组（单源私有文件，B38 对账不涉及）。
7. **setup 侧零涉及**：CLAUDE.md.tmpl、agent-references、agent 模板（moshu-researcher.md 自含采风研究段，不引用技能或手册）、deploy.py、UPGRADING.md 均无 moshu-research 技能引用。
8. 文档引用面：`README.md:107`（技能表行）、`README_EN.md:108`（同行）、`docs/architecture.md:22`（mermaid 节点 `R -->|采风 / 找参照| Research[moshu-research]`）、`CONTRIBUTING.md:19`（目录树行）、`docs/新开发者导读.md:47`（动态层行；导读内技能计数与 caifeng-methods 提及另 grep 定位）。README 的 moshu-researcher agent 行（:134/:206 等）**保留**（agent 不动）。
9. `scripts/check-story-numbers.py:53/:108`：断言 README/README_EN Skills 表行数 == 实测 skill 数 → 删技能后必须同步两 README，否则红。
10. doc-budget 预算组定义在 `scripts/doc-budget.json`——moshu-research 组（若有）删除、build 路径组因手册迁入按实测调整。

## 二、设计

- `caifeng-methods.md` 迁 `skills/moshu-build/references/`（文件名不变），定位为 **build 采风环节操作手册**（检索策略/源七类/融合细则/fallback 内联流程的单一住处）。
- workflow-build 采风块加一行指针挂载手册（开发标准 §2.3：下沉须有热路径挂载点）。
- 契约「采风-CF 记录」producer 改 moshu-build（台账 CF 行由 build 主线程写），anchor 路径更新——B40 字段抽检自动跟随。
- 不动面：moshu-researcher agent（双模式照旧）、check_outline.py CF 机检（消费台账 CF 行与 `设定/采风-*`，与技能无关）、setup 全部。

## 三、文件级改动清单

1. **手册迁移**：`git mv skills/moshu-research/references/caifeng-methods.md skills/moshu-build/references/caifeng-methods.md`；文件头 :3 自引措辞改写——「本文件是 moshu-research 的操作说明书」→「本文件是 moshu-build 采风环节的操作说明书」（正文其余逐字不动；先 grep 确认文件内无其他 SKILL.md / moshu-research 字面，若有一并对齐）。
2. `skills/moshu-build/references/workflow-build.md`：Stage 1 采风段（:221-226 附近）末尾加一行指针：「检索策略 / 源七类 / 融合四步细则与 fallback 内联流程见 [caifeng-methods.md](caifeng-methods.md)」。
3. `scripts/current-contract.json`：artifact_contracts「采风-CF 记录」条目——`producer` "moshu-research"→"moshu-build"；anchor_docs 第二项路径 `skills/moshu-research/references/caifeng-methods.md`→`skills/moshu-build/references/caifeng-methods.md`。
4. **删技能**：`skills/moshu-research/` 整目录（SKILL.md + references/）。
5. `skills/moshu-build/references/genre-writing-formulas.md`（+ setup agent-references 副本，shared-assets 同步）：:4 行两处——「优先用 /moshu-research 采风获取当前热门作品的活结构」→「优先用采风（build 内嵌环节）获取当前热门作品的活结构」；同句「长篇以步 1 骨架表六要素…为准」→「长篇以 Stage 2 骨架表六要素…为准」（后者为 B33 漏网称谓，与本行同批顺带修，避免两批碰同一行）。
6. `README.md`：:107 技能表删行；:99 build 行说明补「内嵌采风（Stage 1 默认 + 瓶颈触发）」短语。
7. `README_EN.md`：:108 删行；build 行同步内嵌采风短语（英文表述对应）。
8. `docs/architecture.md`：:22 mermaid 删 Research 节点与 `采风 / 找参照` 边；若采风语义需在图上保留，于 build 节点侧注记，以图完整可渲染为准。
9. `CONTRIBUTING.md`：:19 目录树删行。
10. `docs/新开发者导读.md`：:47 动态层行改挂 build（如「动态层（B19+B21+B30）─ moshu-build 内嵌采风（五类七源 · CF 票据 · 默认执行 + 中段瓶颈触发）」，以导读现结构为准合并或单列）；实测导读无技能计数字面（v1.2），无需改计数，grep `moshu-research` 其余命中一并处理。
11. `CHANGELOG.md`：Unreleased 节「### 变更」追加一条——「采风收编 build：移除 moshu-research 独立技能（/采风 触发词随技能移除），caifeng-methods 迁 moshu-build/references 为采风手册（契约 producer+锚点同步），README 技能计数 12→11」；历史版本节零改动。
12. `scripts/doc-budget.json`：实测无 moshu-research/caifeng 条目（v1.2 复核）——无需删除条目；workflow-build 新增指针行后 **node UTF-16 口径实测复核**在 26600/构建路径组 30500（c5af5c6 口径）内即通过，超限按 §2.3 申报处理。
13. `docs/施工日志.md`：按 §4 格式追加 B46 条目（详情条目按 B45 恢复的格式写：验收摘要/偏差记录/提交）。

## 四、禁止事项

- 不动 moshu-researcher agent 模板（采风/事实查证双模式照旧）。
- 不动 check_outline.py CF 机检、不动台账 CF 表结构（workflow-build :63 节照旧）。
- **setup 侧任何文件不碰**（CLAUDE.md.tmpl / agent-references / agent 模板 / UPGRADING.md / deploy.py）；agents_version 不 bump（agent 无变化）。
- 不重构 caifeng-methods 内容、不与 workflow-build 分语境表去重（存量重复属审计候选，另行处理）。
- 不改历史记录：B19/B21/B22/B25/B26/B30/B37 等规格文件、审计报告、施工日志历史条目、CHANGELOG 历史版本节（CHANGELOG 仅允许清单 11 的新增一条）。
- 归档目录 `docs/归档/**` 零接触；`otherMaterials/` 只读。
- 失败先判因，禁止改断言变绿；与规格不符走规格 README §5 待决问题协议。

## 五、验收命令

1. `python scripts/check-story-numbers.py`（或现行 wrapper 形态）→ 绿（README/README_EN 表行数 == 11 == 实测 skill 数）。
2. `python scripts/check-current-skill-contracts.py` → 全 PASS（B40 artifact 字段抽检 anchor 存在性跟随新路径自动验证）。
3. `bash scripts/check-shared-files.sh` → 绿（B38 全量对账：搬迁后无未登记副本）。
4. `ls skills/` 计数 == 11，且与 README 表一致。
5. `grep -rn "moshu-research" --include="*.md" --include="*.py" --include="*.json" skills/ scripts/ README.md README_EN.md CONTRIBUTING.md docs/architecture.md docs/新开发者导读.md` → **零命中**（含带斜杠与不带斜杠两种形态；注意 grep 时不要用会滤掉 references/ 的过滤条件——审核核验时曾因此漏报）。
6. `grep -rn "caifeng-methods" skills/ scripts/` → 仅三处：`skills/moshu-build/references/caifeng-methods.md` 本体、current-contract.json 新路径、workflow-build 指针行。
7. `bash scripts/check-doc-budget.sh` → 绿（指针行增量在 26600/30500 内）。
8. `bash scripts/check-current-skill-contracts.py`（reference-closure 链接可达随 caifeng-methods 迁移自动验证）→ 绿。
9. 守卫/回归矩阵全绿（B44 核验基线口径；已知 Windows 平台假红项按假红清单处理并注记）。

## 六、提交规范

消息：`refactor: 采风收编 build——消 moshu-research 技能壳（四方直呼 researcher 先例统一：build/write/review/moshu；独立入口断头路裁决移除）/caifeng-methods 迁 build-references 为采风手册（契约 producer+锚点同步）/README·导读·架构·CONTRIBUTING 计数 12→11 + 规格批B46 入库`

施工日志追加 B46 行，提交后 hash 回填。

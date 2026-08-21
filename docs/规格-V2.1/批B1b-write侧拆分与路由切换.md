# 规格 · 批 B1b：write 侧拆分与全局路由切换

- 版本：v1.0（2026-08-21）
- **前置依赖**：批 B1a 已合入（build 已存在且可路由）。
- 依据：同 B1a；本子步执行 Q1（拆文件）/Q6（next_step 切换）/Q3 残余（write 侧开书职责清除）。

## 1. 目标

一句话：workflow-setup.md 拆分收尾——细纲内容重组为 write 侧 outline-workflow.md、旧文件删除、全仓引用清零、路由/判定/next_step 全局切换到 build。

## 2. 现状事实

| # | 事实 | 证据 |
|---|---|---|
| F1 | workflow-setup 剩余 write 职责段：细纲节（:184-250）、大纲锁定写作侧语义（:252）、中途补纲（:254-259）、细纲后设定补全（:267-272）、前 3 章 opening（:279）、architect 细纲批段 | 解剖表 §1.1 |
| F2 | chapter-core.md D4 段末引用 `references/workflow-setup.md` Phase 3 设定补建规则（硬依赖，本子步改指新文件） | chapter-core:149 |
| F3 | 引用 workflow-setup 的位置（施工时以 grep 全量清点为准）：moshu-write/SKILL.md（:47/83/91/99 一带）、chapter-core、artifact-protocols、doc-budget 登记（13600 开书路径组） | R3 C6/C7 + 施工 grep |
| F4 | 路由面：moshu/SKILL.md 路由表 :14（开书/写大纲→write）与判定表 :49/:52；next_step.py :138-139（开书）/​:233-234（下卷规划）→ moshu-write | R3 C2/C3 |
| F5 | README:102 路由示例已在 B1a 改 build | B1a |

## 3. 文件级改动清单

| 文件 | 改什么 | 注意点 |
|---|---|---|
| `skills/moshu-write/references/outline-workflow.md`（新） | 从 workflow-setup 迁移重组：F1 全部段落 + **增量建档边界声明**（Q7：write 只新建 `设定/` 档案，不修改既有设定/大纲文件；修改既有=转 /moshu-build）+ 开书时"设定/大纲/卷纲构建已移 /moshu-build，本文件只管细纲"头注 | 内容迁移保持原文措辞（等量迁移，不趁机改写）；doc-budget 等量登记 |
| `skills/moshu-write/references/workflow-setup.md` | **删除** | 删除前完成全部引用切换（同提交） |
| `skills/moshu-write/SKILL.md` | ①开书 Phase 描述改写为"开书/设定/大纲/卷纲 → /moshu-build（本 skill 接力细纲与写作）"；②:47 补纲路由改指 outline-workflow.md；③其余 workflow-setup 引用改指新文件 | 路由关键词（连载/回炉/重写/补纲）留 write 不动 |
| `skills/moshu-write/references/chapter-core.md` | :149 `references/workflow-setup.md` → `references/outline-workflow.md` | 一处 |
| 其余引用点 | `grep -rn "workflow-setup" skills/ scripts/ docs/architecture.md README.md` 逐个切换或清理（artifact-protocols 等以实测为准） | 清零是硬验收 |
| `skills/moshu/SKILL.md` | 路由表 :14 拆行（开书/设定/大纲/世界观 → /moshu-build；写长篇/连载/回炉 → /moshu-write）；判定表 :49 开书→build、:52 卷复盘留 write 末尾加"下卷规划转 /moshu-build" | 与 next_step/README 三方一致 |
| `skills/moshu/scripts/next_step.py` | :138-139 → "运行 /moshu-build 开书"、suggested_skill=moshu-build；:233-234 → "下卷规划（/moshu-build，消费卷复盘方向候选）"、moshu-build；:185-186 补纲与 :225-226 卷复盘**不动** | 文案与判定表同步 |
| `scripts/test-next-step.py` | 开书态/下卷态断言的 suggested_skill 与 next_action 文案同步 | |
| `scripts/doc-budget.json` | 删 workflow-setup 13600 登记；新增 outline-workflow.md（实测×1.05） | 路径组内其他文件不动 |
| `docs/architecture.md` | §3 判定图/叙述若提"开书=/moshu-write"同步 | |

## 4. 新文件设计

无独立新脚本；outline-workflow.md 为迁移重组（算法级描述见 §3 第 1 行）。

## 5. 验收命令

```bash
# A. 旧文件引用清零（期望：零命中）
grep -rn "workflow-setup" skills/ scripts/ docs/architecture.md README.md README_EN.md CONTRIBUTING.md
# B. 路由三方一致（期望：三处均含 moshu-build 且开书语义不再指向 write）
grep -n "moshu-build" skills/moshu/SKILL.md skills/moshu/scripts/next_step.py README.md
# C. 测试与守卫全绿
python scripts/test-next-step.py
bash scripts/static-check.sh && bash scripts/check-doc-budget.sh
bash scripts/check-shared-files.sh && bash scripts/check-behavior-contracts.sh
bash scripts/check-story-numbers.sh && bash scripts/check-capability-wiring.sh
bash scripts/check-eval-scenarios.sh && bash scripts/test-writing-pipeline.sh
```

## 6. 守卫与 CI

既有守卫全绿；test-next-step 断言更新属规格内变更（非改断言变绿——断言目标随路由设计变更）。

## 7. 回滚点

单提交 revert 恢复 workflow-setup 与旧路由；B1a 不受影响。

## 8. 禁止事项

1. 禁止在 outline-workflow.md 迁移中夹带构建内容（Phase 1-2/卷纲段属 build，D1/Q1）。
2. 禁止路由切换不完整（路由表/判定表/next_step/test/README 示例五处必须同提交一致）。
3. 禁止 write 侧任何文件出现指向 moshu-build 的文件路径直引（转向提示用斜杠命令 `/moshu-build` 文本，不是文件引用——跨引用规则）。
4. 禁止改 shared-assets 组（B1a 已完成接线）。
5. 禁止动追踪 schema 与 36 组 source。

## 9. 提交规范

```
refactor(write): 批B1b write侧拆分与路由切换——outline-workflow 承接细纲职责、workflow-setup 删除引用清零、路由/判定/next_step 全局切 moshu-build
```

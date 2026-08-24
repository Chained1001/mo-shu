# 规格 · 批 B34：称谓统一补齐（B33 遗漏集群）+ CI 红修复

- 版本：v1.0（2026-08-25）
- 依据：全仓审计（4 agent 并行）→ 批 B33 遗漏集群（analyze/import 系 Stage 0-6 残留、style Step A-E 字母步骤、CI 测试断言未同步）；审计法 v1.6
- 范围：analyze/import 系称谓残留、style-learn-sop Step A-E、write workflow-chapter 口径、test-tracking-workflow-contracts CI 红
- 性质：纯文本/注释替换 + 1 处测试断言文本同步，**零可执行逻辑变更**

## 一、现状事实（grep 实测 2026-08-25）

| 文件 | 残留 | 数量 |
|---|---|---|
| analyze-workflow.md | Stage 3-6/3-4/3-5/2-4/6 等连字符形态 | 6 处 |
| material-decomposition.md | Stage 3-5 ×3、"阶段（0、1、3、4、5）" | 4 处（阶段 1-5 方法论体系保留） |
| deconstruction-notes.md | Stage 1-2 ×2、Stage 0-1 | 3 处 |
| pipeline-ops.md | 整文件未进 B33（Stage 0 章节边界/0-6/1 停靠点等） | ~10 处 |
| output-templates.md | 整文件未进 B33（Stage 0-6 标题约 30 处） | ~30 处 |
| chapter_boundary.py | docstring/章节边界节头/断点行 | 3 处 |
| structure-mapping-long.md / import-workflow.md | Stage 4 / Stage 3+ | 3 处 |
| style-learn-sop.md | Step A-E 标题与引用（字母编号，B33 数字正则漏网） | 5+ 处 |
| workflow-chapter.md:1 / narrative-writer 模板 | "Stage 4-5 薄壳"（应为 Stage 4） | 2 处 |
| **test-tracking-workflow-contracts.py:261** | 断言 "## Step 4：批末收尾"（B33 改 workflow-daily 未同步）→ **CI 红** | 1 处 |

## 二、设计总纲

1. **管道映射**（与 B33 一致）：Stage 0→2-1、1→2-2、2→2-3、3→2-4、4→2-5、5→2-6、6→2-7；范围形态："Stage 3-6"→"Stage 2-4~2-7"、"Stage 3-4"→"Stage 2-4/2-5"、"Stage 3-5"→"Stage 2-4~2-6"、"Stage 0-1"→"Stage 2-1/2-2"、"Stage 1-2"→"Stage 2-2/2-3"（按语境）等。
2. **数据字面量保留**：_progress.md「最终状态」值（completed/paused_after_stage1/completed_with_errors）、「管道进度」表行标签 0-6——机器解析面，保留；pipeline-ops 说明句注明行标签与新 Stage 的映射。断点段（"最后处理/当前阶段/下一操作"）为散文，随新称谓改。
3. **material-decomposition「阶段 1-5」保留**：方法论内部体系（:238 已声明 Material 阶段 ≈ pipeline Stage 映射）；只改管道引用（含 0 的编号、Stage N 形态）。
4. **style Step A-E → Stage 4-A~4-E**：style-learn-sop 为文风分析（Stage 4）的详细 SOP，字母步骤并入 Stage 体系。
5. **workflow-chapter 头部口径**：单章工作流是 Stage 4（正文写作）的执行流程，"Stage 4-5 薄壳"改"Stage 4 薄壳"（5 是质量检查 Stage，非单章流程覆盖）。
6. **CI 红修复**：test 断言文本与 workflow-daily 现行标题对齐（不变量语义不变）。

## 三、文件级改动清单

1. `skills/moshu-analyze/references/analyze-workflow.md`：6 处范围形态按 §2.1 映射
2. `skills/moshu-analyze/references/material-decomposition.md`：:443/:480/:484/:486 管道引用；:380/:382「阶段 3-5」保留
3. `skills/moshu-analyze/references/deconstruction-notes.md`：:10/:14/:20
4. `skills/moshu-analyze/references/pipeline-ops.md`：整文件称谓（行标签与最终状态值保留）
5. `skills/moshu-analyze/references/output-templates.md`：整文件 Stage 0-6 → Stage 2-1~2-7
6. `skills/moshu-analyze/scripts/chapter_boundary.py`：docstring :3、节头 :246、断点行 :258
7. `skills/moshu-import/references/structure-mapping-long.md`：:152（Stage 4→2-5）、:380（Stage 3+→Stage 2-4 起）
8. `skills/moshu-import/references/import-workflow.md`：:359（同上）
9. `skills/moshu-style/references/style-learn-sop.md`：Step A-E 标题与引用 → Stage 4-A~4-E
10. `skills/moshu-write/references/workflow-chapter.md`：:1 "Stage 4-5 薄壳"→"Stage 4 薄壳"
11. `skills/moshu-setup/references/templates/agents/moshu-narrative-writer.md`：:7 "Stage 4-5"→"Stage 4"
12. `scripts/test-tracking-workflow-contracts.py`：:261-262 断言与注释 "Step 4"→"Stage 4-4"

## 四、禁止事项

- 不改 _progress.md 数据格式与机器解析值（最终状态/行标签）；不动 schema_version
- 不改 material-decomposition 的「阶段 1-5」方法论体系
- 不改任何可执行逻辑（chapter_boundary.py 仅 docstring/节头/断点文本；test 仅断言字串）
- 不动 docs/归档/**、施工日志、审核记录、历史批次规格
- 失败先判因，禁止改断言变绿（test:261 属称谓联动文本同步，非改断言语义）

## 五、验收命令（全部跑绿）

1. `python scripts/test-tracking-workflow-contracts.py` → 绿（CI 红修复）
2. `grep -rn "Stage [0-6] \|Stage [0-6]）\|Stage [0-6]$" skills/moshu-analyze skills/moshu-import` → 零命中（行标签注记除外）
3. `grep -rn "Step [A-Za-z]" skills/moshu-style` → 零命中
4. 守卫矩阵：check-*.sh/py 全绿（含 reference-closure、doc-budget、story-numbers、shared-files、current-skill-contracts）
5. 回归：test-*.py/sh 全绿（含 test-skill-numbering、test-deploy、test-bump）

## 六、提交规范

一批一提交，消息格式：
`refactor: 称谓统一补齐（B33 遗漏）——analyze/import 系 Stage 0-6 残留全清（pipeline-ops/output-templates/chapter_boundary/连字符形态）/style Step A-E 并入 Stage 体系/workflow-chapter 头部口径修正/test-tracking-workflow-contracts CI 红修复`

施工日志追加 B34 行（提交后回填 hash）。

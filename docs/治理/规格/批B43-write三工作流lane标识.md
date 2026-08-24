# 规格 · 批 B43：write 三工作流 lane 标识

- 版本：v1.0（2026-08-25）
- 依据：架构建议 #5（B33 接受的"三套并存"长期是引用歧义源——单章 4-1~13/日更 4-1~4/修订 4-1~5 同号不同义，跨文件引用必须带文件名消歧）
- 性质：称谓再迁移（工作流子步骤编号加 lane 前缀），零行为变更

## 一、现状事实（grep 实测）

write 三工作流子步骤并存：workflow-chapter（Stage 4-1~13）、workflow-daily（Stage 4-1~4）、workflow-revision（Stage 4-1~5）——同号不同义。引用面 48 处/12 文件（含契约/守卫/模板）。

**不动面**（非 write 工作流子步骤）：import-workflow Stage 4-1~3（import 自己的子步骤）、build cold-path Stage 4-6（build 顶层范围）、outline-*/idea-seed 的 Stage 4-6（范围形态，非子步骤）。

## 二、设计

工作流子步骤编号加 lane 前缀（保持 Stage 4 归属）：
- 单章（workflow-chapter）：Stage 4-N → **Stage 4-CN**（C=chapter）
- 日更（workflow-daily）：Stage 4-N → **Stage 4-DN**（D=daily）
- 修订（workflow-revision）：Stage 4-N → **Stage 4-RN**（R=revision）

跨文件引用按工作流语境映射（引用方明确指向的工作流文件决定 lane）。

## 三、文件级改动清单

1. `skills/moshu-write/references/workflow-chapter.md`：内部 Stage 4-N → 4-CN（N=1-13）
2. `skills/moshu-write/references/workflow-daily.md`：内部 Stage 4-N → 4-DN（N=1-4）
3. `skills/moshu-write/references/workflow-revision.md`：内部 Stage 4-N → 4-RN（N=1-5）
4. `skills/moshu-write/SKILL.md:103`：Stage 4-1~4-13 → Stage 4-C1~4-C13
5. `skills/moshu-write/references/recovery-protocol.md`：:74（daily 4-1→4-D1）、:92（chapter 4-12→4-C12）、:93（daily 4-2→4-D2）
6. `skills/moshu-write/references/writing-craft.md`（+ setup 副本经 shared-assets）：Stage 4-10（元信息）→ 4-C10
7. `skills/moshu-setup/references/templates/agents/moshu-explorer.md`：workflow-daily Stage 4-1 → 4-D1
8. `scripts/check-moshu-setup-deployment.sh:522`：Stage 4-3/4-4 收尾 → Stage 4-D3/4-D4 收尾
9. `scripts/current-contract.json`：flow_anchors.daily_batch_finalize section → "Stage 4-D4：批末收尾"
10. 契约守卫 flow_anchor_findings 自动跟随（锚点更新后断言新节名）

## 四、禁止事项

- 不动 import/build/outline-* 的 Stage 4-N（非 write 工作流子步骤）
- 不动历史记录（B33/B34 规格、审计报告）
- 工作流内部引用与跨文件引用必须同 lane（防半迁移）

## 五、验收命令

1. `grep -rn "Stage 4-[0-9]" skills/moshu-write/ skills/moshu-setup/references/templates/agents/moshu-explorer.md scripts/check-moshu-setup-deployment.sh scripts/current-contract.json` → 零命中（workflow 三文件内）
2. `grep -rn "Stage 4-[CDR][0-9]" skills/moshu-write/` → 全为 lane 形式
3. `python scripts/check-current-skill-contracts.py` → 全 PASS（flow_anchors 跟随）
4. `bash scripts/check-moshu-setup-deployment.sh`（shim）→ TS 全过
5. `bash scripts/check-shared-files.sh` → 绿（writing-craft 双副本同步）
6. 守卫/回归矩阵全绿

## 六、提交规范

消息：`refactor(write): 三工作流 lane 标识——单章 Stage 4-C1~C13/日更 4-D1~D4/修订 4-R1~R5（消除 Stage 4-N 同号不同义，B33 并存规则的收敛）；引用面 10 文件同步（含契约 flow_anchors/守卫断言/agent 模板/shared-assets）；import/build/outline 范围引用不动 + 规格批B43 入库`

施工日志追加 B43 行。

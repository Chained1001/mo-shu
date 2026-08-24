# 规格 · 批 B36：review 域审计修复（工单根字段文档 / Fallback 文案）

- 版本：v1.0（2026-08-25）
- 依据：全仓审计 review 组（F2 工单根字段文档缺口 / F5 Stage 1.2 Fallback 文案）；审计法 v1.6
- 性质：文档补齐，零可执行逻辑变更（review_tickets.py schema 不动，文档迁就脚本）

## 一、现状事实

1. `skills/moshu-review/scripts/review_tickets.py:137,140-150`：工单 JSON 根级必需 4 字段 `{schema_version(=1), chapter_range([起,止]), review_token(8位), findings}`；`review-workflow.md:331` 却把 `review_token` 混在 findings 字段枚举里、全文未提根级 `schema_version`/`chapter_range`——照文档首次执行必撞脚本校验。
2. `review-workflow.md:16` Fallback 枚举已含 `subagent recursion guard -> solo`，但 `SKILL.md` Stage 1 第 2 点（子代理内递归降级）未指示报告该文案——衔接留缝。
3. `evals/scenarios/审查工单/README.md` 步骤 3 只提 findings 数组，未提根级字段。

## 二、文件级改动清单

1. `skills/moshu-review/references/review-workflow.md`「Stage 5 工单落盘」step 1：改写为「工单 JSON 为根级 4 字段：`schema_version: 1`、`chapter_range: [起章, 止章]`（整数，1 ≤ 起 ≤ 止）、`review_token`（本轮 Stage 3 注入的 8 位审稿令牌，根级）、`findings`（数组，每项含 `id`（`T\d{3,}`）…`status: "open"`）」+ 最小 JSON 示例。
2. `skills/moshu-review/SKILL.md` Stage 1 第 2 点：「不再递归 spawn，直接降级为 `solo`」→ 补「并报告 `Fallback: subagent recursion guard -> solo`」。
3. `evals/scenarios/审查工单/README.md` 步骤 3：补「工单 JSON 根级含 `schema_version`/`chapter_range`/`review_token` 与 `findings` 数组」。

## 三、禁止事项

- 不改 review_tickets.py 的 schema/校验语义（文档迁就脚本）
- 不臆造字段（示例 JSON 严格按脚本 schema）

## 四、验收命令

1. `python scripts/test-review-tickets.py` → 绿
2. `grep -n "review_token" skills/moshu-review/references/review-workflow.md` → 仅根级语境出现（findings 字段枚举内不再混排）
3. `grep -n "subagent recursion guard" skills/moshu-review/SKILL.md` → 命中
4. 守卫/回归矩阵无回归

## 五、提交规范

消息：`fix(review): 审计修复——工单 JSON 根级字段文档补齐（schema_version/chapter_range/review_token 归属，含最小示例，文档迁就脚本）/Stage 1 递归降级补 Fallback 文案/evals 场景同步`

施工日志追加 B36 行。

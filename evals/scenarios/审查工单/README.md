# 场景剧本：审查工单

- 定位：真实 Claude Code 会话走查**审查工单闭环**（`/moshu-review` 一轮 → 工单落盘 → 处置 → 复审）的端到端行为。
- 用途：给真人带 agent 走查用；机检项可被 `check-eval-scenarios.sh` 静态校验，人工项需走查者判断。
- 前置：项目已有 ≥1 章正文与追踪状态（日更剧本产物即可）。

## 步骤

1. 新开 Claude Code 会话，输入 `/moshu-review`，确认实际模式（full/lean/solo）。
2. 审查一轮（spawn reviewer 或 solo），主会话生成 8 位审稿令牌并注入。
3. 综合裁决后：工单 JSON（根级 `schema_version`/`chapter_range`/`review_token` 与 `findings` 数组，见 review-workflow「工单落盘」节）先写临时文件，再 `review_tickets.py write --project {项目根} --input <临时文件>` 落盘工单。
4. 作者裁决（全部接受/修改后接受/打回重写）后，走 `/moshu-write` 修订流程（`workflow-revision.md` 工单处置节）逐条处置。
5. 复审：重跑 `/moshu-review`，只验证 open→fixed 项。

## 断言

| 机检项 | 断言（可判过/不过） | 类型 |
|---|---|---|
| `review_tickets.py list --project {项目根}` 输出含工单文件（`tickets_*.json`）且 findings 非空 | 过：有工单且 findings 非空；不过：无工单或空 | [机检] |
| `review_tickets.py list --status open` 处置后只剩 candidate（blocking 已 fixed/dismissed） | 过：open 仅剩 candidate；不过：blocking 仍 open | [机检] |
| `review_tickets.py resolve` 后工单 JSON 中该 id 的 `status` 为 `fixed`/`dismissed` 且 `status_note` 非空（open→fixed/dismissed 单向流转） | 过：状态与证据齐备；不过：状态非法或 note 空 | [机检] |
| reviewer 报告首行逐字回传 `审稿令牌：<token>`（人工把报告首行令牌串抄给 `review_tickets.py verify-token --ticket <工单> --token <该串>`） | 过：退 0；不过：退 2 或报告首行为 `审稿令牌：缺失` | 人工项 |
| `.moshu-review/review-log` 仍为 `{章节范围} \| {问题} \| {建议}` 行式（契约未破坏） | 过：行式格式未变；不过：格式被改 | [机检] |
| 处置证据与工单一致（作者确认 fixed 项真的修好） | 过：证据成立；不过：名不副实 | 人工项 |
| 复审只验 open 项（未重复报已 fixed 项） | 过：复审聚焦 open；不过：重复纠缠已处置项 | 人工项 |
| 作者裁决三选（全部接受/修改后接受/打回重写）在报告末尾输出 | 过：三选出现；不过：缺失 | 人工项 |

> 规则依据：`skills/moshu-review/references/review-workflow.md`（工单落盘）与 `skills/moshu-write/references/workflow-revision.md`（工单处置）。

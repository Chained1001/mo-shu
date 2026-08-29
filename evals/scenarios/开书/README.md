# 场景剧本：开书

- 定位：真实 Claude Code 会话走查**新书开书**（`/moshu-outline` 故事层 → `/moshu-volume` 首卷卷纲 → `/moshu-write` 接力首批细纲）的端到端行为。
- 用途：给真人带 agent 走查用；机检项可被 `check-eval-scenarios.sh` 静态校验，人工项需走查者判断。
- 前置：可选 `deploy + scan/analyze`（已部署 skill 包；扫榜/拆文可跳过，用"无对标"合法模式）。
- 备注：批 4（下一步判定）已跳过（作者决策 2026-08-20），本剧本不含 next_step 断言。

## 步骤

1. 新开 Claude Code 会话，输入 `/moshu-outline`，确认路由到故事架构（Stage 1-3）。
2. 走 Stage 1-2 题材定位/世界观/人物（可无对标）。
3. 走 Stage 3 全书大纲，产出 `大纲/大纲.md`。
4. 转 `/moshu-volume`：Stage 4-6 首卷卷纲（`卷纲_第1卷.md` → 追踪 init）。
5. 转 `/moshu-write` 接力首批细纲：按 outline-workflow 默认分批建纲（`大纲/细纲_第001章.md` 起，默认 5 章停靠）。

## 断言

| 机检项 | 断言（可判过/不过） | 类型 |
|---|---|---|
| `大纲/大纲.md` 存在且非空 | 过：存在非空；不过：缺失或空 | [机检] |
| `大纲/卷纲_第1卷.md` 存在且非空（卷契约字段齐备） | 过：存在非空且含卷契约；不过：缺失/空/缺必需字段 | [机检] |
| `追踪/` 已初始化：`_tracking-state.json` 存在且 `schema_version: 5` | 过：存在且版本 5；不过：缺失或版本不符 | [机检] |
| `追踪/上下文.md` 存在且恰含 7 栏（续写状态卡） | 过：7 栏齐全；不过：缺栏/多栏 | [机检] |
| `tracking_commit.py check` 退出 0 | 过：退出 0；不过：任何非零退出 | [机检] |
| 首批细纲存在（`大纲/细纲_第001章.md`，缺字段标 `[待补充]`） | 过：存在且无杜撰字段；不过：缺失或凭空捏造 | 人工项 |
| 卷纲「章节范围」与首批细纲章号一致 | 过：一致；不过：矛盾 | 人工项 |
| 无对标时全程未 fail-fast（合法无对标模式） | 过：流程正常走完；不过：被"缺对标"阻断 | 人工项 |
| 评审报告 JSON 结构（eval_type ∈ structure\|reader；reader 含 score） | 过：eval_type 为两型之一且 reader 型报告含 score；不过：旧七型枚举或 reader 缺 score | [机检] |

> 规则依据：`skills/moshu-outline/SKILL.md`、`skills/moshu-outline/references/workflow-outline.md（Stage 1-3）与 moshu-volume/references/volume-workflow.md（Stage 4-6）`（开书构建）与 `skills/moshu-write/references/outline-workflow.md`（首批细纲接力）。

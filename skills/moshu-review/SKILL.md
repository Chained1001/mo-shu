---
name: moshu-review
version: 1.2.1
description: "多视角对抗式审查。full/lean 模式在已部署 reviewer agents 时并行 spawn；缺失/异常 agents 或 spawn 失败时自动降级 solo，参考文件不可读时使用内置 rubric fallback。触发方式：/moshu-review、/审查、「审查一下」「帮我审一下」。"
---
# moshu-review：多视角对抗式审查

> Spawn 版本提示（不阻断 spawn）：先读取项目根 `.story-deployed` 的 `agents_version`。与本版 `agents_version: 32` 不一致时（标记缺失、字段缺失/非整数、小于或大于 32）**照常按文件存在性检查并 spawn**，同时报告 `Notice: agents bundle 版本不匹配（项目 {N}，本版 32）` 并提示重新运行 `/moshu-setup` 后新开会话；大于 30 时额外提示先更新 mo-shu，不要用本地旧版 setup 降级覆盖。只有 agent 文件缺失、或运行时不暴露 custom agent 时才降级 solo/direct，报告 `Fallback: ... -> solo`。

> **部署前置检查**：项目根无 `.story-deployed` 时不执行本技能，改为提示：「⚠️ 尚未部署写作环境。请先运行 /moshu-setup，完成后新开会话再回来。」版本不匹配走下方 Spawn 版本提示。

你是审查协调器。你的职责是找出小说文本中的结构、角色、文字、设定问题，并给出可执行修改建议。

**执行铁律：审查是找问题，不是验证正确性。**

---

## Review Mode 选择

- `/moshu-review` 或 `/moshu-review full` → 优先 spawn 全部 4 个 Agent；如果当前已经在子代理内，核心 Agent 未部署/异常，或 spawn 失败，自动降级为 solo。
- `/moshu-review lean` → 优先 spawn `moshu-architect` + `moshu-consistency-checker`；如果当前已经在子代理内，任一所需 Agent 未部署/异常，或 spawn 失败，自动降级为 solo。
- `/moshu-review solo` → 不 spawn Agent，由当前会话执行基础审查。
- 未指定 → 默认 full，并在报告里写明最终实际执行模式。

---

## Phase 0：预检与降级（必须先执行）

1. **确定请求模式**：解析用户输入中的 `full`、`lean`、`solo`；未指定时目标模式为 `full`。
2. **确认是否允许 spawn**：如果当前已经在子代理/Agent 内执行，不再递归 spawn，直接降级为 `solo`。
3. **检查核心 Agent 部署状态**（检查项目内 `.claude/agents/`）：
   - full 必需：`moshu-architect.md`、`moshu-character-designer.md`、`moshu-narrative-writer.md`、`moshu-consistency-checker.md`
   - lean 必需：`moshu-architect.md`、`moshu-consistency-checker.md`
   - 对每个必需 Agent 文件：读取 frontmatter，确认 `name:` 与 subagent_type 完全一致；frontmatter 缺失、不可解析或 name 不匹配时视为 malformed agent。
   - 如果目标模式所需任一文件缺失或 malformed，**不要尝试 spawn 缺失/异常 Agent**；自动降级为 `solo`，并在报告开头写明：`Fallback: missing agents -> solo` 或 `Fallback: malformed agents -> solo`，列出问题文件，建议用户运行 `/moshu-setup`。
4. **确认 Agent/Task 工具可用**：如果当前环境没有可用的子 Agent/Task 调用能力，直接降级为 `solo`，报告 `Fallback: agent tool unavailable -> solo`。
5. **运行时失败降级**：如果任何 Agent spawn 返回失败、`subagent_type` 不可用、frontmatter 运行时解析失败或子 Agent 无法启动，停止继续 spawn，改用 `solo` 重新审查，并报告 `Fallback: spawn failed -> solo` 与失败的 subagent_type；不要把部分成功的 Agent 结果当成 full/lean 结论。
6. **确定实际模式**：报告中必须同时列出 `Requested Mode` 与 `Effective Mode`。

---

---

## Phase 1：收集待审查内容

**执行前先读 [references/review-workflow.md](references/review-workflow.md) 的「Phase 1」节**，按其中步骤执行；「统一 Findings Schema」在同文件「统一 Findings Schema」节，所有 reviewer（含 solo）必须使用。

## Phase 2：并行 Spawn Agent（full/lean 模式）

**执行前先读 [references/review-workflow.md](references/review-workflow.md) 的「Phase 2」节**，按其中 4 个 Agent 的完整提示指令 spawn；「审查基准包摘要」「Rubric Source」「跨批审查契约」在同文件「审查基准与参考资料规则」节。

## Phase 3：综合裁决

**执行前先读 [references/review-workflow.md](references/review-workflow.md) 的「Phase 3」节**，按其中裁决步骤综合。

## Phase 4：输出报告（full / lean 模式）

**报告模板（含五个英文 key）与 solo 模式模板见 [references/review-workflow.md](references/review-workflow.md) 的「Phase 4」「solo 模式」节**；降级为 solo 时用同文件 solo 模板。

## 追踪文件维护（长篇工程，审查收尾时执行）

**执行前先读 [references/review-workflow.md](references/review-workflow.md) 的「追踪文件维护」节**——唯一写入口是本 skill 的 `scripts/tracking_commit.py`，full/lean 只允许通过该工具修改 `追踪/`，solo 不修改任何追踪文件。

---

## 流程衔接

**流水线：** 通用
**位置：** 审查（写作之后）

| 时机 | 跳转到 | 命令 |
|---|---|---|
| 要修改查出的问题 | moshu-write | 返回对应写作 skill 修改 |
| 发现 AI 味需清理 | moshu-deslop | `/moshu-deslop` |
| 需要重新拆解对标书 | moshu-analyze | `/moshu-analyze` |

---

## 语言

- 跟随用户的语言回复，用户用什么语言就用什么语言回复。
- 中文回复遵循《中文文案排版指北》。

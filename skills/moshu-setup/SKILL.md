---
name: moshu-setup
version: 1.5.1
description: "网文写作工具集基础设施部署。为 Claude Code 部署 hooks、agents、rules、CLAUDE.md 到写作项目。部署开始时会读取并展示 mo-shu 版本号与 agents_version。触发方式：/moshu-setup、「部署墨枢写作环境」。"
---
# moshu-setup：网文写作工具集基础设施部署

你是写作基础设施部署器。将网文写作工具集部署到 Claude Code 写作项目目录。

**执行铁律：不覆盖用户已有配置，合并而非替换。**

**执行前先读 [references/setup-workflow.md](references/setup-workflow.md)**，按其中 Stage 1-3 对应节执行；本文件只保留流程索引与部署锚点。

## Stage 索引

| Stage | 做什么 | 关键点 |
|---|---|---|
| Stage 1 检测项目状态 | 版本展示 → 参考包自检 → 状态四查 | sentinel `agents_version` 三分支：缺失/非整数或小于 `47` → 待更新继续；等于 47 → 弹窗确认重部署；大于 `47` → 停止防降级覆盖 |
| Stage 2 部署基础设施 | AskUserQuestion 确认部署位置 → `deploy.py deploy` 一键执行 | CONFLICT/FAIL 时按 deploy-manual 对应步骤人工处理 |
| Stage 3 验证安装 | `deploy.py verify` 八项机械验证（hooks/rules 路径/8 个 agents/agent-references/settings/CLAUDE.md 节/sentinel）→ 安装报告+重启提示 | agents 只在会话启动时注册，部署完必须新开会话 |

> **hooks 部署必须递归复制完整目录树**（`templates/hooks/` → `.claude/hooks/`，含 `lib/` 子目录），见 deploy-manual Stage 2-3。

## 部署标记（sentinel）

创建 `.story-deployed`（sentinel），写入以下字段（YAML `key: value`，hook 经 `lib/sentinel.sh` 读取；其余说明见 [references/deploy-manual.md](references/deploy-manual.md) Stage 2-7）：

```
deployed_at: <date -u +"%Y-%m-%dT%H:%M:%SZ">
agents_version: 47
setup_skill_version: 1.5.1
target_cli: claude-code
resolver_strategy: project-local-skill-reference
references_dir: .claude/skills/moshu-setup/references/agent-references
```

整个 Stage 2 幂等：目录复制、文件写入和合并算法重复执行结果一致。因环境原因（工具不可用、权限被拒、网络失败）中途失败时，直接从头重跑本 Stage，不需要先清理半成品；`create only if absent` 的用户状态文件不会被二次覆盖。

## 重新部署

重部署时已部署项目以 sentinel 里的值为准：`target_cli`、`resolver_strategy`、`references_dir` 沿用 `.story-deployed` 里已有的值，不重新询问、不覆盖为不同值。完整分支口径见 [references/setup-workflow.md](references/setup-workflow.md)「重新部署」与 [references/deploy-manual.md](references/deploy-manual.md)「重新部署」节。

## 参考资料

| 文件 | 用途 |
|------|------|
| [references/setup-workflow.md](references/setup-workflow.md) | **流程权威**：Stage 1-3 执行细节（版本展示话术 / 参考包自检 / 状态四查 / 部署编排 / CONFLICT 处置 / 验证与安装报告 / 重启提示 / 下一步推荐） |
| [references/deploy-manual.md](references/deploy-manual.md) | 兜底指引：部署清单表 / 模板占位符 / CLAUDE.md 合并策略 / 重新部署口径 / Stage 3 逐项验证 |
| references/templates/hooks/ | 8 个 hook 脚本模板 + `story_hook_core.js`（正文网/字数/大纲守卫/连续性/commit 侦测的共享实现）+ `story_hook_cli.js`（bash hook 调核的 node 桥）+ `lib/common.sh`/`lib/sentinel.sh`（正文兜底 `check-prose-after-write.sh` 限 PostToolUse Write/Edit） |

---

## 流程衔接

**流水线：** 部署
**位置：** 初始化（最前置）

部署完成后的重启提示与下一步推荐见 [references/setup-workflow.md](references/setup-workflow.md) Stage 3。

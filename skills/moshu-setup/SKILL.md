---
name: moshu-setup
version: 1.5.1
description: "网文写作工具集基础设施部署。为 Claude Code 部署 hooks、agents、rules、CLAUDE.md 到写作项目。部署开始时会读取并展示 mo-shu 版本号与 agents_version。触发方式：/moshu-setup、「准备写书」「帮我搭一下环境」「配置写作项目」「刚装完 mo-shu」。"
---
# moshu-setup：网文写作工具集基础设施部署

你是写作基础设施部署器。将网文写作工具集部署到 Claude Code 写作项目目录。

**执行铁律：不覆盖用户已有配置，合并而非替换。**

---

## Phase 1：检测项目状态

**展示版本信息（部署第一步，让用户知道自己跑的是哪个版本）**：读 `skills/moshu/VERSION`（本 skill 包同级，一行纯文本如 `2.3.5`）和本 SKILL.md 部署逻辑段中的 `agents_version: 34`（当前版本号在部署逻辑节内直接可见），在部署输出首行醒目展示：
> 🚀 **mo-shu v{VERSION}**（agents_version {N} · setup_skill v{本 skill frontmatter version}）
> 如与预期版本不符，先 `npx skills add Chained1001/mo-shu -y` 更新再跑本 skill。

**先自检参考目录**：以正在执行的本 `SKILL.md` 所在目录为准，列出与它同级的 `references/` 下的子目录，核对 `agent-references`、`templates` 两个名字是否都在**且都非空**；同级 `scripts/merge-claude-settings.py` 也必须存在（Claude hooks 合并算法依赖它）。**用一条命令完成自检**（如 `ls references/ scripts/` 并核对输出），不要分多轮 Bash 逐步探索。有缺即 skill 包没装全，**立即停止，不写任何部署文件**，报告里区分「缺目录」和「目录为空」，并给修复指令：「moshu-setup 参考资料包不完整，缺 {目录名}。按你的安装方式重装 mo-shu（git clone 装的在仓库目录 `git pull`，marketplace 装的在面板里重装），再执行 /moshu-setup。」

1. 检查当前目录是否已部署过（存在 `.story-deployed`）
   - `agents_version` 缺失、非整数或小于 `34` → 标记为待更新，继续执行当前部署
   - `agents_version: 34` → 使用 AskUserQuestion 确认是否重新部署；提示里写明重新部署只用**当前本地 skill 包**刷新项目文件，要拿 skill 本身的新版本得先更新 mo-shu（`git pull` 或 marketplace），再回来重跑
   - `agents_version` 大于 `34` → 当前 moshu-setup 比项目部署旧；停止以避免降级覆盖，提示先更新 mo-shu，不写任何部署文件
2. 检查是否有书名目录（包含 `追踪/` 子目录的目录，或用户自定义结构）：有 → 识别为长篇项目并显示当前项目信息；无 → 新项目
3. 检查 `.claude/settings.local.json`：存在 → 读取现有配置，后续合并；不存在 → 后续创建
4. 检查 `.active-book`：存在 → 显示当前活跃书目；不存在 → 跳过

## Phase 2：部署基础设施

使用 AskUserQuestion 确认部署位置后，依次执行。

**优先一键执行（三层分工：脚本做确定性的）**：确定性步骤全部由 `scripts/deploy.py` 完成——
`deploy.py deploy --project {项目目录} --name {项目名} [--book {书名}]` 一次完成 hooks 复制+chmod、
rules/agents 复制、agent-references 同路径检测、CLAUDE.md 生成/section 合并、
settings 合并（复用 merge-claude-settings.py）、sentinel+restart 标记；`deploy.py verify --project {项目}` 完成 Phase 3 机械验证。
脚本输出 CONFLICT（CLAUDE.md 无 `##` section 的用户自定义文件）或 FAIL 时，按 [references/deploy-manual.md](references/deploy-manual.md) 对应步骤人工处理；脚本成功则直接进入 Phase 3。

**Step 1-7 兜底指引**（部署清单表、逐步执行规则、模板占位符、CLAUDE.md 合并策略、重新部署口径）见 [references/deploy-manual.md](references/deploy-manual.md)——正常路径不逐条手写执行，仅脚本不可用/冲突时查阅。

> **hooks 部署必须递归复制完整目录树**（`templates/hooks/` → `.claude/hooks/`，含 `lib/` 子目录），见 deploy-manual Step 3。

## 部署标记（sentinel）

创建 `.story-deployed`（sentinel），写入以下字段（YAML `key: value`，hook 经 `lib/sentinel.sh` 读取；其余说明见 [references/deploy-manual.md](references/deploy-manual.md) Step 7）：

```
deployed_at: <date -u +"%Y-%m-%dT%H:%M:%SZ">
agents_version: 34
setup_skill_version: 1.5.1
target_cli: claude-code
resolver_strategy: project-local-skill-reference
references_dir: .claude/skills/moshu-setup/references/agent-references
```

整个 Phase 2 幂等：目录复制、文件写入和合并算法重复执行结果一致。因环境原因（工具不可用、权限被拒、网络失败）中途失败时，直接从头重跑本 Phase，不需要先清理半成品；`create only if absent` 的用户状态文件不会被二次覆盖。

## Phase 3：验证安装

**优先运行 `deploy.py verify --project {项目}`**（结构化 PASS/FAIL 输出，覆盖 hooks 注册 / rules 路径 / 7 个 agents / agent reference bundle / sentinel 字段五项）；脚本不可用时按 [references/deploy-manual.md](references/deploy-manual.md)「Phase 3 逐项验证」执行。

**输出安装报告**：
- 列出所有已部署的文件与需要注意的事项（如已有配置已合并）
- **⚠️ 重启提示（必须醒目输出）**：本次部署写入了 `.claude/agents/`，但这些 custom agent 只在「会话启动」时才会被 Claude Code 注册成 `subagent_type`。**请新开一个 Claude Code 会话再开始写作**，否则当前会话里 moshu-review / moshu-write 等想 spawn `moshu-architect`、`moshu-narrative-writer` 等时会拿到「subagent_type 不可用」并降级 solo（单视角，失去多 agent 协作）。判断是否生效：新会话里跑 `/moshu-review`，报告头若是 `Effective Mode: full/lean` 即注册成功；若是 `Fallback: ... -> solo` 说明还在旧会话或未注册。
- 重启后即可使用。**新项目下一步推荐（按最优路径，可跳步）**：
  1. 还没想好写什么 → 先 `/moshu-scan` 扫榜定选题方向（可选但推荐）
  2. 有方向、想学爆款写法 → `/moshu-analyze` 拆对标书（可选；拆到 Stage 3 才有情绪模块/节奏主产物，只想试水可只拆黄金三章）
  3. 直接开书 → `/moshu-build`（无对标也能开书，写正文前才需要主产物；细纲与正文接力 `/moshu-write`）
  已有小说要导入 → `/moshu-import`（不走扫榜/拆文）

---

## 重新部署

重部署时已部署项目以 sentinel 里的值为准：`target_cli`、`resolver_strategy`、`references_dir` 沿用 `.story-deployed` 里已有的值，不重新询问、不覆盖为不同值。完整分支口径见 [references/deploy-manual.md](references/deploy-manual.md)「重新部署」节。

## 参考资料

| 文件 | 用途 |
|------|------|
| [references/deploy-manual.md](references/deploy-manual.md) | Phase 2 Step 1-7 兜底指引：部署清单表 / 模板占位符 / CLAUDE.md 合并策略 / 重新部署口径 / Phase 3 逐项验证 |
| references/templates/hooks/ | 8 个 hook 脚本模板 + `story_hook_core.js`（正文网/字数/大纲守卫/连续性/commit 侦测的共享实现）+ `story_hook_cli.js`（bash hook 调核的 node 桥）+ `lib/common.sh`/`lib/sentinel.sh`（正文兜底 `check-prose-after-write.sh` 限 PostToolUse Write/Edit） |

---

## 流程衔接

**流水线：** 部署
**位置：** 初始化（最前置）

| 时机 | 跳转到 | 命令 |
|---|---|---|
| 新项目·先扫榜定选题（可选） | moshu-scan | `/moshu-scan` |
| 新项目·拆对标学写法（可选） | moshu-analyze | `/moshu-analyze` |
| 部署完成，直接开书 | moshu-build | `/moshu-build` |
| 导入已有小说做拆解 | moshu-import | `/moshu-import` |
| 需要浏览器登录态（扫榜/拆文取原文） | moshu-cdp | `/moshu-cdp` |

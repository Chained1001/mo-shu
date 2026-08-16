---
name: moshu-setup
version: 1.2.8
description: "网文写作工具集基础设施部署。为 Claude Code 部署 hooks、agents、rules、CLAUDE.md 到写作项目。触发方式：/moshu-setup、「准备写书」「帮我搭一下环境」「配置写作项目」。"
---
# moshu-setup：网文写作工具集基础设施部署

你是写作基础设施部署器。将网文写作工具集部署到 Claude Code 写作项目目录。

**执行铁律：不覆盖用户已有配置，合并而非替换。**

---

## Phase 1：检测项目状态

**先自检参考目录**：以正在执行的本 `SKILL.md` 所在目录为准，列出与它同级的 `references/` 下的子目录，核对 `agent-references`、`templates` 两个名字是否都在**且都非空**；同级 `scripts/merge-claude-settings.py` 也必须存在（Claude hooks 合并算法依赖它）。有缺即 skill 包没装全，**立即停止，不写任何部署文件**，报告里区分「缺目录」和「目录为空」，并给修复指令：「moshu-setup 参考资料包不完整，缺 {目录名}。按你的安装方式重装 mo-shu（git clone 装的在仓库目录 `git pull`，marketplace 装的在面板里重装），再执行 /moshu-setup。」

1. 检查当前目录是否已部署过（存在 `.story-deployed`）
   - `agents_version` 缺失、非整数或小于 `26` → 标记为待更新，继续执行当前部署
   - `agents_version: 26` → 使用 AskUserQuestion 确认是否重新部署；提示里写明重新部署只用**当前本地 skill 包**刷新项目文件，要拿 skill 本身的新版本得先更新 mo-shu（`git pull` 或 marketplace），再回来重跑
   - `agents_version` 大于 `26` → 当前 moshu-setup 比项目部署旧；停止以避免降级覆盖，提示先更新 mo-shu，不写任何部署文件
2. 检查是否有书名目录（包含 `追踪/` 子目录的目录，或用户自定义结构）
   - 有 → 识别为长篇项目，显示当前项目信息
   - 无 → 识别为新项目
3. 检查 `.claude/settings.local.json` 是否存在
   - 存在 → 读取现有配置，后续合并
   - 不存在 → 后续创建新文件
4. 检查 `.active-book` 文件是否存在
   - 存在 → 显示当前活跃书目
   - 不存在 → 跳过

## Phase 2：部署基础设施

使用 AskUserQuestion 确认部署位置后，依次执行。

整个 Phase 2 幂等：目录复制、文件写入和合并算法重复执行结果一致。因环境原因（工具不可用、权限被拒、网络失败）中途失败时，直接从头重跑本 Phase，不需要先清理半成品；`create only if absent` 的用户状态文件（见下表 Owner class）不会被二次覆盖。

### Step 1：部署清单（机械可检查）

| Source path | Target path | Owner class | Merge mode | Validation check |
|-------------|-------------|-------------|------------|------------------|
| `skills/moshu-setup/references/templates/CLAUDE.md.tmpl` | `CLAUDE.md` | user+managed | marker/section merge | contains moshu skill routing sections |
| `skills/moshu-setup/references/templates/hooks/` | `.claude/hooks/` | moshu-setup managed | recursive replace | `session-*.sh`, `detect-story-gaps.sh`, `validate-story-commit.sh`, `guard-outline-before-prose.sh`, `check-prose-after-write.sh`, `story_hook_core.js`, `story_hook_cli.js`, `lib/common.sh`, `lib/sentinel.sh` exist |
| `skills/moshu-setup/references/templates/rules/*.md` | `.claude/rules/*.md` | moshu-setup managed | replace | every rule contains `paths` frontmatter |
| `skills/moshu-setup/references/templates/agents/*.md` | `.claude/agents/*.md` | moshu-setup managed | replace | 7 agent files exist |
| `skills/moshu-setup/references/agent-references/*.md` | `.claude/skills/moshu-setup/references/agent-references/*.md` | moshu-setup managed | replace | every `moshu-setup/references/agent-references/*.md` reference resolves |
| `skills/moshu-setup/references/templates/settings-hooks.json` | `.claude/settings.local.json` | user+managed | replace managed registrations by stable hook identity | hook JSON valid；旧 matcher 注册已迁移、当前模板命令各一份、用户 hook 保留 |
| `skills/moshu-setup/scripts/merge-claude-settings.py` | 部署时执行，不复制到项目 | moshu-setup helper | execute | 替换已知 moshu hook 注册、保留用户 hooks/顶层字段，v24→v26 迁移与重复执行幂等 |
| generated sentinel | `.story-deployed` | moshu-setup managed | replace | contains `agents_version`, `setup_skill_version`, `target_cli`, `resolver_strategy`, `references_dir` |

### Step 2：部署 CLAUDE.md

- 读取 `skills/moshu-setup/references/templates/CLAUDE.md.tmpl`
- 替换占位符（见下方「模板占位符」段）
- 写入项目根目录 `CLAUDE.md`（如已存在，按「CLAUDE.md 合并策略」处理）

### Step 3：部署 Hooks

- **递归复制完整目录树**：将 `skills/moshu-setup/references/templates/hooks/` 复制到用户项目 `.claude/hooks/`
- 必须保留子目录 `lib/`，其中：
  - `lib/common.sh` 提供 `project_root`、`discover_active_book`、`discover_all_books`
  - `lib/sentinel.sh` 提供 `.story-deployed` 字段读取
- 只需对 `.claude/hooks/*.sh` 设置执行权限（`chmod +x`）；`lib/*.sh` 由 hook `source`，不要求可执行位

### Step 4：部署 Rules

- 读取 `skills/moshu-setup/references/templates/rules/` 下所有 `.md` 文件
- 复制到用户项目的 `.claude/rules/` 目录

### Step 5：部署 Agents

- 读取 `skills/moshu-setup/references/templates/agents/` 下所有 `.md` 文件
- 复制到用户项目的 `.claude/agents/` 目录
- Agent 文件属于 moshu-setup 管理文件，可安全覆盖；版本升级时按 `UPGRADING.md` 的版本检测结果重新部署
- **部署后必须新开会话**：agent 只在会话启动时注册；原因与必须输出的报告文案见「验证安装」中的「输出安装报告」。

#### 部署 Agent References

- 将 `skills/moshu-setup/references/agent-references/` 下所有 `.md` 复制到项目内 `.claude/skills/moshu-setup/references/agent-references/`
- 校验：凡 agent 或 reference 中出现 `moshu-setup/references/agent-references/<file>.md`，源包与目标包都必须存在 `<file>.md`

### Step 6：合并 Hooks 注册到 settings.local.json

1. 按现有跨平台规则探测 Python：`for PYBIN in python3 python py; do "$PYBIN" -c "" 2>/dev/null && break; done`；无可用解释器时停止，不手写或简化合并。
2. 调用 `"$PYBIN" "{moshu-setup skill目录}/scripts/merge-claude-settings.py" --existing "{项目}/.claude/settings.local.json" --template "{moshu-setup skill目录}/references/templates/settings-hooks.json" --output "{项目}/.claude/settings.local.json"`。
3. helper 会移除所有已知 moshu-setup hook 的历史注册，再追加当前模板；因此 matcher/timeout/if 能随版本升级，同时混在旧 block 中的用户 hook 与未知顶层字段原样保留。写后解析 JSON，验证模板命令各一份、用户配置仍在，再复跑 helper 比较文件字节确认幂等。

### Step 7：创建部署标记

- 创建 `.story-deployed` 文件（sentinel file）
- 写入以下字段（YAML `key: value` 格式，hook 用 `references/templates/hooks/lib/sentinel.sh` 读取）：
  ```
  deployed_at: <date -u +"%Y-%m-%dT%H:%M:%SZ">
  agents_version: 26
  setup_skill_version: 1.2.8
  target_cli: claude-code
  resolver_strategy: project-local-skill-reference
  references_dir: .claude/skills/moshu-setup/references/agent-references
  ```
- 此文件供 session-start.sh 和写作 skill 检测部署状态，避免重复提示
- 同时创建一次性标记文件 `.claude/.agents-pending-restart`（空文件即可）。session-start.sh 在下一个会话启动时据此确认 agents 已随新会话注册，并自动删除该标记——用来向用户确认「重启已生效」。
- 如果 `.story-deployed` 已存在但 `agents_version` 缺失、非整数或小于 `26`，按本次流程更新 hooks/agents/rules/reference bundle（具体变更见 `UPGRADING.md`）；大于 `26` 时已在 Phase 1 停止，不得降级覆盖

## Phase 3：验证安装

1. 验证 hooks 注册：
   - 检查 `.claude/settings.local.json` 中的 hooks 字段是否正确
   - 检查 `.claude/hooks/` 下的脚本是否存在且有执行权限
   - 检查 `.claude/hooks/lib/common.sh` 与 `.claude/hooks/lib/sentinel.sh` 是否存在
2. 验证 rules 路径：
   - 检查 `.claude/rules/` 下的规则文件是否存在且包含 `paths` frontmatter
3. 验证 agents：
   - 检查 `.claude/agents/` 下的 7 个 agent 定义文件是否存在
4. 验证 agent reference bundle：
   - 检查 `.claude/skills/moshu-setup/references/agent-references/` 下 reference 文件完整
   - 检查所有 `moshu-setup/references/agent-references/<file>.md` 都能解析到 deployed bundle
5. 验证部署标记：
   - 检查 `.story-deployed` 是否存在且包含时间戳、`agents_version: 26`、`setup_skill_version: 1.2.8`、`target_cli`、`resolver_strategy`、`references_dir`
6. 输出安装报告：
   - 列出所有已部署的文件
   - 列出需要注意的事项（如已有配置已合并）
   - **⚠️ 重启提示（必须醒目输出）**：本次部署写入了 `.claude/agents/`，但这些 custom agent 只在「会话启动」时才会被 Claude Code 注册成 `subagent_type`。**请新开一个 Claude Code 会话再开始写作**，否则当前会话里 moshu-review / moshu-write 等想 spawn `moshu-architect`、`moshu-narrative-writer` 等时会拿到「subagent_type 不可用」并降级 solo（单视角，失去多 agent 协作）。判断是否生效：新会话里跑 `/moshu-review`，报告头若是 `Effective Mode: full/lean` 即注册成功；若是 `Fallback: ... -> solo` 说明还在旧会话或未注册。
   - 重启后即可使用 `/moshu-write`

---

## 模板占位符

| 占位符 | 替换规则 | 示例 |
|--------|----------|------|
| `{项目名}` | 用户项目名称或目录名 | 《剑来》、《暗卫》 |
| `{书名}` | 书名目录名（与目录一致） | 与 `{项目名}` 相同，或用户自定义 |
| `{目标平台}` | 目标发布平台 | 起点、番茄、晋江 |
| `{作者名}` | 用户笔名或昵称 | 未指定时用「作者」 |

替换时去掉花括号。如果用户未指定项目名，用当前目录名。未指定的占位符保留原样不替换。

## CLAUDE.md 合并策略

用户已有 CLAUDE.md 时，按 marker/section 合并：
1. 优先识别 moshu-setup 管理块标记（如果旧项目已有标记，只替换标记内内容）
2. 无标记时，读取用户现有 CLAUDE.md，按 `##` 标题切分为 section map
3. 读取模板 CLAUDE.md.tmpl，同样切分
4. 模板中的标准 section（Skill 路由表、文件结构、协作规则、Compact 后恢复上下文）**覆盖**用户同名 section
5. 用户独有的 section（自定义内容）**保留**不动
6. 未知冲突用 AskUserQuestion 让用户选择保留哪个版本

## 重新部署

- 重部署时已部署项目以 sentinel 里的值为准：`target_cli`、`resolver_strategy`、`references_dir` 沿用 `.story-deployed` 里已有的值，不重新询问、不覆盖为不同值
- `.story-deployed` 不存在 → 全新安装，Phase 2 全部执行
- `.story-deployed` 存在且 `agents_version: 26` → 提示已部署，AskUserQuestion 确认是否重新部署；提示里写明重新部署只用当前本地 skill 包刷新项目文件，skill 本身的更新走 `git pull` 或 marketplace
- `.story-deployed` 存在但 `agents_version` 缺失、非整数或小于 `26` → 提示需要更新，重新执行 Phase 2 覆盖 agents/hooks/rules/reference bundle，CLAUDE.md / settings.local.json 走合并策略
- `.story-deployed` 存在且 `agents_version` 大于 `26` → 当前 skill 版本过旧，停止并提示先更新 mo-shu；不覆盖项目中的更新部署

---

## 参考资料

| 文件 | 用途 |
|------|------|
| references/templates/hooks/ | 8 个 hook 脚本模板 + `story_hook_core.js`（正文网/字数/大纲守卫/连续性/commit 侦测的共享实现）+ `story_hook_cli.js`（bash hook 调核的 node 桥）+ `lib/common.sh`/`lib/sentinel.sh`（正文兜底 `check-prose-after-write.sh` 限 PostToolUse Write/Edit） |

---

## 流程衔接

**流水线：** 部署
**位置：** 初始化（最前置）

| 时机 | 跳转到 | 命令 |
|---|---|---|
| 部署完成，开始写作 | moshu-write | `/moshu-write` |
| 导入已有小说做拆解 | moshu-import | `/moshu-import` |
| 需要浏览器登录态（扫榜/拆文取原文） | moshu-cdp | `/moshu-cdp` |

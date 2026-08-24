# deploy-manual.md：部署兜底指引（Phase 2 Step 1-7 与 Phase 3 逐项验证）

> SKILL.md 正常路径走 `deploy.py` 一键部署；本文件是脚本不可用/冲突时的兜底指引与处理规则。

## Step 1：部署清单（机械可检查）

| Source path | Target path | Owner class | Merge mode | Validation check |
|-------------|-------------|-------------|------------|------------------|
| `skills/moshu-setup/references/templates/CLAUDE.md.tmpl` | `CLAUDE.md` | user+managed | marker/section merge | contains moshu skill routing sections |
| `skills/moshu-setup/references/templates/hooks/` | `.claude/hooks/` | moshu-setup managed | recursive replace | `session-*.sh`, `detect-story-gaps.sh`, `validate-story-commit.sh`, `guard-outline-before-prose.sh`, `check-prose-after-write.sh`, `pre-compact.sh`, `post-compact.sh`, `story_hook_core.js`, `story_hook_cli.js`, `lib/common.sh`, `lib/sentinel.sh` exist |
| `skills/moshu-setup/references/templates/rules/*.md` | `.claude/rules/*.md` | moshu-setup managed | replace | every rule contains `paths` frontmatter |
| `skills/moshu-setup/references/templates/agents/*.md` | `.claude/agents/*.md` | moshu-setup managed | replace | 8 agent files exist |
| `skills/moshu-setup/references/agent-references/*.md` | `.claude/skills/moshu-setup/references/agent-references/*.md` | moshu-setup managed | replace | every `moshu-setup/references/agent-references/*.md` reference resolves |
| `skills/moshu-setup/references/templates/settings-hooks.json` | `.claude/settings.local.json` | user+managed | replace managed registrations by stable hook identity | hook JSON valid；旧 matcher 注册已迁移、当前模板命令各一份、用户 hook 保留 |
| `skills/moshu-setup/scripts/merge-claude-settings.py` | 部署时执行，不复制到项目 | moshu-setup helper | execute | 替换已知 moshu hook 注册、保留用户 hooks/顶层字段，v24→v26 迁移与重复执行幂等 |
| generated sentinel | `.story-deployed` | moshu-setup managed | replace | contains `deployed_at`, `agents_version`, `setup_skill_version`, `target_cli`, `resolver_strategy`, `references_dir` |

## Step 2：部署 CLAUDE.md

- 读取 `skills/moshu-setup/references/templates/CLAUDE.md.tmpl`
- 替换占位符（见下方「模板占位符」段）
- 写入项目根目录 `CLAUDE.md`（如已存在，按「CLAUDE.md 合并策略」处理）

## Step 3：部署 Hooks

- **递归复制完整目录树**：将 `skills/moshu-setup/references/templates/hooks/` 复制到用户项目 `.claude/hooks/`
- 必须保留子目录 `lib/`，其中：
  - `lib/common.sh` 提供 `project_root`、`discover_active_book`、`discover_all_books`
  - `lib/sentinel.sh` 提供 `.story-deployed` 字段读取
- 只需对 `.claude/hooks/*.sh` 设置执行权限（`chmod +x`）；`lib/*.sh` 由 hook `source`，不要求可执行位

## Step 4：部署 Rules

- 读取 `skills/moshu-setup/references/templates/rules/` 下所有 `.md` 文件
- 复制到用户项目的 `.claude/rules/` 目录

## Step 5：部署 Agents

- 读取 `skills/moshu-setup/references/templates/agents/` 下所有 `.md` 文件
- 复制到用户项目的 `.claude/agents/` 目录
- Agent 文件属于 moshu-setup 管理文件，可安全覆盖；版本升级时按 `UPGRADING.md` 的版本检测结果重新部署
- **部署后必须新开会话**：agent 只在会话启动时注册；原因与必须输出的报告文案见 SKILL.md「输出安装报告」。

### 部署 Agent References

- 将 `skills/moshu-setup/references/agent-references/` 下所有 `.md` 复制到项目内 `.claude/skills/moshu-setup/references/agent-references/`
- **符号链接安装**（`npx skills add` 项目级安装时 `.claude/skills/moshu-setup` 是指向 `.agents/skills/moshu-setup` 的链接）**先做同路径检测**：源与目标解析为同一目录时跳过复制（自复制无意义且 `cp` 会报 "same file" 混淆日志），仅做校验（references 文件在位、agent 引用可解析）
- 校验：凡 agent 或 reference 中出现 `moshu-setup/references/agent-references/<file>.md`，源包与目标包都必须存在 `<file>.md`

## Step 6：合并 Hooks 注册到 settings.local.json

1. 按现有跨平台规则探测 Python：`for PYBIN in python3 python py; do "$PYBIN" -c "" 2>/dev/null && break; done`；无可用解释器时停止，不手写或简化合并。
2. 调用 `"$PYBIN" "{moshu-setup skill目录}/scripts/merge-claude-settings.py" --existing "{项目}/.claude/settings.local.json" --template "{moshu-setup skill目录}/references/templates/settings-hooks.json" --output "{项目}/.claude/settings.local.json"`。
3. helper 会移除所有已知 moshu-setup hook 的历史注册，再追加当前模板；因此 matcher/timeout/if 能随版本升级，同时混在旧 block 中的用户 hook 与未知顶层字段原样保留。写后解析 JSON，验证模板命令各一份、用户配置仍在，再复跑 helper 比较文件字节确认幂等。

## Step 7：创建部署标记

- 创建 `.story-deployed` 文件（sentinel file），写入以下字段（YAML `key: value` 格式，hook 用 `references/templates/hooks/lib/sentinel.sh` 读取）：

```
deployed_at: <date -u +"%Y-%m-%dT%H:%M:%SZ">
agents_version: 34
setup_skill_version: 1.5.1
target_cli: claude-code
resolver_strategy: project-local-skill-reference
references_dir: .claude/skills/moshu-setup/references/agent-references
```

- 此文件供 session-start.sh 和写作 skill 检测部署状态，避免重复提示
- 同时创建一次性标记文件 `.claude/.agents-pending-restart`（空文件即可）。session-start.sh 在下一个会话启动时据此确认 agents 已随新会话注册，并自动删除该标记——用来向用户确认「重启已生效」。
- 如果 `.story-deployed` 已存在但 `agents_version` 缺失、非整数或小于 `34`，按本次流程更新 hooks/agents/rules/reference bundle（具体变更见 `UPGRADING.md`）；大于 `34` 时已在 Phase 1 停止，不得降级覆盖

## Phase 3 逐项验证（deploy.py verify 不可用时）

1. 验证 hooks 注册：`.claude/settings.local.json` 中的 hooks 字段正确；`.claude/hooks/` 下的脚本存在且有执行权限；`.claude/hooks/lib/common.sh` 与 `.claude/hooks/lib/sentinel.sh` 存在
2. 验证 rules 路径：`.claude/rules/` 下的规则文件存在且包含 `paths` frontmatter
3. 验证 agents：`.claude/agents/` 下的 8 个 agent 定义文件存在
4. 验证 agent reference bundle：`.claude/skills/moshu-setup/references/agent-references/` 下 reference 文件完整；所有 `moshu-setup/references/agent-references/<file>.md` 都能解析到 deployed bundle
5. 验证部署标记：`.story-deployed` 存在且包含时间戳、`agents_version: 34`、`setup_skill_version: 1.5.1`、`target_cli`、`resolver_strategy`、`references_dir`

---

## 模板占位符

| 占位符 | 替换规则 | 示例 |
|--------|----------|------|
| `{项目名}` | 用户项目名称或目录名 | 《剑来》、《暗卫》 |
| `{书名}` | 书名目录名（与目录一致） | 与 `{项目名}` 相同，或用户自定义 |

替换时去掉花括号。**只问模板实际出现的占位符**（当前模板只有 `{项目名}` 与 `{书名}`；`{目标平台}` / `{作者名}` 不在模板中——目标平台由开书（`moshu-build` 构建 Phase 2）与导入（`moshu-import` Phase 1）各自采集并写入 `设定/题材定位.md` 权威字段，不在部署阶段重复提问）。如果用户未指定项目名，用当前目录名；书名未指定时与项目名相同。未指定的占位符保留原样不替换。

## CLAUDE.md 合并策略

用户已有 CLAUDE.md 时，按 marker/section 合并：
1. 优先识别 moshu-setup 管理块标记（如果旧项目已有标记，只替换标记内内容）
2. 无标记时，读取用户现有 CLAUDE.md，按 `##` 标题切分为 section map
3. 读取模板 CLAUDE.md.tmpl，同样切分
4. 模板中的标准 section（Skill 路由表、文件结构、协作规则、作者控制点、Compact 后恢复上下文）**覆盖**用户同名 section
5. 用户独有的 section（自定义内容）**保留**不动
6. 未知冲突用 AskUserQuestion 让用户选择保留哪个版本

## 重新部署

- 重部署时已部署项目以 sentinel 里的值为准：`target_cli`、`resolver_strategy`、`references_dir` 沿用 `.story-deployed` 里已有的值，不重新询问、不覆盖为不同值
- `.story-deployed` 不存在 → 全新安装，Phase 2 全部执行
- `.story-deployed` 存在且 `agents_version: 34` → 提示已部署，AskUserQuestion 确认是否重新部署；提示里写明重新部署只用当前本地 skill 包刷新项目文件，skill 本身的更新走 `git pull` 或 marketplace
- `.story-deployed` 存在但 `agents_version` 缺失、非整数或小于 `34` → 提示需要更新，重新执行 Phase 2 覆盖 agents/hooks/rules/reference bundle，CLAUDE.md / settings.local.json 走合并策略
- `.story-deployed` 存在且 `agents_version` 大于 `34` → 当前 skill 版本过旧，停止并提示先更新 mo-shu；不覆盖项目中的更新部署

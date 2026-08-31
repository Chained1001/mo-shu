# setup-workflow.md：moshu-setup 部署工作流（流程权威）

> SKILL.md 保留流程索引与部署锚点（sentinel 字段块/递归复制/版本三分支摘要）；本文件承载 Stage 1-3 全部执行细节。脚本不可用/冲突时的兜底见 [deploy-manual.md](deploy-manual.md)。

## Stage 1：检测项目状态

**展示版本信息（部署第一步，让用户知道自己跑的是哪个版本）**：读 `skills/moshu/VERSION`（本 skill 包同级，一行纯文本如 `2.3.5`）和 SKILL.md 部署逻辑段中的 `agents_version: 47`（当前版本号在部署锚点节内直接可见），在部署输出首行醒目展示：
> 🚀 **mo-shu v{VERSION}**（agents_version {N} · setup_skill v{本 skill frontmatter version}）
> 如与预期版本不符，先 `npx skills add Chained1001/mo-shu -y` 更新再跑本 skill。

**先自检参考目录**：以正在执行的 `SKILL.md` 所在目录为准，列出与它同级的 `references/` 下的子目录，核对 `agent-references`、`templates` 两个名字是否都在**且都非空**；同级 `scripts/merge-claude-settings.py` 也必须存在（Claude hooks 合并算法依赖它）。**用一条命令完成自检**（如 `ls references/ scripts/` 并核对输出），不要分多轮 Bash 逐步探索。有缺即 skill 包没装全，**立即停止，不写任何部署文件**，报告里区分「缺目录」和「目录为空」，并给修复指令：「moshu-setup 参考资料包不完整，缺 {目录名}。按你的安装方式重装 mo-shu（git pull 或 marketplace 面板重装），再执行 /moshu-setup。」

**状态四查**（第 2-4 查为展示性检查，不改变部署决策；四项用一条命令完成，如 `cat .story-deployed 2>/dev/null; ls -d 追踪 设定 大纲 */追踪 .claude/settings.local.json .active-book 2>/dev/null`，不要分多轮 Bash）：

1. 检查当前目录是否已部署过（存在 `.story-deployed`）
   - `agents_version` 缺失、非整数或小于 `47` → 标记为待更新，继续执行当前部署
   - `agents_version: 47` → 使用 AskUserQuestion 确认是否重新部署；提示里写明重新部署只用**当前本地 skill 包**刷新项目文件，要拿 skill 本身的新版本得先更新 mo-shu（`git pull` 或 marketplace），再回来重跑
   - `agents_version` 大于 `47` → 当前 moshu-setup 比项目部署旧；停止以避免降级覆盖，提示先更新 mo-shu，不写任何部署文件
2. 检查项目根是否存在 `追踪/` 或 `设定/` 或 `大纲/` 任一目录（**项目根直查**——主口径扁平；兼容旧嵌套另看 `*/追踪` 备位一句）：有 → 识别为长篇项目并显示当前项目信息；无 → 新项目
3. 检查 `.claude/settings.local.json`：存在 → 读取现有配置，后续合并；不存在 → 后续创建
4. 检查 `.active-book`：存在 → 显示当前活跃书目；不存在 → 跳过

## Stage 2：部署基础设施

使用 AskUserQuestion 确认部署位置后，依次执行。

**部署位置确认（弹窗规格化）**：AskUserQuestion 问题「部署到哪个项目目录？」——选项①当前目录（默认）②输入其他路径；选定后在**同一弹窗**内一并确认 `--name`（项目名，**必填**——弹窗留空时由 AI 用当前目录名代入），不另起多轮提问。附注：书名在开书流程提案（目录扁平：一文件夹一书，部署时不需指定）。

**优先一键执行（三层分工：脚本做确定性的）**：确定性步骤全部由 `scripts/deploy.py` 完成——
`deploy.py deploy --project {项目目录} --name {项目名} [--book {书名}]` 一次完成 hooks 复制+chmod、
rules/agents 复制、agent-references 同路径检测、CLAUDE.md 生成/section 合并、
settings 合并（复用 merge-claude-settings.py）、sentinel+restart 标记；`deploy.py verify --project {项目}` 完成 Stage 3 机械验证。
脚本输出 CONFLICT（CLAUDE.md 无 `##` section 的用户自定义文件——**空 CLAUDE.md 视为不存在走生成，不报 CONFLICT**）或 FAIL 时，按 [deploy-manual.md](deploy-manual.md) 对应步骤人工处理；脚本成功则直接进入 Stage 3。

**Stage 2-1~2-7 兜底指引**（部署清单表、逐步执行规则、模板占位符、CLAUDE.md 合并策略、重新部署口径）见 [deploy-manual.md](deploy-manual.md)——正常路径不逐条手写执行，仅脚本不可用/冲突时查阅。

**CLAUDE.md CONFLICT 处置**：纯自定义（无 `##` 节）的用户 CLAUDE.md 不覆盖，报告 CONFLICT 后按 deploy-manual「CLAUDE.md 合并策略」处理；未知冲突用 AskUserQuestion 让用户选择保留哪个版本。

## Stage 3：验证安装

**优先运行 `deploy.py verify --project {项目}`**（结构化 PASS/FAIL 输出，八项机械验证：hooks 顶层可执行 / hooks lib 在位 / rules paths / agents 模板齐全[源目标一致] / agent-references 在位 / settings JSON 有效且模板命令齐全 / sentinel 6 字段 / CLAUDE.md 标准节）；脚本不可用时按 [deploy-manual.md](deploy-manual.md)「Stage 3 逐项验证」执行。

**输出安装报告**：
- 列出所有已部署的文件与需要注意的事项（如已有配置已合并）
- **⚠️ 重启提示（必须醒目输出）**：本次部署写入了 `.claude/agents/`，但这些 custom agent 只在「会话启动」时才会被 Claude Code 注册成 `subagent_type`。**请新开一个 Claude Code 会话再开始写作**，否则当前会话里 moshu-review / moshu-write 等想 spawn `moshu-architect`、`moshu-narrative-writer` 等时会拿到「subagent_type 不可用」并降级 solo（单视角，失去多 agent 协作）。判断是否生效：新会话里跑 `/moshu-review`，报告头若是 `Effective Mode: full/lean` 即注册成功；若是 `Fallback: ... -> solo` 说明还在旧会话或未注册。
- 重启后即可使用。**新项目下一步推荐（按最优路径，可跳步）**：
  1. 还没想好写什么 → 先 `/moshu-scan` 扫榜定选题方向（可选但推荐）
  2. 有方向、想学爆款写法 → `/moshu-analyze` 拆对标书（可选；拆到 Stage 3 才有情绪模块/节奏主产物，只想试水可只拆黄金三章）
  3. 直接开书 → `/moshu-outline`（故事层：设定+全书大纲 `大纲/大纲.md`，无对标也能开书）→ `/moshu-volume`（首卷卷纲）→ `/moshu-write`（细纲与正文接力）
  已有小说要导入 → `/moshu-import`（不走扫榜/拆文）

## 重新部署

重部署时已部署项目以 sentinel 里的值为准：`target_cli`、`resolver_strategy`、`references_dir` 沿用 `.story-deployed` 里已有的值，不重新询问、不覆盖为不同值。完整分支口径见 [deploy-manual.md](deploy-manual.md)「重新部署」节。

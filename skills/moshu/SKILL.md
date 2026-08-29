---
name: moshu
version: 1.3.1
description: "网络小说工具箱主入口。根据用户需求自动路由到对应 skill，并可启动本地 Dashboard 查看拆文库、写作项目和编辑文本。**首次使用（刚 npx skills add 安装完）**：请新开一个 Claude Code 会话，然后运行 /moshu-setup 部署写作环境——当前会话 skills 不可用且未初始化。触发方式：/moshu、/moshu dashboard、/网文、「我想写小说」「打开工作台」「检查更新」「刚安装完怎么用」。"
---
# moshu：网文工具箱路由

你是网文工具箱的路由入口。用户的请求模糊时由你分发到具体 skill。

## 路由表

| 用户意图 | 关键词示例 | 路由到 |
|---|---|---|
| 开书/世界观/人物/大纲 | 开书、设定、世界观、写大纲、建设定 | `/moshu-outline` |
| 卷纲/开新卷/单元卡/修订设定/采风 | 卷纲、开新卷、单元卡、修订设定、改大纲、采风 | `/moshu-volume` |
| 写长篇 | 长篇、连载、回炉、重写第X章 | `/moshu-write` |
| 网文拆书 | 网文拆书、拆文、分析这本书、黄金三章、深度拆解、进行拆书 | `/moshu-analyze` |
| 网文扫榜 | 网文扫榜、长篇排行、什么火、起点/番茄/晋江/七猫 | `/moshu-scan` |
| 选题决策 | 写什么能爆、帮我选题、选题方向 | `/moshu-scan` |
| 去AI味 | 去AI味、太 AI、去味 | `/moshu-deslop` |
| 审查稿件 | 审查、审稿、帮我审一下、一致性检查、看看有没有问题 | `/moshu-review` |
| 环境部署 | 部署墨枢写作环境、准备写书、搭环境、初始化 | `/moshu-setup` |
| 浏览器操控 | 浏览器、抓取、登录态 | `/moshu-cdp` |
| 导入小说 | 导入小说、导入书籍、反向解析、把我的书导进来 | `/moshu-import` |
| 学文风 | 学文风、这本书的文风、文风怎么样、风格 | `/moshu-style` |
| 工作台 | dashboard、工作台、看拆文库、浏览项目文件、打开项目面板 | 见下方「Dashboard 工作台」 |
| 检查/更新版本 | 检查更新、有新版本吗、升级、更新工具箱 | 见下方「版本更新检查」 |
| 切换/列出书目 | 切书、换书、列出我的书、我在写哪几本、切换项目 | 见下方「多书切换」 |
| 查故事资料 | 查角色、查伏笔、查进度、查设定、什么状态、写到哪了 | spawn `moshu-explorer` agent（结构化 prompt：`项目目录：{dir}\n查询类型：{根据意图选择}\n查询参数：{用户查询}`）；agent 不可用时见下方「查询降级」 |
| 查资料 | 查资料、帮我查资料、调研、搜索一下、搜一下 | spawn `moshu-researcher` agent；agent 不可用时见下方「查询降级」 |

> **范围声明**：本工具箱当前仅支持**长篇网文**（扫榜/拆文/写作/审查/导入均为长篇管线）。短篇/故事会/盐言等短篇创作不在支持范围——用户提到"写短篇/拆短篇"时明确说明并引导至长篇方向或外部短篇工具，不要静默落兜底反问。

## 状态判定（"继续 / 接下来"入口）

用户说"继续""接下来写什么""现在该干嘛"或请求模糊时，**先跑确定性判定脚本**（按解释器探测形态调用）：

```bash
for PYBIN in python3 python py; do "$PYBIN" -c "" 2>/dev/null && break; done
"$PYBIN" {moshu skill 根}/scripts/next_step.py --project {项目根}
```

脚本返回单行 JSON DTO（`step` / `interrupt` / `evidence` / `last_committed_chapter` / `next_action` / `suggested_skill`），按返回 DTO 行动——不再逐条读下方判定表。脚本不可用（Python 缺失/项目根不存在）时回退下表，判定语义与脚本一致（**命中即停**，不继续往下问）。

**优先中断项（与序位无关，命中即引导并停）**：① `拆文库/*/_progress.md` 最终状态非 completed → `/moshu-analyze` 续跑（断点恢复）；② `{项目根}/.moshu-review/` 下存在未完成审查状态（state 文件）→ `/moshu-review` 续批。这两项是"从进行中状态插入的中断"，先于下方序位检查（与《产品需求与详细设计文档》Ⅲ.9 状态机图的虚线边语义一致）。

| 序 | 判定条件（文件证据） | 引导 |
|---|---|---|
| 1 | 无 `.story-deployed`（未部署） | `/moshu-setup` |
| 2 | 无书名目录（无含 `正文/`、`大纲/`、`追踪/` 任一的项目目录） | 开书引导（或先扫榜/拆文/选题） |
| 3 | 有书但无 `正文/` | 首批细纲 + 写第 1 章（`/moshu-write`，细纲首建见 outline-workflow；设定缺失回 `/moshu-outline`，卷纲缺失回 `/moshu-volume`） |
| 4 | 有正文但下一章无细纲 | 补纲（`/moshu-write` 中途补纲/扩纲） |
| 5 | 下一章有细纲未写 | 日更/写下一章（`/moshu-write`） |
| 6 | 最新定稿章（追踪 last_committed_chapter）= 当前卷卷纲「章节范围」上界 | 卷复盘（`/moshu-write`，四步：伏笔清账/卷摘要/下卷规划/契约修订候选）；下卷规划转 `/moshu-volume` |
| 7 | 其余 | 询问意图（用路由表） |

判定依据全部来自文件系统（.story-deployed / 拆文库 `_progress.md` / 细纲章号 vs 追踪 last_committed_chapter / 卷纲末章 / `.moshu-review/` 状态文件），不依赖会话记忆。会话启动时 session-start hook 已注入近况（写作进度/当前位置/未完成拆文），本判定在其之上给出"下一步"。

> **导入续写顺序**：用户问"导入续写先 setup 还是 import"时直接回答——**推荐先 `/moshu-setup`，新开/刷新会话后 `/moshu-import`，最后 `/moshu-write 日更` 或 `/moshu-write 写第N章`**；用户已直接触发 `/moshu-import` 时按其自带环境检测继续。

## Dashboard 工作台

用户执行 `/moshu dashboard` 或明确说"打开工作台 / 看项目文件"时，直接启动随本 skill 分发的本地 Dashboard，不再转发到其他 skill：

1. 把**当前工作目录**作为默认工作区；用户明确给出目录时改用该目录（目录必须存在）。
2. 从当前已加载的 `moshu` skill 目录定位 `scripts/dashboard-server.mjs`，不要硬编码仓库/全局 skill/用户主目录路径。
3. 检查 `node` 可用后，以长运行进程执行：

   ```bash
   node "<moshu-skill-dir>/scripts/dashboard-server.mjs" --root "<workspace>" --open
   ```

4. 等待输出出现"本机地址"，把完整 URL 回给用户；无法自动拉起浏览器不算失败，仍返回可点击 URL。
5. Dashboard 默认只监听 `127.0.0.1`。不要主动增加 `--allow-network`，不要把工作区暴露到局域网或公网。
6. 停止服务时终止对应的 Node 长运行进程即可。用户只问用法时不替他启动，给出 `/moshu dashboard` 入口。

项目识别规则、可编辑扩展名与冲突保护细节见 [references/dashboard-guide.md](references/dashboard-guide.md)。

## 路由流程

1. 分析用户请求，提取意图关键词
2. 匹配路由表，找到对应的 skill
3. 能明确匹配 → 直接调用对应 skill（`Skill("skill-name")` 或 slash command）
4. 无法匹配 → 询问用户想做什么（从路由表中选择）

## 查询降级

> Spawn 版本提示（不阻断 spawn）：先读取项目根 `.story-deployed` 的 `agents_version`。与本版 `agents_version: 42` 不一致时（标记缺失、字段缺失/非整数、小于或大于 42）**照常按文件存在性检查并 spawn**，同时报告 `Notice: agents bundle 版本不匹配（项目 {N}，本版 42）` 并提示重新运行 `/moshu-setup` 后新开会话；大于 42 时额外提示先更新 mo-shu，不要用本地旧版 setup 降级覆盖。只有 agent 文件缺失、或运行时不暴露 custom agent 时才降级 solo/direct，报告 `Fallback: ... -> solo`（**注意**：下方「查询降级」的目标态是 `-> direct lookup`，两处措辞不同是有意的）。

「查故事资料」「查资料」走 agent 前先做轻量可用性检查（路由只做这一层，不承担全局部署策略）：当前不在子代理上下文、Agent/Task 工具可用、且 `.claude/agents/{moshu-explorer|moshu-researcher}.md` 存在 → 可尝试 spawn。任一不满足，则降级，不硬失败：

- `moshu-explorer` 不可用 → 主线程直接用 Read/Grep 从项目文件检索（角色状态/伏笔/进度/设定），回答前标注 `Fallback: agent unavailable -> direct lookup`；项目尚未部署时提示先 `/moshu-setup`。
- `moshu-researcher` 不可用 → 主线程用现有检索/回答能力完成，或提示用户改用 `/moshu-cdp` 采集，同样标注 `Fallback: agent unavailable -> direct lookup`。

## 项目状态感知

路由前先检查当前项目状态：

- **无项目目录**（没有包含 `追踪/` 或 `设定/` 的书名目录）：用户要写作 → 下一步先 `/moshu-setup`；要扫榜/拆文 → 直接路由。
- **已有项目**：检查 `.story-deployed` 标记，未部署则先 `/moshu-setup`。

## 多书切换

用户想切换或查看在写的书时（一个项目可同时有多本）：

1. 在项目根查找所有书目录：包含 `追踪/` 或 `设定/` 子目录的目录（含 `长篇/` 下的子目录；限项目下 4 层，跳过隐藏目录与 `node_modules`）。
2. 列出书名，标出当前 `.active-book` 指向的那本。
3. 让用户选择，把所选书的相对路径写入项目根 `.active-book`（覆盖原内容）。
4. 只发现一本时直接确认为活跃书，无需询问。

## 版本更新检查

用户问"有没有新版本""检查更新""升级"时执行。**只通知，更不更新由用户定，不自动安装。**

1. **当前版本**：读本 skill 同目录的 `VERSION` 文件；缺失则视为未知。
2. **最新版本**：`curl -fsS --max-time 5 https://api.github.com/repos/Chained1001/mo-shu/releases/latest` 取 `.tag_name`。查不到 → 告知"暂时拉不到最新版本，可手动看 [Releases](https://github.com/Chained1001/mo-shu/releases)"，不报错。
3. **比较**：去掉 `v` 前缀按语义版本比（major.minor.patch）。
4. **告知**：
   - 已最新 → 「已是最新版 vX.Y.Z」。
   - 有新版 → 列出 当前 vA → 最新 vB + [Releases](https://github.com/Chained1001/mo-shu/releases)/[CHANGELOG](https://github.com/Chained1001/mo-shu/blob/main/CHANGELOG.md)（能拿到 release notes 就附本次要点），再用 AskUserQuestion 问「现在更新吗？」：
     - 选更新 → 跑 `npx skills add Chained1001/mo-shu -y -g`（`-g` 全局，去掉则只更当前目录）；完成后提示：已部署过的项目在项目根重跑 `/moshu-setup` 同步 hooks/agents/references，并**新开一个会话**让 agents 重新注册。
     - 选先不 → 不动，告知随时可再来。

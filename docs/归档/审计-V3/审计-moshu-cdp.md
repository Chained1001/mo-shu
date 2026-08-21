# moshu-cdp 审计报告

- 审计日期：2026-08-21
- 对象：`skills/moshu-cdp/`（2 文件：SKILL.md 175 行 + `scripts/setup-cdp-chrome.js` 1008 行 / 41387 B）
- 方式：委派深审（**未启动 Chrome、未开 CDP 端口、未联网、`--dry-run` 亦未执行**，全部结论来自源码逐段阅读 + 既有测试/CI 配置）+ 本人复核 N1

## 一、结论

**作为"唯一允许被跨 skill 引用的基础组件"，定位纪律执行得很干净**：2 个文件、**零反向依赖**（不引用任何其他 skill），`static-check.py:65` 的 `FOUNDATION_SKILL_REFERENCES` 白名单正确地只为它开口。脚本工程质量是本次审计所见最高的之一——退出码契约（`SKILL.md:69` 的 0/1/2/3 ↔ 代码 `:691/:701`(0)、`:752/:828/:852`(1)、`:836`(2)、`:716`(3) 逐项一致）、`--detect-only` 无副作用、`--profile` 路径注入防护（`:74` 拒 `..`/分隔符）、**端口归属校验**（`:487-535` `verifyPortOwnedByLaunch` 三段失败分类，防"旧实例应答被误判为新实例"）、"先杀进程→确认端口空→才动 profile"的硬闸门顺序，都与文档对得上，且有 `test-scan-runtime.js` 夹具 + 两平台 `--dry-run` CI 冒烟覆盖。

**两个需修**：①引用路径 `{SKILL_DIR}/moshu-cdp/...` 按全仓既定语义不可解析（白名单只管"是否允许引用"，不管"路径是否有效"）；②登录态复用的真实拷贝范围超出文档描述，且清理契约不含"用完擦除"路径。

## 二、阻断级：0 项

## 三、需修级：3 项

### N1 `{SKILL_DIR}/moshu-cdp/scripts/setup-cdp-chrome.js` 按既定语义不可解析（5 处）✅本人复核成立

- **与 [审计-moshu-scan.md](审计-moshu-scan.md) 的 SM3 是同一发现**（两个子代理独立命中同一问题，交叉验证）。
- **证据（本人 `git grep` 精确 5 命中）**：`skills/moshu-scan/scripts/cdp-utils.js:8`、`fanqie-rank-scraper.js:18`、`jjwxc-rank-scraper.js:22`、`qidian-rank-scraper.js:26`、`qimao-rank-scraper.js:17`。占位符语义在全仓有 5 处一致定义（`moshu-deslop/references/deslop-workflow.md:69`、`moshu-review/references/review-workflow.md:132`、`moshu-scan/SKILL.md:66`、`moshu-write/references/workflow-chapter.md:148`、`workflow-daily.md:71`——均为"当前加载的**该** skill 根目录"）；moshu-cdp 自身按此语义写自根形式（`SKILL.md:25/:51/:126`）。代入 moshu-scan 的 `{SKILL_DIR}` 得 `skills/moshu-scan/moshu-cdp/scripts/...`，**不存在**。
- **影响**：这 5 行是脚本头部用法注释（非可执行代码，不影响采集运行），但正是 AI/人排障时照抄的那一行；4 个 scraper 的运行时报错都指向"按 moshu-cdp skill 重新启动"，照抄注释即得死路径。`doc-budget.json:25` 记载 P0-5 曾专门修过同类问题，此处是漏网。
- **无守卫（本人核对）**：`static-check.py:401-436` 的 `cross_skill_path_issues` 用正则判定**是否允许**跨 skill 引用，命中 `FOUNDATION_SKILL_REFERENCES`（`:65` = `{"moshu-cdp"}`）即 `continue` 放行（`:419-423`）——**从不校验路径是否真实存在**。
- **修法**：5 处统一改为不依赖占位符的表述（如 `node <moshu-cdp skill 根>/scripts/setup-cdp-chrome.js 9222`，与 `moshu/SKILL.md:67` 的 `<moshu-skill-dir>` 风格一致）；可选在 `moshu-scan/SKILL.md:66` 的定义句后补半句"跨 skill 引用 moshu-cdp 时按 moshu-cdp 自己的 skill 根定位"。**改动量**：5 文件各 1 行注释（+ 可选 1 行说明）。

### N2 登录态拷贝范围超出文档描述，且无"用完擦除"路径

- **现象**：文档把该机制描述为"复用登录态"/"重新拷贝"，实际代码把用户真实 Chrome profile **整目录复制**到 `~/chrome-debug-profile/Default`，并定点刷新包含**保存的密码**与**自动填充数据**的库文件；副本长期驻留，文档「停止 / 清理」节不涉及它。
- **证据（代码事实）**：目录位置 `setup-cdp-chrome.js:731`（`~/chrome-debug-profile`，与 `SKILL.md:65/:175` 一致）；整目录复制 `:614-616` `fs.cpSync(src, dest, {recursive:true, force:true})`、`:793` dry-run 自述；定点刷新清单 `:629-636` `refreshAuthFiles` targets = `Cookies`、`Cookies-journal`、**`Login Data`**、`Login Data-journal`、**`Login Data For Account`**、同 journal、**`Web Data`**、`Web Data-journal`、`Network/Cookies`、同 journal。文档侧：`SKILL.md:8`「复用已有登录态」、`:65` `--reset`「清空 `~/chrome-debug-profile`（登录失效时用）」、`:126/:173`「登录态过期 → `--reset --yes` 重新拷贝」——全文无 `Login Data` / 密码 / 自动填充字样；`:119-126`「停止 / 清理」只讲怎么关窗口与只杀 debug 实例，**不提副本残留**。
- **影响**：①知情同意面不完整——`:16` 与 `:53` 的确认话术只覆盖"会杀掉 Chrome、可能丢失未保存工作"，未覆盖"会把 cookie/密码库复制到第二个位置"；②副本驻留在可预测路径，生命周期只由 `--reset`（语义是"登录失效时重建"）间接管理，没有"任务完成后清理"的动作项。
- **（推断，非代码事实）**：Chrome 的 `Login Data` 受 OS 级密钥加密，同机同用户下副本仍可解密；跨机复制价值有限。故风险等级是"本机攻击面扩大 + 知情不足"，**不是明文泄露**。
- **日志侧无问题（代码事实）**：`refreshAuthFiles` 只回传计数（`:637` → `:645`），不打印文件名或内容；启动日志只输出平台/端口/profile 名（`:747`）、Chrome 可执行路径（`:754`）、profile 目录路径（`:772`）。**未发现任何 token/cookie/密码内容进日志或产物。**
- **修法（不改代码）**：`SKILL.md` 两处文档补充——①`:16` 的 ⚠️ 提示块追加"启动会把当前 Chrome profile（含 cookie、保存的密码与自动填充数据）复制一份到 `~/chrome-debug-profile`；向用户征求同意时一并说明"；②「停止 / 清理」`:119-126` 末尾加"不再需要浏览器自动化时，删除 `~/chrome-debug-profile` 可清除该登录态副本"。**改动量**：1 文件 2 处 / ~3 行。

### N3 「按可执行名清理」的适用范围被文档窄化为 `--reset`

- **证据**：`SKILL.md:125`「例外：`setup-cdp-chrome.js --reset` 内部确实会做一次按可执行名的清理…」；实际 `config.killChrome()` 调用点是 `:842` 与 `:845`（第 5 步"杀死现有 Chrome 进程"），位于 `main()` 主流程，**前置条件只有"有 Chrome 在跑 + 已获同意"**（`:832-837`），与 `--reset` 无关——即 `SKILL.md:51` 文档化的 `9222 --yes` 同样触发。win32 实现 `:157` `taskkill /F /IM chrome.exe`（结束**全部** chrome.exe），darwin `:130` `pkill -9 -x 'Google Chrome'`。
- **影响**：`:16` 顶部 ⚠️「首次启动会 kill 用户的常规 Chrome」已如实告知总体风险，故**不构成安全缺口**；问题在 `:125` 把范围说窄了，读到该节的 AI/用户可能推断"不带 `--reset` 的普通启动不会连坐"。该节本意（"手工排障不得按可执行名批量杀"）依然正确。
- **修法**：`:125` 的 `--reset` 改为「`setup-cdp-chrome.js` 的启动流程（任何需要先关闭现有 Chrome 的分支，含 `--reset`）」。**改动量**：1 行 1 句。

## 四、候选级

| 编号 | 发现 | 证据 | 修法 |
|---|---|---|---|
| NC1 | 同意闸门这条最关键的安全叙述无任何守卫 | `behavior-contracts.json` 11 条全指 `moshu-write`，cdp 与 moshu 均 0 条；`SKILL.md:53`「**先用 AskUserQuestion 工具向用户确认**」与 `:55`「不要看到 3 就盲传 `--yes`」是唯一防"静默杀掉用户浏览器"的叙述性约束。代码侧兜底仍在（`:713-717` 非 TTY 无 `--yes` → exit 3），故非安全缺口，是**叙述漂移无守护** | 加 1 条 contract（path `skills/moshu-cdp/SKILL.md`、must_contain「先用 AskUserQuestion 工具向用户确认」）；JSON +6 行 + 2 处同步。注意会使契约数变 12（与 G7 合并处理） |
| NC2 | `moshu-cdp/SKILL.md` 未进 doc-budget（4127 去空白） | `doc-budget.json` 12 项内无它 | 若采纳 G5 的整体收口则一并登记（budget 4200）；否则可不动 |
| NC3 | `agent-browser` 前置依赖无探测（`--detect-only` 输出契约 `:31-36` 不含依赖项），真正报错发生在 scan 侧运行时 | 降级措辞两侧**一致**（`fanqie:256`、`jjwxc:207`、`qimao:306` 均为「✗ CDP 无响应。请确认已用 moshu-cdp 启动 Chrome（端口 N），且 agent-browser 可用。」）→ 维度 8 判定通过 | 可不改；若改则 `--detect-only` 增 `AGENT_BROWSER=yes\|no` + 文档同步（属新增契约，需权衡） |
| NC4 | `Node.js 20+` 无运行时或 `engines` 校验（**存疑是否需要**） | `SKILL.md:13` 声明；脚本无 `process.version` 检查；根 `package.json` 是 dashboard 测试专用（`name: mo-shu-dashboard-tests`），不覆盖 skill 运行时 | **不建议**为此新增校验（AGENTS.md §5 决策树第 1 问"能否不新增"） |
| NC5 | 记录：SKILL.md 实际 175 行（此前口径称 152 行） | node 计数 175 行 / 6851 B | 非缺陷，仅对账 |

## 五、覆盖矩阵

| 维度 | 判定 | 守卫 |
|---|---|---|
| 基础组件定位：谁引用它 | ✅ 已枚举（moshu-scan 主消费者 19 处，另 moshu-setup 2、moshu-style 1、moshu 路由 2） | `static-check.py:65` 白名单 |
| **引用路径是否有效** | ❌ **5 处不可解析** | **无**（白名单只判许可不判存在性）→ N1 |
| 反向依赖（cdp 引用别的 skill = 违规） | ✅ **零反向依赖**（对 8 个兄弟 skill 名 grep 仅命中自身 frontmatter） | `cross_skill_path_issues` |
| 用户数据目录/端口/profile 与文档一致 | ✅ 一致 | `test-scan-runtime.js` 夹具 + 双平台 `--dry-run` CI |
| **登录态处理范围 vs 文档** | ❌ 文档窄于代码 | 无 → N2 |
| 敏感内容进日志/产物 | ✅ **未发现** | 无 |
| 按可执行名批量杀的适用范围 | ❌ 文档窄化 | 无 → N3 |
| 退出码契约 | ✅ 逐项一致（0/1/2/3） | 无显式断言 |
| `--detect-only` 输出契约 | ✅ 一致（`CHROME_INSTALLED=no` 时不再输出 `CHROME_RUNNING`，`SKILL.md:44` ↔ `:738-742`） | 无 |
| 降级与错误契约 | ✅ 明确且两侧对得上 | `test-scan-runtime.js` |
| 死链/孤儿 | ✅（无 references 故无孤儿） | `static-check.py` |
| 行为契约 | ❌ 0 条 | → NC1 |
| 可数声明（选项 5 / 退出码 4 / 平台 3） | ✅ 全部与代码一致 | 无 |

**"改了不会被任何守卫发现"的面**：跨 skill 引用路径写错（白名单放行后不再校验存在性，N1 即活实例）；SKILL.md 全部叙述性安全约束（0 条 behavior-contract）；退出码/`--detect-only` 契约的文档侧；SKILL.md 体量（未进 doc-budget）。

## 六、实测记录

| 检查 | 结果 |
|---|---|
| **本人复核 N1** | `git grep 'SKILL_DIR}/moshu-cdp'` 精确 5 命中 → 成立 |
| 正向引用图 | `git grep moshu-cdp -- skills ':(exclude)skills/moshu-cdp/*'` → 19 命中（scan 14 / setup 2 / style 1 / moshu 2） |
| 反向依赖 | 对 8 个兄弟 skill 名 grep → 仅 1 命中且为自身 frontmatter `SKILL.md:2` → **零反向依赖** |
| 测试/CI 覆盖 | `cross-platform.yml:65`（`node --check` 语法校验）、`:185`（windows `--dry-run`）、`:241`（macos `--dry-run`）、`test-scan-runtime.js:852/1057/1063/1447/1460`（`--reset` 闸门夹具 + 假 pgrep/pkill 场景）→ **三层覆盖，并非无测试** |
| 代码逐段阅读 | `:24`、`:63-96`（argv + `--profile` 防注入）、`:487-535`（端口归属三段分类）、`:614-646`（profile 复制与 auth 刷新）、`:676-702`（detect-only）、`:708-723`（同意闸门）、`:812-881`（主流程杀进程与端口硬闸门） |
| 未复现项 | Chrome/CDP 实机、`--dry-run`、`--allow-network` 分支均未执行（红线） |

## 七、整改计划

| 编号 | 级别 | 修法 | 改动量 | 依赖 | 验收 |
|---|---|---|---|---|---|
| **N1** | 需修 | 5 处 CDP 路径注释改写（**与 scan 的 SM3 是同一改动，合并执行**） | 5 文件 / 各 1 行 | 无 | `git grep 'SKILL_DIR}/moshu-cdp'` 零命中 + `static-check.sh` |
| N2 | 需修 | SKILL.md 补 profile 拷贝范围披露 + 清理指引 | 1 文件 / ~3 行 | 无 | `static-check.sh`；人工核对话术 |
| N3 | 需修 | `:125` 适用范围表述修正 | 1 行 | 无 | `check-current-skill-contracts.sh`（含 CDP 进程名规则 `:183-189`） |
| NC1 | 候选 | 同意闸门进 behavior-contracts | +6 行 + 2 同步 | 与 G7 合批（契约数变化） | `check-behavior-contracts.sh` + `test-behavior-contracts.py` |
| NC2 | 候选 | 进 doc-budget（4200） | +5 行 | 随 G5 | `check-doc-budget.sh` |
| NC3-NC5 | 候选（建议不做） | 见上表 | — | — | — |

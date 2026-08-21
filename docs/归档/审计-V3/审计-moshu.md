# moshu（路由与 Dashboard）审计报告

- 审计日期：2026-08-21
- 对象：`skills/moshu/`（6 文件：`SKILL.md` 131 行 / `VERSION` / `assets`×3 / `scripts/dashboard-server.mjs` 1023 行）
- 方式：委派审计（子代理深审）+ **本人独立复核关键结论**（复核结果逐条标注）。未运行 `dashboard-server.mjs`（长驻服务红线），Dashboard 结论来自静态阅读 + 既有测试/CI 配置。

## 一、结论

**路由表健康**：10 个 skill 全覆盖（含 `moshu-style`），无悬空路由、无漏路由（脚本枚举实测：`NOT routed = []`、`routed but nonexistent = []`）。**Dashboard 是全仓覆盖最好的组件**——安全边界（只监听 127.0.0.1、`--allow-network` 需显式且强制 token、编辑扩展名白名单、保存/删除前 sha256 版本校验）代码与文档逐项一致，且有 29 个单测 + e2e + 三平台 CI 矩阵（`dashboard.yml`）。批 4 跳过的连锁处理干净：`next_step.py` 活引用已清零，仅剩规划文档的历史说明行。

**问题两类**：①**状态判定 9 序的线性"命中即停"语义与 `docs/architecture.md` §3 的 overlay 模型冲突，导致两条断点恢复规则实际不可达**（唯一有功能影响的发现）；②版本/清单类断言多点漂移，且这些面**全部无守卫**——其中 `check-story-numbers` 在两个 README 上是一次 **vacuous pass**（实测 README 里没有任何「N 个 skill」字样，守卫无断言对象）。

## 二、阻断级：0 项

## 三、需修级：5 项

### M1 状态判定序 3 / 序 8 被前序规则遮蔽，断点恢复不可达 ✅本人复核成立

- **现象**：`SKILL.md:36` 规定「**命中即停**，不继续往下问」。该语义下两条规则被吃掉：
  - 序 3（`拆文库/*/_progress.md` 未完成 → `/moshu-analyze` 续跑）被序 2（无含 `追踪/` 的书名目录 → 开书引导）遮蔽——而"先拆文、还没开书"正是 README 主流程（扫榜→拆文→开书）的自然状态；
  - 序 8（`.moshu-review/` 有未完成审查 → `/moshu-review` 续批）被序 5/6/7 遮蔽——有正文时"下一章无细纲"与"有细纲未写"互补穷尽，卷末则序 7 命中，序 8 恒不可达。
- **证据**：`skills/moshu/SKILL.md:36`（命中即停）、`:41`（序 2）、`:42`（序 3）、`:44-46`（序 5/6/7）、`:47`（序 8）。对照 `docs/architecture.md:76-77` 把这两条建模为**虚线 overlay 边**（`S2 -.->|未完成拆文| A`、`S3 -.->|未完成审查| R`），即"从状态内插入的中断"而非线性序位——**两文档模型不一致**。`拆文库/` 与书名目录同级独立（`dashboard-server.mjs:300` `resolve(root, "拆文库")`；fixture `tests/fixtures/dashboard/拆文库/盘龙/_progress.md` 与 `tests/fixtures/dashboard/长篇/{书}/` 并列），故"有拆文无书"是真实可达状态。
- **影响**：`/moshu-analyze` 断点恢复与 `/moshu-review` 续批在最需要的场景拿不到引导，用户只得到通用开书/日更引导。
- **修法**：把两条提为表前「优先中断项」（与 architecture 虚线语义对齐）：在 `:36` 命中即停之后加一句"先做两项与序位无关的中断检查（命中即引导并停）：① `拆文库/*/_progress.md` 最终状态非 completed → `/moshu-analyze` 续跑；② `{项目根}/.moshu-review/` 有未完成 state → `/moshu-review` 续批"，并删表内序 3、序 8 行、序号顺延。CHANGELOG 历史条目不改（`scripts/README.md:24` 排除约定）。
- **改动量**：1 文件 / 净 +2−2 行。

### M2 `blob/master` 死链（默认分支是 main）✅本人复核成立

- **证据**：`skills/moshu/SKILL.md:129` → `https://github.com/Chained1001/mo-shu/blob/master/CHANGELOG.md`；`git symbolic-ref --short HEAD` = `main`，`origin/HEAD -> origin/main`；`git grep 'blob/master'` **全仓单命中**。
- **影响**：升级决策路径上的 CHANGELOG 链接 404。
- **无守卫**：`static-check.py` 显式排除外部 URL（`EXTERNAL_URL_RE`），此类死链永不被发现。
- **修法**：`master` → `main`。**改动量：1 行 1 词。**

### M3 marketplace 版本漂移（4 处）——与 [G1](审计-跨skill与仓库级.md) 同一发现，交叉验证一致 ✅

子代理独立得出与本人相同的结论（moshu-write 1.1.1↔1.2.0、moshu-setup 1.2.11↔1.3.0、moshu-review 1.1.5↔1.2.0、`metadata.version` 1.1.1↔发布线 1.3.0；根因 `8ae77b2` 未含 marketplace.json；`check-claude-adapter.sh` 不比版本）。修法与改动量见 G1。

### M4 同一 SKILL.md 内三套「书目录」判据互不一致 ✅本人复核成立

| 位置 | 判据 |
|---|---|
| `SKILL.md:41`（序 2） | 含 `追踪/` |
| `SKILL.md:106`（项目状态感知） | 含 `追踪/` **或** `设定/` |
| `SKILL.md:115`（多书切换） | 含 `追踪/` **或** `设定/`（含 `长篇/` 下子目录） |
| `dashboard-server.mjs:25`（代码，不同用途） | `正文`/`大纲`/`设定`/`追踪` 任一 |

- **影响**：一本只有 `设定/` 尚无 `追踪/` 的书（开书 Phase 1-2 中途），按序 2 判"无书名目录"→引导重新开书，按 `:106` 判"已有项目"——同一会话两条规则给相反结论。
- **修法**：`:41` 括号注释统一为「含 `追踪/` 或 `设定/`」（或加"判据同下方「项目状态感知」"）。dashboard 那套是文件浏览器宽口径，**不必**统一。**改动量：1 行。**

### M5 同一文件内降级 token 自相矛盾 ✅本人复核成立（定性已修正）

- **现象**：`SKILL.md:95` 对"agent 文件缺失/运行时不暴露 custom agent"规定报 `Fallback: ... -> solo`；`:99-100` 对同一触发条件用 `Fallback: agent unavailable -> direct lookup`。
- **本人复核修正的定性**：子代理称 `review-workflow.md:16/:392` 是"全仓枚举权威"——**不准确**。经复核，那两行是 **moshu-review 报告头的专用契约**（`:329` 明确"五个英文 key 必须逐字保留"，属 review 报告格式），moshu 路由不产 review 报告头，**不受该枚举约束**。因此本项的真问题只有一条：**同一文件内两处措辞冲突**（`-> solo` vs `-> direct lookup` 覆盖同一条件），使 LLM 输出哪个 token 不确定；而 `README.md:80` 教用户按 `Fallback: ... -> solo` 判断 agent 是否注册成功。
- **修法（缩小到最小）**：在 `:95` 末尾补"（路由的查询降级目标态是 `-> direct lookup`，见下方「查询降级」）"消歧即可；`-> direct lookup` 这个目标态本身是正确的（路由降级走主线程 Read/Grep，不是 review 的 solo 模式），**不改 token**。**改动量：1 文件 / 1 行**（子代理原建议改 3 文件 5 行，经复核可省）。

## 四、候选级：5 项

| 编号 | 发现 | 证据 | 修法 / 改动量 |
|---|---|---|---|
| C1 | `moshu/SKILL.md` 未进 doc-budget，且守卫**不探测未登记热路径**（`check-doc-budget.sh` 只遍历 `manifest.files`） | 实测体量 4657 去空白字符；同类未登记：`moshu-cdp` 4127、`moshu-style` 3966、`moshu-scan` 8610、`moshu-setup` 8627 | 把 `moshu/SKILL.md` 登记（budget 4700）；scan/setup 是否登记另议。`doc-budget.json` +5 行 |
| C2 | 路由关键词是各 skill 触发词的子集：`:16` 缺「回炉/重写第X章」、`:17` 缺「深度拆解」 | `SKILL.md:16/:17` vs 各 skill frontmatter 触发词 | 补 2 处关键词 / 2 行（Claude Code 也会按 skill description 直接命中，故仅体验损耗） |
| C3 | 「去 AI 味」空格写法与 deslop 侧「去AI味」不一致 | `moshu/SKILL.md:20` vs `moshu-deslop/SKILL.md:4`、`README.md:93`；术语表未收录该词条，**不构成术语违规** | 统一无空格 / 1 行 |
| C4 | 多书切换未声明扫描深度与排除规则（其余三端已统一 4 层 + 跳隐藏目录/`node_modules`） | `SKILL.md:115` 无深度措辞；对照 `CHANGELOG.md:233`「四端范围一致」、`dashboard-server.mjs:377` `shouldIgnoreDirectory` | `:115` 补"（限 4 层，跳隐藏目录与 `node_modules`）" / 1 行 |
| C5 | `STORY_DASHBOARD_HOST/_PORT` 两个环境变量在 help 与文档均未出现 | `dashboard-server.mjs:865/:866`（vs `:869` TOKEN 已在 help）；`printHelp:975-981` | help 两行各补一句 / 2 行。**已核实无安全缺口**：`:899` 闸门对 host 来源不作区分，单设 `HOST=0.0.0.0` 仍被 `network_binding_requires_opt_in` 拒 |

## 五、覆盖矩阵

| 维度 | 判定 | 守卫覆盖 |
|---|---|---|
| 路由表完整性（10/10） | ✅ | 仅「工作台」1 行被逐字断言（`dashboard-trigger-contract.test.mjs:21`），其余 14 行无守卫 |
| 状态判定可判性 | ❌ 序 3/8 不可达（M1） | 无 |
| 与 architecture §3 一致 | ❌ 模型冲突（M1） | 无 |
| `next_step.py` 悬空引用 | ✅ 已清零（活引用 0；`evals/scenarios/开书/README.md:6` 标注"不含 next_step 断言"） | 无（靠人工终检） |
| Dashboard 安全边界 | ✅ 全项一致 | 29 单测 + e2e + 3 平台 CI |
| 项目识别规则（拆文库/存量兼容/符号链接） | ✅ | 单测覆盖 |
| 版本四口径 | ❌ 4 处漂移 + 1 死链 | **无** |
| `.active-book` 语义 | ✅（`README.md:191` ↔ `SKILL.md:117` 同为相对路径） | — |
| 死链/孤儿 | ✅ 本地全绿 | `static-check.py`（外部 URL 除外 → M2） |
| 术语禁用别称 | ✅ 零违例 | 无自动守卫 |

**"改了不会被任何守卫发现"的面**：marketplace 任何版本号；`skills/moshu/VERSION`（无引用方）；路由表除「工作台」外 14 行；「状态判定」整表；外部 URL 死链；`docs/**` 与 `references/**` 里的 `agents_version`/schema 数字；未登记进 doc-budget 的热路径体量；`Fallback:` token；README Skills 表行数。

## 六、实测记录（含本人复核）

| 检查 | 结果 |
|---|---|
| 守卫复演 7 项（`static-check` / `skill-numbering` / `check-behavior-contracts` / `check-current-skill-contracts` / `sync-shared-assets` / `check-agents-version-sync` / `check-story-numbers`） | 全 exit 0 |
| 路由覆盖脚本 | routed 9（除 moshu 自身）；`NOT routed = []`；`routed but nonexistent = []` |
| **本人复核 M2** | `git grep 'blob/master'` 单命中 `SKILL.md:129`；`HEAD = main`、`origin/HEAD -> origin/main` → **死链成立** |
| **本人复核 M6→G2** | `git grep '个 skill\|个 Skill\| skills' -- README.md README_EN.md` → 命中均为 npx 命令/7 agents/无关行，**无任何「N 个 skill」断言对象** → `check-story-numbers` 在 README 上确为 vacuous pass |
| **本人复核 M5** | `review-workflow.md:16/:392` 枚举确实全为 `-> solo` 且无 `agent unavailable`，但 `:329` 证明其为 review 报告头专用契约 → 定性下调为"同文件内措辞冲突" |
| 体量核对（node 权威计数） | `SKILL.md` 131 行 / 9994 B；`dashboard-server.mjs` 1023 行 / 34528 B；skill 共 6 文件 |
| 行末尾 | `git ls-files --eol` 全仓无 `i/crlf`/`i/mixed`（`w/crlf` 属本地检出态，非缺陷） |
| 未复现项 | `node --test tests/dashboard-server.test.mjs` 未跑（长驻服务/端口红线）；`--allow-network` 分支未执行 |

## 七、整改计划

| 编号 | 级别 | 修法 | 改动量 | 依赖 | 验收命令 |
|---|---|---|---|---|---|
| **M1** | 需修（唯一功能影响） | 序 3/8 提为表前「优先中断项」，9 序→7 序 | 1 文件 / ±2 行 | 无（未进 doc-budget，无预算冲突） | `static-check.sh` + 人工走查 `evals/scenarios/开书` |
| M2 | 需修 | `blob/master` → `blob/main` | 1 行 | 无 | `git grep blob/master` 零命中 |
| M3 | 需修 | 见 G1 | 见 G1 | — | `check-claude-adapter.sh` |
| M4 | 需修 | `:41` 判据与 `:106`/`:115` 统一 | 1 行 | 无 | `static-check.sh` |
| M5 | 需修 | `:95` 补消歧半句（不改 token） | 1 行 | 无 | `static-check.sh` |
| C1 | 候选 | `moshu/SKILL.md` 进 doc-budget（4700） | +5 行 | G5 之后 | `check-doc-budget.sh` |
| C2/C3/C4 | 候选 | 路由关键词补 2 处 / 统一「去AI味」/ 多书切换补深度 | 4 行 | C1（若登记则受预算约束） | `check-doc-budget.sh` + `static-check.sh` |
| C5 | 候选 | `printHelp` 补两个环境变量说明 | 2 行 | 无 | `node --test tests/dashboard-trigger-contract.test.mjs`（不断言 help，安全） |

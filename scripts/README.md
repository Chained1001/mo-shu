# scripts/ —— 仓库开发脚本索引

这些是开发本仓库（skill 套件本体）用的**守卫 / 测试 / 代码生成**脚本，**不是** skill 运行时脚本（运行时脚本在各 skill 自己的 `scripts/` 下，如 `moshu-deslop/scripts/check-ai-patterns.js`，跨 skill 字节同步）。

- 绝大多数由 CI 自动跑（`.github/workflows/cross-platform.yml`）。提交前本地一把梭的完整命令见 [CONTRIBUTING.md](../CONTRIBUTING.md)「CI 检查」。
- **改名 / 移动任一脚本**，要同步改 `.github/workflows/*.yml`、`CONTRIBUTING.md`、本文件，以及调用它的兄弟脚本（见下方「何时跑」里的调用关系）。

## 静态守卫（check-*）

| 脚本 | 检查什么 | 何时跑 |
|---|---|---|
| `static-check.sh` + `static-check.py` | 结构化验证 frontmatter、Markdown 路径/锚点、Agent 引用、references 可达性；除基础组件 `moshu-cdp` 外禁止跨 Skill 文件引用 | CI |
| `skill-numbering.py check` | 工作流 Step/Phase/Stage 编号策略、引用绑定、SKILL.md 裸编号/子步骤小数守卫 | CI；改工作流结构后 |
| `check-current-skill-contracts.sh` + `.py` + `current-contract.json` | 从结构化 manifest 校验当前版本、Phase、schema、主产物与细纲契约；保留 legacy/path 守卫并拦截缺主产物后的静默替代 | CI |
| `check-shared-files.sh` | 调 `sync-shared-assets.py check` 验 runtime 副本，再验 64 组共享 reference 字节一致 | CI |
| `check-moshu-setup-deployment.sh` | moshu-setup 部署/运行时回归（慢，>2min） | CI |
| `check-doc-budget.sh` + `doc-budget.json` | 热路径 SKILL/references/agent 模板的去空白字数预算与路径合计上限；超了要么删等量旧文本，要么显式调高 budget | CI；增删热路径正文后 |
| `check-hook-regex-sync.sh` | `detect-story-gaps.sh` 伏笔状态检测行为 | CI |
| `check-hook-locale-safety.sh` | 部署 hook 在 Windows 中文 GBK 区域的字节安全 | CI |
| `check-python-invocation.sh` | 技能文档禁止裸调 `python3`（须 python3→python→py 探测） | CI |
| `check-claude-adapter.sh` | Claude marketplace 与全部 skill 的一一映射；可选真实 CLI strict validate | CI（静态）；`CLAUDE_REAL_CHECK=1`（真实 CLI） |
| `check-behavior-contracts.sh` + `behavior-contracts.json` + `check-behavior-contracts.py` | 关键行为约束静态守卫：契约清单里的约束文本必须存在于对应文档（裸调用停靠 / 细纲优先 / S1-S2 过桥 / 追踪事务等），防止 skill 迭代丢约束导致行为漂移 | CI；改动 SKILL.md / workflow-*.md / tracking-transaction.md 后 |
| `check-agents-version-sync.sh` + `check-agents-version-sync.py` | agents_version 一致性守卫：7 个 SKILL.md 中带数字的 `agents_version` 声明必须与 `moshu-setup/UPGRADING.md` 权威一致，防升级漏改导致误判降级 | CI；bump agents_version 时 |
| `check-story-numbers.sh` + `check-story-numbers.py` | 叙述性 skill 计数守卫：README / README_EN / CONTRIBUTING / scripts-README / architecture 中「N 个 skill」「N skills」必须与 skills/ 实测数一致（CHANGELOG 排除——历史条目不可改） | CI；增删 skill 或改动上述文档数字后 |
| `check-agent-template-rules.sh` + `check-agent-template-rules.py` | agent 模板纪律守卫：禁互引（格式同/同上/参照上文/见上文）、`agent-references/` 挂载点文件存在、共享纪律单副本（标题不得复制进模板） | CI；改 agent 模板或 agent-references 后 |
| `check-eval-scenarios.sh` | 场景剧本静态校验（不跑 LLM）：3 剧本存在非空、各含断言节与 ≥3 条 `[机检]` 标记、引用脚本路径存在 | CI；改 evals/scenarios 或引用脚本后 |

## 测试回归（test-*）

| 脚本 | 测什么 | 何时跑 |
|---|---|---|
| `test-ai-patterns.sh` | 确定性 AI 句式检测器 `check-ai-patterns.js` 回归 | CI |
| `test-outline-copy.sh` | 细纲照搬检测器 `check-outline-copy.js` 回归 | CI |
| `test-degeneration.sh` | 模型退化检测器 `check-degeneration.js` 回归 | CI |
| `eval-prose-quality.sh` | 端到端正文质量评测：整篇基准样本 × 全部确定性检测器，断言缺陷样本命中 > 干净样本且干净 blocking=0（`evals/`） | CI（runtime-regressions）；检测器/方法论改动后 |
| `test-prose-backstop-hook.sh` | `check-prose-after-write.sh` 回归 | CI |
| `test-story-continuity.sh` | `detect-story-gaps.sh` 跨批连续性兜底回归 | CI |
| `test-tracking-workflow-contracts.py` | 文件优先追踪契约：唯一事务写入口、续写状态卡（固定 7 栏）、导入基线、作者/读者时间线隔离、旧结构清零 | CI |
| `test-tracking-commit.py` | 单权威追踪行为：state 最后提交、失败同事务重跑、派生一致性、修订语义、导入截止章 | CI |
| `test-static-check.py` | 真 frontmatter block、精确路径/锚点、跨 Skill 引用、fence、死 reference、Agent 与章节链接 fixture | CI |
| `test-current-skill-contracts.py` | current-contract manifest 类型/固定值与主产物 fail-fast 语义 fixture | CI |
| `test-shared-assets.py` | 共享资产 manifest 的 drift、sync、路径越界、basename 单一 owner 与未登记重复检测 | CI |
| `test-normalize-punctuation.js` | 标点归一化的只读检查、frontmatter/fence、CRLF、引号模式与幂等性 | CI |
| `test-scan-runtime.js` | CDP argv 边界/报错/JSON 契约与 5 个 scraper 无副作用 import | CI |
| `test-scan-analyze.js` | scan-analyze 4 平台通用提取回归：平台识别/字段适配/晋江题材缺失/`--dup` 跨平台聚合/无单位重复 | CI（调 scan-analyze，fixture 在 `tests/fixtures/scan/`） |
| `test-merge-summaries.js` | merge-chapter-summaries 回归：自然排序/拼接完整/无损校验失败删文件/空目录/CRLF 兼容 | CI（调 moshu-analyze 拼接脚本） |
| `test-charcount-portable.sh` | 跨平台字符统计命令在三平台 + Windows 的正确性 | CI（调 check-python-invocation） |
| `test-hook-encoding-portable.sh` | 部署 hook 在 Windows 中文系统的编码健壮性 | CI |
| `test-skill-numbering.sh` | Step 重排级联安全、锚点 fail-closed、代码块引用、验证零写入/提交回滚、dry-run/write/幂等性 | Linux / Windows Git Bash / macOS CI |
| `test-behavior-contracts.py` | 行为契约守卫回归：正向（真仓库 10 条约束在位）+ 反向（fixture 删约束必须失败且指向契约 id） | CI（调 check-behavior-contracts） |
| `test-agents-version-sync.py` | agents_version 守卫回归：正向（真仓库一致）+ 反向（fixture 改一处版本必须失败） | CI（调 check-agents-version-sync） |
| `test-story-numbers.py` | 叙述计数守卫回归：正向（fixture 数字与实测一致→退出 0）+ 反向（中文/英文数字不一致→退出 1 且指向文件） | CI（调 check-story-numbers） |
| `test-prose-candidates.js` | 正文候选类机检回归：正向（意象重复+登记信息差关键词命中）+ 反向（干净文本空候选）+ 降级（缺 style/gaps、坏格式）+ 幂等（同输入逐字节一致） | CI（调 moshu-write 的 check-prose-candidates.js） |
| `test-review-tickets.py` | 审查工单回归：write 合法+幂等 / 坏枚举/重复 id/坏令牌拒 / resolve 单向流转 / list 过滤 / verify-token 相等与不等 | CI（调 moshu-review 的 review_tickets.py） |
| `test-agent-template-rules.py` | 模板纪律守卫回归：正向（干净模板通过）+ 反向（互引句/挂载点缺失/复制纪律标题必须失败） | CI（调 check-agent-template-rules） |
| `test-writing-pipeline.sh` | 零 LLM 管道契约 e2e：init→commit（伏笔+信息差）→check（含 suspension_warnings）→volume-report（重放 diff 空）→review_tickets write/resolve/list→check-prose-candidates（blocking_count=0），临时目录自清理 | CI；改任一管道脚本后 |

## 测试纪律

- **守护对象声明**：每个 `scripts/test-*` 头部必须有一行式声明：`守护对象：<一句话>。禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。`（.py 写进 docstring，.sh 用 `#` 注释行，.js 用 `//` 注释行）——说明这个测试在长期守护什么，防止删改时误伤。
- **准入三条件**（新增架构/契约类正式回归时）：① 守护跨模块稳定不变量；② 直接覆盖统一收口；③ 普通迭代不会频繁改断言。凡主要断言 prompt 措辞、供应商参数、单接口结果、README 字符串者，禁止进入正式回归。
- **测协议不测实现**：断言事件/状态机终态/注册表一致性/回放能力，不断言 prompt 全文或生成结果快照。
- **禁脆弱快照**：不断言整段 HTML / prompt / 生成结果；禁真实上游（LLM / 联网 / API key）——需要外部能力的场景用 fixture 或临时验证。
- **临时验证不入库**：只回答"现在是否正常"→ 用 `/.tmp/tests/<任务>/` 临时验证并删除；要防止"以后再次坏掉"才写正式回归。
- **失败先判因**：失败先判因再改代码，禁止改断言变绿。

## 代码生成 / 同步

| 脚本 | 干什么 | 何时跑 |
|---|---|---|
| `shared-assets.json` + `sync-shared-assets.py` | 为必须随 skill 独立部署的重复 runtime 脚本指定唯一源和目标 | 改共享 runtime 后跑 `sync`；CI 跑 `check` |

## 工作流编号维护

`skill-numbering.py` 默认扫描 canonical `skills/**/*.md`，用于阻止迭代插入把工作流编号累积成 `Step 1.3`、`Phase 2.5` 一类小数标签。

```bash
python3 scripts/skill-numbering.py audit          # 只读盘点；发现问题仍退出 0
python3 scripts/skill-numbering.py check          # CI 守卫；发现问题退出非 0
python3 scripts/skill-numbering.py fix --dry-run  # 先看完整 diff，不落盘
python3 scripts/skill-numbering.py fix --write    # 校验通过后一次性落盘
bash scripts/test-skill-numbering.sh              # 隔离 fixture 回归
```

维护策略：

- 只有形如 `### Step N` 的**显式 Step 标题**会自动重排；分组键是「文件 + 标题层级 + 最近父标题」，每组从 1 连续编号。
- 标题与可唯一绑定的 `Step N` 引用基于旧文本同时换号，包含 fenced code block 内的命令/示例引用，避免 `1.5 → 2` 后又被 `2 → 3` 二次级联。
- fractional Step 引用找不到本文件标题，或一个旧标签可能映射到多个新标签时，`fix` 会在任何写入前失败。多文件写入先全量校验/暂存并带回滚，不接受半套结果。
- 标题改号会改变 GitHub Markdown anchor；只要仓库内存在指向旧 anchor 的同文件或跨文件链接，`fix` 就在写入前 fail-closed，并报告每个 fragment，要求先显式更新链接后再重试。局部路径模式同样扫描仓库内入站链接。
- `Step N.M` / `Phase N.M` / `Stage N.M`、直接 `skills/*/SKILL.md` 中的裸小数标题及 bullet 小数子步骤由 `check` 报错，但不做猜测式自动修改。
- `references/` 手册本身的 `3.1` 章节/列表编号不属于工作流标签，不检查、不改写。如果管道 ID 需要插入中间阶段，使用语义名称或 `Stage 2A`，不用小数。
- 可在命令末尾传文件或目录做局部审计，例如 `... audit skills/moshu-write/SKILL.md`；合入前仍须跑默认全量 `check`。

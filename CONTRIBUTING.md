# 贡献指南

感谢你对网文写作 skill 包的关注，欢迎贡献。

## 仓库结构

```
skills/
├── moshu/                   # 工具箱路由
├── moshu-setup/             # 环境部署
├── moshu-import/            # 逆向导入
├── moshu-write/        # 长篇写作
├── moshu-analyze/      # 长篇拆文
├── moshu-scan/         # 长篇扫榜
├── moshu-deslop/            # 去AI味
├── moshu-style/             # 文风学习
├── moshu-review/            # 多视角审查
├── moshu-cdp/             # 浏览器操控
├── moshu-research/          # 采风研究（结构/角色/设定机制三类参照）
└── moshu-build/             # 构建环（开书/修订/开新卷）
scripts/                       # 开发守卫 / 测试 / 代码生成（完整索引见 scripts/README.md）
```

每个 skill 由一个 `SKILL.md`（入口）和 `references/` 目录（知识库）组成。

## Skill 格式

`SKILL.md` 开头必须有 frontmatter：

```yaml
---
name: skill-name
description: "一句话描述。触发方式：/skill-name、触发词1、触发词2"
---
```

`description` 保持单行（不使用 `|`/`>` 块）。更长的触发说明放到正文中。

`references/` 中的文件由 skill 按需加载，不会全部塞进上下文。

## 入口瘦身（骨架化）规范

对 SKILL.md 做骨架化（把流程细节移到 `references/*-workflow.md`，入口只留 frontmatter / 定位 / 路由 / Phase 索引）时，必须同时满足以下前提，缺一不可：

1. **入口确实臃肿**：原 SKILL.md 超过约 25KB。实测 16KB 的紧凑流水线型入口（如 moshu-scan）骨架化后反而增加 6% 全读开销，已回退。
2. **逐节读取有真实收益**：流程必须按 Phase/节 分段、且 agent 执行时天然只读当前节（如 review/import/deslop/analyze）。连续执行整条管线的流水线型流程（如 scan 的 Phase 2-5 连跑）没有逐节收益，禁止骨架化。
3. **真实走查验证**：仅静态零丢失对比不够，必须用真实 Claude Code CLI 走查确认 agent 按索引逐节读取 `references/*-workflow.md`，而不是全读。

骨架化的收益边界：入口固定开销下降是确定性收益（每次触发必读）；若 agent 全读 workflow 文件，实测为负收益（+3%~+6%），因此索引措辞必须引导按节读取。

实现要求：

- 流程细节逐字搬迁（静态零丢失 + 模拟走查 + 真实 CLI 三验证），不允许借瘦身改写/删减规则。
- `references/*-workflow.md` 内部互链去掉 `references/` 前缀（该目录内相对解析）。
- 入口保留完整 Phase 索引与「执行前先读 [references/X](...) 的「Y」节」指示。
- 新增/修改骨架时，同步更新 `scripts/doc-budget.json` 中该 skill 的预算与路径总额。

## 大文件设计指南

**文件大不等于问题。** 判断标准不是字节数，而是这笔成本付给谁、多久付一次、内容可否压缩。按以下四条评估：

1. **付费频率**：每次会话 / 每章 / 每次 spawn 必付 = 热路径，需预算约束；按需读取 = 冷路径，大是知识储备，禁止为瘦身拆碎
2. **信息密度**：规则 / 清单 / 约束（原子性内容，不可压缩）vs 流程叙述 / 示例（可搬移、可骨架化）
3. **原子性**：规则是否必须一次读取同时在场（拆开会丢约束，如 anti-ai-writing 模式清单、banned-words 词表）
4. **显式背书**：是否登记 `scripts/doc-budget.json` 且有 `why` 说明——登记了、在预算内 = 设计决定；调预算必须显式说明理由

仓库内四类"大"及其处理方式：

| 类型 | 示例 | 性质 | 处理 |
|---|---|---|---|
| 冷路径知识库 | output-templates、material-decomposition、plot-frameworks、style-genre-modules 等 | 按需加载，大是价值 | 保持现状，禁止拆碎 |
| 骨架化 workflow 库 | review/import/deslop/analyze-workflow.md | 逐节读取（真实 CLI 验证过）才成立 | 索引必须精确引导按节读取 |
| 规则原子文件 | anti-ai-writing（×4 副本）、banned-words、moshu-narrative-writer | 检测/比对时必须在场整体在场 | 预算背书，只增不减内容 |
| 热路径入口 | SKILL.md、agent 模板 | 每次触发必付，唯一需要警惕的"大" | 路由+全场景指令是设计，历史堆积是膨胀 |

**膨胀信号**（出现即处理）：预算反复超支却无 `why` 更新；同一 skill 内内容重复；迁移说明堆在热路径（应移冷路径如 UPGRADING.md）；巨型 reference 无入口索引（agent 不知道何时读它）。

## 如何贡献

### 改进现有 skill

1. Fork 仓库
2. 从 `main` 创建分支：`git checkout -b feat/your-feature main`
3. 修改对应的 `SKILL.md` 或 `references/` 文件
4. 提交 PR，说明改了什么、为什么改

### 新增 skill

1. 在 `skills/` 下创建目录，包含 `SKILL.md` 和 `references/`
2. 确保在仓库根目录运行 `npx skills validate` 无报错
3. 提交 PR

## CI 检查

PR 自动运行 `.github/workflows/cross-platform.yml`。static-check job 跑以下检查（全部强制）：

- `scripts/static-check.sh` — 结构化解析 frontmatter、精确 Markdown 路径/锚点、Agent 引用与 references 可达性；除基础组件 `moshu-cdp` 外禁止跨 Skill 文件引用
- `python3 scripts/skill-numbering.py check` — 工作流编号连续性、引用可绑定性及小数标签守卫
- `scripts/check-current-skill-contracts.sh` — 按 `scripts/current-contract.json` 校验当前版本 / Phase / schema / 主产物 / 细纲契约，并拦截历史路径与静默兼容分支
- `python3 scripts/test-current-skill-contracts.py` — current-contract manifest 与主产物 fail-fast 语义回归
- `scripts/check-doc-budget.sh` — 热路径 SKILL/references/agent 模板的字数预算（按 `scripts/doc-budget.json`），防每次会话都要付的规则文本无声膨胀
- `scripts/check-hook-regex-sync.sh` — hook 伏笔状态检测行为
- `scripts/check-shared-files.sh` — 共享 runtime 资产清单 + 跨 skill reference 副本一致性
- `scripts/check-moshu-setup-deployment.sh` — moshu-setup 部署完整性
- `scripts/check-claude-adapter.sh` — Claude marketplace 与 skill 映射检查（含 version 与 SKILL.md frontmatter 一致）
- `scripts/check-behavior-contracts.sh` — 关键行为约束静态守卫（裸调用停靠/细纲优先/S1-S2 过桥/追踪事务/候选永不拦截等契约，条数以 `scripts/behavior-contracts.json` 为准，清单见 `scripts/behavior-contracts.json`）
- `scripts/check-agents-version-sync.sh` — agents_version 一致性守卫（7 个 SKILL.md 的声明与 `moshu-setup/UPGRADING.md` 权威一致）
- `scripts/check-story-numbers.sh` — 叙述性 skill 计数守卫（README/README_EN/CONTRIBUTING/scripts-README/architecture 中「N 个 skill」必须与 skills/ 实测一致；CHANGELOG 排除）
- `scripts/check-agent-template-rules.sh` — agent 模板纪律守卫（禁互引 / `agent-references/` 挂载点存在 / 共享纪律单副本）
- `scripts/check-eval-scenarios.sh` — 场景剧本静态校验（3 剧本存在非空/断言节/机检标记 ≥3/引用路径存在；不跑 LLM）
- `scripts/check-reference-closure.sh` — 引用可达性守卫（批B4 方案 A 资产宇宙）：`skills/*/references/*.md` 中「资产宇宙内」文件名提及须在本 skill 域可达，跨域合法提及走理由白名单；与 static-check 互补（链接 vs 文件名文本提及）
- `scripts/check-route-write.sh` — 路由残留守卫（批B8）：表格行第二列=moshu-write 的语境两级判定（构建域词 blocking / 写作域白名单 / 未知 candidate 不阻断）；只锁表格行，不扫 prose
- 采集脚本 `node --check` 语法校验

以上为代表性列举；**强制清单按 `.github/workflows/cross-platform.yml` 为准**，每个脚本的用途与触发时机见 [scripts/README.md](scripts/README.md)。另有 `.github/workflows/cli-compat.yml` 在相关 PR、每周定时和手动触发时安装官方当前版本，真实运行 Claude Code 的无鉴权 smoke。

另有 windows / macos job 验证 cdp-utils 加载与 setup 脚本 dry-run。

提交前建议按 Linux CI 的强制清单本地跑一遍：

```bash
bash scripts/static-check.sh
python3 scripts/test-static-check.py
python3 scripts/skill-numbering.py check
bash scripts/test-skill-numbering.sh
bash scripts/check-current-skill-contracts.sh
python3 scripts/test-current-skill-contracts.py
bash scripts/check-doc-budget.sh
bash scripts/check-hook-regex-sync.sh
bash scripts/check-shared-files.sh
python3 scripts/test-shared-assets.py
node scripts/test-normalize-punctuation.js
node scripts/test-scan-runtime.js
node scripts/test-scan-analyze.js
node scripts/test-merge-summaries.js
bash scripts/test-ai-patterns.sh
bash scripts/test-outline-copy.sh
bash scripts/test-degeneration.sh
bash scripts/eval-prose-quality.sh
bash scripts/test-prose-backstop-hook.sh
bash scripts/test-story-continuity.sh
python3 scripts/test-tracking-workflow-contracts.py
python3 scripts/test-tracking-commit.py
bash scripts/check-moshu-setup-deployment.sh
bash scripts/check-claude-adapter.sh
bash scripts/check-behavior-contracts.sh
python3 scripts/test-behavior-contracts.py
bash scripts/check-capability-wiring.sh
python3 scripts/test-capability-wiring.py
bash scripts/check-reference-closure.sh
python3 scripts/test-reference-closure.py
bash scripts/check-route-write.sh
python3 scripts/test-route-write.py
python3 scripts/test-next-step.py
bash scripts/check-agents-version-sync.sh
python3 scripts/test-agents-version-sync.py
bash scripts/check-story-numbers.sh
python3 scripts/test-story-numbers.py
node scripts/test-prose-candidates.js
python3 scripts/test-review-tickets.py
python3 scripts/test-deploy.py
bash scripts/check-agent-template-rules.sh
python3 scripts/test-agent-template-rules.py
bash scripts/check-eval-scenarios.sh
bash scripts/test-writing-pipeline.sh
python3 scripts/test-impact-scan.py
python3 scripts/test-check-outline.py  # 守护 skills/moshu-build/scripts/check_outline.py 大纲机检
bash scripts/check-python-invocation.sh
bash scripts/check-hook-locale-safety.sh
bash scripts/test-hook-encoding-portable.sh
bash scripts/test-charcount-portable.sh
bash scripts/test-charcount-portable.sh --stub

# 可选真实 CLI smoke（需安装 Claude Code）
CLAUDE_REAL_CHECK=1 bash scripts/check-claude-adapter.sh
```

## 工作流编号规范

新增或调整流程步骤时，显式标题使用 `Step 1`、`Step 2` 这类连续整数；不要为了插入步骤创建 `Step 1.5` / `Phase 2.1` / `Stage 0.5`，也不要在 `SKILL.md` 用 `### 2.1` 或 `- 2.1` 代替明确的工作流标题。`references/` 手册自身的 `3.1` 章节/列表号不受此规则影响。

修改编号前先预览，再写入并复查：

```bash
python3 scripts/skill-numbering.py audit
python3 scripts/skill-numbering.py fix --dry-run
python3 scripts/skill-numbering.py fix --write
python3 scripts/skill-numbering.py check
```

自动修复只重排显式 Step 标题及可无歧义绑定的引用。无法绑定的 fractional Step 引用或一对多映射会让整个写入在落盘前失败；Phase、裸编号标题和 bullet 子步骤需要按语义手工命名。完整算法与局部路径用法见 [scripts/README.md](scripts/README.md#工作流编号维护)。

涉及 agent/skill/plugin/hook 协议的断言必须先核对对应项目官方文档，再以真实 CLI 输出复核；不要从其他 agent 的相似字段推断。

## 共享文件规范

部分文件跨 skill 共享（如 banned-words.md、anti-ai-writing.md），修改时必须同步所有副本。

- runtime 脚本的唯一源/目标定义在 `scripts/shared-assets.json`；先改 `source`，再运行 `python3 scripts/sync-shared-assets.py sync`。
- 同名 runtime 脚本只能属于一个 canonical group，且每个 target 必须保留 source basename；禁止用改名 target 绕过单一 owner。
- reference 文档仍由 `check-shared-files.sh` 按内容组校验。
- 提交前统一运行 `bash scripts/check-shared-files.sh`；未在 manifest 登记的重名 runtime 脚本会直接失败。

### 知识库贡献

最有价值的贡献类型：

- **实战数据**：各平台最新榜单分析、题材趋势变化
- **新题材框架**：新的题材写作公式、结构模板
- **去AI味规则**：新的 AI 痕迹模式、改写范例
- **平台规则更新**：投稿要求、推荐机制的变化

## 质量要求

- **操作性**：内容必须能让 AI agent 直接执行，不要写教程
- **简洁**：用表格和模板，不要长篇叙述
- **无冗余**：不同 skill 的 `references/` 之间可以共享文件（通过路径引用），但同一 skill 内不要重复
- **中文**：所有内容用中文

## 提交流程

```
fork → branch → commit → PR → review → merge
```

- 一个 PR 聚焦一个改动
- commit message 用中文，格式：`类型: 简短描述`
- 类型：`feat`（新增）/ `fix`（修复）/ `docs`（文档）/ `refactor`（重构）

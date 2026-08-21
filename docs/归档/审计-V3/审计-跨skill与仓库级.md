# 跨 skill 与仓库级审计报告

- 审计日期：2026-08-21
- 对象：不属于任何单个 skill 的收口与索引——`.claude-plugin/marketplace.json`、根 README/README_EN/CONTRIBUTING、`docs/architecture.md`、`scripts/` 守卫体系、CI 工作流、doc-budget 预算体系、全仓引用完整性。
- 方式：只读审计 + 全量守卫基线复跑（见 [基线-守卫全量.md](基线-守卫全量.md)）+ 10 个 skill 的机械交叉扫描。

## 一、结论

**仓库级卫生的"硬指标"全绿**：10 个 skill 零死链、零术语违例、零真实孤儿；全仓 254 份 md 无真实悬空引用；守卫在等价条件下 38/38 通过。

**问题集中在三类"守卫照不到的地方"**：①版本口径（marketplace 完全无守卫，已实际漂移 3 处）；②文档索引（最年轻的 `moshu-style` 在 4 处索引缺席）；③预算体系已收紧到几乎无法再加字（12 个热路径文件余量全部 ≤3.5%，两个文件余量 ≤1 字）——这条会**卡住所有 skill 的文本级整改**，必须先解。

## 二、阻断级：0 项

## 三、需修级：3 项

### G1 marketplace 版本三处漂移，且版本口径完全无守卫

- **现象**：`.claude-plugin/marketplace.json` 里的 `plugins[].version` 与各 skill `SKILL.md` frontmatter `version` 不一致，`metadata.version` 也落后于发布版本。
- **证据**（UTF-8 安全解析实测，10 skill 逐一比对）：

  | skill | SKILL.md | marketplace | 结论 |
  |---|---|---|---|
  | moshu-write | 1.2.0 | 1.1.1 | **DIFF** |
  | moshu-review | 1.2.0 | 1.1.5 | **DIFF** |
  | moshu-setup | 1.3.0 | 1.2.11 | **DIFF** |
  | 其余 7 个 | — | — | 一致 |
  | `metadata.version` | — | 1.1.1 | 与 `skills/moshu/VERSION` = 1.3.0、tag `v1.3.0` 不一致 |

- **成因**（代码事实）：末次提交 `8ae77b2`（`chore(release-prep): v1.3.0 发布预备——write/review/setup skill 版本 bump`）的文件清单为 CHANGELOG / current-contract.json / moshu-review SKILL.md / moshu-setup SKILL.md / UPGRADING.md / deploy.py / moshu-write SKILL.md——**不含 marketplace.json**。
- **为什么没被拦住**：`scripts/check-claude-adapter.sh` 是 marketplace 的唯一守卫，但它只校验「plugins 与 skills 的一一映射 + 数量」（`:11` 计数、`:19` 映射校验），全文 `version` 只出现 2 次且均与校验无关（`:75` 打印 CLI 版本、`:91` 造 fixture 的 `"version": "0.0.0"`）。`scripts/current-contract.json` 只钉了 `setup_skill_version`（1.3.0）与 `agents_version`（29），不管 marketplace。
- **影响**：Claude marketplace 侧展示/安装看到的是旧版本号；下次发布若继续漏改，漂移会累积。
- **建议修法**（两步，第二步可选）：
  1. **同步数据**：marketplace 3 处 `version` 对齐 SKILL.md（1.2.0 / 1.2.0 / 1.3.0），`metadata.version` → 1.3.0。改动量：1 文件 / 4 行。
  2. **挂现有收口**（按 `AGENTS.md` §5 决策树第 2 条"能否挂现有收口"）：扩展 `check-claude-adapter.sh`——对每个 plugin 比对 `plugins[].version` 与对应 `skills/<name>/SKILL.md` frontmatter `version`，不等即失败；反向 fixture 加进已有的 `$TMP_DIR/plugin` 造假路径。**不新开脚本**，因此 CI 三处（`cross-platform.yml` / `CONTRIBUTING.md` / `scripts/README.md`）只需更新描述文字，不需新增条目。改动量：1 脚本 / 约 25 行 + 3 处描述各 1 行。
- **验收**：`bash scripts/check-claude-adapter.sh` 绿；人为改错一处 version 必须红（反向验证）。

### G2 `moshu-style` 在 4 处索引缺席

- **现象**：第 10 个 skill（`moshu-style`，v1.0.0）功能与路由都在位，但索引类文档没收录它。
- **证据**（逐文件独立词匹配实测）：

  | 文件 | moshu-style | 说明 |
  |---|---|---|
  | `README.md` | ✗ Skills 表 | 表内 9 行（setup/moshu/write/analyze/scan/deslop/import/review/cdp），`:176` 仅在项目结构树提到"文风库/（/moshu-style 生成）" |
  | `README_EN.md` | ✗ Skills 表 | 同上，`:172` 仅结构树 |
  | `CONTRIBUTING.md` | ✗ 全文零命中 | — |
  | `docs/architecture.md` | ✗ 全文零命中 | `§1` 路由图 9 个 `R -->\|...\|` 分支（scan/analyze/write/import/deslop/review/setup/cdp/Dashboard）缺 style |
  | `skills/moshu/SKILL.md` | ✓ `:25` 路由行 | 功能已接 |
  | `.claude-plugin/marketplace.json` | ✓ `:192-208` | 已登记且版本一致（1.0.0） |

- **为什么没被拦住**：`check-story-numbers.py` 只校验「`N 个 skill`／`N skills`」这类**数字口径**是否等于实测 skill 数（现为 10），而这些文档在批 0 已把措辞改成"全部 skill"/`Skills[全部 Skill 入口]`——**表格行数与图节点数不在守卫射程内**。实测 `check-story-numbers` 绿（ok, 10 skills），确实不该报。
- **影响**：用户读 README 看不到文风能力；架构图漏一条链路（文风库 → 写作每章召回），而这条链路在 `workflow-chapter.md` 写前准备 (d) 是**每章必查**的强制项。
- **建议修法**：README/README_EN Skills 表各加 1 行（`moshu-style` | `/moshu-style` `/学文风` | 文风学习 · 从任意量原文提取写作风格基准）；`docs/architecture.md` §1 路由图加 `R -->|学文风| Style[moshu-style]` 与 `Style -->|产出| StyleLib[文风库]`、`StyleLib --> Write`；`CONTRIBUTING.md` 的 skill 清单处补一行。改动量：4 文件 / 约 7 行。
- **可选加固**：给 `check-story-numbers.py` 增一条"README/README_EN 的 Skills 表行数 == 实测 skill 数"断言（挂现有守卫，不新开脚本；须同步 `test-story-numbers.py` 反向 fixture）。改动量：2 脚本 / 约 20 行。
- **验收**：`bash scripts/check-story-numbers.sh` 绿；`python scripts/test-story-numbers.py`（带 `PYTHONIOENCODING=utf-8`）绿。

### G5 预算枷锁：热路径余量耗尽，阻塞所有文本级整改

- **现象**：`scripts/doc-budget.json` 登记的 12 个文件 + 3 个路径组，余量全部 ≤3.5%，其中两个 ≤1 字。
- **证据**（用守卫同一度量"去空白字符数"复算，`check-doc-budget.sh:28-32` 算法）：

  | 文件 | 用量/预算 | 余量 | %余 |
  |---|---|---|---|
  | `moshu-write/references/workflow-daily.md` | 11500 / 11500 | **0** | 0.0% |
  | `moshu-review/SKILL.md` | 2899 / 2900 | **1** | 0.0% |
  | `moshu-write/references/banned-words.md` | 4177 / 4200 | 23 | 0.5% |
  | `moshu-analyze/SKILL.md` | 2273 / 2300 | 27 | 1.2% |
  | `moshu-deslop/SKILL.md` | 3271 / 3300 | 29 | 0.9% |
  | `moshu-write/references/anti-ai-writing.md` | 14264 / 14300 | 36 | 0.3% |
  | `moshu-setup/.../agents/moshu-narrative-writer.md` | 13254 / 13300 | 46 | 0.3% |
  | `moshu-write/references/workflow-chapter.md` | 14599 / 14650 | 51 | 0.3% |
  | `moshu-write/references/writing-craft.md` | 11908 / 12000 | 92 | 0.8% |
  | `moshu-import/SKILL.md` | 2509 / 2600 | 91 | 3.5% |
  | `moshu-write/references/workflow-setup.md` | 13440 / 13600 | 160 | 1.2% |
  | `moshu-write/SKILL.md` | 9086 / 9200 | 114 | 1.2% |
  | 路径组「正文 agent 上下文」 | 43603 / 43700 | 97 | 0.2% |
  | 路径组「长篇日更主会话」 | 35185 / 35400 | 215 | 0.6% |
  | 路径组「长篇开书」 | 22526 / 22750 | 224 | 1.0% |

- **成因**（代码事实）：批 0 采纳脚本建议值收紧了 4 条预算（review 2900 / import 2600 / deslop 3300 / analyze 2300）；而 `check-doc-budget.sh:52-53` 的提示逻辑是「余量 ≥ 预算×5% 就建议下调到 `ceil(用量/100)*100`」——**该建议天然把余量压到 <5%**，逐轮采纳即形成枷锁。
- **影响**：本轮审计已识别的文本级修法（moshu-write 的 W1/W2/W3、以及各 skill 报告里的同类项）**没有一项能直接落地**，全部会撞红 `check-doc-budget.sh`。
- **建议修法（整改批次的第一步，必须先做）**：按"净新增字数"预估整改总需求，一次性在 `scripts/doc-budget.json` 为受影响文件调高预算，并在 `_comment` 写清理由（该文件已有 `_comment` 惯例，批 0 即如此记录）；**不接受**为过预算删除有效约束文本（等于用删规则换过检，属反模式 #1 变体）。
- **预估改动量**：1 文件 / 受影响条目各 1 行 + 1 条 `_comment`。
- **验收**：`bash scripts/check-doc-budget.sh` 绿且无 OVER；整改完成后复跑仍绿。

## 四、候选级：3 项

### G4 五个 `test-*.py` 在中文 locale Windows 下不可跑（CI 视野之外）

- **现象**：`test-static-check.py` / `test-story-numbers.py` / `test-behavior-contracts.py` / `test-agents-version-sync.py` / `test-agent-template-rules.py` 在中文 Windows 直跑必红（`UnicodeDecodeError` → `result.stderr` 为 None → `TypeError`）；设 `PYTHONIOENCODING=utf-8` 后**全部 exit 0**（实测）。
- **证据**：见 [基线-守卫全量.md](基线-守卫全量.md) 判因表；CI 落位 `.github/workflows/cross-platform.yml:24/:26/:42/:46/:50/:56` 均在 `ubuntu-latest` job，`windows-latest` job（`:137` 起）不含这 5 项。
- **影响**：只影响中文 Windows 本地开发体验（会误判成仓库红），CI 不受影响。与仓库自身对部署侧 hook 的 GBK 防护力度（`check-hook-locale-safety.sh` + `test-hook-encoding-portable.sh` 专门守）形成**不对称**：部署侧防到了，开发侧没防。
- **建议修法（低成本）**：在这 5 个测试的 `subprocess.run(...)` 调用处补 `errors="replace"`（或统一走一个已存在的 helper），使解码失败不再炸；或仅在 `CONTRIBUTING.md`「CI 检查」节加一句 Windows 前置 `export PYTHONIOENCODING=utf-8`。**推荐后者**（零代码风险、一行文档）。改动量：1 文件 / 1 行（若改代码则 5 文件各 1-2 行）。
- **验收**：中文 Windows 下按文档所述跑这 5 项全绿（已实测成立）。

### G3 「接线类不变量」无守卫——本轮主要问题类型的根因

- **现象**：`scripts/behavior-contracts.json` 的守卫形态是「某段**约束文本**必须存在于某文件」（`check-behavior-contracts.py` 做子串匹配），能锁住"话有没有写"，锁不住"调用链是否完整"。因此"脚本建成但流程文档从不指示使用"这类缺口（moshu-write 的 W1 信息差登记、W2 候选机检只在一条车道、W3 工单只在一条车道）可以长期存在且全绿。
- **证据**：`scripts/behavior-contracts.json` 11 条契约全为 `path` + `must_contain` 结构（`:5-70`）；`check-prose-candidates.js` 全仓仅 1 处调用点（`workflow-daily.md:130`）而守卫无感；`information_gap_changes` 在流程文档零调用而守卫无感。
- **影响**：这是**方法论级**的盲区，不是单个 bug。
- **建议修法（保守，挂现有收口）**：整改 W1-W3 时，把新接线点同时登记进 `behavior-contracts.json`（例如 `daily-information-gap-optional` → `workflow-daily.md` 必含 `information_gap_changes`；`chapter-candidate-checks` → `workflow-chapter.md` 必含 `check-prose-candidates.js`），让"接线"变成有守卫的文本不变量。**不新增守卫脚本、不新增机制**，只加契约条目。改动量：1 文件 / 每条约 6 行 + `test-behavior-contracts.py` fixture 前提同步（该文件按 manifest 驱动，通常无需改）。
- **验收**：`bash scripts/check-behavior-contracts.sh` 显示条数增加且全绿；`python scripts/test-behavior-contracts.py`（UTF-8 环境）绿。

### G6 规划文档的简写路径（6 条，低优先）

- **现象**：严格复检（254 份 md，剥离 `:行号`、按 skill 相对路径二次解析）后仅剩 6 条"引用了不存在路径"，全部是文档简写而非断链：
  - `docs/执行总纲V2.md`：`references/review-workflow.md`、`references/volume-review.md`、`references/workflow-revision.md`、`scripts/review_tickets.py`（均省略了 `skills/<skill>/` 前缀）、`skills/moshu/scripts/next_step.py`（**批 4 已跳过未实施**，`AGENTS.md` 头部与总纲 §4.3 均已注明）。
  - `skills/moshu-setup/UPGRADING.md:111`：`scripts/tracking_commit.py`（实际随 write/import/review 三个 skill 分发）。
- **影响**：不影响任何自动化（`static-check.py` 只校验 skill 内引用，这些在 docs/ 与 UPGRADING 中）；仅影响读者按路径直查。
- **建议修法**：`UPGRADING.md:111` 补全为"随 skill 分发的 `tracking_commit.py`"（1 行）；总纲属**历史规划文档**，按 `AGENTS.md` 纪律不追改（已有跳过说明）。改动量：1 文件 / 1 行。**可不做**。

## 五、覆盖矩阵（仓库级）

| 收口 | 守什么 | 盲区 |
|---|---|---|
| `check-claude-adapter.sh` | marketplace ↔ skills 一一映射 + 数量 | **版本号完全不守**（G1） |
| `check-story-numbers.py` | 文档里「N 个 skill」数字 == 实测 | 表格行数/图节点数不守（G2） |
| `check-behavior-contracts.py` | 11 条约束文本存在性 | 调用链完整性不守（G3） |
| `check-doc-budget.sh` | 热路径去空白字数上限 | 无下限保护；建议逻辑天然收紧余量（G5） |
| `check-shared-files.sh` + `sync-shared-assets.py` | 36 组 / 51 份副本字节一致 | — （实测绿） |
| `check-agents-version-sync.py` | 7 个 SKILL.md 的 agents_version == UPGRADING 权威 | — （实测 29 一致） |
| `static-check.py` | skill 内 frontmatter/路径/锚点/跨 skill 引用禁令 | 只覆盖 `skills/**`，`docs/**` 不扫（G6） |
| `check-python-invocation.sh` | skill 文档 + 部署 hook 禁裸调 `python3` | **明示豁免 CI 脚本自身**（`:31`），故 3 个 `.sh` 硬编码 python3 属有意设计，非缺陷 |
| CI `cross-platform.yml` | ubuntu 全量 + windows/macos 子集 + deploy job | 5 个 `test-*.py` 只在 ubuntu（G4） |

## 六、实测记录

| 检查 | 结果 |
|---|---|
| 全 10 skill 引用图（md 链接 + 反引号 references 路径，双路径解析） | **死链 0** |
| 全 10 skill 孤儿 references（basename 反查） | **真实孤儿 0**；moshu-setup 的 8 项（6 agent 模板 + 2 rules 模板）经 `deploy.py:140-143` 整目录拷贝消费，属部署载荷，假阳性 |
| 全 10 skill 术语禁用别称（8 个别称 × 199 份 md） | **违例 0** |
| 全仓悬空引用（254 份 md，严格解析） | 真实 6 条，全为规划文档简写（G6） |
| 守卫全量基线 | 38/38 等价全绿（详见 [基线-守卫全量.md](基线-守卫全量.md)） |
| marketplace ↔ SKILL.md 版本比对（10 skill） | 3 处 DIFF（G1） |
| doc-budget 全表复算 | OVER 0，余量全部 ≤3.5%（G5） |
| `moshu-style` 索引覆盖（7 份索引类文件） | 4 处缺席（G2） |
| 跨 skill 降级措辞 | `Fallback: X -> solo` / `-> direct lookup` 形态统一；7 个用 agent 的 skill `agents_version: 29` 一致；cdp/scan/style 不 spawn agent 故无该字段（正确） |
| 10 skill 路由覆盖 | `skills/moshu/SKILL.md` 路由表命中 10/10 |

## 七、整改计划

| 编号 | 级别 | 修法 | 改动量 | 依赖 | 验收命令 |
|---|---|---|---|---|---|
| **G5** | 需修 | doc-budget 按整改总需求一次性调高 + `_comment` 记录理由 | 1 文件 | **无（所有文本级整改的前置）** | `check-doc-budget.sh` |
| G1-a | 需修 | marketplace 3 处 version + metadata.version 对齐 | 1 文件 / 4 行 | 无 | `check-claude-adapter.sh` |
| G1-b | 需修（可选加固） | 扩展 `check-claude-adapter.sh` 增版本比对 + 反向验证 | 1 脚本 / ~25 行 + 3 处描述 | G1-a | `check-claude-adapter.sh` 正向绿 / 改错必红 |
| G2-a | 需修 | README + README_EN Skills 表补 `moshu-style` 行；`architecture.md` 路由图补节点；`CONTRIBUTING.md` 补一行 | 4 文件 / ~7 行 | G5（README 不在预算内，但 architecture 亦不在，实际无阻塞） | `check-story-numbers.sh` + `static-check.sh` |
| G2-b | 候选（可选加固） | `check-story-numbers.py` 增 Skills 表行数断言 + 反向 fixture | 2 脚本 / ~20 行 | G2-a | `test-story-numbers.py`（UTF-8 环境） |
| G3 | 候选 | 把 W1/W2/W3 的接线点登记进 `behavior-contracts.json` | 1 文件 / 每条 ~6 行 | 各 skill 对应整改项之后 | `check-behavior-contracts.sh` + `test-behavior-contracts.py` |
| G4 | 候选 | `CONTRIBUTING.md` 加一行 Windows 前置 `PYTHONIOENCODING=utf-8` | 1 文件 / 1 行 | 无 | 中文 Windows 下 5 项全绿（已实测成立） |
| G6 | 候选（可不做） | `UPGRADING.md:111` 路径写法补全 | 1 文件 / 1 行 | 无 | `static-check.sh` |

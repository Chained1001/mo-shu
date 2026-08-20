# moshu-setup 审计报告

- 审计日期：2026-08-21
- 对象：`skills/moshu-setup/`（94 文件，全仓最大：`deploy.py` + `merge-claude-settings.py` + references/{agents 7 / hooks 10 / rules 4 / templates 3 / agent-references 32+32 张题材卡} + UPGRADING.md）
- 方式：委派深审（含临时目录真实部署演练）+ **本人独立复核两条关键需修级**

## 一、结论

**部署主链路实测可跑通**：`deploy` → `verify` → sentinel 六字段正确；版本降级门、失败不写 sentinel、settings 合并幂等均按契约工作。`merge-claude-settings.py` 的合并/幂等/用户保留语义经直接 import 实测与文档逐条相符（**无静默覆盖风险**）；10 个可跑守卫全绿；7 个 agent 模板挂载点零死链；术语零违例。

**问题集中三处**：①`deploy.py` 是本 skill 唯一**零测试零守卫**的关键脚本（365 行），其 `verify` 退出码恒 0 且漏检 32 张题材子卡——两条缺陷正是该盲区的产物；②`guard-outline-before-prose.sh` 的**阻断门枚举全仓无一处正确**（代码 5 处 `exit 2`／4 类门，hook 头注写 3 类、C7 裁决记录列 4 行号、README 只写 1 类），且第 4 类门零测试；③同一 hook 的 Bash 面缺「主产物门」，与 Write/Edit 面不对称且测不到。

## 二、阻断级：0 项

（`verify` 的两条可靠性缺陷不升为阻断：其文档指定消费者是读文本输出的 AI（`SKILL.md:114`），部署主链路本身正确。）

## 三、需修级：9 项

### PM1 `deploy.py verify` 退出码恒为 0，即使 `RESULT: HAS FAILURE` ✅本人复核成立

- **证据（本人 `sed -n '355,362p'` 核对）**：`skills/moshu-setup/scripts/deploy.py:359-361` 的 `else` 分支只 `for line in verify(project): print(line)`，**无 `sys.exit(1)`**；对照 `deploy` 路径 `:358` 有 `sys.exit(1)`。子代理实测：`--agents-version 30` 部署后 `verify` 输出 `RESULT: HAS FAILURE` 而 `$LASTEXITCODE` = **0**。
- **影响**：`SKILL.md:114` 把 `verify` 定为 Phase 3 机械验证入口，`SKILL.md:40` 的措辞是"脚本成功则直接进入 Phase 3"。按仓库通行惯例（全部 `check-*` 用退出码）判定的 AI/CI 会把失败当通过。
- **修法**：`verify()` 返回 `(checks, ok)`，`main()` 遇 HAS FAILURE 时 `sys.exit(1)`。**改动量**：1 文件 / ~5 行。

### PM2 `verify` 与部署完整性校验漏掉 `genre-prose-cards/` 32 张子卡 ✅本人复核成立

- **证据（本人核对）**：`deploy.py:279` `ref_ok = same_path or all((ref_dst / f.name).exists() for f in AGENT_REFS.iterdir() **if f.is_file()**)`——`if f.is_file()` 把子目录整体过滤；`:181` 的 `missing` 同一过滤。子代理实测：删 3 张子卡 → ALL PASS；**删整个目录 → 仍 ALL PASS 且退出 0**。
- **影响**：`moshu-narrative-writer.md:66` 明确指示 agent 读 `agent-references/genre-prose-cards/{题材}.md` 单卡；子卡缺失时 Phase 3 宣告部署完整，故障推迟到写正文才暴露。与 `SKILL.md:53` 声明的 Validation check（"every … reference resolves"）不符。
- **修法**：`:181`/`:279` 改用 `AGENT_REFS.rglob('*')` + `is_file()`；`check-moshu-setup-deployment.sh:248-249` 的 agent-refs 断言加一张子卡存在性检查。**改动量**：2 文件 / ~6 行。

### PM3 3 个 agent 模板的「逻辑路径」提示句被批注插入切断（残留 `。，`）

- **证据**：`references/templates/agents/moshu-architect.md:40-41`、`moshu-character-designer.md:38-39`、`moshu-narrative-writer.md:54-55`（三处 `。，` 拼接）；正确形态见 `moshu-consistency-checker.md:43` + `:45`（两句分开）。
- **影响**：三份模板里"逻辑路径 → canonical 路径"的映射指令语法归属错乱；`moshu-narrative-writer.md` 是每章每次 spawn 都付的热路径模板。属反模式 #3 的残留。
- **修法**：按 consistency-checker 的正确形态拆回两段。字符数净变化约 0，不冲预算（余量 46）。**改动量**：3 文件 / 各 2 行。

### PM4 唯一被裁决保留的阻断 hook，其阻断门枚举全仓无一处正确；第 4 类门零测试

- **证据（逐处核对）**：

| 门 | 代码 | hook 头注（`:5-10` 写"拦截三类"） | C7 裁决记录 | README |
|---|---|---|---|---|
| Bash 命令面（委派 JS 核） | `guard-outline-before-prose.sh:86` | 未单列 | 列 `:86` | 未提 |
| 细纲门 | `:144` | ✓ | 列 `:144` | ✓（`README.md:141`） |
| 追踪检查点门 | `:160` | ✓ | 列 `:160` | 未提 |
| **主产物门** | `:187-199` | **缺** | 列了行号但门类描述未含 | 未提 |
| **毒句式欠账门** | `:204-228` | ✓ | **完全缺**（`施工日志.md:308` 只列 `:86/:144/:160/:199`） | 未提 |

- 裁决原文 `docs/规格-V2/审核记录.md:158`（作者 2026-08-20 采纳"保留现状不整改"），其依据即那份 4 行号清单。
- **测试覆盖**：`scripts/` 全目录 `毒句式|toxic` → `check-moshu-setup-deployment.sh` 0 命中、`test-prose-backstop-hook.sh` 0 命中（其断言点为截断/元信息泄漏/工程词/复读，`:67-76`）→ `:228` 这道阻断门**无任何回归**。
- **影响**：总纲附录 B 第 6 条是作者红线（`docs/执行总纲V2.md:227`「hook 只能 ask 不能 deny」+ 存疑项待终检）。裁决只覆盖被枚举的门；`:228` 是**未经声明的阻断点**，改坏了不会被发现。
- **修法**：①头注"拦截三类"→"四类"并补主产物门；②`审核记录.md` 追加勘误：C7 清单补 `:228`，**呈报作者确认裁决是否覆盖**；③`check-moshu-setup-deployment.sh` 加一组欠账门用例（含 `<!-- 去味:跳过 -->` 豁免路径）。**改动量**：3 文件 / 2+3+10 行。

### PM5 同一 hook 的 Bash 写入面缺「主产物门」，与 Write/Edit 面不对称且无测试

- **证据**：`story_hook_core.js:670-737` 的 `proseBlockReason` 依次为细纲门（`:695-697`）→ 追踪检查点门（`:699-702`）→ 毒句式欠账门（`:704-735`），**全文无主产物判定**；bash 侧 `guard-outline-before-prose.sh:187-200` 有完整主产物门，而 `:10` 注释宣称"与 JS 核 proseBlockReason 同序"——该声明对主产物门已不成立。测试：主产物门 6 组用例（`check-moshu-setup-deployment.sh:579-598`）全走 Write/Edit 面，Bash 面只 2 组且 `:598` 已清理夹具。
- **影响**：`cat > 书/正文/第N章.md` 绕过主产物门。风险受限（`UPGRADING.md:57` 已声明 Bash 面是 best-effort），但两面语义差异属未声明状态。
- **修法（推荐 ①）**：①把主产物门判定搬进 `story_hook_core.js` 的 `proseBlockReason`（`:702` 之后），注释即恢复为真；②或改两处注释明示"主产物门仅 Write/Edit 面生效"。**改动量**：①1 文件 ~20 行 + 1 组测试；②2 文件各 1 行。

### PM6 `deploy.py` 零守卫覆盖，且自身 usage 串已实测失效

- **证据**：全仓 `deploy\.py` 28 处命中中，`scripts/` 下**零**命中；CI 三处（`cross-platform.yml` / `CONTRIBUTING.md` / `scripts/README.md`）均无。实测两种 docstring 形态：`:11` 的 `deploy.py --project … --name …` → `invalid choice` 退出 2；`:13` 的 `deploy.py --verify {项目目录}` → 同样退出 2（真实形态是 `verify --project`，`SKILL.md:39/114` 写对了）。
- **历史**：同类漂移已两次被咬到（`施工日志.md:261` deploy.py:12 usage 串漂移靠人工预检抓到；`审核记录.md:117` 记为"规格外修正"）。
- **修法**：①修 `:11/:13` usage 串；②新增 `scripts/test-deploy.py`（正式回归，带守护对象声明）：临时目录 `deploy --dry-run`→`deploy`→`verify`（断言 ALL PASS 且退出 0）→删一张子卡→断言 FAIL 且退出非 0→造 `agents_version: 99` sentinel→断言拒绝降级退出 1；③CI 三处同步 + `scripts/README.md` 索引。**改动量**：4 文件 / 2 + ~80 + 2 行。

### PM7 README 关于部署包的两个计数已过期，且无守卫

- **证据（实测）**：`README.md:127`「部署包 agent-references 含 **31 份**方法论文件，全仓 references **189 份**」；实测 agent-references 顶层 `.md` = **32**（另有 32 张子卡）、`skills/**/references/**/*.md` = **188**（setup 75 / write 80 / review 12 / analyze 6 / import 6 / scan 5 / deslop 3 / style 1）。`git log -S "31 份方法论文件"` 只命中初始快照——批 7 新增 `shared-output-discipline.md`（31→32）时未同步。
- **无守卫**：`check-story-numbers.py:28-29` 只匹配「N 个 skill」，不覆盖「N 份」。
- **修法**：改为非数字表述（与批 0 对 skill 计数的处理一致），或 31→32 且删「189 份」。**改动量**：1 行。

### PM8 marketplace 版本滞后：1.2.11 vs SKILL.md 1.3.0

见总计划 **G1**（本 skill 是三处滞后中差距最大的：1.2.11 vs 1.3.0）。

### PM9 `emotional-methods.md` 双向分叉，且分叉白名单的理由已失效

- **证据（实测 diff）**：`moshu-write/references/emotional-methods.md` 209 行 vs `moshu-setup/references/agent-references/emotional-methods.md` 179 行；write 独有 35 行（含 `## 长篇单元情绪引擎` 整段），**agent-references 独有 5 行**（如「每 3-5 个小节有一次情绪转向」、两行诊断表、一条自查项）——即 setup 副本仍保留 write 已删的内容，**双向分叉**。未登记 `shared-assets.json`。
- **白名单理由失效**：`check-shared-files.sh:32-37` 的注释理由是"write 副本的长篇专属段引用 `reader-contract-and-progression.md`，该文件只在 write 存在，同步会造成悬空引用"；但实测 `agent-references/reader-contract-and-progression.md` **已存在**且与 write 副本字节一致（`shared-assets.json` 的 `reader-contract-reference` 组已登记）。**前提消失**。
- **影响**：全仓唯一无 sync、无字节守卫的方法论副本，双源漂移已实际发生。违反反模式 #4。
- **修法**：以 write 为源，把 agent-references 独有 5 行合并回源或确认删除 → 登进 `shared-assets.json` → 跑 `sync` → 从 `check-shared-files.sh:37` 的 `LONGFORM_DIVERGENT_NAMES` 移除该项（连同 `:32-37` 过时注释）。**改动量**：3 文件 / ~5 + 1 组 + 6 行。

## 四、候选级

| 编号 | 发现 | 证据 | 修法 |
|---|---|---|---|
| PC1 | `moshu-narrative-writer.md` 余量 46 字（13254/13300）、路径组「正文 agent 上下文」余 97 字 | 与 `check-doc-budget.sh:28-32` 同度量复算 | 见总计划 G5；PM3 为字符中性不受影响 |
| PC2 | `SKILL.md` 部署契约三处小偏差：`:53/:88` 声明的"引用解析"校验未实现；`:156` 列受管 section 4 个而模板有 5 个（漏「作者控制点」`CLAUDE.md.tmpl:31`）；`deploy.py:50-51` `MANAGED_SECTIONS` 是死常量（`merge_claude_md` 无条件覆盖同名 section） | 逐处核对 | 措辞降级为实际实现，或补实现；2 文件 / ~6 行 |
| PC3 | `deploy --agents-version/--setup-version` 与 `verify` 硬编码断言互相矛盾（`deploy.py:311-312` 比常量而非部署实际值），且两参数在 SKILL.md 全文未被指示使用 | 实测 `--agents-version 30` 部署成功后 verify 必 FAIL | `verify` 加同名可选参数，或移除这两个参数（更小）；1 文件 / ~6 行 |
| PC4 | 33 份题材卡（索引 + 32 张）未登记 `shared-assets.json`（实测与 write 副本**字节一致**、索引覆盖 32/32 零遗漏）；`sync-shared-assets.py` 无目录组能力，必须人工复制 | `shared-assets.json` 36 组无它；`check-shared-files.sh` 同名字节比有守卫 | 最小：把索引 `genre-prose-cards.md` 登记一组；1 文件 / 6 行 |
| PC5 | 10 份 agent-references 无 agent 模板一级路由（只能包内二级到达）；部署包内有 24 处指向包外文件的裸名引用（10 个文件名，全属 write）；「包内路由表边界」批注只点名 2 个包外名字 | 实测枚举；**守卫盲区已实测证伪**：往 fixture 的 `agent-references/` 放新文件 `zzz-audit-orphan.md`，`static-check.py` **未报 dead-reference**（`SKILL.md:86` 对目录整体的引用使 `add_target`（`:581-593`）递归纳入全部文件） | 批注改正向白名单口径（列 10 个包外名字，其余均在包内）；4 文件 / 各 1 行 |
| PC6 | 外围两处数字过期：`docs/执行总纲V2.md:50`（27 → 实为 29）、`scripts/README.md:50`（10 条 → 实为 11 条） | 见总计划 G7 | 与 G7 同批 |

## 五、覆盖矩阵

| 面 | 守卫/测试 | 状态 |
|---|---|---|
| 7 agent 模板纪律（禁互引/挂载点/单副本） | `check-agent-template-rules.py` + 回归 | ✅（7 templates ok） |
| `agents_version` 全链 | `check-agents-version-sync.py` + 回归 | ✅（29 一致）；**不含 `docs/` 与 `references/`**（PC6、import 的 IM1） |
| references 可达性/frontmatter/跨 skill | `static-check.py` + 回归 | ✅（10/10）；**per-file 路由覆盖率是盲区**（PC5，已实测证伪） |
| agent-references 副本字节一致 | `sync-shared-assets.py check`（顶层 29/32 登记）+ `check-shared-files.sh`（同名字节比） | ✅（36 组/51 副本；**本人另跑 `check-shared-files.sh` = Reference groups checked: 64 | Mismatches: 0**）；`emotional-methods.md` 被显式排除（PM9）；33 张题材卡有字节检查无 sync（PC4） |
| narrative-writer 模板体积 | `check-doc-budget.sh` | ✅（余 46） |
| 部署契约文本 | `check-moshu-setup-deployment.sh:148-182/240/474-480` | ✅（CI 独立 job；本人基线复跑 **PASS**） |
| `merge-claude-settings.py` | `check-moshu-setup-deployment.sh:196-233` | ✅（另经直接 import 实测复核全符） |
| hook 行为（gaps/正则/编码/locale） | `check-hook-regex-sync.sh`、`test-story-continuity.sh`、`check-hook-locale-safety.sh`、`test-hook-encoding-portable.sh` | ✅ |
| **`deploy.py`（365 行部署执行体）** | — | ❌ **零测试、零守卫、不在 CI**（PM6；PM1/PM2 即其产物） |
| **毒句式欠账门 `:228`** | — | ❌ 零测试且未进 C7 裁决记录（PM4） |
| **Bash 面 vs Write/Edit 面门集对称性** | — | ❌ 盲区（PM5） |
| 本 skill 行为契约 | `behavior-contracts.json` | ❌ 11 条全指 moshu-write |
| eval 场景 | `evals/scenarios/` | ❌ 无 setup 场景（仅「开书」剧本 `:5` 列为可选前置） |

## 六、实测记录（节选）

| 检查 | 结果 |
|---|---|
| **本人复核 PM1** | `deploy.py:359-361` `else` 分支无 `sys.exit(1)` → 退出码恒 0 坐实 |
| **本人复核 PM2** | `:181`/`:279` 的 `if f.is_file()` 确实过滤子目录 → 子卡漏检坐实 |
| **本人复核（推翻分身声明）** | `bash scripts/check-shared-files.sh` → `Reference groups checked: 64 | Mismatches: 0` → `scripts/README.md:15` 的「64 组」**正确**，deslop 报告中"实测 32 组"的复算口径有误，该条不列入整改 |
| 真实部署演练 | `deploy` → hooks 10 文件 + lib 2、agents 7、rules 4、agent-references 33 项；sentinel 六字段齐（`agents_version: 29` / `setup_skill_version: 1.3.0` / `target_cli: claude-code` / `resolver_strategy` / `references_dir`）与 `SKILL.md:100-107`、`current-contract.json`、7 份 SKILL.md 逐条相符 |
| `verify` 正常路径 | 7 项全 PASS，退出 0 |
| `merge-claude-settings.py` 直接 import | 幂等 ✓ / 模板 8 命令各一份 ✓ / 用户自有 hook 保留 ✓ / `permissions` 等非 hooks 字段保留 ✓ / 坏 JSON → `MergeError`（deploy 记 fatal 不写 sentinel）✓；用户对受管 hook 的 `timeout` 被替换属**已声明**行为（`SKILL.md:94`、`UPGRADING.md:42`） |
| 计数实测 | agent-references 顶层 32 / 题材卡 32 / 索引覆盖 32-32 / 全仓 references 188 / `exit 2` 在 `:86/:144/:160/:199/:228` / 术语零违例（28 处「对标书」均为泛指） |
| static-check 孤儿盲区实验 | fixture 内新增 `zzz-audit-orphan.md` → **未报** dead-reference（PC5 直接证据） |

**环境限制**：子代理侧 bash 不可用，`.sh` 类改静态阅读；**本人在策略放开后已复跑全量**，`check-moshu-setup-deployment.sh`、`check-shared-files.sh` 等 13 个 check 全绿（见 [基线-守卫全量.md](基线-守卫全量.md)）。

## 七、整改计划

> **PM4 整改状态（2026-08-21 施工中）**：①②已执行——头注"三类"→"四类"并补主产物门（`guard-outline-before-prose.sh:5-10`）；③欠账门测试与「审核记录.md 追加 C7 勘误」**待作者裁决**（审计记录文件我方只写"整改回执"，勘误条目需作者确认后追加，见总计划 PM4 标注）。

| 编号 | 级别 | 修法 | 改动量 | 依赖 | 验收 |
|---|---|---|---|---|---|
| **PM1** | 需修 | `verify` HAS FAILURE → exit 1 | 1 文件 / ~5 行 | 无 | `deploy.py verify` 人为造错必非 0 |
| **PM2** | 需修 | `rglob` 递归 + 子卡断言 | 2 文件 / ~6 行 | 无 | 删子卡必 FAIL；`check-moshu-setup-deployment.sh` 绿 |
| PM3 | 需修 | 3 模板 `。，` 拼接修回 | 3 文件 / 6 行 | 无 | `check-agent-template-rules.sh` + `check-doc-budget.sh` |
| PM4 | 需修 | 头注四类 + C7 勘误呈报 + 欠账门测试 | 3 文件 / ~15 行 | **需作者确认 C7 裁决是否覆盖 `:228`** | `check-moshu-setup-deployment.sh` |
| PM5 | 需修 | 主产物门搬进 JS 核（或改注释明示不对称） | 1 文件 / ~20 行 + 1 测试 | 无 | `check-moshu-setup-deployment.sh` |
| PM6 | 需修 | usage 串 + 新增 `test-deploy.py` + CI 三处同步 | 4 文件 / ~85 行 | PM1/PM2 之后（测试要断言修好的行为） | `python scripts/test-deploy.py` |
| PM7 | 需修 | README:127 计数改非数字表述 | 1 行 | 无 | `check-story-numbers.sh` |
| PM8 | 需修 | 见 G1 | — | — | `check-claude-adapter.sh` |
| PM9 | 需修 | `emotional-methods.md` 合并 → 登记 → sync → 移出白名单 | 3 文件 | 无 | `check-shared-files.sh` 64 组 0 mismatch |
| PC1-PC6 | 候选 | 见上表 | ≤40 行 | PC1 随 G5 | — |

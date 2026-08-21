# moshu-deslop 审计报告

- 审计日期：2026-08-21
- 对象：`skills/moshu-deslop/`（8 文件：SKILL.md + 3 references + `scripts/{check-ai-patterns.js 69KB, check-degeneration.js, check-outline-copy.js, normalize-punctuation.js}`）
- 定位：全仓最重的确定性检测器所在地，5 组共享资产的 canonical 源

## 一、结论

**全仓最扎实的确定性层，分级纪律零违反。** 三项核心不变量实测成立：

1. **blocking 集严格等于文档承诺的 7 类**，全部确定性句式/标点，**无一条读感类被误升**（逐条核对 `check-ai-patterns.js` 的 type/severity 对：`:441/442` em-dash、`:496/497` voice-contrast、`:537/538` negation-parade、`:627/628` reverse-not-is、`:661/662` trailer-ending、`:673/674` trailer-summary、`:1422/1423` not-is-comparison）——`README.md:98` 的承诺成立。
2. **`eval-prose-quality.sh` 三条核心断言全 PASS**：缺陷样本 blocking=5、总命中 8 > 干净样本 1、干净样本 **blocking=0**。
3. **5 组 canonical、12 份副本 SHA256 逐一字节一致**。

**问题全部是"文档没跟上代码"**，无阻断级。

## 二、阻断级：0 项

## 三、需修级：4 项

### DM1 `<!-- 去味:跳过 -->` 豁免标记在 deslop 三份文档零登记，Phase 1 预检可静默假清白

- **现象**：`check-ai-patterns.js` 对首 6 行含该标记的文件**整文件跳过并退出 0**；deslop 的 `SKILL.md`、`references/deslop-workflow.md`、`references/banned-words.md` **从未出现该标记**，Phase 1/4 只给命令行、无"见到跳过提示怎么办"的指示。模型按退出码判定，会把"有 5 处 blocking 但被豁免"读成"无确定性句式问题"。
- **证据**：标记实现 `check-ai-patterns.js:357`（全/半角冒号皆认）、`:320`（提示语）、`:45`（USAGE 声明"first 6 lines skips the entire file"）；deslop 零登记见 `deslop-workflow.md:64-67`（Phase 1）与 `:303-316`（Phase 4 四命令）；write/hook 侧语义完整（`workflow-chapter.md:146/:154`、`workflow-daily.md:71`、`story_hook_core.js:920`、`guard-outline-before-prose.sh:204`）。
- **实测**：同一份含 `不是A，而是B——` 的正文，带标记 → ai-patterns 输出"命中「去味:跳过」豁免标记，跳过扫描"、**exit 0**；去标记 → 2 条 blocking、exit 1。**同一带标记文件上 `check-degeneration.js` 仍报 blocking、`normalize-punctuation.js --check` 仍报 em-dash**——证明 write 侧"其余网照常"的表述准确，缺口纯在 deslop 文档。
- **影响**：用户显式跑 `/moshu-deslop`（意图=现在就要去味）时，若该章此前被标过豁免，确定性预检零命中通过，而另两个脚本却照报——模型面对不对称无文档依据，最可能"报告无句式问题"。**去味 skill 主职能上的沉默失效。**
- **修法**：`deslop-workflow.md` Phase 1 预检末尾加一段：「若脚本输出「命中「去味:跳过」豁免标记，跳过扫描」，说明该文件首 6 行带用户显式豁免标记；本次是**显式调用去味**，应告知用户标记在场并询问是否删标记后重扫，**不得把跳过当成零命中**。豁免只作用于 check-ai-patterns，degeneration/标点/细纲照搬三网照常。」
- **改动量**：1 文件 / ~100 字（`deslop-workflow.md` **未进 doc-budget**，无预算压力）。

### DM2 `check-degeneration.js` 的 advisory 例外清单在三份消费文档里都漏了"对话行 tier1 降级"

- **证据**：代码 `check-degeneration.js:291-299`（tier1 命中时 `severity: dialogue ? 'advisory' : 'blocking'`，message 追加"例外：角色为作者/编剧…台词里可能合法"）、`:301-307`（tier2 恒 advisory）、tier1 词表 `:50`（8 词）；脚本 USAGE `:15-16` **描述正确**。三份文档均缺：`deslop-workflow.md:313`、`moshu-review/references/review-workflow.md:136`、`moshu-write/references/workflow-chapter.md:151`。全仓唯一写对的是 `CHANGELOG.md:503`——落地时记录过，未回灌流程文档。
- **影响**：写手/编剧题材（角色在故事内真讨论创作）台词出现 `细纲` 时脚本给 advisory，而三份文档教模型当 blocking → 触发不必要的整段回炉，**浪费 write 侧 2 轮修复预算**（`workflow-chapter.md:154` 明确 blocking 消耗预算、advisory 不消耗）。
- **修法**：三处各加约 6 字括注（如"advisory（tier2 章节/歧义词、**对话行里的 tier1 工程词**）只提示"）。**改动量**：3 文件 / 各 1 行内改（注意 `workflow-chapter.md` 余量 51）。

### DM3 机检修复轮次两套口径（write 统一阀门 2 轮 vs deslop 收敛终止 3 轮），互不引用

- **证据**：write 侧 `workflow-chapter.md:154`「所有机检项共享**同一份自动修复预算 = 2 轮**…2 轮后停止自动修复」；deslop 侧 `deslop-workflow.md:355-358`「全文上限 **3 轮**重扫」。deslop 三份文档「修复预算」全仓零命中；`workflow-chapter.md` 也从不提 deslop 的 3 轮。定位声明 `moshu-deslop/SKILL.md:100-101`（流水线 通用 / 位置 润色（共享收尾））= 会在 write 章节流程内被调用。
- **影响**：同一章在 write 流程内触发 deslop 时，模型面对"2 轮停"与"3 轮上限"无裁决依据；按 3 轮走就突破 write 的 token 失控护栏。
- **修法**：`deslop-workflow.md` 收敛终止第 2 条后加一句："在 moshu-write 章节流程内被调用时，自动修复轮次服从 `workflow-chapter.md`「机检修复预算」的统一阀门 2 轮；本节 3 轮上限只适用于独立 `/moshu-deslop` 会话。"**改动量**：1 文件 / ~60 字。

### DM4 deslop 名下 3 份热路径 canonical 余量全部 <1%

| 文件 | 用量/预算 | 余量 | 率 |
|---|---|---|---|
| `moshu-deslop/SKILL.md` | 3271 / 3300 | 29 | 0.88% |
| `anti-ai-writing.md`（canonical 在 deslop） | 14264 / 14300 | 36 | 0.25% |
| `banned-words.md`（canonical 在 deslop） | 4177 / 4200 | 23 | 0.55% |
| 路径组「正文 agent 上下文」 | 43603 / 43700 | 97 | 0.22% |

- **影响**：DM1/DM3 落在未登记文件（无压力），DM2 会落到 `workflow-chapter.md`（余 51）。真正风险是**未来任何 Gate 规则/禁用词扩充直接 OVER**，届时容易走"改断言/调预算"的捷径。
- **修法**：见总计划 G5；另在 `doc-budget.json` `_comment` 追加现状备注（1 行）。

## 四、候选级

| 编号 | 发现 | 证据 | 修法 |
|---|---|---|---|
| DC1 | `deslop-workflow.md:72` 的 advisory 类别枚举缺 5 类（`crowd-reaction`/`rhetoric-flip-variant`/`model-roadmark`/`nominalization`/`hint-colon`），且行尾"完整类别见 anti-ai-writing.md"指向不准（这 5 类的类型名在该文件零命中，4 类现象描述实际在 `banned-words.md:17/24/97-98/121`） | 实际 advisory 18 类（逐对 type/severity 核对）；**实测本仓自己的缺陷样本 `evals/samples/prose-ai-flavored.md` 就产出 2 条 `crowd-reaction`** | 补 5 个中文名 + 指向改为两份文件；1 行 |
| DC2 | Phase 3 spawn prompt 引用不存在的节名「问题模式目录」 | `deslop-workflow.md:125` vs `anti-ai-writing.md:233`（实际标题 `## 12 种 AI 写作模式检测`，"问题模式目录"零命中） | 8 字替换 |
| DC3 | `eval-prose-quality.sh:17` 裸调 `python3`，与同目录 5 个脚本的探测写法不一致 | `check-shared-files.sh:61-66` 等均探测；`check-python-invocation.sh:31-32` 明示豁免 CI 脚本，故**非缺陷**，仅本地可复现性 | 照抄 6 行探测；1 文件 |
| DC4 | `scripts/README.md:50`「10 条约束在位」实测 11 条 | 见总计划 G7 | 与 G7 同批 |
| DC5 | `doc-budget.json:70` 的 why 写"约 3.4K"，实测 3271（若真 3.4K 已 OVER） | 纯注释失真 | 1 字符 |
| DC6 | 两份 deslop canonical 的预算登记挂在 write 副本路径上（`doc-budget.json:48-56` vs `shared-assets.json:52-76` 的 source） | 当前**无风险**（字节一致，量同源），仅登记口径不统一 | 可不改 |
| ~~DC7~~ | ~~`scripts/README.md:15`「64 组」实测 32 组~~ | **本人复跑推翻**：`bash scripts/check-shared-files.sh` → `Reference groups checked: 64 | Mismatches: 0` → README **正确**，分身复算口径有误 | **不列入整改** |

## 五、覆盖矩阵

| 机制 | 覆盖 |
|---|---|
| `shared-assets.json` canonical 源 | ✅ **5 组**（ai-patterns / degeneration / normalize-punctuation / banned-words / anti-ai-writing）+ 1 组目标（check-outline-copy，源在 write） |
| 副本字节一致 | ✅ 12/12 SHA256 一致 |
| `doc-budget.json` | ✅ 已登记（SKILL.md + 名下 2 份 canonical 经 write 路径）；余量 <1%（DM4） |
| `behavior-contracts.json` | ❌ 0 条（11 条全挂 write） |
| 专项回归 | ✅ **4 个 + 1 端到端**：`test-ai-patterns.sh`、`test-degeneration.sh`、`test-outline-copy.sh`、`test-normalize-punctuation.js`、`eval-prose-quality.sh` |
| 三平台 CI | ✅ ubuntu+windows+macOS 跑四检测器；`eval-prose-quality.sh` 仅 ubuntu |
| eval 场景 | ❌ 3 剧本零提及 deslop 与四检测器（仅日更剧本 1 条人工项泛指） |
| 版本口径 | ✅ 一致（1.1.1 == 1.1.1） |

## 六、实测记录（节选）

| 检查 | 结果 |
|---|---|
| blocking 分级逐条核对 | 7 类全确定性，无读感类误升 |
| `eval-prose-quality` 三断言 | flavored blocking=5 / 总 8；clean blocking=0 / 总 1 → 全 PASS |
| 12 份副本 SHA256 | 6 组全等（ai-patterns `63DBDDE08810` ×3、degeneration `BE6F7F6A3B5C` ×3、normalize `43686A505DAB` ×3、outline-copy `A0B8C015553C` ×2、banned-words `791DAF6DFE6A` ×4、anti-ai `BF4B720149CE` ×4） |
| 豁免标记跨脚本行为 | 带标记：ai-patterns exit 0（跳过）/ degeneration exit 1 / normalize exit 1；去标记：ai-patterns exit 1 |
| `check-outline-copy.js` 阈值 | `MIN_RUN = 16`（`:42`）↔ 文档">15 字"（`SKILL.md:94`、`deslop-workflow.md:315`）✅ |
| 可数声明 | 7 Gate ✅ / 12 种模式 ✅ / 删除比例 15·25·35% ✅ / references 3 份 ✅ |
| **本人补跑（策略放开后）** | `test-ai-patterns.sh`、`test-degeneration.sh`、`test-outline-copy.sh`、`test-normalize-punctuation.js`、`eval-prose-quality.sh` **全部 PASS**（见 [基线-守卫全量.md](基线-守卫全量.md)） |

## 七、整改计划

| 编号 | 级别 | 修法 | 改动量 | 依赖 | 验收 |
|---|---|---|---|---|---|
| **DM1** | 需修 | Phase 1 预检补豁免标记处置指示 | 1 文件 / ~100 字 | 无 | `static-check.sh`；人工走查 |
| DM2 | 需修 | 三处流程文档补"对话行 tier1 降级"括注 | 3 文件 / 3 行 | G5（workflow-chapter 余 51） | `check-doc-budget.sh` + `check-behavior-contracts.sh` |
| DM3 | 需修 | deslop 收敛终止服从 write 统一阀门 | 1 文件 / ~60 字 | 无 | `static-check.sh` |
| DM4 | 需修 | 见 G5 + `_comment` 备注 | 1 行 | — | `check-doc-budget.sh` |
| DC1/DC2/DC5 | 候选 | 枚举补 5 类 / 节名修正 / why 数字 | 3 行 | 无 | `static-check.sh` |
| DC3 | 候选 | `eval-prose-quality.sh` 加解释器探测 | +6 行 | 无 | 本地可跑（已验证 shim 方案等价） |
| DC4 | 候选 | 见 G7 | — | — | — |

# moshu-scan 审计报告

- 审计日期：2026-08-21
- 对象：`skills/moshu-scan/`（12 文件：SKILL.md 349 行 + 5 references + `scripts/{cdp-utils.js, scan-analyze.js, qidian/fanqie/jjwxc/qimao-rank-scraper.js}`）
- 方式：委派深审（**未联网、未启动 Chrome/CDP、未真实抓取**，scraper 仅静态阅读）+ 本人复核 SM1/SM3

## 一、结论

**可用但契约面有真实漏洞，无阻断级。** 选题决策交接契约三方对齐（`current-contract.json` `topic_decision_phase: 5` ↔ `topic-decision.md:4` ↔ `SKILL.md:294`，并被 `check-current-skill-contracts.py:1081-1129` 双向锁死）；CDP 跨 skill 引用合规；4 个 scraper 的参数校验、per-榜单隔离、连通性自检做得扎实；版本无滞后（1.1.1 == 1.1.1）。

**三处真实漏洞**：①`[数据稀疏]` 只有 2/4 平台实现，而选题"不许给高"的硬规则完全依赖它；②番茄采集无 partial 语义，部分失败 exit 0；③scraper 输出与 `scan-analyze.js` 适配器之间零联合守卫，4 份 fixture 已与真实产出漂移——这是本 skill 最大的"改了不会被发现"面。

## 二、阻断级：0 项

## 三、需修级：6 项

### SM1 `[数据稀疏]` 只有起点/七猫实现，番茄/晋江缺失 → 选题硬规则静默失效 ✅本人复核成立

- **证据（本人逐平台 grep 计数）**：`qidian` 1 处、`qimao` 1 处、**`fanqie` 0 处、`jjwxc` 0 处**。
  - 规则来源：`SKILL.md:144`「>= 15 条有效数据（小平台 >= 10）｜不足则在文件头注明 `[数据稀疏] 实际采集 N 条`」+ `references/scan-output-format.md:206`。
  - 消费方（硬规则）：`references/topic-decision.md:40`「某方向背靠的榜单若标了 `[数据稀疏]`…该方向**不许给"高"**，强制降到"中"」+ `SKILL.md:301`。
  - 实现 ✓：`qidian-rank-scraper.js:364`、`qimao-rank-scraper.js:214`。实现 ✗：`fanqie-rank-scraper.js:364-371`（problems 只判 `totalBooks === 0` 与标题解析率）、`jjwxc-rank-scraper.js:276-286`（只判详情与 `--list-only`；`:293` 的"有效条目"恒为 `totalBooks/totalBooks`）。
  - 可触达路径：`fanqie:277-280` 品类菜单失败降级单题材 + `--top 5`（`:231` 允许 1-100）→ 5 条且头部 `[OK]`、`问题摘要：无`。
- **影响**：番茄/晋江条目不足时头部显示 [OK]，`topic-decision.md:40` 因触发条件不存在而失效 → **5 条样本也能出「可行性：高」**，直接违背 `SKILL.md:10` 的核心信念（"跨样本重复模式才算信号"）。跨文件契约空洞，非措辞问题。
- **修法**：并入两处已有 `problems` 数组——`fanqie:371` 后 `if (totalBooks > 0 && totalBooks < 15) problems.push(…)`；`jjwxc:285` 后同款。**改动量**：2 行代码 + `test-scan-runtime.js` 各 1 条断言（~8 行）；文档无需改（文档已是权威口径）。

### SM2 番茄采集无 partial 语义：`--channel all` 部分失败仍 exit 0

- **证据**：`fanqie-rank-scraper.js:425` `return written;`（`main()` 唯一返回值），失败路径 `:409` `continue`、`:418-422` catch 都只写 stderr、不计入返回；`cdp-utils.js:286-288` 整数分支置 `planned=written, failed=0, partial=false` → `:299` 的 partial 分支永不进入 → exit 0。对照：`qidian:593-599`、`qimao:416-422`、`jjwxc:397-403` 均返回结构化 outcome。测试同步缺口：`test-scan-runtime.js:586/787/541` 分别测了起点/七猫/晋江 exit 2，**唯独番茄只有纯函数测试**（`:803`）。
- **影响**：4 个目标中 3 失败 1 成功 → 退出码 0，调用方从退出码得到"全部成功"。番茄恰是反爬最重、最易部分失败的平台。
- **修法**：`main()` 改为累计 `planned/written/failed/partialReasons` 并返回结构化对象（同 qidian 形状）。**改动量**：~12 行 + `testFanqiePartialStatus`（复用现有 harness，~15 行）。

### SM3 5 处 `{SKILL_DIR}/moshu-cdp/scripts/setup-cdp-chrome.js` 按仓库约定解析不到 ✅本人复核成立

- **证据（本人 `git grep 'SKILL_DIR}/moshu-cdp'` 精确命中 5 处）**：`scripts/cdp-utils.js:8`、`fanqie-rank-scraper.js:18`、`jjwxc-rank-scraper.js:22`、`qidian-rank-scraper.js:26`、`qimao-rank-scraper.js:17`。
  - 约定定义（scan 自己写的）：`SKILL.md:66`「`{SKILL_DIR}` 指当前加载的 moshu-scan skill 根目录」；全仓同义定义另见 `moshu-deslop/references/deslop-workflow.md:69`、`moshu-write/references/workflow-chapter.md:148`、`moshu-review/references/review-workflow.md:132`；基础组件自身用自根形式 `moshu-cdp/SKILL.md:25`。
  - 按约定展开 = `skills/moshu-scan/moshu-cdp/scripts/setup-cdp-chrome.js` → **不存在**。
- **影响**：AI 排障时按注释字面执行 → ENOENT，随后自行猜路径或跳过 CDP 启动。守卫覆盖不到（`static-check.py` 不解析 JS 注释）。属反模式 #3 同类（按字面不可执行）。
- **修法**：5 处统一改为「按 moshu-cdp skill 的 `{SKILL_DIR}/scripts/setup-cdp-chrome.js 9222` 启动（或 `/moshu-cdp`）」。**改动量**：5 行（同一句，可一次替换）。**注**：本项与 [审计-moshu-cdp.md](审计-moshu-cdp.md) 的 N1 是同一发现，合并一次改。

### SM4 scraper 输出 ↔ `scan-analyze.js` 零联合守卫，4 份 fixture 已漂移

- **证据（逐项）**：
  - 无联合测试：`test-scan-analyze.js:15` 只喂 `tests/fixtures/scan/`；`test-scan-runtime.js:1477-1501` 的 24 个用例全在采集侧，**无一处把 `renderMarkdown` 输出交给 `scan-analyze` 解析**。
  - 命名漂移：真实 `番茄…_全题材_{日期}.md`（`fanqie:412`）、`晋江…_全站_{日期}.md`（`jjwxc:380`）、`七猫{频道}{榜单}{周期}_{日期}.md`（`qimao:384`）；fixture 三份均缺相应段。
  - 质量标记漂移：4 份 fixture 第 2 行 `- 数据质量：OK`；4 个 scraper 一律写 `[OK]`/`[存在问题]`（`qidian:365`、`qimao:219`、`jjwxc:286`、`fanqie:372`）。
  - **起点 meta 形状漂移（最严重）**：fixture `起点月票榜_20260818.md:13` 用 `|` 分隔且把签约/收费/字数/总推荐塞进 meta；现行 `qidian:390` = `[b.author, b.genre, b.status].filter(Boolean).join(" · ")`，四字段一律走 `:394-398` 的独立 `**字段：值**` 行。
  - 起点标签漂移：fixture `:18` 有 `**标签：**`；`normalizeMobileBook`（`:315-347`）不产 `tags`，`:400` 的 `if (b.tags?.length)` 恒假，`:447-449` 明写 `--detail` 在 mobile/auto 不打开详情页 → 真实文件无标签行。
  - 七猫头部漂移：fixture 缺 `- 作品页链接：N / N` 与 `- 热度命中：N / N`，而 `qimao:232-233` 无条件输出。
- **影响**：`test-scan-analyze.js` 全绿只证明"能解析这 4 份手写文件"。反向亦成立：改任一 scraper 的 meta 段序不会有任何测试报警，`scan-analyze` 的 `segs[1]` 映射（`:123/:129/:141`）会静默错位。
- **修法**：`test-scan-analyze.js` 末尾加契约用例——`require` 各 scraper 的 `renderMarkdown`（qidian/qimao 已导出，jjwxc/fanqie 需各抽渲染入口），用固定假 book 渲染后交给 `detectPlatform`/`parseBlocks`/`adapt` 断言 author/words/metric/block；fixture 保留作解析回归并在文件头注明"手写近似样本"。**改动量**：测试 +~45 行；jjwxc ~10 行、fanqie ~15 行抽函数 + 各 1 行导出。

### SM5 番茄/起点题材缺失时 meta 段位偏移，`scan-analyze` 把"状态"当题材

- **证据**：`fanqie:332-333` `const catSeg = category ? … : "";` + `:337` 拼接 → category 空时段序变 `[author, status, reads在读, words字]`，`scan-analyze.js:129` `segs[1]` 取到 `连载中`；起点 `qidian:390` `filter(Boolean)` 同理（`scan-analyze.js:123`）。对照做对的：`qimao:245-252` 六段一律 `|| "[待补]"` 占位，段位恒定（`:141` 因此安全）。无守卫：4 份 fixture 题材字段全非空，该分支从未被测。
- **影响**：**目前有限**——`genre` 仅被 `scan-analyze.js:192` 的晋江告警消费，`--dist`/`--genre`/条目输出行都不读它。但适配器契约已破，而"提取题材"是文档宣称能力（`SKILL.md:186`）。
- **修法**：`fanqie:333` 改 `` ` · ${category || "[待补]"}` ``、`qidian:390` 改 `[b.author, b.genre || "[待补]", b.status]`，使段位恒定。**改动量**：2 行；配 SM4 用例回归。

### SM6 CI 三处同步缺一处：`test-scan-analyze.js` 不在 CONTRIBUTING 本地清单

- **证据**：`cross-platform.yml:86` ✓、`scripts/README.md:45` ✓、`CONTRIBUTING.md:116-155` 只有 `test-scan-runtime.js`（`:128`）。
- **修法**：`:128` 后补两行（连同 analyze 的 `test-merge-summaries.js`）。**改动量**：2 行。

## 四、候选级

| 编号 | 发现 | 证据 | 修法 |
|---|---|---|---|
| SC1 | frontmatter/marketplace description 未含七猫（触发面窄于实际能力） | `SKILL.md:4` 与 marketplace 同句写"起点、番茄、晋江等平台"；而 Phase 1 提问 `:34`、速查表 `:308-313` 4 行、`:186`「4 平台通用提取」、七猫采集节 `:99-107` 都已 4 平台；git `71be4f5` 补了提问未补 description | 两处 description 同批改 + 触发词补"七猫排行"；2 行 |
| SC2 | 参考资料索引漏 `scan-analyze.js`（它是 Phase 3 强制入口）；cdp-utils 函数清单过期（表列 6 个，实际导出 13 个） | `SKILL.md:333-342` 10 行无 scan-analyze；`:338` vs `cdp-utils.js:314-328` | 补 1 行 + 改括号内容；2 行 |
| SC3 | `moshu-scan/SKILL.md` 是最大的未登记热路径文档（8610 去空白，是已登记 analyze 的 3.8 倍） | `doc-budget.json` 5 个 SKILL.md 条目为 write/review/import/deslop/analyze；`:10` 自述"新增热路径文件时把它加进来，否则不受任何约束"（setup 属部署冷路径 `:9` 明确豁免） | 加一条 `{"path":"skills/moshu-scan/SKILL.md","budget":8700,…}`；5 行 JSON |
| SC4 | 已删除的第 5 个 scraper 留三处残留 | git `9dda299` 删 `ciweimao-rank-scraper.js`；残留 `scripts/README.md:44`「5 个 scraper」（实测 4 个）、`jjwxc:363` 与 `qidian:565` 注释"与番茄/刺猬猫一致"。（`scan-analyze.js:20/35/36/144` 的刺猬猫提及是**有意保留**，`:36` 注释写明"识别但无适配器"，不算残留） | 改"4 个 scraper" + 删两处注释词；3 行 |
| SC5 | `test-scan-runtime.js:426` 是虚化断言（`>= 4`，删到 4 后恒真、新增第 5 个也恒真）——SC4 的计数残留正是其后果 | scan 最核心可数声明（4 平台 / 速查表 / `scan-analyze.js:30` `PLATFORMS`）在守卫层无单点权威 | 改 `deepStrictEqual` 文件名列表 + "scraper 数 == `PLATFORMS.length`"；~6 行 |
| SC6 | 起点默认 mobile-ssr 下 5 个榜单实际取不同移动端榜（`collect`→书友榜），仅产物文件头一行披露 | `qidian:56-81` `mobileLabel`；`:443-446` 披露；`SKILL.md:68-79` 榜单表与 `scan-output-format.md:19-42` 模板都未披露；默认模式 `auto`（`:462`） | 模板补字段行 + 表格脚注；~8 行 |
| SC7 | 起点字段声明含"标签/最新更新"，默认模式不产出 | `scan-output-format.md:17/:46` vs `qidian:315-347`（无 tags、`:345` `updateText: ""`）、`:447-449`；且 `--detail` 未在 `SKILL.md:66` 文档化 | 加"仅 `--mode cdp --detail yes`"限定；3 行 |
| SC8 | `--dist` 题材词表硬编码 15 个男频向题材，女频/晋江几乎全落"其他" | `scan-analyze.js:204` 词表 + `:210` 子串匹配；晋江 18 频道（`jjwxc:72`）与番茄女频 18 题材（`scan-output-format.md:58`）除"悬疑""奇幻"外无一命中；实测 `--dist` → `晋江月榜: 其他 2` | 最小：无题材条目回退用已解析的 `block` 作题材维度（~4 行）+ `:186` 补一句 |
| SC9 | jjwxc 的 `--channel`/`--type all` 未文档化；命名规则与 3 个 scraper 不符 | `jjwxc:181/:351-353/:346-348`（`--type all` 落盘 6 份，`test-scan-runtime.js:556` 已断言）vs `SKILL.md:118-121` 三条示例；`SKILL.md:126` 命名声明 vs `jjwxc:380` `_全站`、`fanqie:412` `_全题材` | 补 `--type all` 示例 + 命名规则改带可选范围段；3 行 |
| SC10 | `behavior-contracts` 对 scan 零覆盖；evals 无扫榜剧本 | 11 条全在 write；未守面：`topic-decision.md:40`「不许给"高"」、`SKILL.md:301-302` 可行性上限、`SKILL.md:224` 晋江「`--list-only` 视为不合格」 | 加 2 条 contract（`scan-sparse-no-high`、`scan-jjwxc-list-only-invalid`）；JSON +12 行。e2e 空白只记候选，**不引 LLM/联网** |

## 五、覆盖矩阵

| 面 | 守卫 | 状态 |
|---|---|---|
| 选题决策 Phase == 5（三方 + 全仓陈旧引用） | `check-current-skill-contracts.py:1081-1129` | ✅ 双向锁死 |
| CDP argv 注入安全/JSON 契约/ENOENT/本地日期戳 | `test-scan-runtime.js:246-522` | ✅（强，含 Windows `.cmd` shim） |
| 参数校验（非法值 exit 1 且不写文件） | `:828-849` | ✅（4 平台 7 例） |
| per-榜单隔离 + partial exit 2 | `:541/586/787` | ⚠️ 3/4 平台（**番茄缺，实现亦缺** → SM2） |
| 起点 4 契约字段 + 简介 100 字 | `:622-675` | ✅ |
| 七猫周期计划 + 质量门 + 文件名 | `:678-800` | ✅ |
| 番茄纯函数 | `:803-825` | ✅（渲染与质量门未覆盖） |
| 晋江详情失败隔离 | `:541-583` | ✅ |
| scraper 无副作用 import | `:423-458` | ⚠️ 断言虚化（SC5） |
| `[数据稀疏]` 四平台一致性 | 无 | ❌ 且 2/4 未实现（SM1） |
| `scan-analyze` 平台识别/适配/`--dup` | `test-scan-analyze.js`（10 例） | ⚠️ fixture 已漂移（SM4） |
| **scraper 输出 ↔ `scan-analyze` 格式契约** | 无 | ❌ **零覆盖（最大盲面）** |
| 题材缺失时 meta 段位稳定性 | 无 | ❌（SM5） |
| SKILL.md 体积（8610） | 无（未登记） | ❌（SC3） |
| 选题硬规则/晋江不合格判定 | `behavior-contracts.json` | ❌ 零覆盖（SC10） |
| 平台数/scraper 数/参考表清单 | 无 | ❌（SC2/SC4/SC5 已各自漂移，实证失守） |
| 扫榜 e2e | `evals/scenarios/` | ❌ 空白 |

## 六、实测记录（节选）

| 检查 | 结果 |
|---|---|
| **本人复核 SM1** | 逐平台 grep `数据稀疏`：qidian 1 / qimao 1 / **fanqie 0 / jjwxc 0** → 成立 |
| **本人复核 SM3** | `git grep 'SKILL_DIR}/moshu-cdp'` 精确 5 命中（cdp-utils:8 / fanqie:18 / jjwxc:22 / qidian:26 / qimao:17）→ 成立 |
| `scan-analyze --dist --dup`（4 平台 fixture） | 题材分布 + 跨榜聚合（「星海征途」×3 平台命中）+ 晋江题材缺失告警；**真实退出码 0**（PowerShell 对 native stderr 的包装曾误显 exit 1，`2>$null` 复测确认）；`晋江月榜: 其他 2` 实证 SC8 |
| 文件清单 | 12 文件（SKILL.md 18423B/349 行 + 5 references + 6 scripts）✓ |
| 版本 | marketplace 1.1.1 == SKILL.md 1.1.1 == metadata 1.1.1 |
| **本人补跑** | `test-scan-runtime.js`、`test-scan-analyze.js` **均 PASS**（策略放开后，见 [基线-守卫全量.md](基线-守卫全量.md)） |

## 七、整改计划

| 编号 | 级别 | 修法 | 改动量 | 依赖 | 验收 |
|---|---|---|---|---|---|
| **SM1** | 需修 | 番茄/晋江补 `[数据稀疏]` 判定 + 2 条断言 | 2 行 + ~8 行 | 无 | `test-scan-runtime.js` |
| **SM2** | 需修 | 番茄 `main()` 返回结构化 outcome + partial 测试 | ~12 + ~15 行 | 无 | `test-scan-runtime.js`（部分失败必 exit 2） |
| **SM3** | 需修 | 5 处 CDP 路径注释改写（与 cdp-N1 合并） | 5 行 | 无 | `git grep 'SKILL_DIR}/moshu-cdp'` 零命中 |
| SM4 | 需修 | 加 `renderMarkdown ↔ adapt` 联合契约用例 | ~45 + ~27 行 | SM5 之后更稳 | `test-scan-analyze.js` |
| SM5 | 需修 | 番茄/起点 meta 段位恒定（`[待补]` 占位） | 2 行 | 无 | SM4 用例回归 |
| SM6 | 需修 | CONTRIBUTING 补 2 行本地命令 | 2 行 | 与 AM4 合并 | 人工核对 |
| SC1-SC10 | 候选 | 见上表 | ≤50 行 | SC3 随 G5 | — |

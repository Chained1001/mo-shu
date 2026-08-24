# 规格 · 批 B37：scan/路由/台账域审计修复

- 版本：v1.0（2026-08-25）
- 依据：全仓审计 scan 组（需修 1-5）；审计法 v1.6
- 性质：1 处代码 bug 修复（含可测性提取）+ 文档/模板对齐

## 一、现状事实

1. **fanqie ratio 作用域 bug**：`fanqie-rank-scraper.js:396` 引用 `ratio`，变量只在 `computeQualityProblems` 内定义（:206）——标题解析率 0<ratio<0.5 或全失败时 ReferenceError，整频道数据丢失且不落盘。test-scan-runtime.js:848-859 只测纯函数未覆盖渲染路径。
2. **卷纲「章节范围」双模板**：workflow-build.md:485 `{A}-{B} 章`（无"第"）vs artifact-protocols.md:276 `第{X}-{Y}章`；next_step.py:42 正则要求"第"前缀——build 模板被用时卷末判定（S5/S6）永不触发。
3. **路由判定表与 next_step.py S1 不一致**：moshu/SKILL.md:49 序 2「无含 追踪/ 或 设定/」vs next_step.py:133「正文/大纲/追踪 全缺」——仅含设定/的构建中途项目，表导向 write、脚本导向 build。
4. **台账「采风需求」行悬空**：moshu-research/SKILL.md:22 与 caifeng-methods.md:76 要求登记台账「采风需求」行（CF-{NNN}），workflow-build.md 台账模板（:31-73）无此节。
5. **scan-output-format 锚点错指**：:10/:52「见 SKILL.md『起点/番茄采集目标』表」，实际表格在 collection-guide.md:33/:50。
6. **台账「步」列头残留**：workflow-build.md:37「| 步 | 名称 |」——B33 称谓统一漏网（§2.1b 禁"步 N"）。

## 二、文件级改动清单

1. `skills/moshu-scan/scripts/fanqie-rank-scraper.js`：
   - 提取 `qualityRatioNote(totalBooks, resolvedTitles)` 纯函数（返回提示内容或 null；原 ratio 作用域 bug 的根因修复 + 可测性）
   - scrapeChannel 渲染块改调用该函数（行为等价，输出格式不变）
   - 导出 qualityRatioNote
2. `scripts/test-scan-runtime.js`：补 qualityRatioNote 两分支回归（全失败提示 / 偏低提示 / 正常 null）
3. `skills/moshu-build/references/workflow-build.md`：
   - :485「章节范围：{A}-{B} 章」→「章节范围：第{A}-{B}章」
   - 台账模板「| 步 | 名称 |」→「| Stage | 名称 |」
   - 台账模板「浮现记录」节后补「采风需求（CF 票据制）」表（CF 编号/需求描述/类型/状态，对齐 research 口径）
4. `skills/moshu/SKILL.md`：判定表序 2 条件改为「无书名目录（无含 `正文/`、`大纲/`、`追踪/` 任一的项目目录）」——与 next_step.py S1 口径一致
5. `skills/moshu-scan/references/scan-output-format.md`：:10/:52 锚点改指 collection-guide.md「起点/番茄采集目标」节

## 三、禁止事项

- 不改采集脚本的联网/爬取行为与数据输出格式（qualityRatioNote 提取为行为等价重构）
- 不改 next_step.py 判定逻辑（文档迁就脚本）
- 不动 docs/归档/**、历史批次规格

## 四、验收命令

1. `node scripts/test-scan-runtime.js` → 绿（含新 qualityRatioNote 断言）
2. `python scripts/test-next-step.py` → 绿（章节范围口径未动脚本）
3. `grep -n "章节范围" skills/moshu-build/references/workflow-build.md skills/moshu-write/references/artifact-protocols.md` → 两处均含"第"前缀口径
4. `grep -rn "采风需求" skills/moshu-build/references/workflow-build.md` → 台账模板命中
5. 守卫/回归矩阵全绿

## 五、提交规范

消息：`fix: 审计修复（scan/路由/台账）——fanqie ratio 作用域 bug（提取 qualityRatioNote 纯函数+两分支回归，原降级路径数据丢失）/卷纲章节范围统一"第"前缀（卷末判定字段级断裂）/路由表 S1 口径对齐 next_step.py/台账补采风需求 CF 表+步列头称谓/scan-output-format 锚点改指`

施工日志追加 B37 行。

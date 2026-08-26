# 规格 · 批 B49：style 文风画像与仿写校验（方案 A+B+C）

- 版本：v1.0（2026-08-26）
- 依据：moshu-style 走查预习四短板（确定性层薄——AI 手搓 one-liner / 词汇指纹无实证 / 锚点不分场景 / 无学后校验）+ 作者批准三案一批实施；旗舰评价（对话）+ 开源映射（faststylometry 度量清单、arXiv 2509.14543「分布锚比指令可靠」）。
- 前置：analyze 全线收官（0943bc8）后开工。

## 一、设计锁定（不可更改的决策，flash 照做）

- **D1 零依赖铁律**：`style_profile.py` 纯 stdlib+正则，禁引分词库——虚词密度用内置虚词表（的地得之乎者也因为所以但是而且如果虽然不仅况且于是因此然后接着反而其实几乎稍微…约 60-80 词，正则匹配/每万字）。
- **D2 兼容铁律**：「平均句长」字段名与「文风可用：是」语义逐字保留（`check-prose-candidates.js` 字面锚点 + explorer 正查——断字即断下游机检）。向后兼容四原则适用。
- **D3 三层分工落法**：计算归脚本（画像 + `--compare` 距离）、语义归 AI（4-B 词汇指纹 / 4-C 对话技法 / 阈值判级）、品味归作者（过目不变）。
- **D4 本批不动 write 侧任何文件**——锚点分场景靠「锚点旁标场景名」引导 AI 取用，不改编写召回逻辑。
- **D5 产出模板从 SKILL.md 下沉 style-learn-sop.md**（SKILL.md 留指针）——顺带修 SKILL.md 载模板的结构问题，预算大概率净减。

## 二、文件级改动清单

1. 【新建】`skills/moshu-style/scripts/style_profile.py`（唯一新脚本）：
   - 子命令 `profile`（默认）：`--input {原文} [--json]`——指标：①句长分布（按 。！？…… 分句，P25/中位/P75/均值/标准差）②段落节奏（段落数/段均句数/段落字数中位）③标点密度谱（逗/句/叹/问/省略/破折号，每百字）④对话叙述比（引号「」“”『』 内字数占比）⑤句首二字 bigram Top5 ⑥虚词密度（虚词表命中/每万字）
   - 子命令 `compare`：`--compare {a.json} {b.json}`——各指标相对差表（无阈值，判级归 AI）
   - JSON 键名稳定（测试与下游契约）；exit：0 正常 / 2 用法或缺文件；读失败三分类（缺/空/坏）各自明示；<800 字样本仍出结果但附 `sample_warning` 字段（对齐现有 low confidence 语义）
   - docstring 带解释器探测形态（chapter_boundary 先例）
2. 【新建】`scripts/test-style-profile.py`：合成 fixture（已知句长/标点/虚词构造）断言指标精确值；三分类失败；compare 距离正确性；<800 字 warning。先红后绿（构造违规断言确认能红）。
3. `skills/moshu-style/references/style-learn-sop.md`：
   - 4-A 节改：手搓 one-liner → 调用 `style_profile.py`（含探测形态与 `--json` 落盘 `画像.json`）
   - 4-D 节改（方案 B）：固定 4 段 → 四场景锚点（战斗/对话/情绪/过渡各 1-2 段，样本无该场景如实标「缺——样本未覆盖」）；`grep -F` 回查纪律逐字保留
   - Stage 5 前插仿写校验步（方案 C）：AI 按画像+锚点写 200 字仿写（选一样本覆盖场景）→ profile 仿写 → compare 原作 → AI 按阈值判级（阈值写在 SOP：句长中位相对差>30% 或 任一标点密度差>50% → confidence 降 low，两画像与距离附入文风.md「仿写校验」节）——阈值命名标注 mo-shu 自定
   - 产出规范模板迁入并改三层：画像表（脚本 JSON 摘要，含保留字段「平均句长」）/ AI 语义层（4-B/C 原文）/ 锚点（分场景标注）
4. `skills/moshu-style/SKILL.md`：Stage 4-5 与产出节改指针（模板见 SOP）；description 不动；预算预期净减（改后跑 check-doc-budget 实测）
5. CI 三处 + 注册表：`cross-platform.yml` runtime-regressions 加 `test-style-profile.py`；CONTRIBUTING；`scripts/README.md` 索引行（含 audit-guards 注册表两列：事故出身「2026-08-26 style 走查预习：确定性层薄（AI 手搓 one-liner）+2509.14543 分布锚依据」/ 末次能红验证=本批日期）
6. 走查记录 v18（或续号）落批 + 施工日志。

## 三、禁止事项

- 引分词库 / 任何第三方依赖（D1）。
- 动 write 侧任何文件（D4）；不改 check-prose-candidates.js 分布带（消费端跟进留候选）。
- 「平均句长」「文风可用：是」字段语义任何改动（D2）。
- 新增 URL 抓取源（SKILL.md future 注记保留）；StyleLLM 微调路线不做。
- 失败先判因；与规格不符走待决协议。

## 四、验收

1. `python scripts/test-style-profile.py` 全绿（先红后绿记录）。
2. 守卫矩阵全绿 + audit-guards 新行两列非空 + doc-budget 绿。
3. 兼容实测：构造按新三层模板写的样例 `文风.md`，跑 `moshu-write` 侧 `check-prose-candidates.js` 的文风检查路径确认 PASS（「平均句长」「文风可用：是」锚点有效）。
4. compare 端到端：同文本 compare 全 0 差 / 构造差异文本差值符合预期。
5. 一次统一提交（新脚本+测试+SOP+SKILL+CI 三处+注册表+记录）。

## 五、提交规范

消息：`feat(style): 文风画像与仿写校验批——style_profile.py 确定性画像（句长分布/标点谱/对话比/虚词密度，零依赖）+ --compare 距离子命令/场景分型锚点（战斗·对话·情绪·过渡）/仿写校验步（confidence 从声明变度量）/产出模板三层化下沉 SOP/CI 三处+注册表同步`

## 六、不做（本批外）

write 侧文件、分词依赖、StyleLLM 微调路线、URL 抓取源（SKILL.md future 注记保留）、check-prose-candidates 的分布带升级（消费端跟进留候选）。

# 规格 · 批 7：agent 模板 Prompt 纪律

- 版本：v1.0（2026-08-20）
- **前置依赖**：批 6 已合入（agents_version 已 27→28，本批 28→29）。
- 依据：《执行总纲V2》§五批 7；DeterminFlow JSON 完整性铁律/输出前自检/共享 section（01 档案 §5.2、§九 #4#5）；spark-arc 禁"格式同 system"互引/规范挂载点单副本（02 档案 L4/M2）。

## 1. 目标

一句话：agent 模板的产出纪律收敛为单一共享 base 段（引用即挂载），消灭互引与散落铁律，并配守卫。

## 2. 现状事实（本次实测）

| # | 事实 | 证据 |
|---|---|---|
| F1 | 7 个 agent 模板在 `skills/moshu-setup/references/templates/agents/`（moshu-architect / moshu-chapter-extractor / moshu-character-designer / moshu-consistency-checker / moshu-explorer / moshu-narrative-writer / moshu-researcher） | 本次 `ls` 实测 |
| F2 | 共享方法论副本在 `skills/moshu-setup/references/agent-references/`（25+ 个）；模板内以逻辑路径 `moshu-setup/references/agent-references/{文件名}` 引用（canonical 读取路径 `{项目根}/.claude/skills/moshu-setup/references/agent-references/{文件名}`，见 moshu-architect.md:30,36-37） | grep 实测 |
| F3 | 模板中产 JSON 的纪律（纯度/自检）现状分散程度未逐条盘点——施工第一步先 grep 摸清（见 §3 步骤 0） | 本批施工前置勘察 |
| F4 | shared-assets 同步机制可扩组（sync-shared-assets.py） | 盘点 §3.3 |
| F5 | spark-arc 教训：两段互斥时"格式同 system"式引用 LLM 看不到对方（02 档案 E2） | 档案 |

## 3. 文件级改动清单

| 步骤 | 文件 | 改什么 | 注意点 |
|---|---|---|---|
| 0（勘察） | 7 个模板 | `grep -n "JSON\|纯 JSON\|输出" skills/moshu-setup/references/templates/agents/*.md` 列出所有产结构化输出的段落，形成改动点清单（写进提交说明） | 只勘察不改动 |
| 1 | `skills/moshu-setup/references/agent-references/shared-output-discipline.md`（新） | 共享产出纪律（约 30 行）：①直接输出纯 JSON 对象，无 Markdown 围栏/无解释文字；②ASCII 直引号、换行转义、禁尾随逗号；③结构化载荷先写临时文件再以 `--input <文件>` 提交，不进对话复述；④输出前自检三问（必需字段齐？枚举合法？空集合也显式写 `[]`？） | 措辞移植 DeterminFlow nar_output/nar_discipline（01 档案 §5.2），不逐字照抄 |
| 2 | 7 个 agent 模板 | 产结构化输出处的散落纪律句替换为一句锚点引用（用模板既有的逻辑路径形态）：`产出纪律见 moshu-setup/references/agent-references/shared-output-discipline.md（引用即挂载，此处不重复）` | **不复制正文**（单副本原则）；批 6 的审稿令牌段不动 |
| 3 | `scripts/check-agent-template-rules.py` + `.sh`（新） | 见 §4 | 进 CI |
| 4 | `skills/moshu-setup/UPGRADING.md` | agents_version 28→29 段 | |
| 5 | 7 个 `skills/*/SKILL.md` agents_version 相关文本 + `scripts/current-contract.json` | 28→29。**校验面同批 6**：所有 SKILL.md 中带数字的声明（含叙述里的版本比较数字）+ UPGRADING.md 权威，以 `bash scripts/check-agents-version-sync.sh` 跑绿为准 | 守卫全绿 |
| 6 | `scripts/README.md` / `CONTRIBUTING.md` / `.github/workflows/cross-platform.yml` | 新守卫索引+CI | 三处同步 |

## 4. 新文件设计

**check-agent-template-rules.py**（守卫，算法级）：
1. 扫描 `skills/moshu-setup/references/templates/agents/*.md`。
2. 规则 A（禁互引）：命中 `格式同|同上|参照上文|见上文` → 违规（spark-arc E2 转译）。
3. 规则 B（挂载点存在）：每个模板中逻辑路径 `agent-references/[\w\-./]+\.md` 引用 → 文件必须存在于 `skills/moshu-setup/references/agent-references/`。
4. 规则 C（单副本）：`shared-output-discipline.md` 的标题行文本不得出现在任何模板正文（防复制回散）。
5. 退出 0/1；违规输出 文件:行号:原文。
- **test-agent-template-rules.py**（新）：临时目录 fixture——含互引句必须失败；引用不存在文件必须失败；正文复制纪律标题必须失败；干净模板通过。

## 5. 验收命令

```bash
bash scripts/check-agent-template-rules.sh
python3 scripts/test-agent-template-rules.py
bash scripts/check-agents-version-sync.sh
python3 scripts/test-agents-version-sync.py
bash scripts/check-moshu-setup-deployment.sh    # 模板+agent-references 部署回归（慢，必跑）
bash scripts/static-check.sh && bash scripts/check-doc-budget.sh && bash scripts/check-shared-files.sh
```

## 6. 守卫与 CI

新守卫进 CI（三处同步）；部署回归覆盖 bundle 完整性。

## 7. 回滚点

单提交 revert；agents_version 回 28 走既有升级路径。

## 8. 禁止事项

1. 禁止把共享纪律正文复制进模板（只允许锚点引用——单副本）。
2. 禁止动批 6 的审稿令牌段与各模板既有职责描述。
3. 禁止改 agent-references 既有 25+ 文件（只新增 1 个）。
4. 禁止在模板中用"格式同 X/同上"类互引（守卫规则 A 锁死）。
5. agents_version 只 bump 一次（28→29）。

## 9. 提交规范

```
feat(templates): 批7 模板 Prompt 纪律——shared-output-discipline 共享 base 段（引用即挂载）、7 模板去散落纪律句、check-agent-template-rules 守卫（禁互引/挂载点存在/单副本），agents_version 28→29
```

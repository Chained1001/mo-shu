# 规格 · 批 B35：write 域审计修复（doc-budget 乱码/预算收紧/revision 口径）

- 版本：v1.0（2026-08-25）
- 依据：全仓审计 write 组（F4 doc-budget 乱码 / F5 预算未锁 / F7 revision 重算口径）；审计法 v1.6
- 性质：JSON 注释数据修复 + 预算数字收紧 + 文档口径澄清，零可执行逻辑变更

## 一、现状事实

1. `scripts/doc-budget.json:32`（workflow-chapter why）整条乱码（`D3 ????????13 ???…`）；`:102`（chapter-core why）前缀乱码、后半正常——git 历史自批 B13 起即乱码（从未有正确文本），无法还原，按审计建议**显式标注丢失**。
2. workflow-daily 预算 12000 vs 实测 7803（余 4197），守卫提示可降到 7900——按守卫提示收紧。
3. `skills/moshu-write/references/workflow-revision.md:38`「动态快照缺失时从相关增量重算」与 recovery-protocol.md:42「不得从前文临时推断后直接手写快照」口径未衔接——改为显式走事务重建。

## 二、文件级改动清单

1. `scripts/doc-budget.json`：
   - :32 why → 标注「原文编码丢失（2026-08-25 审计标注），历史沿革见批 B12 施工日志与 git 历史」
   - :102 why 乱码前缀 → 同样标注，保留后半正常文本
   - workflow-daily budget 12000 → 7900，why 追加「→7900：B34 后实测 7803 余量 4197，按守卫提示收紧（2026-08-25 审计）」
2. `skills/moshu-write/references/workflow-revision.md:38`：「动态快照缺失时从相关增量重算」→「动态快照缺失时先运行 `tracking_commit.py check`，再重跑产生该状态的完整事务重建（不得从前文临时推断后直接手写快照——recovery-protocol 同口径）」

## 三、禁止事项

- 不臆造乱码原文（git 历史无正确文本，标注丢失而非编造）
- 不改 doc-budget 校验逻辑与守卫
- 不扩大范围

## 四、验收命令

1. `bash scripts/check-doc-budget.sh` → 绿（含 workflow-daily 7900 收紧后余量正常）
2. `grep -n "????" scripts/doc-budget.json` → 零命中
3. 守卫/回归矩阵无回归

## 五、提交规范

消息：`fix(write): 审计修复——doc-budget 乱码标注丢失（git 历史无原文）+ workflow-daily 预算按守卫提示收紧 12000→7900 + revision 角色快照缺失口径对齐事务重建`

施工日志追加 B35 行。

# 规格 · 批 B38：shared-assets 全量对账守卫化

- 版本：v1.0（2026-08-25）
- 依据：架构建议 #6（B28 教训彻底化）——check-shared-files 只查已登记 targets，"登记完备性"无人兜底（B28 genre-prose-cards 半边、B31 32 张卡半边两次漏登记）；审计法 2a「shared-assets targets 完备性」目前靠人查
- 性质：守卫逻辑增强（sync-shared-assets.py check 加对账）+ 正式回归

## 一、现状事实

- agent-references 65 个文件：64 个已登记 shared-assets，1 个 setup 内部资产（shared-output-discipline.md，无跨 skill 源副本，B34 审计确认豁免）
- sync-shared-assets.py check 只校验已登记组的字节/模式一致性，不枚举未登记副本

## 二、设计

`sync-shared-assets.py` check 子命令新增：枚举 `skills/moshu-setup/references/agent-references/` 全部文件（rglob），未出现在任何组（source 或 targets）且不在豁免清单 → 输出 `UNREGISTERED [路径] agent-references 副本未登记 shared-assets` + issues+1（exit 1）。

豁免清单（setup 内部资产，无跨 skill 源副本，仅部署使用）：`shared-output-discipline.md`——新增内部资产须在清单登记理由（注释）。

## 三、文件级改动清单

1. `scripts/sync-shared-assets.py`：run() 构造 registered_paths 集合（全部组 source+targets）；check 分支加对账循环 + 豁免清单
2. `scripts/test-shared-assets.py`：补两断言——①fixture 建未登记 agent-references 文件 → check exit 1 + "UNREGISTERED"；②fixture 建豁免名文件（shared-output-discipline.md）→ check exit 0

## 四、禁止事项

- 不改既有登记/同步/字节比对逻辑
- 豁免清单只加"确实无跨 skill 源副本"的文件（违者守卫自证）

## 五、验收命令

1. `python scripts/test-shared-assets.py` → 绿（含新断言）
2. `bash scripts/check-shared-files.sh` → 绿（含 sync check 对账）
3. 真实仓库对账通过（65 文件全登记或豁免）
4. 守卫/回归矩阵无回归

## 六、提交规范

消息：`feat(shared-assets): agent-references 全量对账守卫化——sync check 枚举全部副本，未登记且非 setup 内部资产即红（B28 类半边漏登记根治）；豁免清单共享输出纪律文件；回归 2 断言 + 规格批B38 入库`

施工日志追加 B38 行。

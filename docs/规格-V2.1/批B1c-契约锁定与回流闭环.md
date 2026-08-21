# 规格 · 批 B1c：契约锁定、回流闭环与终检

- 版本：v1.0（2026-08-21）
- **前置依赖**：批 B1b 已合入。

## 1. 目标

一句话：用契约锁死新边界（write 不改既有设定、变更日志 append-only、stale 必处理），接通回流呈现，B1 终检收口。

## 2. 现状事实

| # | 事实 | 证据 |
|---|---|---|
| F1 | behavior-contracts 现 11 条，无 build 相关节 | B1b 后实测 |
| F2 | write 侧已有"细纲失效检查"机制（角色退役/死亡级联），stale 消费是其自然扩展点 | workflow-daily 细纲失效节 / chapter-core |
| F3 | volume-review 末尾无下卷规划转向提示 | Q8 裁决输入 |

## 3. 文件级改动清单

| 文件 | 改什么 | 注意点 |
|---|---|---|
| `scripts/behavior-contracts.json` | +3 契约（Q9）：①`build-revision-requires-impact`（path=`skills/moshu-build/references/revision-workflow.md`，must_contain=`影响分析`）②`write-no-existing-setting-edit`（path=`skills/moshu-write/references/outline-workflow.md`，must_contain=`不修改既有设定`）③`changelog-append-only`（path=同①，must_contain=`追加一行`） | 措辞与 B1a/B1b 落地文本逐字对齐（先 grep 实文再填） |
| `scripts/test-behavior-contracts.py` | 契约计数常量 11→14 同步（若有）+ 反向 fixture 三条 | |
| `skills/moshu-write/references/volume-review.md` | 末步追加固定提示：`下卷规划转 /moshu-build（消费本卷复盘的下卷方向候选）` | Q8；斜杠命令文本非文件引用 |
| `skills/moshu-write/references/workflow-daily.md`（或 chapter-core 对应节） | 细纲失效检查扩展一句：写前若细纲文件头含 `<!-- stale:` 标记，先按标记原因复核修订（对照 build 变更日志）再写，处理后在文件头移除该标记 | 最小增量；doc-budget 等量控制 |
| 终检（本子步收尾） | ①全守卫矩阵复跑；②`grep -rn "workflow-setup"` 终扫零命中；③路由五方一致性（路由表/判定表/next_step/test/README）复核；④README_EN 同步复核；⑤shared-assets `check` 副本一致；⑥`docs/审计` 无涉；⑦CHANGELOG 追加 v1.5.0 条目（B1 全量：新技能/拆分/路由/契约；**不改历史条目**） | 终检清单结果记施工日志 |

## 4. 新文件设计

无新文件。

## 5. 验收命令

```bash
bash scripts/check-behavior-contracts.sh        # 14 条在位
python scripts/test-behavior-contracts.py       # 反向 fixture 过
bash scripts/static-check.sh && bash scripts/check-doc-budget.sh
bash scripts/check-shared-files.sh && bash scripts/check-story-numbers.sh
bash scripts/check-capability-wiring.sh && bash scripts/check-claude-adapter.sh
bash scripts/check-agent-template-rules.sh && bash scripts/check-eval-scenarios.sh
bash scripts/test-writing-pipeline.sh && python scripts/test-impact-scan.py
python scripts/test-next-step.py && python scripts/test-tracking-commit.py
grep -rn "workflow-setup" skills/ scripts/ docs/architecture.md README.md README_EN.md CONTRIBUTING.md   # 零命中
grep -n "moshu-build" skills/moshu/SKILL.md skills/moshu/scripts/next_step.py README.md README_EN.md    # 路由五方一致
```

## 6. 守卫与 CI

无新增守卫；既有矩阵全绿为硬门；CHANGELOG/版本轨按 v1.5.0 收口（VERSION/README"最近更新"/CHANGELOG 三轨 + marketplace metadata）。

## 7. 回滚点

单提交 revert；B1a/B1b 不受影响。

## 8. 禁止事项

1. 禁止契约 must_contain 措辞与实际文档文本不一致（先 grep 后填）。
2. 禁止 stale 消费扩展成自动修改细纲（处理权在作者——只提示复核）。
3. 禁止 CHANGELOG 触碰历史条目。
4. 禁止本子步顺手改 B1a/B1b 之外的任何机制。

## 9. 提交规范

```
feat(contracts): 批B1c 契约锁定与回流闭环——3 新契约（修订须影响分析/write不改既有设定/变更日志append-only）、stale 消费接入、卷复盘转向提示、v1.5.0 终检收口
```

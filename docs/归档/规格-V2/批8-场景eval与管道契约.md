# 规格 · 批 8：场景 eval 与管道契约测试

- 版本：v1.0（2026-08-20）
- **前置依赖**：批 6 已合入（工单结构是场景断言对象）。
- 依据：《执行总纲V2》§五批 8；DeterminFlow evals 行为断言+测试守护 evals 存在（01 档案 §7.3、§九 #12）；04 盘点空白 #9/#10。

## 1. 目标

一句话：端到端行为有可审计剧本（3 场景）、核心管道有零 LLM 契约级 e2e。

## 2. 现状事实（本次实测）

| # | 事实 | 证据 |
|---|---|---|
| F1 | evals 现状：客观侧仅 1 对样本（evals/samples/ 两文件）+ eval-prose-quality.sh；README 自认主观维度不评 | 盘点空白 #9 |
| F2 | e2e 仅 dashboard（tests/e2e/dashboard.spec.mjs）；写作/拆文/导入管道零端到端 | 盘点空白 #10 |
| F3 | 现有可串链脚本：tracking_commit.py（init/commit/check/volume-report）、review_tickets.py（write/resolve/list）、check-prose-candidates.js | 批 3/5/6 产物 |
| F4 | DeterminFlow 模式：evals.json 场景+行为断言（"不重跑 build""0012/0011"式），且有测试断言 evals 存在且非空 | 01 档案 §7.3 |

## 3. 文件级改动清单

| 文件 | 改什么 | 注意点 |
|---|---|---|
| `evals/scenarios/日更一章/README.md`（新，**必须**） | 步骤（日更流程一轮）→断言（tracking check 绿、续写状态卡 7 栏、信息差/悬置输出存在、候选机检跑过且未拦截、章文件非空） | 剧本=给真人带 agent 走查用；断言区分"机检项/人工项"两栏 |
| `evals/scenarios/开书/README.md`（新，**可裁**） | 剧本：前置（deploy+scan/analyze 可选）→步骤（/moshu-write 开书 Phase 1-3）→断言（`大纲/大纲.md`、`卷纲_第1卷.md`、`追踪/` 初始化） | 总纲 §4.3 弹性项；若裁，check-eval-scenarios 只校验保留项；next_step 断言已按批 4 跳过剔除（2026-08-20 作者决策） |
| `evals/scenarios/审查工单/README.md`（新，**可裁**） | 步骤（/moshu-review 一轮→工单落盘→/moshu-write 处置→复审）→断言（tickets JSON 过 review_tickets list、open→fixed 流转、令牌回传、review-log 未被破坏） | 总纲 §4.3 弹性项；若裁同上 |
| `scripts/check-eval-scenarios.sh`（新） | 静态校验（不跑 LLM）：3 个 README 存在且非空；各含"断言"节与 ≥3 条机检项标记（`[机检]` 前缀）；剧本内引用的脚本路径存在 | 移植"测试守护 evals 存在" |
| `scripts/test-writing-pipeline.sh`（新） | 零 LLM 管道契约 e2e，见 §4 | fixture 全在临时目录，自清理 |
| `evals/README.md` | 增"场景层"说明：三剧本定位/跑法（人工走查+脚本校验断言可机检项）/与客观样本层的关系 | 一节增量 |
| `scripts/README.md` / `CONTRIBUTING.md` / `.github/workflows/cross-platform.yml` | 两脚本索引+CI | 三处同步 |

## 4. 新文件设计

**test-writing-pipeline.sh**（算法级）：
1. 临时目录构造假书项目（`正文/`、`大纲/细纲_第001章.md`、`追踪/` 缺省）。
2. 依次执行并断言：
   - `tracking_commit.py init`（构造 init JSON，schema_version=2）→ 退出 0；
   - `tracking_commit.py commit`（一章事务：含 foreshadow_changes 1 条 + information_gap_changes 1 条）→ 退出 0，state schema_version=5；
   - `check` → 退出 0 且输出含 last_committed_chapter=1；
   - `volume-report --from-chapter 1 --to-chapter 1` → `追踪/卷报告_第1-1章.md` 存在且非空；重跑 diff 为空（确定性）；
   - `review_tickets.py write`（fixture findings JSON：blocking 1 条+candidate 1 条）→ 工单文件生成；`resolve --id T001 --status fixed` → 再 `list --status open` 只剩 candidate；
   - `check-prose-candidates.js --prose fixture正文.md` → 退出 0、blocking_count=0；
3. 全部通过退出 0；任一步失败打印步骤名与非零退出。
4. 结束清理临时目录（trap）。

## 5. 验收命令

```bash
bash scripts/check-eval-scenarios.sh        # 期望：3 场景校验 ok
bash scripts/test-writing-pipeline.sh       # 期望：全链 pass，退出 0
bash scripts/static-check.sh && bash scripts/check-doc-budget.sh
```

## 6. 守卫与 CI

两新脚本进 CI（三处同步）；test-writing-pipeline 是核心管道的长期回归（非临时验证）。

## 7. 回滚点

单提交 revert；全部新增文件，无既有文件结构变更（evals/README 只增节）。

## 8. 禁止事项

1. 禁止在 CI 里跑任何 LLM（场景剧本是人工走查物，CI 只做静态校验）。
2. 禁止把 test-writing-pipeline 做成 `.tmp` 临时验证（它是正式回归，守护管道契约）。
3. 禁止剧本断言写成模糊措辞（每条须可判"过/不过"）。
4. 禁止 fixture 留在工作区（临时目录+trap 清理）。
5. 禁止改 evals/samples 既有两样本与 eval-prose-quality.sh。

## 9. 提交规范

```
feat(evals): 批8 场景 eval 与管道契约——3 场景剧本（行为断言+机检标记）、check-eval-scenarios 静态校验、test-writing-pipeline 零 LLM 全链回归
```

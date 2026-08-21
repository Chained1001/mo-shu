# 规格 · 批 B1a：新建 moshu-build 技能（构建环诞生）

- 版本：v1.0（2026-08-21）
- **前置依赖**：基线 `8f049da`（v1.4.0 闭环后）。V2.1 协议沿用 `docs/规格-V2/README.md`；施工日志与审核记录沿用 `docs/规格-V2/` 两文件（状态总表追加 B1 行）。
- 依据：`docs/研究-v4/02-设计提案.md`（D1-D6 已确认）+ `03-落地核对.md`（九裁决 Q1-Q9 已落档）。

## 1. 目标

一句话：新建 moshu-build 技能（开书构建/修订工作流/开新卷三职责），**纯新增、write 零改动**，全部守卫保持绿。

## 2. 现状事实（R3 已核，抽验属实）

| # | 事实 | 证据 |
|---|---|---|
| F1 | workflow-setup.md（293 行）为构建/写作混合文件，本子步**只读不改**（其内容是 workflow-build.md 的改写底稿） | 解剖表 §1.1 |
| F2 | static-check 禁止跨 skill 引用（除 moshu-cdp）→ build 消费 references 只能走 shared-assets 副本 | static-check.py:62-65 |
| F3 | 36 组 source 均在 write；10 个双用文件无组（Q2 清单） | shared-assets.json 实测 |
| F4 | marketplace 10 插件，adapter 动态计数；README/README_EN Skills 表 10 行（D4 断言守卫） | C1/C4/C5 |
| F5 | doc-budget 判据"触发即全量加载"（审计-V3 G-3 口径）；构建会话符合 | Q5 裁决 |

## 3. 文件级改动清单

| 文件 | 改什么 | 注意点 |
|---|---|---|
| `skills/moshu-build/SKILL.md`（新） | frontmatter：name `moshu-build`、version `1.0.0`、description 含触发词（开书/建书/设定/世界观/大纲/卷纲/修订设定/开新卷）；正文：三职责概览、入口三分（开书→workflow-build / 修订→revision-workflow / 开新卷→workflow-build 开新卷节）、与 write 边界声明（细纲归 write；write 只做增量建档——Q7 口径）、追踪 init 职责声明（Q3） | 薄壳原则：流程细节全下沉 references |
| `skills/moshu-build/references/workflow-build.md`（新） | 从 workflow-setup **改写**（非逐字拷贝）：Phase 1（:11-62）+ Phase 2（:65-124）+ 卷级大纲段（:128-182）+ artifact 创建（:274-277，含 tracking init）+ architect 卷纲辅助段（:281-292 卷级部分）；头注标"源自 moshu-write/workflow-setup.md 拆分（B1a），细纲部分见 write 侧 outline-workflow.md（B1b 建）"；开新卷节（:6 语义扩写：消费 `卷复盘_第X卷.md` 下卷方向候选） | 引用的 references 用 build 侧相对路径（shared-assets 副本落地后生效）；本子步 write 的 workflow-setup 不删——双存至 B1b 切换 |
| `skills/moshu-build/references/revision-workflow.md`（新） | 修订工作流五步（设计提案 §3.2）：①impact_scan 影响分析（三清单，`last_committed_chapter` 分界——D2）②作者裁决（AskUserQuestion 三选：改/不改/缩小范围）③留痕落盘（修订 + `大纲/变更日志.md` 追加一行：日期/对象/变更/影响摘要——D6）④级联标记（受影响**未写细纲**文件头加 `<!-- stale: 设定修订 YYYY-MM-DD 对象 -->`——D3；正文与追踪不标不改）⑤红线三条提示级确认（主角核心人设/力量体系/核心主线——D4）；末节：回流入口（读 open 工单设定类条目 + 追踪连贯性风险，转为修订提案） | 变更日志 append-only 一句写死 |
| `skills/moshu-build/scripts/impact_scan.py`（新） | 见 §4 | build 专属，不进 shared-assets |
| `scripts/test-impact-scan.py`（新） | 回归（正反 fixture），头部守护对象声明 | CI 三处同步 |
| `scripts/shared-assets.json` | workflow-build/revision-workflow 实际引用的每个 reference：有组→targets 加 `skills/moshu-build/references/<名>`；无组（Q2 十文件）→建组（source=write 侧现路径）再加 target。预期清单（以施工后 grep 清点为准）：outline-methods、outline-structure-theory、outline-rhythm、outline-conflict、genre-catalog、genre-core-mechanics、genre-prose-cards、genre-readers、genre-writing-formulas、character-relations、emotional-arc-design、emotional-methods、reversal-toolkit、idea-seed、reader-contract-and-progression、beat-cards、naming-cards、style-genre-modules、artifact-protocols、female-audience-writing、plot-frameworks | **既有组 source 一律不动**（Q4）；改完 `python scripts/sync-shared-assets.py sync` 生成副本 |
| `.claude-plugin/marketplace.json` | +moshu-build 条目，version=1.0.0（须与 frontmatter 一致，adapter 校验） | |
| `README.md` / `README_EN.md` | Skills 表 +moshu-build 行（C5 守卫强制 11 行）；README:102 路由示例"帮我开书"→moshu-build（B1b 路由切换的先行一致性，本子步一并改避免表与示例矛盾） | |
| `docs/architecture.md` | 总览图 +Build 节点与"设定/大纲/卷纲"供给链 | |
| `scripts/capability-wiring.json` | 新能力：story-construction（producer=workflow-build.md）、setting-revision（producer=revision-workflow.md，consumer 含 impact_scan） | |
| `scripts/doc-budget.json` | 新增"构建路径"组：moshu-build/SKILL.md + workflow-build.md + revision-workflow.md，预算=完工实测×1.05 取整，_comment 记"Q5 裁决：开书高 token 会话触发即全量" | |
| `scripts/README.md` / `CONTRIBUTING.md` / `.github/workflows/cross-platform.yml` | test-impact-scan 三处同步 | |

## 4. 新文件设计

**impact_scan.py**（算法级，纯只读零 LLM）：
- `--project <书项目根> --keyword <关键词/实体名>`（必填，可多次 `--keyword`）。
- 读 `追踪/_tracking-state.json` 取 `last_committed_chapter`（记 L；缺失→错误码 2 明示"追踪未初始化，先 /moshu-build 开书"——读失败三分类）。
- 三清单：①`大纲/细纲_第*章.md` 解析章号 > L 的文件中 grep 关键词命中行（未写细纲清单）；②`正文/第*章*.md` 章号 ≤ L 中命中（已写正文清单）；③state 的 characters/foreshadow/timeline/information_gaps 四域 JSON 序列化文本中命中（追踪条目清单）。
- 输出单行 JSON：`{"keyword":..., "unwritten_outlines":[{file,line}], "written_chapters":[{file,line}], "tracking_hits":[{domain,key}], "boundary_chapter":L}`；退出 0（无命中=空数组，退出仍 0——分析工具非判定器）。
- 零写入；仅标准库。

**test-impact-scan.py**：fixture 项目（init 出 state，3 章 commit，5 份细纲）——①关键词命中未写细纲+已写正文+追踪三处；②干净关键词三清单全空；③无 state → 退出 2 且报文含"先 /moshu-build"。

## 5. 验收命令

```bash
python scripts/test-impact-scan.py            # 全 pass
bash scripts/static-check.sh                  # 新 skill 结构过（frontmatter/引用可达）
bash scripts/check-claude-adapter.sh          # 11 插件
bash scripts/check-story-numbers.sh           # ok (11 skills)
python scripts/sync-shared-assets.py check    # 副本一致
bash scripts/check-shared-files.sh
bash scripts/check-doc-budget.sh && bash scripts/check-capability-wiring.sh
bash scripts/check-behavior-contracts.sh && bash scripts/static-check.sh
node --check / python 语法门由 static-check 覆盖
```

## 6. 守卫与 CI

test-impact-scan 进 CI（三处同步）；既有守卫全绿为硬门。

## 7. 回滚点

纯新增提交，revert 即回到无 build 状态；shared-assets 加 target 可单独还原。

## 8. 禁止事项

1. 禁止改动 moshu-write 任何文件（含 workflow-setup——B1b 的活）。
2. 禁止动既有组 source（Q4：真源全留 write）。
3. 禁止 build 内出现指向其他 skill 的文件路径直引（只允许 shared-assets 副本的 skill 内相对引用）。
4. 禁止 workflow-build/revision-workflow 逐字拷贝时夹带细纲内容（细纲归 write，D1）。
5. 禁止 impact_scan 写任何文件或影响退出码语义以外的行为。

## 9. 提交规范

```
feat(build): 批B1a 新建 moshu-build——开书/修订/开新卷三职责（workflow-build+revision-workflow+impact_scan），shared-assets 副本接线，marketplace/路由表/守卫四联动
```

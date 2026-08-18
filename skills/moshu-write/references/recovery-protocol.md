# 失败恢复协议

流程中断是常态（工具失败、文件损坏、主产物缺失、模型输出异常），不是意外。本文件按失败类型给出统一判定与恢复路径；各 workflow 的失败处理处引用本文件对应节，不重复展开。

**总原则**：

1. **不拼装降级结果**：主产物缺失时显式修复（`missing_primary_contract` + `repair_action`），不得用摘要/投影文件假装已召回权威模块。
2. **不手改派生文件**：`追踪/` 下的派生视图（上下文.md、伏笔.md、时间线、角色状态、逐章记录）只能由 `tracking_commit.py` 生成；手改会破坏 `check` 一致性且无法自动恢复。
3. **失败必可重试**：同一事务 JSON 重跑 `commit` 是幂等的（append 只接受内容完全相同的既有逐章记录）；先修环境/数据，再重跑**同一份**操作，不另造新操作。
4. **分类先于动作**：先判失败类型（A/B/C/D），再走对应恢复分支；不盲目重跑整个流程。

---

## A 类：环境 / 工具失败

**特征**：脚本不可用（node 缺失、`tracking_commit.py` 无法运行、hook 损坏）、权限被拒、磁盘满、路径错误。

**恢复动作**：

| 子类型 | 判定 | 恢复 |
|---|---|---|
| node 缺失 / 核损坏 | `node -e ""` 失败；`story_hook_cli.js` 子命令抛错 | 守卫按 fail-open 放行并在 stderr 提示；修复部署后重试（`/moshu-setup` 重新部署 hooks） |
| 追踪工具不可用 / 权限 / 磁盘满 | `commit` 写入失败 | `_tracking-state.json` 未推进；保留原事务 JSON，修正写入环境后重跑同一 `commit` |
| 路径错误 | 脚本报路径不存在 | 先核对工作区/项目根，再重跑；不盲改脚本 |

**不做什么**：不因工具问题改写成别的手段（如绕过 `tracking_commit.py` 手写派生文件）；不删除 `_tracking-state.json` 重来。

---

## B 类：状态 / 文件失败

**特征**：`_tracking-state.json` 缺失/schema 不符、续写状态卡修订不一致、派生视图被手改、逐章记录被手写、角色状态文件缺失。

**恢复动作**：

| 子类型 | 判定 | 恢复 |
|---|---|---|
| 无正文、state 缺失 | `tracking_commit.py check` 报缺失 | 构造 `last_chapter=0` 的 init 事务执行 `init` |
| 已有正文、state 缺失 | `check` 报缺失 | 走 `/moshu-import` 的「旧追踪项目迁移」重建 `追踪/`（不重跑全书拆解；`init` 会把旧结构移入 `追踪/_旧追踪存档/`） |
| 派生视图被手改 | `check` 报 `derived view differs from _tracking-state.json` | 重新提交**该章**的 `mode=revision` 事务让工具整份重建；`expected_state_revision` 取 `追踪/_tracking-state.json` 的 `state_revision` 字段 |
| 逐章记录被手写 | 同章 `append` 报 `chapter delta N already exists with different content` | 删掉那个手写文件后重跑原事务 |
| 角色状态文件缺失 | `check` 报缺失/孤儿 | 先运行 `check`，再重跑产生该状态的完整事务；不得从前文临时推断后直接手写快照 |
| 伏笔/时间线文件缺失 | 视为当前语义检查点损坏 | 停止写正文；先 `check`，再用事务修复。卷纲/大纲中的计划不能代替已发生事实的当前检查点 |

**不做什么**：不手工补派生视图、不删 state 重来、不忽略返回码。

---

## C 类：主产物缺失

**特征**：对标权威文件缺失（`剧情/情绪模块.md`、`剧情/节奏.md`、文风），或本项目主产物缺失。

**恢复动作**：

| 子类型 | 判定 | 恢复 |
|---|---|---|
| `剧情/情绪模块.md` / `剧情/节奏.md` 缺失 | 写前准备/卷纲排节奏时按「对标书路径查找」两处皆缺 | 设置 `missing_primary_contract: true`，给出 `repair_action`：重跑 `/moshu-analyze` Stage 3+ 或重新 `/moshu-import`；停止写前准备/大纲排节奏 |
| 有对标书但 `文风.md` 缺失 | 文风召回时 | 有 `设定/文风.md`（含实质内容）走自定义文风模式继续；否则 fail-fast，提示先运行 `/moshu-analyze` Stage 1 停靠点生成表达层文风（或全量拆解后 Stage 6 补全）并 `/moshu-import` 同步。**完全无对标项目**则跳过文风召回、不阻塞 |
| `设定/题材正文提示卡.md` 缺失 | 写前召回 | 不阻塞；从 `设定/题材定位.md` 精确匹配 `genre-prose-cards.md` 索引生成，无命中用 `style-genre-modules.md` 兜底 |

**注意**：情绪/节奏轴（`missing_primary_contract`）独立于文风轴，自定义文风模式**不豁免**其 fail-fast；补的是 `剧情/情绪模块.md` / `剧情/节奏.md`，不是写 `设定/文风.md`。

---

## D 类：模型 / agent 失败

**特征**：agent 未部署或 spawn 失败、输出不完整、一致性检查报冲突、模型产出质量异常。

**恢复动作**：

| 子类型 | 判定 | 恢复 |
|---|---|---|
| 辅助 agent 不可用 | `.claude/agents/{name}.md` 不存在或 spawn 失败 | 由主线程直接执行对应职责（explorer→手动加载；researcher→主线程检索；consistency-checker→参照 quality-checklist 直接检查；narrative-writer→主线程按 anti-ai-writing/banned-words 执行；architect→主线程完成） |
| explorer 返回不完整 | `context_load` 结果缺项 | 回退到手动加载步骤（daily Step 1 手动清单） |
| 一致性检查 S1/S2 冲突 | 报告含 S1/S2 | 每条当场显式判定并落盘其一：①已修复（改正文/细纲后复核）；②进 `continuity_risks`（跨章风险，下章起持续核对）；③进 `next_chapter_commitments`（下一章必须修）。未判定的冲突不得进入下一章 |
| 模型产出质量异常 | 检测器 blocking 命中 / 字数不达标 / 退化 | 按对应流程修复：毒句式欠账先清再写下一章（写前 hook 拦截）；字数<90% 按情节点预算找欠账点（`outline_underfilled` 先补纲）；blocking 重写最多 2 次，仍失败报告证据让用户定夺 |

**不做什么**：不把"spawn 失败"误报为完成；不把"任务已启动"当成"任务已完成"。

---

## 分级查找（只读恢复）

状态摘要里没有、但本章确实需要的旧信息，按成本递增分级查找，**每一步的读取量都有上限**（详见 `workflow-daily.md`「旧信息查找步骤」）：续写状态卡（0）→ 定点 grep/小文件（当前行）→ explorer 子查询（相关条目）→ 逐章记录 grep 最近 5 条 → 单章正文（1 个紧凑增量）→ 全量读取（**日更禁止**，仅 `/moshu-review` 或用户明确要求时）。

---

## 引用关系

| 场景 | 引用位置 |
|---|---|
| 单章写作失败处理 | `workflow-chapter.md` 步骤 12「更新追踪」 |
| 日更批量失败处理 | `workflow-daily.md` 步骤 2 事务提交 5 条 + 批末校验 |
| 回炉大修失败处理 | `workflow-revision.md`「提交与重试」 |
| 追踪事务语义 | `tracking-transaction.md`（唯一提交点 / append 幂等 / 退役表述） |

# 规格 · 批 B30：评审 Agent + 多维采风触发 + 中段融合指引

- 版本：v1.0（2026-08-24）
- 前置依赖：B29 已合入。
- 依据：作者三轮设计讨论——①多维采风（任意创作维度、任意 Stage 中段触发）②合三为一的评审人（编辑+作者+读者→单一 agent）③评审→采风→融合→再评闭环。

---

## 一、现状事实（施工前复核）

1. `ls skills/moshu-setup/references/templates/agents/`——现有 7 个 agent（architect/character-designer/consistency-checker/explorer/narrative-writer/researcher/chapter-extractor），无评审 agent。
2. `grep -n "评审\|评审人\|evaluator" skills/moshu-build/references/workflow-build.md`——零命中（停靠屏无评审机制）。
3. `grep -n "创作瓶颈\|瓶颈信号" skills/moshu-build/references/workflow-build.md`——零命中（Stage 2-6 无中段采风触发指引）。
4. `grep -n "融合四步" skills/moshu-build/references/workflow-build.md`——融合四步只写在 Stage 1 采风段（全局语境），无分语境版本。
5. `grep "agents_version" scripts/current-contract.json`——当前 33。

## 二、设计总纲

### 三件产出 = 一个闭环

```
产出① 评审 Agent（moshu-evaluator）→ 评"好不好"
产出② 停靠屏集成（spawn + 报告展示 + 采风触发选项）→ 连接评审与采风
产出③ 多维采风触发（Stage 2-6 瓶颈信号 + 分语境融合指引）→ 让采风在任意创作点可用

形成闭环：创作 → 评审（发现弱点）→ 采风（定向补弱）→ 融合 → 再评 → 通过
```

---

## 三、产出①：moshu-evaluator Agent 模板

**新建** `skills/moshu-setup/references/templates/agents/moshu-evaluator.md`：

```markdown
---
name: moshu-evaluator
description: |
  创作质量评审员。接收构建产物（骨架/单元卡/角色弧线/整体卷纲），
  从编辑（商业/结构）、作者（技艺/新鲜度）、读者（留存/体验）三个维度评审，
  输出结构化 JSON 评审报告（具体发现+改进建议+优先级）。
  被 moshu-build 停靠屏调用。只评审不修改、不触发采风。
  Fallback：agent 不可用时由主会话 AI 自评四问（有自评偏差，标注 Fallback）。
tools: [Read, Glob, Grep]
disallowedTools: [Edit, Write, Bash, MultiEdit]
model: sonnet
maxTurns: 10
memory: project
---

# Story Evaluator — 创作质量评审员

你是创作质量评审员，负责从三个维度评审构建产物。你只评审不修改。
你没有参与创作过程——这是你的价值：不被创作语境污染的独立判断。

**审稿令牌**：spawn prompt 首行带 8 位令牌，你必须在报告首行逐字回传。

## 评审对象类型

| eval_type | 被评什么 | 典型来源 |
|---|---|---|
| outline | 全书骨架（八列表+势力场+暗线+底牌） | Stage 2 产物 |
| unit | 首卷单元卡（各单元桥段+节奏+支线） | Stage 4 产物 |
| character | 角色弧线页（弧线六阶段+关系+升级绑弧光） | Stage 3 产物 |
| final | 整体大纲+卷纲（定稿终审） | Stage 6 产物 |

## 评审准则（三维度×差异化问题）

### 编辑维度（商业/结构之眼）

- **硬伤检查**：指出 1 个逻辑漏洞/设定矛盾/节奏断裂，或声明"无"——
  必须主动搜索过才算，不接受"看起来没有问题"。
- **商业判断**：如果你是起点责编，这个产物的签约理由和拒签理由各 1 条。

### 作者维度（技艺/新鲜度之眼）

- **新鲜度检查**：核心桥段/结构在已出版作品里见过类似的吗？
  举 2 个例子（作品名+桥段名）。举不出来说明什么（太平淡 or 太新没验证）？
- **工艺检查**：如果是有经验的成功作者来写，会改哪一处？

### 读者维度（留存/体验之眼）

- **追读动力**：读者翻到下一单元/下一卷的动力是什么？一句话。
- **弃书点**：最可能关掉阅读的章位/位置？那里有什么钩子？够不够兜住？

### 综合判断

- **只改一处**：如果只改一处让品质提升最大，改什么？为什么？

## 评审纪律

- 每个维度必须给具体发现（指认位置/举例子），禁止泛泛评价（"挺好的""还可以"）。
- 评审对象是计划层产物（大纲/单元卡），不是正文——不要评文笔，评结构和设计。
- 你不做决策（通过/不通过归作者），只提供判断依据。
- 不建议直接触发采风（那是作者的选择），但可以在 improvement_priority 里建议。

## 输出格式

\```json
{
  "status": "success",
  "token_echo": "{token}",
  "eval_type": "unit",
  "editor": {
    "hard_flaw": "具体硬伤（指认位置）或 '无'",
    "commercial_pro": "签约理由 1 条",
    "commercial_con": "拒签理由 1 条"
  },
  "author": {
    "freshness": "新鲜度判断",
    "similar_examples": ["作品名·桥段名", "作品名·桥段名"],
    "craft_change": "如果是成功作者会改什么"
  },
  "reader": {
    "retention_hook": "追读动力一句话",
    "drop_point": "弃书点+原因",
    "hook_assessment": "钩子够不够"
  },
  "if_one_change": "只改一处改什么",
  "overall": "通过 | 需改进 | 需重构"
}
\```

## 被调用协议

skill 通过 Agent(subagent_type: "moshu-evaluator") 调用你。
你收到的 prompt 会包含：
- token: 审稿令牌（首行，必须逐字回传）
- eval_type: outline | unit | character | final
- target_path: 被评文件路径（绝对路径）
- benchmark_path: 设定/理想书评.md 路径（评审的北极星尺子）
- context: 触发原因和评审重点
- project_dir: 项目目录

先读被评文件和理想书评，再按三维度评审，最后输出 JSON。
```

**模板纪律自查**：
- 自包含（无跨 agent 引用）✓
- 只读工具（Read/Glob/Grep，禁 Write/Edit/Bash）✓
- 审稿令牌（同 consistency-checker 范式）✓
- JSON 输出（结构化）✓
- fallback 声明（description 内）✓

## 四、产出②：workflow-build 停靠屏集成

### 停靠 1/2/3 各加一个评审块（~15 行/处）

在每个停靠屏的 AskUserQuestion 之前追加：

```
（展示完内容后）

🔍 独立评审（spawn moshu-evaluator）：

spawn Agent(subagent_type: "moshu-evaluator", prompt: "
  token: {8位令牌}
  eval_type: {outline|unit|character|final}
  target_path: {产物文件路径}
  benchmark_path: 设定/理想书评.md
  context: 停靠N·{Stage名}产物评审
  project_dir: {项目目录}
")

→ 评审报告回来 → 附屏展示（三维度+if_one_change+overall）
→ 采纳前用 review_tickets.py verify-token 校验令牌

（然后进入 AskUserQuestion）

选项升级：
○ ✅ 确认进下一步
○ 🔧 按评审建议调整（AI 按报告改进）
○ 🔄 触发采风（评审弱项定向补弱——进入采风触发流程）
○ 📝 我自己改
```

### Fallback 路径

```
Agent 不可用 → AI 在停靠屏自评四问（简化版，标注 Fallback）：
  ① 编辑问："这个设计有什么商业硬伤？指出 1 个或声明'无'"
  ② 作者问："核心桥段见过类似的吗？举 2 个例子或说'新在哪'"
  ③ 读者问："弃书点在第几章？钩子兜住了吗？"
  ④ 改进问："只改一处改什么？"
  标注 "Fallback: evaluator unavailable -> self-evaluation"
```

## 五、产出③：多维采风触发 + 分语境融合

### Stage 2/3/4/5/6 各加创作瓶颈信号指引（~5 行/处）

在每个 Stage 的方法论指引块末尾追加：

```
> **创作瓶颈信号**（非强制，AI 遇到时自行判断）：
> - "这个桥段/结构写得太平了" → 可触发情节采风（CF 票据登记，检索类似桥段的爽点设计）
> - "这个角色行为说服力不够" → 可触发角色采风（检索类似角色弧线的处理手法）
> - "这个设定/规则想不出来" → 可触发机制采风（检索类似设定的规则设计）
> 触发后按融合四步在当前设计语境内执行（对照对象=当前正在设计的单元卡/角色页/骨架行）。
> 瓶颈采风产物回来 → 当前设计更新 → CF 标记已消费。
```

### 分语境融合指引（追加到融合四步附近，~12 行）

```
#### 融合四步的分语境执行（中段采风用）

Stage 1 全局采风 → 对照核心设定表 → 验证方法论（现有版本）
Stage 2 骨架采风 → 对照八列表+势力场 → 验证八节点/势力场设计
Stage 3 角色采风 → 对照角色弧线页 → 验证弧线六阶段/升级绑弧光
Stage 4 单元采风 → 对照当前单元卡 → 验证 BC-ID 节拍卡
Stage 5 整合采风 → 对照伏笔表/线索矩阵 → 验证伏笔四态
Stage 6 打磨采风 → 对照卷级五问 → 验证 LOCK 四查
```

## 六、agents_version bump

- 33→34（新增 evaluator agent 模板）
- UPGRADING.md 加 v33→v34 条目
- deploy.py DEFAULT_AGENTS_VERSION 33→34
- 9 文件字面量同步（用 bump 脚本 --confirm）
- deploy-manual.md agent 清单+版本更新
- current-contract.json agents_version 33→34

## 七、文件级改动清单

| # | 文件 | 改什么 |
|---|---|---|
| 1 | `skills/moshu-setup/references/templates/agents/moshu-evaluator.md` | **新建**评审 agent 模板 |
| 2 | `skills/moshu-build/references/workflow-build.md` | 停靠 1/2/3 各加评审块（spawn+展示+选项升级+fallback） |
| 3 | 同上 | Stage 2/3/4/5/6 各加创作瓶颈信号指引 |
| 4 | 同上 | 融合四步附近加分语境执行表 |
| 5 | `skills/moshu-setup/UPGRADING.md` | v33→v34 条目 |
| 6 | `skills/moshu-setup/SKILL.md` | agents_version 字面量 33→34 |
| 7 | `skills/moshu-setup/references/deploy-manual.md` | agent 清单 7→8+版本更新 |
| 8 | `skills/moshu-setup/scripts/deploy.py` | DEFAULT_AGENTS_VERSION 33→34 |
| 9 | `scripts/current-contract.json` | agents_version 33→34 |
| 10 | 其余 agents_version 字面量文件 | 用 bump 脚本 --confirm |
| 11 | `docs/施工日志.md` | B30 条目 |
| 12 | `docs/规格/批B30-*.md` | 规格随批 |

## 八、禁止事项

1. evaluator agent **只读**——禁 Write/Edit/Bash（纯评审零副作用）
2. 评审报告 **不落盘为文件**——附屏呈现即弃（评审是即时参考，不是持久产物；如需留档由作者手动要求）
3. 评审 **不阻断**——报告附屏后仍由作者选择（评审 overall="需重构"也不能阻止作者选"确认"）
4. 创作瓶颈信号是 **指引非强制**——AI 自行判断，不设机检断言（评审质量无法确定性校验）
5. 分语境融合 **不新建脚本**——AI 语义操作（融合四步已有，只是对照对象不同）
6. agents_version bump **必须用 bump 脚本** --confirm
7. evaluator 模板 **自包含**——禁互引其他 agent（check-agent-template-rules 会查）

## 九、验收命令

```bash
# 产出①：agent 模板
ls skills/moshu-setup/references/templates/agents/moshu-evaluator.md
grep -c "token_echo\|三维度\|eval_type" skills/moshu-setup/references/templates/agents/moshu-evaluator.md  # ≥3
grep -c "disallowedTools.*Edit.*Write.*Bash" skills/moshu-setup/references/templates/agents/moshu-evaluator.md  # 1
# 产出②：停靠屏集成
grep -c "moshu-evaluator" skills/moshu-build/references/workflow-build.md  # ≥3（三停靠各1）
grep -c "触发采风.*评审\|评审.*采风" skills/moshu-build/references/workflow-build.md  # ≥1（联动选项）
grep -c "Fallback.*evaluator\|evaluator.*Fallback" skills/moshu-build/references/workflow-build.md  # ≥1
# 产出③：瓶颈信号+分语境
grep -c "创作瓶颈信号" skills/moshu-build/references/workflow-build.md  # ≥5（Stage 2-6 各1）
grep -c "分语境\|对照当前单元卡\|对照角色弧线页" skills/moshu-build/references/workflow-build.md  # ≥2
# agents_version
python scripts/bump-agents-version.py 34  # dry-run 预览（当前33→34）
python scripts/check-agents-version-sync.py  # 全一致 34
bash scripts/check-agent-template-rules.sh  # 新模板过禁互引
# 全量
bash scripts/static-check.sh && bash scripts/check-doc-budget.sh && bash scripts/check-shared-files.sh && python scripts/check-reference-closure.py
```

## 十、提交规范

`feat(moshu-build): 评审 Agent + 多维采风触发 + 中段融合指引——新建 moshu-evaluator（三维度评审·只读·审稿令牌·JSON）、停靠屏集成（spawn+报告+采风触发选项+fallback 自评）、Stage 2-6 创作瓶颈信号+分语境融合表、agents_version 33→34；形成创作→评审→采风→融合→再评闭环（作者三轮设计讨论；B30）`

# 规格 · 批 B74：spawn 契约单一真源（注册表+守卫——调用参数从人肉对齐变机检对齐）

- 版本：v1.0（2026-08-28，旗舰起草；来源：B72 审计 §7.3 架构师视角「只改一处」+D2 参数遗漏事故——作者裁定立项）
- **目的**：解决「8 个 agent 的调用参数散在十几个流程文件里手写，每加参数就有十几处要同步」——从结构性缺陷变注册表+守卫收口，防再漏。**这是工程收口不是行为变更**——所有 agent 的实际调用行为零变化。
- 性质：新建注册表+守卫（零 schema/零 agent 模板变更）。单批单提交。

## 一、设计依据

| 项 | 现状（实证） | 缺口 |
|---|---|---|
| spawn 参数定义 | 各 agent 模板「被调用协议」节列出预期参数——但仅是文档描述，无数性约束 | 8 模板/8 份协议，无注册表 |
| spawn 调用点 | 散布在 moshu/SKILL/analyze-workflow/cold-path/workflow-build/deslop-workflow/import-workflow/chapter-core 等十几个文件，每处手写 prompt 含参数 | 已漏过 D2 两状态值——人肉对齐不可持续 |
| 守卫 | capability-wiring 管「确定性脚本能力接线」，不管 agent spawn 参数 | 无 spawn 参数守卫 |

## 二、文件级改动清单

### 改动 1：新建 `scripts/spawn-contracts.json`（注册表）

每个 agent 一条注册（8 条），结构仿 capability-wiring：

```json
{
  "agents": [
    {
      "name": "moshu-narrative-writer",
      "required_params": ["项目目录", "章节", "细纲文件", "输出路径"],
      "optional_params": ["上一章", "场景类型", "语声锚", "称谓行", "文风锚点", "genre_prose_card", "selected_emotion_module", "rhythm_reference", "写法参照", "重点情节点标签", "禁止提前释放", "字数目标", "情节点预算"],
      "callers": [
        {"file": "skills/moshu-write/references/chapter-core.md", "must_contain": "moshu-narrative-writer", "context": "正文写作"},
        {"file": "skills/moshu-deslop/references/deslop-workflow.md", "must_contain": "moshu-narrative-writer", "context": "去AI味"}
      ]
    },
    ...
  ]
}
```

8 个 agent 全部登记（narrative-writer/architect/character-designer/consistency-checker/evaluator/explorer/chapter-extractor/researcher）。

### 改动 2：新建 `scripts/check-spawn-contracts.sh`（守卫）

三查（能力接线同构）：
1. **注册面完备**：8 个 agent 模板文件全部有注册条目；
2. **调用面覆盖**：每个 caller 文件存在且含 `must_contain` 锚文本；
3. **必需参数覆盖**：每个 caller 文件的 spawn 上下文段（锚文本 ±30 行）含全部 `required_params` 字样——缺失即红（阻断语义：参数缺失=调用会失败）。

### 改动 3：§2.5 四处同步

scripts/README.md 守卫表 + cross-platform.yml static-guards 步 + CONTRIBUTING.md + CI 三处。

### 改动 4：D2 事故锚定

在注册表 narrative-writer 条目的 optional_params 中加入 D2 事故涉及的两个状态值名（flash 复核实际名称），注释标「D2 参数遗漏事故锚定——本守卫防再漏」。

## 三、验收

1. 注册表 8 agent 全齐，grep 每个 agent 名恰 1 条注册。
2. check-spawn-contracts.sh 三查全绿；构造违规 fixture（删一个 caller 的 required_param 字样）→ 红。
3. 四处同步 grep 全命中。
4. 守卫矩阵全绿。

## 四、禁止事项

**不改任何 agent 模板**（「被调用协议」节保留——它是文档面，注册表是机检面，两者互补不替代）；**不改任何调用点的实际 prompt 文本**（本批只建守卫不动行为——如有参数缺失处，后续行为批修复）；零 schema/零 agents_version bump。

## 五、提交规范

`feat(守卫): B74 spawn 契约单一真源——spawn-contracts.json 注册表（8 agent×required/optional×callers）+ check-spawn-contracts.sh 三查守卫（注册完备/调用覆盖/必需参数覆盖）+ D2 事故锚定 + 四处同步——调用参数从人肉对齐变机检对齐`

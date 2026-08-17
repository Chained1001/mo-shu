---
name: moshu-import
version: 1.0.2
description: "逆向导入已有小说。将已写好的小说（半成品或完本）反向解析为标准项目目录结构，兼容 moshu-write 后续写作流程；内部复用 moshu-analyze 的拆解管道。触发方式：/moshu-import、「导入小说」「导入书籍」「反向解析」「把我的书导进来」。"
---
# moshu-import：逆向导入已有小说

你是小说项目逆向工程师。只处理长篇导入。

**交付物是写作工程**：把作者已有的书重建为可续写的**写作工程**（项目结构 + 拆文库分析资产）。`拆文库/{导入书名}/` 是重建工程的数据源，不能当成用完即弃的中间产物，也不能替代交付物本身——交付物应让作者能直接续写。执行时以「建工程」为可见目标，别把「拆文」当成终点或对外标签。

---

> Agent 兼容性：检查专业 agent 是否可用时，检查 `.claude/agents/{agent}.md`；不存在或运行时不暴露 custom agent registry 时必须降级为 solo/direct，报告 `Fallback: project custom agents unavailable -> solo`。Claude Code 兼容面保留 `subagent_type`。
>
> Spawn 版本提示（不阻断 spawn）：先读取项目根 `.story-deployed` 的 `agents_version`。与本版 `agents_version: 26` 不一致时（标记缺失、字段缺失/非整数、小于或大于 26）**照常按文件存在性检查并 spawn**，同时报告 `Notice: agents bundle 版本不匹配（项目 {N}，本版 26）` 并提示重新运行 `/moshu-setup` 后新开会话；大于 26 时额外提示先更新 mo-shu，不要用本地旧版 setup 降级覆盖。只有 agent 文件缺失、或运行时不暴露 custom agent 时才降级 solo/direct，报告 `Fallback: ... -> solo`。

## 核心原则

### 名词与目录边界（全流程硬约束）

- `{导入书名}`：用户自己已经写到一半或已经完本、现在要重建为工程的小说；它的分析源固定为 `拆文库/{导入书名}/`。
- `{对标书名}`：用户另行选择的外部参考作品；它必须是独立拆解产物，来源固定为 `拆文库/{对标书名}/`，且不得指向本次导入源。
- `moshu-import` 可以复用拆解管道分析 `{导入书名}`，但**不得把 `{导入书名}` 登记为主/副对标，不得把 `拆文库/{导入书名}/` 或项目 `设定/` 复制进 `对标/`**。

### 原则 1：先分析后迁移

先用拆解管道完整拆解小说（输出到 `拆文库/{导入书名}/`），再将分析结果迁移为项目结构。该目录保存本书导入分析，保留不丢弃，但不属于外部对标视图。

### 原则 2：复用不重复

拆解能力复用 moshu-analyze 的完整管道，不在 moshu-import 内另写一套等价拆解逻辑；迁移时以 `拆文库/{导入书名}/` 的产物为唯一数据源，引用而不复制，不重复生成分析文件。



---

## Phase 1：确认导入源

**执行前先读 [references/import-workflow.md](references/import-workflow.md) 的「Phase 1」节**，按其中 Step 1-6 执行（导入续写入口顺序、旧追踪项目迁移、意图确认、输入识别、基本信息、环境检测、原文备份）。

## Phase 2：深度分析

**执行前先读 [references/import-workflow.md](references/import-workflow.md) 的「Phase 2」节**——驱动 moshu-analyze 完整拆解管道（Stage 0-6），调用契约、拆文库结构、恢复机制与质量检查见同节。

## Phase 3：结构迁移

**执行前先读 [references/import-workflow.md](references/import-workflow.md) 的「Phase 3」「Phase 3-L」节**——长篇统一走 3-L 迁移，完整步骤（骨架/正文标准化/角色/关系/设定/大纲/细纲/追踪初始化/题材定位/对标同步/文风）见同节与 `references/structure-mapping-long.md`。

## Phase 4：项目激活

**执行前先读 [references/import-workflow.md](references/import-workflow.md) 的「Phase 4」节**——质量检查、完成报告模板与项目激活见同节。

## 大型作品处理（>200 章）

**处理规则见 [references/import-workflow.md](references/import-workflow.md) 的「大型作品处理」节**——拆解可分批、追踪初始化必须一次覆盖全部已写章节。

## 参考资料索引

**按阶段加载表见 [references/import-workflow.md](references/import-workflow.md) 的「参考资料索引」节**；本 skill 自带 references 按场景加载，涉及别的 skill 的方法论时运行对应 /命令由该 skill 自行加载。

---

## 流程衔接

**流水线：** 长篇
**位置：** 导入（在开书之前）

| 时机 | 跳转到 | 命令 |
|---|---|---|
| 导入完想继续写（长篇） | moshu-write | `/moshu-write` + "日更" |
| 导入完想审查质量 | moshu-review | `/moshu-review` |
| 想深入分析对标（长篇） | moshu-analyze | `/moshu-analyze` |
| 从零开新书（长篇） | moshu-write | `/moshu-write` + "开书" |
| 项目未部署环境 | moshu-setup | `/moshu-setup` |

---

## 语言

- 跟随用户的语言回复，用户用什么语言就用什么语言回复
- 中文回复遵循《中文文案排版指北》
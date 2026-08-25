[English](README_EN.md) | **中文**

# mo-shu

长篇网文写作 skill 包，覆盖扫榜、拆文、写作、审查、导入、文风、去AI味的全流程。内置适配 Claude Code。

## 核心思路

> **套路 = 确定性的情绪满足**

专业作者的方法论三步走：

1. **扫榜**：分析热门榜单，洞察题材、人设、切入点。
2. **拆文**：拆解大纲节奏与剧情素材，建立个人模块库。
3. **商业化写作**：学习并运用钩子、爽感、期待感等核心技巧。

围绕四条线展开：爆款逆向 · 剧情模块化重组 · 上下文状态分层管理 · 人机协同。

> **最近更新（v2.4.0）**：**创作-评审-采风闭环**——评审 Agent（moshu-evaluator，三维度只读·停靠屏例行）+ 多维采风触发（Stage 2-6 创作瓶颈信号+分语境融合）+ 方法论苏格拉底化（设计问句替代清单·填空式模板）+ Stage 命名标准化 + 机检格式容错 + 冷热分离性能优化 + **全仓审计修复闭环（B31-B45）**——版本散射闭合、共享资产全量对账守卫化、契约层单一真源（部署清单/产物字段/流程锚点）、write 三工作流 lane 标识、审计守卫化闭环（审计法 v1.7 + 开发标准 v1.3）+ agents_version 34（8 agent）。**v2.2-2.3 主体**：构建管线五层（骨架八列/势力场/暗线层次/舞台演进/支线配角高光）+ 三书逆向萃取 + 大纲机检 + 采风技能 agent 化 + 17 批迭代。更早版本变更见 [CHANGELOG.md](CHANGELOG.md)。

## 流程总览

```mermaid
flowchart LR
    classDef entry fill:#f0f0f0,color:#333,stroke:#999,stroke-width:1px
    classDef phase fill:#e8f4fd,color:#1a1a2e,stroke:#4a9be8,stroke-width:1px
    classDef final fill:#fce4ec,color:#333,stroke:#e57373,stroke-width:1px

    entry_l{{"长篇作者"}}:::entry
    entry_r{{"已有方向"}}:::entry
    entry_i{{"已有小说"}}:::entry

    subgraph S0 ["  环境部署"]
        setup["/moshu-setup"]:::phase
    end

    subgraph S1 ["  扫榜选材"]
        direction TB
        scan_l["长篇扫榜"]:::phase
    end

    subgraph S2 ["  拆文学习"]
        direction TB
        analyze_l["长篇拆文"]:::phase
        import_l["已有小说导入"]:::phase
    end

    subgraph S3 ["  落笔创作"]
        direction TB
        write_l["长篇写作"]:::phase
    end

    subgraph S4 ["  精修定稿"]
        deslop["去 AI 味"]:::final
    end

    entry_l --> setup
    setup --> scan_l
    scan_l --> analyze_l
    analyze_l --> write_l
    entry_r -.->|跳过准备| write_l
    entry_i -.->|推荐先部署| setup
    setup -.->|逆向导入| import_l
    import_l -.->|续写| write_l
    write_l --> deslop
```

> 完整架构与项目全书见 [产品需求与详细设计文档（PRD+FSD）](docs/mo-shu项目-产品需求与详细设计文档（PRD+FSD）.md)（理念与概念词典/全流程走查/全仓清单，单文件）。

## 安装（三步走）

```bash
npx skills add Chained1001/mo-shu -y -g
```

### 安装后必做（新用户看这里）

| 步骤 | 做什么 | 为什么 |
|---|---|---|
| **① 新开窗口** | 安装完成后，**关闭当前 Claude Code 窗口，在写作目录新开一个** | Skills 在会话启动时加载——安装会话里 `/moshu-build` 等命令不可用 |
| **② 部署环境** | 新窗口里运行 `/moshu-setup` | 部署 hooks、agents、rules、CLAUDE.md 到你的写作项目 |
| **③ 再开窗口** | setup 完成后再新开一个窗口，开始 `/moshu-build` 构建 | agents 在会话启动时注册，setup 会话里不可用 |

> 💡 快速记忆：**装完→开窗→setup→再开窗→build**

升级后若项目已跑过 `/moshu-setup`，建议重跑一次同步 hooks/agents/references。每版变更见 [CHANGELOG.md](CHANGELOG.md) 与 [Releases](https://github.com/Chained1001/mo-shu/releases)。

**多 agent 协作要先部署再新开会话：** 8 个专业 agent（moshu-architect、moshu-narrative-writer、moshu-consistency-checker 等）由 `/moshu-setup` 写入项目 `.claude/agents/`。Claude Code 在会话启动时更稳定地注册 custom agent。判断是否生效：新会话里跑 `/moshu-review`，报告头是 `Effective Mode: full/lean` 即注册成功，是 `Fallback: ... -> solo` 说明当前运行时未暴露该 agent。

**导入续写顺序：** 推荐先在写作项目根运行 `/moshu-setup`（部署 hooks/agents），新开/刷新会话后运行 `/moshu-import` 导入已有小说，再用 `/moshu-write 日更` 或 `/moshu-write 写第N章` 续写。也可以直接运行 `/moshu-import`；它会先检测是否已 setup，未部署时让你选择先去 setup 或继续串行导入。

## Skills

| Skill | 触发 | 说明 |
|:------|:-----|:-----|
| `moshu-setup` | `/moshu-setup` 「部署墨枢写作环境」 | 环境部署 · Claude Code（已有配置安全合并） |
| `moshu` | `/moshu` `/moshu dashboard` | 工具箱路由 · 模糊意图分发 + 本地拆文/项目 Dashboard |
| `moshu-write` | `/moshu-write` `/写长篇` | 长篇写作 · 细纲与正文输出、日更续写、大修、卷复盘执行 |
| `moshu-build` | `/moshu-build` `/建书` | 开书构建 · Stage 1-6 六步流程（理想书评→骨架八列→人物弧线→单元卡→整合→定稿）、三维度评审、内嵌采风（Stage 1 默认 + 瓶颈触发）、设定修订、开新卷 |
| `moshu-analyze` | `/moshu-analyze` | 长篇拆文 · 黄金三章、爽点设计、节奏分析 |
| `moshu-scan` | `/moshu-scan` | 长篇扫榜 · 起点/番茄/晋江市场趋势 |
| `moshu-deslop` | `/moshu-deslop` `/去AI味` | 去AI味 · 检测并清除 AI 写作痕迹 |
| `moshu-style` | `/moshu-style` `/学文风` | 文风学习 · 从任意量原文提取写作风格基准（句长/标点/对话技法/锚点），产出 `文风库/文风.md` |
| `moshu-import` | `/moshu-import` `/导入小说` | 逆向导入 · 将已有小说反向解析为标准项目结构 |
| `moshu-review` | `/moshu-review` `/审查` | 多视角审查 · 4 Agent 多视角审稿 + 番茄/起点评分标准 |
| `moshu-cdp` | `/moshu-cdp` | 浏览器操控 · CDP 协议复用登录态抓取数据 |

> `moshu-deslop` 的本地检查是写作 lint：blocking 只限确定性句式/标点问题，其他提示按读感判断；朱雀等外部检测只作自测参考，不替代人工读感。

自然语言同样触发：
- 「帮我开书」→ `moshu-build`（细纲与正文 → `moshu-write`）
- 「这篇太 AI 了」→ `moshu-deslop`
- 「把我的书导进来」→ `moshu-import`
- 「打开工作台」→ `moshu dashboard`（本机浏览拆文库与写作项目，可轻量编辑）
- 「沈栀现在什么状态」→ 自动 spawn `moshu-explorer` agent

### Story Dashboard

运行 `/moshu dashboard` 打开本地写作工作台，浏览拆文库与
长篇项目文件树，并完成搜索、Markdown 预览、文本编辑、冲突保护保存和确认删除。
服务仅监听 `127.0.0.1`，小说内容不会上传。

## Agent 体系

写作 skill 内部通过 8 个专业 Agent 协作，各司其职：

| Agent | 模型 | 职责 |
|:------|:-----|:-----|
| **moshu-architect** | Opus | 故事架构 · 题材定位、大纲结构、钩子/反转设计、情绪弧线 |
| **moshu-character-designer** | Sonnet | 角色设计 · 角色档案、语言风格、动机链、对话创作 |
| **moshu-narrative-writer** | Sonnet | 叙事写手 · 正文写作、去AI味、格式合规 |
| **moshu-consistency-checker** | Haiku | 一致性检查 · 事实冲突扫描、伏笔追踪、S1-S4 分级报告 |
| **moshu-researcher** | Sonnet | 资料研究 · CDP 搜索+正文提取、多源交叉验证、结构化参考文件输出 |
| **moshu-explorer** | Haiku | 故事查询 · 角色/伏笔/设定/进度只读查询，日更上下文快速加载 |
| **moshu-chapter-extractor** | Haiku | 章节提取 · 摘要+情节点+角色提及，并行拆文核心单元 |
| **moshu-evaluator** | Sonnet | 创作评审 · 三维度（编辑/作者/读者）只读评审构建产物，停靠屏例行调用 |

Agent 按需加载 `references/` 中的写作理论（角色设计、对话技法、反转工具箱等），部署包 agent-references 含全套方法论文件（数量随版本增长），全仓 references 数百份，不预占上下文。

## 自动化 Hooks

`/moshu-setup` 为 Claude Code 部署 8 个自动化 hook：

| Hook | 触发时机 | 功能 |
|:-----|:---------|:-----|
| session-start.sh | 会话开始 | 显示分支、进度快照、拆文状态 |
| session-end.sh | 会话结束 | 记录会话日志到 `追踪/session-log.txt`（默认关闭，`STORY_SESSION_LOG=1` 启用） |
| detect-story-gaps.sh | 会话开始 | 检测六项写作缺口：正文-设定失衡/伏笔异常/大纲缺失/拆文未完成/连续性 staleness/标题去重 |
| pre-compact.sh | 上下文压缩前 | 保存进度快照路径和行数摘要 |
| post-compact.sh | 上下文压缩后 | 提示读取进度快照恢复上下文 |
| validate-story-commit.sh | git commit 时 | 检查硬编码属性、设定必填字段（仅警告，不阻断） |
| guard-outline-before-prose.sh | 写正文前（Write/Edit） | 缺对应细纲时阻止首次创建正文（阻断），强制先搭大纲 |
| check-prose-after-write.sh | 正文写入后（Write/Edit） | 轻量扫描截断、工程词、毒句式和字数欠账（提醒，不阻断） |

## 项目文件结构

一部长篇动辄几十万字、几百章。设定冲突、伏笔断线、时间线对不上——写到最后全靠记忆硬撑，迟早翻车。

用文件系统把设定、大纲、正文、追踪拆开，每个维度独立维护。对话只负责创作，不负责记忆。

**长篇：**

```
{书名}/
├── 设定/
│   ├── 世界观/          # 背景、力量体系等，按主题拆文件
│   ├── 角色/            # 每个人物一个文件（江晨.md、钟嘉嘉.md）
│   ├── 势力/            # 每个势力/组织一个文件（火箭军文工团.md）
│   ├── 关系.md          # 角色关系映射
│   ├── 题材定位.md      # 题材核心梗+对标分析+终局底牌
│   ├── 理想书评.md      # 全书北极星尺子（Stage 1 产出）
│   ├── 题材正文提示卡.md  # 题材边界/爽点/禁止漂移
│   ├── 构建台账.md      # 六步状态/构建态/待定项/浮现记录
│   ├── 角色弧线.md      # 六弧线六阶段+情绪引擎+低压侧
│   └── 采风-CF*.md      # 采风产物（五类七源·CF 票据制）
├── 大纲/
│   ├── 大纲.md          # 全书骨架（八列表+势力场+暗线+常驻压力+升级台阶）
│   ├── 角色弧线.md      # 角色弧线（Stage 3 产物，同设定/角色弧线.md）
│   ├── 单元卡.md        # 首卷剧情单元（BC-ID 章功能+支线登记+配角高光）
│   ├── 整合记录.md      # 伏笔四态+反转+线索矩阵+动机链+Stage 6 打磨记录
│   ├── 变更日志.md      # append-only 变更记录
│   ├── 卷纲_第一卷.md   # 每卷一个：定稿 v1.0
│   ├── 细纲_第001章.md  # 每章一个：内容概括+多线情节+人物关系/出场顺序+钩子
│   └── ...
├── 正文/
│   ├── 第001章_章名.md
│   └── ...
├── 对标/                # 对标参考（结构化子目录从拆文库同步）
│   └── {对标书名}/
│       ├── 原文/            # 对标书原文章节
│       ├── 角色/            # 结构化角色卡（从 analyze 输出同步）
│       ├── 剧情/            # 结构化剧情线/节奏/情绪模块（从 analyze 输出同步）
│       ├── 设定/            # 结构化设定（从 analyze 输出同步）
│       ├── 技法总结.md      # 拆书 Stage 2-7 产出（情绪交替/可借鉴技巧/分层建议）
│       └── 拆文报告.md      # analyze skill 输出的拆文报告
├── 文风库/                # 文风（/moshu-style 生成；每章写作前文风召回）
│   └── 文风.md            # 句长/标点/对话技法/锚点（任意量原文可学）
├── 追踪/                # 文件优先的连续性状态
│   ├── _tracking-state.json # 唯一结构化权威状态（不进正文 prompt）
│   ├── 上下文.md        # 派生续写状态卡（固定 7 栏，≤12KB）
│   ├── 逐章记录/        # 每章未来相关连续性记录/修订覆盖层（≤3072 bytes）
│   ├── 角色状态/        # 派生核心角色快照（江晨.md、钟嘉嘉.md）
│   ├── 伏笔.md          # 派生伏笔当前视图
│   └── 时间线/          # 派生作者真相.md + 读者已知.md
├── 参考资料/            # moshu-researcher 输出的研究资料
│   └── {topic}.md       # 按研究主题拆分
```

**拆文库：** 拆文 skill 默认输出到项目根目录 `拆文库/{书名}/`，产出结构化目录（角色/剧情/设定/章节），其中长篇剧情目录包含 `节奏.md` 和 `情绪模块.md`，是 analyze 的源数据（source of truth）。写作 skill 通过 `对标/{书名}/剧情/` 等子目录消费这些资产（项目级引用视图），或自动回退读取 `拆文库/`。

**`.active-book`：** 项目根目录的文本文件，内容是当前活跃书目的**相对路径**（如 `长篇/我的小说`），hook 和写作 skill 据此定位当前项目。

## 知识体系

各 skill 自带 `references/` 知识库，按需加载，不占上下文。

<details>
<summary>展开各 skill 知识库主题清单</summary>

| 主题 | 内容 | 所在 skill |
|:-----|:-----|:-----------|
| 大纲排布 | 五步大纲法 · 故事结构分级 · 节点设计法 · 升级感设计 | moshu-write |
| 开头设计 | 开篇模式 · 前 500 字设计 · 黄金三章开头策略 | moshu-write |
| 人物设计 | 角色设定 · 人物提取 · 关系映射 · 动机链 · 群像 | moshu-write |
| 钩子技法 | 章尾钩子 14 式 · 章首钩子 7 式 · 段落级钩子 · 悬念编排 | moshu-write |
| 情绪设计 | 6 种弧形模板 · 期待感管理 · 题材赛道策略 | moshu-write |
| 题材框架 | 长篇八节点 · 8 大题材开头模板 | moshu-write |
| 对话技法 | 节奏 · 潜台词 · 信息控制 · 对话模式数据库 | moshu-write |
| 反转工具箱 | 类型 · 时机 · 误导底层路径 | moshu-write |
| 风格模块 | 对话 · 打斗 · 智斗 · 镜头式写作 · 装逼打脸 · 白描 | moshu-write |
| 高级技法 | 小纲四步法 · 高潮逆推 · 双线结构 · AB 交织法 | moshu-write |
| 去AI味 | 预防 · 三遍去AI法 · 改写范例库 · 禁用词表 | deslop / moshu-write |
| 质量检查 | 通用 · 长篇专项 · 毒点排查 | moshu-write |
| 拆文方法 | 黄金三章 · 情绪曲线 · 结构拆解 | moshu-analyze |
| 读者画像 | 9 维画像 · 目标读者分析 | moshu-scan |
| 市场数据 | 题材趋势 · 平台特性 · 采集格式 · 投稿指南 | moshu-scan |
| 多视角审稿 | 多视角审稿 · 评分标准 · 毒点排查 | moshu-review |

</details>

## 适用平台

**长篇** 起点中文网 · 番茄小说 · 晋江文学城 · 七猫小说 · 刺猬猫

## 致谢

- 本项目基于 [worldwonderer/oh-story-claudecode](https://github.com/worldwonderer/oh-story-claudecode)（MIT License）二次开发，感谢原作者。
- [LINUX DO - The New Ideal Community](https://linux.do) — 社区支持
- [FanqieRankTracker](https://github.com/wen1701/FanqieRankTracker) — 番茄小说字体反爬解码方案参考
- [Zhuque AIGC Detector CLI](https://github.com/Sophomoresty/zhuque) — 去 AI 味实验中的外部复测工具参考

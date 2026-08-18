# mo-shu 架构图

> 本文件用 Mermaid 描述 mo-shu 的整体架构、写作流水线与“下一步”状态机。
> 在 GitHub / Claude Code 中可直接渲染；也可用支持 Mermaid 的编辑器查看。

## 1. 总览：用户入口 → Skill → 脚本/Agent → 文件系统

```mermaid
flowchart LR
    U[作者 / 用户] --> R{moshu 路由}

    R -->|扫榜 / 选题| Scan[moshu-scan]
    R -->|拆文| Analyze[moshu-analyze]
    R -->|写作| Write[moshu-write]
    R -->|导入| Import[moshu-import]
    R -->|去 AI 味| Deslop[moshu-deslop]
    R -->|审查| Review[moshu-review]
    R -->|环境部署| Setup[moshu-setup]
    R -->|浏览器 CDP| CDP[moshu-cdp]
    R -->|本地工作台| Dash[Dashboard]

    Setup -->|部署到项目| Hooks[Hooks 自动化]
    Setup -->|部署到项目| Agents[7 个专业 Agent]
    Setup -->|部署到项目| Rules[Rules]
    Setup -->|部署到项目| Claude[CLAUDE.md]

    Analyze -->|产出| Library[拆文库]
    Library --> Write
    Import -->|复用拆解管道| Library
    Import -->|重建| Project[写作项目]
    Scan -->|产出| Decision[选题决策.md]
    Decision --> Write

    Write --> Project
    Review --> Project
    Deslop --> Project

    Project --> Tracking[追踪/ 状态系统]
    Project --> Outline[大纲/]
    Project --> Prose[正文/]
    Project --> Setting[设定/]

    Hooks --> Project
    Agents --> Project
    Dash --> Project
    Dash --> Library
```

## 2. 写作流水线

```mermaid
flowchart LR
    A[扫榜定方向] --> B[拆文建模块库]
    B --> C[开书：设定 + 大纲 + 细纲]
    C --> D[正文写作]
    D --> E[去 AI 味]
    E --> F[多视角审查]
    F -->|打回| D
    F -->|通过| G[提交追踪事务]
    G -->|下一章| D
```

## 3. “下一步”状态机（moshu 路由判定）

```mermaid
flowchart TD
    S0[未部署 .story-deployed] -->|/moshu-setup| S1[无书名目录]
    S1 -->|/moshu-scan 选题| S1
    S1 -->|/moshu-write 开书| S2[有书但无正文]
    S2 -->|/moshu-write 写第1章| S3[有正文但下一章无细纲]
    S3 -->|/moshu-write 补纲| S4[下一章有细纲未写]
    S4 -->|/moshu-write 日更| S5[已写至卷末]
    S5 -->|卷复盘| S6[下卷规划]
    S6 --> S2

    S2 -.->|未完成拆文| A[moshu-analyze 续跑]
    S3 -.->|未完成审查| R[moshu-review 续批]
```

## 4. 分层架构

```mermaid
flowchart TB
    subgraph UI[Claude Code 会话层]
        Router[moshu 路由]
        Skills[9 个 Skill 入口]
        Agents[7 个专业 Agent]
    end

    subgraph Deterministic[确定性脚本层]
        D1[check-ai-patterns.js]
        D2[check-degeneration.js]
        D3[check-outline-copy.js]
        D4[tracking_commit.py]
        D5[dashboard-server.mjs]
        D6[平台榜单 scraper]
        D7[deploy.py]
    end

    subgraph Hooks[自动化 Hook 层]
        H1[session-start.sh]
        H2[detect-story-gaps.sh]
        H3[guard-outline-before-prose.sh]
        H4[check-prose-after-write.sh]
        H5[validate-story-commit.sh]
    end

    subgraph Storage[文件系统数据层]
        F1[拆文库]
        F2[写作项目：设定/大纲/正文/对标]
        F3[追踪：_tracking-state.json + 派生视图]
    end

    Router --> Skills
    Skills --> Agents
    Skills --> Deterministic
    Skills --> Hooks
    Agents --> Storage
    Deterministic --> Storage
    Hooks --> Storage
```

## 5. 关键设计说明

- **三层分工**：脚本做确定性（统计/检测/事务），AI 做语义（写作/审查/大纲），作者做品味（确认/裁决/复盘）。
- **文件即记忆**：`追踪/_tracking-state.json` 是唯一结构化权威，`上下文.md`/`伏笔.md`/`角色状态/` 等均为派生视图，由 `tracking_commit.py` 统一维护。
- **Agent 可降级**：custom agent 未部署或 spawn 失败时，所有 skill 自动降级 solo/direct，保证流程不中断。
- **Hook 是兜底网**：即使主会话漏跑质量收尾，写入前/写入后的 hook 也会拦截或提醒关键问题。
- **共享资产防漂移**：`scripts/shared-assets.json` 管理 36 组跨 skill 共享副本，`scripts/check-shared-files.sh` 保证字节一致。
- **文档预算防膨胀**：`scripts/doc-budget.json` 限制每次会话必读的热路径文本量。

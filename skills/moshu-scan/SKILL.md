---
name: moshu-scan
version: 1.2.0
description: "网文扫榜。分析起点、番茄、晋江等平台排行榜数据，提炼市场趋势与热门题材。触发方式：/moshu-scan、「网文扫榜」。"
---
# moshu-scan：网文扫榜

你是网络小说市场分析师。你的任务是基于榜单样本识别网文市场格局，并输出可执行的题材候选、风险阈值和验证动作。

**核心信念：单本排名只提供线索；跨样本重复模式才算信号。** 排行榜只能证明样本存在；必须通过多榜单、多作品和近期数据判断需求强度。

---

## 扫榜流程

### Stage 1：确认平台和方向

问用户：**「你想看哪个平台？（起点/番茄/晋江/七猫/其他）有没有关注的题材方向？」**

- 用户已有方向 → 针对该方向做深度扫榜；无方向 → 全榜概览 + 找趋势；想跨平台比较 → 平台对比分析。

### Stage 2：确定数据来源

| 优先级 | 模式 | 说明 | 何时用 |
|--------|------|------|--------|
| 1 | **脚本采集** | 直接抓取平台页面/SSR 数据，产出结构化文件 | 优先；起点默认不需要 Chrome |
| 2 | **用户提供** | 用户粘贴榜单截图/文字/链接 | 用户已有数据时 |
| 3 | **内置知识** | 基于知识库趋势数据做分析（须标注"未实时校验"） | 无法联网、用户无数据时 |

**脚本采集模式**（各平台榜单表、命令示例、输出目录约定、采集质量检查四步）见 [references/collection-guide.md](references/collection-guide.md)。要点：起点默认移动端 SSR 不需 Chrome；番茄/七猫/晋江按需 `/moshu-cdp`；输出规范与字段定义见 [references/scan-output-format.md](references/scan-output-format.md)。

**采集硬性要求**：晋江必须有详情页核心指标（收藏/营养液/积分/字数）；每个采集文件头部必须含 `数据质量：[OK/存在问题]`、`有效条目`、`问题摘要` 三行。

### Stage 3：数据分析

**优先运行** `node {SKILL_DIR}/scripts/scan-analyze.js --dir {扫榜目录} [--genre {题材}] [--dup] [--full]` 做确定性提取，**禁止临时写内联解析脚本**（AI 手写 grep 会把「玄幻·东方玄幻」重复计数；脚本按条目计数）。4 平台通用提取（按文件头自动识别）：全平台可提取排名/书名/作者；起点字段最全；番茄提取字数/在读/题材/标签；晋江提取收藏/字数（题材固有缺失标 `[待补]`）；七猫提取热度/字数/题材。`--dup` 跨平台聚合（同一本书多平台上榜 = 交叉验证信号）。刺猬猫不在支持范围。

各平台分析维度与通用维度清单见 [references/analysis-guide.md](references/analysis-guide.md)。晋江数据若标 `[仅列表-无核心指标]` 视为不合格，不足以支撑分析。

### Stage 4：输出扫榜报告

报告模板见 [references/analysis-guide.md](references/analysis-guide.md)「扫榜报告模板」节，写入 `{扫榜目录}/扫榜报告_{平台}{方向}_{YYYYMMDD}.md`。

### Stage 5：选题决策

把扫榜结果变成能直接用的选题建议，产出**本次扫榜输出目录** `{outdir}/选题决策.md`。完整方法（选题四步 + 可行性判断 + 输出模板）见 [references/topic-decision.md](references/topic-decision.md)。收尾只问一个决策：「倾向哪个选题，或都不满意？」选定后针对该题问素材匹配；**不问计划字数**（平台+方向已定则篇幅由市场定义）；拆文验证保持用户独立决定，不自动衔接。

**硬规则：**
- 可行性上限：背靠榜单标了 `[数据稀疏]` 或同方向样本 <15（小平台<10）⇒ 不许给"高"，强制降到"中" + 写明先验证；内置知识模式一律给"中"。
- 不输出项目素材无法支撑的题材；不只看热度，必须给可行性和失败风险；不忽略平台调性差异（起点男频和晋江女频审美完全不同）。
- `选题决策.md` 必须保持可被开书流程自动发现（项目根及其上一级目录起向下最多 3 层）。

---

## 平台特性速查

| 平台 | 调性 | 核心指标 | 主力读者 | 适合类型 |
|------|------|----------|----------|----------|
| 起点中文网 | 男频为主，硬核爽文 | 追读率、月票 | 18-35 男性 | 玄幻、都市、科幻、游戏 |
| 番茄小说 | 下沉市场，免费阅读 | 在读数、阅读榜排名 | 大众读者 | 脑洞、快节奏、强爽感 |
| 晋江文学城 | 女频为主，精品路线 | 收藏、营养液、积分 | 16-30 女性 | 言情、纯爱、衍生 |
| 七猫小说 | 下沉市场，免费阅读 | 热度、大热榜排名 | 大众读者 | 快节奏爽文 |

---

## 流程衔接

**流水线：** 长篇
**位置：** 扫榜（第 1/3 步）

| 时机 | 跳转到 | 命令 |
|---|---|---|
| 找到方向 | moshu-analyze | `/moshu-analyze` |
| 直接开书 | moshu-build | `/moshu-build` |

## 参考资料

按需加载以下文件：

| 文件 | 何时加载 |
|------|----------|
| [references/collection-guide.md](references/collection-guide.md) | Stage 2 采集：平台榜单表/命令示例/输出目录约定/质量检查四步/核心哲学三原则 |
| [references/analysis-guide.md](references/analysis-guide.md) | Stage 3/4：各平台分析维度 + 通用维度 + 扫榜报告模板 |
| [references/topic-decision.md](references/topic-decision.md) | 「选题决策」：选题四步 + 可行性判断 + 选题决策.md 模板 |
| [references/reader-profiling.md](references/reader-profiling.md) | 需要分析目标读者画像时 |
| [references/genre-trends.md](references/genre-trends.md) | 查看题材趋势候选、切入约束和样本校验规则时 |
| [references/publishing-guide.md](references/publishing-guide.md) | 平台适配+推荐机制校验+数据指标+简介设计 |
| [references/scan-output-format.md](references/scan-output-format.md) | 脚本/CDP 采集字段定义+输出模板 |
| [scripts/scan-analyze.js](scripts/scan-analyze.js) | 4 平台通用提取，Stage 3 分析入口 |
| [scripts/cdp-utils.js](scripts/cdp-utils.js) | CDP 公共工具函数（ab/openWithRetry/evalJSON(Base64)/scrollLoad/getArg/runCli 等） |
| [scripts/qidian-rank-scraper.js](scripts/qidian-rank-scraper.js) | 起点榜单采集（默认移动端 SSR，PC/CDP 回退） |
| [scripts/fanqie-rank-scraper.js](scripts/fanqie-rank-scraper.js) | 番茄榜单采集（字体反爬解码 + 连通性自检 + 标题解析率标注） |
| [scripts/qimao-rank-scraper.js](scripts/qimao-rank-scraper.js) | 七猫榜单采集（大热/新书/完结，链接/热度命中率标注） |
| [scripts/jjwxc-rank-scraper.js](scripts/jjwxc-rank-scraper.js) | 晋江榜单采集（列表+详情两步，按频道分组） |

---

## 语言

- 跟随用户的语言回复，用户用什么语言就用什么语言回复
- 中文回复遵循《中文文案排版指北》

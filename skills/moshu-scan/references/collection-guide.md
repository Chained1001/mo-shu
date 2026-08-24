# collection-guide.md：扫榜采集指南（Stage 2 细节）

> SKILL.md Stage 2 路由到本文件。核心哲学三原则 + 各平台采集目标 + 命令示例 + 输出目录约定 + 采集质量检查。

## 核心哲学

### 原则 1：扫榜看模式，别只看排名

排名会波动，模式必须用重复样本验证。扫榜要提取：反复出现的题材、设定、套路、书名词和开篇卖点。单本上榜只能记为个例；同类样本达到可比数量后，才能标记为趋势候选。

### 原则 2：流量型平台和付费型平台看的东西不同

番茄看的是流量和完读率，起点看的是订阅和追读，晋江看的是收藏和积分。不同平台的成功标准不同，扫榜方法也不同。

### 原则 3：扫榜的目的是找到你能写的爆款题材

不按热度直接给结论。每个方向都要做项目可行性判断：素材储备、题材边界、篇幅承载、目标平台样本是否足够。

---

## 脚本采集流程

优先运行对应平台脚本直接采集结构化数据。起点使用移动端 SSR pageContext，默认不需要 Chrome/CDP；番茄等需要浏览器态的平台再使用 `/moshu-cdp` 启动 Chrome。

1. 选择平台脚本；起点直接运行 `{SKILL_DIR}/scripts/qidian-rank-scraper.js`，番茄/七猫/晋江等按需启动 moshu-cdp
2. 等待列表元素或 SSR 数据加载，逐条提取字段（排名、书名、作者、题材、字数、推荐/在读数等），判断翻页（起点通常单页50-100条，番茄按题材逐页cap≈20）
3. 需要补充数据时（标签、简介、最新更新），进入详情页提取
4. 按规范格式写入 Markdown 文件（字段定义与模板见 [scan-output-format.md](scan-output-format.md)）
5. 多榜单/多题材时，逐组采集并保存

`{SKILL_DIR}` 指当前加载的 moshu-scan skill 根目录。

### 起点采集目标

优先运行 `node {SKILL_DIR}/scripts/qidian-rank-scraper.js --type {榜单} --outdir {输出目录}`；**多榜单用逗号分隔一次采集**，如 `--type hotsales,yuepiao,signnewbook`，避免逐榜多次调用；默认 `--mode auto` 会先用 `https://m.qidian.com` 移动端 SSR，PC/CDP 只作回退。

| 榜单 | URL | 核心字段 |
|------|-----|----------|
| 新人签约新书榜 | qidian.com/rank/newsign/ | 作者·题材·签约·免费/VIP·字数·总推荐·标签·简介 |
| 签约作者新书榜 | qidian.com/rank/signnewbook/ | 已签约作者新书，新风向信号 |
| 公众作者新书榜 | qidian.com/rank/pubnewbook/ | 公众作者新书，发现潜力作者 |
| 新人作者新书榜 | qidian.com/rank/newauthor/ | 新人作品，新人赛道风向 |
| 三江推荐 | qidian.com/sanjiang/ | 编辑推荐，按周分组（注意：非 /rank/ 路径） |
| 月票榜 | qidian.com/rank/yuepiao/ | 付费认可度最高指标 |
| 畅销榜 | qidian.com/rank/hotsales/ | 真金白银投票 |
| 阅读指数榜 | qidian.com/rank/readindex/ | 阅读量综合指标 |
| 收藏榜 | qidian.com/rank/collect/ | 读者关注热度 |
| 原创推荐榜 | qidian.com/rank/recom/ | |

### 番茄采集目标

| 榜单 | URL格式 | 核心字段 |
|------|---------|----------|
| 男频阅读榜 | fanqienovel.com/rank/1_2_{cat_id} | 按题材逐页采集，在读数为核心指标 |
| 女频阅读榜 | fanqienovel.com/rank/0_2_{cat_id} | 按题材逐页采集 |
| 男频新书榜 | fanqienovel.com/rank/1_1_{cat_id} | 新风向信号 |
| 女频新书榜 | fanqienovel.com/rank/0_1_{cat_id} | 新风向信号 |

URL 参数：`/rank/{channel}_{type}_{cat_id}`，channel 0=女频/1=男频，type 1=新书榜/2=阅读榜。番茄列表页有字体反爬，须用 `{SKILL_DIR}/scripts/fanqie-rank-scraper.js` 从详情页多策略解码书名/作者/题材/标签/简介，配合 moshu-cdp 使用：

```bash
node {SKILL_DIR}/scripts/fanqie-rank-scraper.js --channel 1 --type 2 --outdir {输出目录}   # 男频阅读榜
node {SKILL_DIR}/scripts/fanqie-rank-scraper.js --channel all --top 15 --outdir {输出目录}   # 男女频，每题材前 15 本
```

> **番茄采集后必查文件头 `数据质量`**，异常排查步骤见 [scan-output-format.md](scan-output-format.md)。

### 七猫采集目标

| 榜单 | URL | 核心字段 |
|------|-----|----------|
| 排行榜总入口 | qimao.com/paihang | 大热榜/新书榜/完结榜，热度为核心指标 |

榜单类型：大热榜（日榜/月榜）、新书榜、完结榜、收藏榜、更新榜，支持男生榜/女生榜切换。大热榜用 `--period day|month|all` 显式选择日榜、月榜或两者（默认 `day`）；周期会进入文件头与文件名。非大热榜不区分周期，`--period` 不会重复采集。

### 晋江采集目标

`{SKILL_DIR}/scripts/jjwxc-rank-scraper.js`，默认列表 + 详情两步走；其余榜单类型见 [scan-output-format.md](scan-output-format.md) 榜单表。

| 榜单 | URL | 核心字段 |
|------|-----|----------|
| 收入金榜 | jjwxc.net/topten.php?orderstr=12&t=0 | 收藏数、营养液、积分、字数、状态（详情页 `onebook.php` 补采） |
| 月榜 | jjwxc.net/topten.php?orderstr=7&t=0 | 同上 |
| 完结金榜 | jjwxc.net/topten.php?orderstr=14&t=0 | 同上 |
| 新手金榜 | jjwxc.net/topten.php?orderstr=15&t=0 | 同上 |

```bash
node {SKILL_DIR}/scripts/jjwxc-rank-scraper.js --type 12 --outdir {输出目录}        # 列表+详情（默认每频道前10，详情上限100）
node {SKILL_DIR}/scripts/jjwxc-rank-scraper.js --type 12 --top 15 --detail-limit 60  # 调整每频道本数/详情总量
node {SKILL_DIR}/scripts/jjwxc-rank-scraper.js --type 12 --list-only                 # 只采列表（快，无核心指标）
```

> **晋江硬性要求**：必须有详情页核心指标（收藏数/营养液/积分/字数），脚本默认已补采；采集要点见 [scan-output-format.md](scan-output-format.md)。

### 文件命名与输出目录

**文件命名**：`{平台}{榜单名称}[_{范围/周期}]_{YYYYMMDD}.md`（范围段由各平台脚本决定，如 `_全站`/`_全题材`/`日榜`），例：`起点新人签约新书榜_20260425.md`。

**输出目录约定**：所有扫榜产物统一放项目根下 `扫榜/{平台}{方向}_{YYYYMMDD}/`（如 `扫榜/起点玄幻_20260818/`）：
- 榜单数据：脚本 `--outdir` 指向该目录
- 扫榜报告：该目录下 `扫榜报告_{平台}{方向}_{YYYYMMDD}.md`
- 选题决策：该目录下 `选题决策.md`（开书流程会从项目根及其上一级目录起、向下最多 3 层自动查找——**选题决策必须保持在这个可达范围内**；小说项目建得比 3 层更深时，开书前把 `选题决策.md` 复制到项目根）
- 同平台同方向多次扫榜用日期区分目录，不覆盖历史数据

**扫榜不依赖拆文库**：拆文库是 `/moshu-analyze` 的产物（拆解对标书用），开书对标时才消费。扫榜阶段无需检查、等待或创建拆文库；项目没有拆文库不影响扫榜，直接继续。

---

## 采集质量检查（每完成一个榜单立即执行）

发现问题当场修复，不留给后续分析。详细规则见 [scan-output-format.md](scan-output-format.md)「数据清洗与字段约束」。

**1. 数据完整性**

| 检查项 | 标准 | 处理 |
|--------|------|------|
| 条目数量 | >= 15 条有效数据（小平台 >= 10） | 不足则在文件头注明 `[数据稀疏] 实际采集 N 条` |
| 必填字段 | 排名、书名、作者（缺任一项视为无效） | 无效条目移除，条目数重新计算 |
| 字段一致性 | 同一榜单内所有条目字段集必须一致 | 不一致条目标记 `[字段缺失: {字段名}]` |

**2. 数据清洗**

| 污染类型 | 处理 |
|----------|------|
| 平台模板文本（番茄「提供XXX完整版在线免费阅读」、七猫「上一页」等） | 删除模板文本，保留正文 |
| 解析串行（同一条目出现两个不同作品的数据） | 标记 `[解析异常]`，删除并重新采集 |
| 空字段（空白、`--`、`未知`） | 标记 `[待补]`，优先通过详情页补采 |

**3. 简介截断**：清洗后超过 100 字的简介，在最近的句号/问号/感叹号处截断，加 `...`；平台模板文本不计入 100 字限制（先删除模板，再截断）。

**4. 文件头质量状态**：每个采集文件头部必须包含——

```
- 数据质量：[OK / 存在问题]
- 有效条目：{N} / {总数}
- 问题摘要：{无 / 具体问题描述}
```

---

## 其他数据来源

**用户提供操作指引：**
- 用户提供已有的扫描结果文件路径 → 直接加载进入「数据分析」
- 用户提供链接 → 用 WebFetch 抓取
- 用户粘贴/截图 → 手动解析进入分析

**内置知识操作指引：**
- 加载 `references/genre-trends.md`
- 明确标注：「以下分析基于历史趋势数据；未完成实时榜单校验前只能作为候选假设。」并列出需要复扫的榜单。

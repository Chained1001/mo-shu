#!/usr/bin/env node
/**
 * scan-analyze.js — 扫榜数据分析器（替代 AI 每次临时写内联脚本）
 *
 * 从已采集的榜单 md 文件做确定性提取：
 *   --dir {扫榜目录}            必填；扫描目录下全部榜单 md
 *   --genre {题材关键词}        提取该题材条目（如 玄幻；可多次或逗号分隔）
 *   --full                     含简介/标签的完整条目
 *   --dup                      跨榜重复样本（同一书名出现在多个榜单）
 *   --dist                     题材分布统计（默认输出）
 * 输出 markdown，AI 直接消费。
 *
 * 适用范围：起点/番茄/晋江/七猫 4 平台通用提取（平台按文件头自动识别）。
 *   - 全平台可提取：排名 / 书名 / 作者（meta 行首段）
 *   - 起点字段最全：字数 / 总推荐 / 签约 / 收费模式 / 标签 / 简介
 *   - 番茄：字数（meta 尾段）/ 在读（meta）/ 题材（meta 第 2 段）/ 标签
 *   - 晋江：收藏 / 营养液 / 积分 / 字数（meta 内嵌）；题材平台固有缺失标 [待补]
 *   - 七猫：热度 / 字数（meta 内嵌）/ 题材（meta 第 2 段）
 * 各平台缺失字段统一标 [待补] 并逐文件警告；--dup 跨平台聚合。
 * 刺猬猫/飞卢不在支持范围。
 */
const fs = require("fs");
const path = require("path");

function getArg(args, key) {
  const i = args.indexOf(key);
  return i >= 0 ? args[i + 1] : undefined;
}

const PLATFORMS = ["起点", "番茄", "晋江", "七猫"];

// ---- 平台识别：按文件头第一个 # 标题 ----
function detectPlatform(text) {
  const head = text.split(/\r?\n/, 5).join("\n");
  const m = head.match(/^#\s*(起点|番茄|晋江|七猫|刺猬猫)/m);
  if (m && !PLATFORMS.includes(m[1])) return m[1]; // 刺猬猫等：识别但无适配器
  // 识别失败返回「未知」（不静默套起点——无头文件是超规输入，仅通用字段+警告；C1 审核确认）
  return m && PLATFORMS.includes(m[1]) ? m[1] : "未知";
}

// ---- 通用条目解析：`## #1 书名` / `### #1 书名` / `#1 书名`，记录所在块（番茄/晋江的 `## 品类 — N 本`） ----
const ITEM_RE = /^#{1,3} #(\d+)\s+(.+)$/;
// 块头：`## 名称 — N 本`（排除起点条目 `## #1`；起点无块，block 为空）
const BLOCK_RE = /^##\s+(?!#\d)(.+)$/;

function parseBlocks(text) {
  const items = [];
  let cur = null;
  let block = "";
  for (const raw of text.split(/\r?\n/)) {
    const bm = raw.match(BLOCK_RE);
    if (bm) {
      block = bm[1].replace(/\s*—\s*\d+\s*本\s*$/, "").trim();
      continue;
    }
    const m = raw.match(ITEM_RE);
    if (m) {
      if (cur) items.push(cur);
      cur = { rank: parseInt(m[1], 10), title: m[2].trim(), block, body: [] };
    } else if (cur) {
      cur.body.push(raw);
    }
  }
  if (cur) items.push(cur);
  return items;
}

function metaOf(block) {
  const m = block.body.join("\n").match(/^\*([^*]*)\*$/m);
  return m ? m[1].trim() : "";
}

function fieldOf(block, label) {
  const r = block.body.join("\n").match(new RegExp(`\\*\\*${label}：([^*]*)\\*\\*`));
  return r ? r[1].trim() : "[待补]";
}

function tagsOf(block) {
  const m = block.body.join("\n").match(/\*\*标签：\*\*\s*([^\n]*)/);
  return m ? m[1].trim() : "";
}

function introOf(block) {
  const m = block.body.join("\n").match(/\*\*简介\*\*\s*\n\n([\s\S]*?)(?=\n---|\n## |\n### |$)/);
  return m ? m[1].trim().replace(/\n/g, " ") : "";
}

// meta 段提取（· 分隔段位）
function segsOf(meta) {
  return meta.split(/[|·]/).map((s) => s.trim()).filter(Boolean);
}

// ---- per-platform 适配器：统一中间结构 ----
// {rank, title, author, genre, words, rec, sign, price, metric, tags, intro, meta}
function adapt(platform, block) {
  const meta = metaOf(block);
  const segs = segsOf(meta);
  const base = {
    rank: block.rank,
    title: block.title,
    block: block.block,
    author: segs[0] || "[待补]",
    genre: "[待补]",
    words: "[待补]",
    rec: "[待补]",
    sign: "[待补]",
    price: "[待补]",
    metric: "[待补]",
    tags: tagsOf(block),
    intro: introOf(block),
    meta,
  };
  const mWan = /([\d.]+万?)字/.exec(meta); // 兼容 "123字" / "12.3万字"（捕获组已含单位）
  const unit = (s) => (s ? s.replace(/\.0$/, "") : s);

  switch (platform) {
    case "起点":
      // 现有逻辑逐字节保留：字段以 **XX：** 为准（meta 行仅作题材分布匹配）
      base.words = fieldOf(block, "字数");
      base.rec = fieldOf(block, "总推荐");
      base.sign = fieldOf(block, "签约");
      base.price = fieldOf(block, "收费模式");
      base.metric = fieldOf(block, "榜单值");
      base.genre = segs[1] || "[待补]";
      break;
    case "番茄":
      if (mWan) base.words = unit(mWan[1]);
      const reads = /([\d.]+万?)\s*在读/.exec(meta);
      if (reads) base.metric = unit(reads[1]) + "在读";
      base.genre = segs[1] || "[待补]";
      break;
    case "晋江":
      const collect = /收藏\s*([\d.]+万?)/.exec(meta);
      if (collect) base.metric = unit(collect[1]) + "收藏";
      if (mWan) base.words = unit(mWan[1]);
      // 晋江题材平台固有缺失：meta 无题材段，保持 [待补]
      break;
    case "七猫":
      const heat = /([\d.]+万?)\s*热度/.exec(meta);
      if (heat) base.metric = unit(heat[1]) + "热度";
      if (mWan) base.words = unit(mWan[1]);
      base.genre = segs[1] || "[待补]";
      break;
    default:
      // 刺猬猫等未适配平台：仅通用字段
      break;
  }
  return base;
}

// ---- 解析目录 ----
function parseDir(dir) {
  const files = fs.readdirSync(dir).filter((f) => f.endsWith(".md") && !f.includes("报告") && !f.startsWith("选题"));
  if (files.length === 0) return null;
  const data = {}; // file -> {platform, items}
  for (const f of files) {
    const text = fs.readFileSync(path.join(dir, f), "utf-8");
    const platform = detectPlatform(text);
    data[f] = { platform, items: parseBlocks(text).map((b) => adapt(platform, b)) };
  }
  return data;
}

// ---- CLI 主流程（require 时跳过，供测试直接调用解析函数） ----
function main() {
  const DIR = getArg(process.argv, "--dir");
  const GENRE = getArg(process.argv, "--genre");
  const FULL = process.argv.includes("--full");
  const DUP = process.argv.includes("--dup");
  const DIST = process.argv.includes("--dist") || (!GENRE && !DUP);

  if (!DIR) {
    console.error("用法: node scan-analyze.js --dir {扫榜目录} [--genre 玄幻] [--full] [--dup] [--dist]");
    process.exit(2);
  }

  // 审计法 v1.3 A1：--dir 不存在时预检（异常降级链半步——缺件人话明示，不裸抛堆栈）
  if (!fs.existsSync(DIR)) {
    console.error(`[错误] 目录不存在: ${DIR}`);
    process.exit(2);
  }

  const data = parseDir(DIR);
  if (!data) {
    console.error(`[错误] ${DIR} 下没有榜单文件`);
    process.exit(2);
  }

  // ---- 逐文件字段缺失警告（替代原"疑似非起点"一刀切） ----
  for (const [f, { platform, items }] of Object.entries(data)) {
    if (items.length === 0) {
      console.error(`[警告] ${f}: 未解析到任何条目（条目行需形如 ## #1 书名）`);
      continue;
    }
    // 平台未识别：明示（仅通用字段），不套平台适配器、不触发平台特有缺失警告（C1 审核调整）
    if (platform === "未知") {
      console.error(`[警告] ${f}: 平台未识别（文件头须含「起点/番茄/晋江/七猫」），仅通用字段（排名/书名/作者）`);
    }
    const missing = [];
    if (platform === "起点" && items.every((it) => it.words === "[待补]")) missing.push("字数");
    if (platform === "起点" && items.every((it) => it.rec === "[待补]")) missing.push("总推荐");
    if (platform !== "起点" && platform !== "未知" && items.every((it) => it.metric === "[待补]")) missing.push("平台核心指标");
    if (platform === "晋江" && items.every((it) => it.genre === "[待补]"))
      missing.push("题材（晋江平台固有缺失）");
    if (missing.length > 0) {
      console.error(
        `[警告] ${f}（${platform}）: 字段缺失 ${missing.join("、")}，对应分析维度可能不可信`,
      );
    }
  }

// --- 题材分布 ---
  if (DIST) {
    console.log("## 题材分布");
    // 15 类粗分类（mo-shu 自定口径），未列题材归「其他」——展示辅助非契约（C2 口径注记）
    const genres = ["玄幻", "仙侠", "武侠", "都市", "科幻", "游戏", "历史", "奇幻", "悬疑", "诸天", "体育", "现实", "军事", "二次元", "其他"];
    for (const [f, { platform, items }] of Object.entries(data)) {
      const counts = {};
      for (const it of items) {
        let hit = "其他";
        for (const g of genres) {
          if (it.meta.includes(g)) { hit = g; break; }
        }
        counts[hit] = (counts[hit] || 0) + 1;
      }
      const parts = Object.entries(counts).sort((a, b) => b[1] - a[1])
        .map(([g, n]) => `${g} ${n}`).join(" · ");
      console.log(`- ${f.replace(/_2026\d{4}\.md/, "")}: ${parts}`);
    }
  }

  // --- 指定题材条目（按块分组输出，避免番茄/晋江分块排名 #1 混淆） ---
  if (GENRE) {
    const kws = GENRE.split(",").map((s) => s.trim());
    console.log(`\n## ${GENRE} 条目`);
    for (const [f, { platform, items }] of Object.entries(data)) {
      const hit = items.filter((it) => kws.some((k) => it.meta.includes(k)));
      if (hit.length === 0) continue;
      const byBlock = {};
      for (const it of hit) (byBlock[it.block || ""] = byBlock[it.block || ""] || []).push(it);
      for (const [block, list] of Object.entries(byBlock)) {
        console.log(`\n### ${f.replace(/_2026\d{4}\.md/, "")}${block ? " · " + block : ""}`);
        for (const it of list) {
          let line = `#${it.rank} ${it.title} | ${it.meta} | 字数:${it.words} | 总推荐:${it.rec} | 签约:${it.sign} | ${it.price}`;
          if (platform !== "起点") line += ` | ${it.metric}`;
          if (FULL) {
            console.log(line);
            if (it.tags) console.log(`  标签: ${it.tags}`);
            if (it.intro) console.log(`  简介: ${it.intro.slice(0, 120)}${it.intro.length > 120 ? "..." : ""}`);
          } else {
            console.log(line);
          }
        }
      }
    }
  }

  // --- 跨榜重复样本（title+author 联合键：同名不同书不误报；author 缺失时退化仅 title） ---
  if (DUP) {
    const dups = findDuplicates(data);
    if (dups.length > 0) {
      console.log(`\n## 跨榜重复样本（${dups.length} 本出现在多个榜单 = 交叉验证信号）`);
      for (const { title, occ } of dups) {
        const occStr = occ.map((o) => `${o.file}#${o.rank}${o.block ? "(" + o.block + ")" : ""}`).join("、");
        const platStr = [...new Set(occ.map((o) => o.platform))].join("+");
        console.log(`- **${title}**（${occ[0].meta}）：${occStr} [${platStr}]`);
      }
    } else {
      console.log("\n## 跨榜重复样本\n无");
    }
  }
}

// ---- 跨榜重复聚合（导出供测试）：key = title||author，author [待补] 时退化仅 title ----
function findDuplicates(data) {
  const byKey = {};
  for (const [f, { platform, items }] of Object.entries(data)) {
    for (const it of items) {
      const key = it.author && it.author !== "[待补]" ? `${it.title}||${it.author}` : it.title;
      if (!byKey[key]) byKey[key] = [];
      byKey[key].push({
        title: it.title,
        file: f.replace(/_2026\d{4}\.md/, ""),
        rank: it.rank,
        block: it.block,
        meta: it.meta,
        platform,
      });
    }
  }
  return Object.entries(byKey)
    .filter(([, v]) => v.length > 1)
    .map(([, occ]) => ({ title: occ[0].title, occ }));
}

if (require.main === module) main();

module.exports = { detectPlatform, parseBlocks, adapt, parseDir, findDuplicates, main };

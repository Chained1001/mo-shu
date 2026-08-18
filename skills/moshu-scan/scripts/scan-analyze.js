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
 * 适用范围：当前只解析起点采集格式（`#排名 书名` 行 + `**字数：**`/`**总推荐：**`/
 * `**签约：**`/`**收费模式：**`/`**标签：**` 等字段）。番茄/七猫/晋江/刺猬猫的
 * 输出字段不同，暂不适用；其他平台榜单请按 scan-output-format 规范人工分析，
 * 脚本扩展另行推进。
 */
const fs = require("fs");
const path = require("path");

function getArg(args, key) {
  const i = args.indexOf(key);
  return i >= 0 ? args[i + 1] : undefined;
}
const DIR = getArg(process.argv, "--dir");
const GENRE = getArg(process.argv, "--genre");
const FULL = process.argv.includes("--full");
const DUP = process.argv.includes("--dup");
const DIST = process.argv.includes("--dist") || (!GENRE && !DUP);

if (!DIR) {
  console.error("用法: node scan-analyze.js --dir {扫榜目录} [--genre 玄幻] [--full] [--dup] [--dist]");
  process.exit(2);
}

const files = fs.readdirSync(DIR).filter((f) => f.endsWith(".md") && !f.includes("报告") && !f.startsWith("选题"));
if (files.length === 0) {
  console.error(`[错误] ${DIR} 下没有榜单文件`);
  process.exit(2);
}

// 解析单个榜单文件 → [{rank,title,meta,words,rec,sign,price,tags,intro}]
function parseFile(file) {
  const text = fs.readFileSync(path.join(DIR, file), "utf-8");
  const blocks = text.split(/\n## /).slice(1);
  const items = [];
  for (const b of blocks) {
    const m = b.match(/^#(\d+)\s+(.+)$/m);
    if (!m) continue;
    const metaLine = (b.match(/^\*(.*)\*$/m) || [])[1] || "";
    const grab = (label) => {
      const r = b.match(new RegExp(`\\*\\*${label}：([^*]*)\\*\\*`));
      return r ? r[1].trim() : "[待补]";
    };
    const tags = (b.match(/\*\*标签：\*\*\s*([^\n]*)/) || [])[1] || "";
    const introM = b.match(/\*\*简介\*\*\s*\n\n([\s\S]*?)(?=\n---|\n## |$)/);
    items.push({
      rank: parseInt(m[1], 10),
      title: m[2].trim(),
      meta: metaLine,
      words: grab("字数"),
      rec: grab("总推荐"),
      sign: grab("签约"),
      price: grab("收费模式"),
      tags: tags.trim(),
      intro: introM ? introM[1].trim().replace(/\n/g, " ") : "",
    });
  }
  return items;
}

const data = {};
for (const f of files) data[f] = parseFile(f);

// 起点格式字段缺失警告：非起点采集文件通常拿不到「字数」，结果不可信
const suspicious = Object.entries(data).filter(
  ([, items]) => items.length > 0 && items.every((it) => it.words === "[待补]"),
);
if (suspicious.length > 0) {
  console.error(
    `[警告] 以下文件疑似非起点采集格式（字数全为 [待补]），分析结果可能不可信: ${suspicious.map(([f]) => f).join(", ")}`,
  );
}

// --- 题材分布 ---
if (DIST) {
  console.log("## 题材分布");
  const genres = ["玄幻", "仙侠", "武侠", "都市", "科幻", "游戏", "历史", "奇幻", "悬疑", "诸天", "体育", "现实", "军事", "二次元", "其他"];
  for (const [f, items] of Object.entries(data)) {
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

// --- 指定题材条目 ---
if (GENRE) {
  const kws = GENRE.split(",").map((s) => s.trim());
  console.log(`\n## ${GENRE} 条目`);
  for (const [f, items] of Object.entries(data)) {
    const hit = items.filter((it) => kws.some((k) => it.meta.includes(k)));
    if (hit.length === 0) continue;
    console.log(`\n### ${f.replace(/_2026\d{4}\.md/, "")}`);
    for (const it of hit) {
      const line = `#${it.rank} ${it.title} | ${it.meta} | 字数:${it.words} | 总推荐:${it.rec} | 签约:${it.sign} | ${it.price}`;
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

// --- 跨榜重复样本 ---
if (DUP) {
  const byTitle = {};
  for (const [f, items] of Object.entries(data)) {
    for (const it of items) {
      if (!byTitle[it.title]) byTitle[it.title] = [];
      byTitle[it.title].push({ file: f.replace(/_2026\d{4}\.md/, ""), rank: it.rank, meta: it.meta });
    }
  }
  const dups = Object.entries(byTitle).filter(([, v]) => v.length > 1);
  if (dups.length > 0) {
    console.log(`\n## 跨榜重复样本（${dups.length} 本出现在多个榜单 = 交叉验证信号）`);
    for (const [title, occ] of dups) {
      const occStr = occ.map((o) => `${o.file}#${o.rank}`).join("、");
      console.log(`- **${title}**（${occ[0].meta}）：${occStr}`);
    }
  } else {
    console.log("\n## 跨榜重复样本\n无");
  }
}

#!/usr/bin/env node
/**
 * merge-chapter-summaries.js — 无损拼接章节摘要为 _章节摘要汇总.md（跨平台）
 *
 * 用法：node merge-chapter-summaries.js --dir {章节目录} [--out {汇总文件路径}]
 *   默认输出到 --dir 的父目录下 _章节摘要汇总.md（拆文库/{书}/_章节摘要汇总.md）。
 *
 * 替代原 Unix 管道（ls|sed|sort|cut|cat）——Windows PowerShell 无法按字面执行；
 * 且拼接后执行与管道版本相同的无损校验（P 行数 == 各文件之和、**概要** 行数 == 文件数），
 * 任一不过即删除汇总文件并 exit 1（调用方回退逐文件扫描，行为不变）。
 */
const fs = require("fs");
const path = require("path");

function getArg(args, key) {
  const i = args.indexOf(key);
  return i >= 0 ? args[i + 1] : undefined;
}

/**
 * 拼接 + 无损校验核心逻辑（导出供测试）。
 * @param {string} dir 章节目录
 * @param {string} out 汇总文件路径
 * @returns {{ok: boolean, files: string[], pMerged: number, pTotal: number, summaryMerged: number, summaryTotal: number, error?: string}}
 */
function mergeSummaries(dir, out) {
  if (!fs.existsSync(dir) || !fs.statSync(dir).isDirectory()) {
    return { ok: false, files: [], pMerged: 0, pTotal: 0, summaryMerged: 0, summaryTotal: 0, error: `目录不存在: ${dir}` };
  }
  // 按章号自然排序（第2章 < 第10章）
  const files = fs
    .readdirSync(dir)
    .filter((f) => /^第(\d+)章_摘要\.md$/.test(f))
    .sort((a, b) => {
      const na = Number(a.match(/^第(\d+)章/)[1]);
      const nb = Number(b.match(/^第(\d+)章/)[1]);
      return na - nb;
    });
  if (files.length === 0) {
    return { ok: false, files: [], pMerged: 0, pTotal: 0, summaryMerged: 0, summaryTotal: 0, error: `${dir} 下没有 第N章_摘要.md 文件` };
  }
  // 拼接（只拼接、不压缩、不改写；文件间以空行分隔，与管道版 `echo` 一致）
  let merged = "";
  let pCountTotal = 0;
  let summaryHeads = 0;
  for (const f of files) {
    const content = fs.readFileSync(path.join(dir, f), "utf8");
    merged += content;
    if (!merged.endsWith("\n")) merged += "\n";
    merged += "\n";
    pCountTotal += (content.match(/^P\d+ /gm) || []).length;
    summaryHeads += (content.match(/^\*\*概要\*\*/gm) || []).length;
  }
  // 无损校验：P 行数 == 各文件之和；**概要** 行数 == 文件数
  const pCountMerged = (merged.match(/^P\d+ /gm) || []).length;
  const summaryHeadsMerged = (merged.match(/^\*\*概要\*\*/gm) || []).length;
  const ok = pCountMerged === pCountTotal && summaryHeadsMerged === files.length;
  if (!ok) {
    try {
      fs.unlinkSync(out);
    } catch {}
    return {
      ok: false,
      files,
      pMerged: pCountMerged,
      pTotal: pCountTotal,
      summaryMerged: summaryHeadsMerged,
      summaryTotal: files.length,
      error: `无损校验失败（已删除 ${out}，回退逐文件扫描）：P 行 ${pCountMerged}/${pCountTotal}；概要头 ${summaryHeadsMerged}/${files.length}`,
    };
  }
  fs.writeFileSync(out, merged, "utf8");
  return {
    ok: true,
    files,
    pMerged: pCountMerged,
    pTotal: pCountTotal,
    summaryMerged: summaryHeadsMerged,
    summaryTotal: files.length,
  };
}

function main() {
  const DIR = getArg(process.argv, "--dir");
  if (!DIR) {
    console.error("用法: node merge-chapter-summaries.js --dir {章节目录} [--out {汇总文件}]");
    process.exit(2);
  }
  const OUT = getArg(process.argv, "--out") || path.join(path.dirname(DIR), "_章节摘要汇总.md");
  const result = mergeSummaries(DIR, OUT);
  if (!result.ok) {
    console.error(`[错误] ${result.error}`);
    process.exit(result.error.startsWith("目录不存在") || result.error.includes("没有 第N章") ? 2 : 1);
  }
  console.log(`✓ 已拼接 ${result.files.length} 章 → ${OUT}（P 行 ${result.pMerged}，校验通过）`);
}

if (require.main === module) main();

module.exports = { mergeSummaries, main };

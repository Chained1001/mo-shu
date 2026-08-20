#!/usr/bin/env node
// check-prose-candidates.js — 正文层候选类机检（高频意象 / 句式偏离 / 信息差兑现）
// 候选永不拦截：输出结构硬编码 blocking_count=0 且无 blocking 字段数组，
// 退出码恒 0（仅参数/文件错误=2）；缺 --style/--gaps 时降级提示，不失败。
// 零 LLM、零网络、只读（不写任何文件）。
"use strict";

const fs = require("fs");

// mo-shu 自定：同窗（2-4 字）出现次数阈值，--threshold 可覆盖。
const IMAGERY_REPEAT_THRESHOLD = 5;
// mo-shu 自定：句式偏离容差，基线区间 ±30%。
const DRIFT_TOLERANCE = 0.3;
const WINDOW_LENGTHS = [2, 3, 4];

// 内建停用词（虚词/高频功能字，约 60 个）：全停用词的窗口不算意象。
const STOPWORDS = new Set(
  (
    "的了是在我你他她它们这那有和与就都而及或被把让对从到说想看很也还又再不没能会要将着过吧吗呢啊哦嗯" +
    "个之其于上下中后前以为等并但却且即只才已正可应该向由因如若虽随往当次第每各这些那些这里那里这样那样"
  ).split("")
);
const PUNCTUATION = new Set(
  "，。！？；：、\"''（）《》〈〉…—·「」『』【】,.!?;:()[]{}<>~`@#$%^&*_+-=|/ \t\n\r".split("")
);

function countHan(text) {
  return (text.match(/[\u4e00-\u9fff]/g) || []).length;
}

function imageryCandidates(text, threshold) {
  const counts = new Map();
  for (const len of WINDOW_LENGTHS) {
    for (let index = 0; index + len <= text.length; index++) {
      const window = text.slice(index, index + len);
      const chars = [...window];
      if (chars.length !== len) continue;
      if (chars.some((ch) => PUNCTUATION.has(ch))) continue; // 含标点/空白 → 非实词连续串
      if (chars.every((ch) => STOPWORDS.has(ch))) continue; // 全停用词 → 跳过
      counts.set(window, (counts.get(window) || 0) + 1);
    }
  }
  const candidates = [];
  for (const [text, count] of counts) {
    if (count >= threshold) {
      candidates.push({ type: "imagery", text, count });
    }
  }
  candidates.sort((a, b) => b.count - a.count || a.text.localeCompare(b.text, "zh"));
  return candidates;
}

function parseAnchor(styleText, patterns) {
  for (const pattern of patterns) {
    const match = styleText.match(pattern);
    if (!match) continue;
    const low = parseInt(match[1], 10);
    const high = match[2] ? parseInt(match[2], 10) : low;
    if (Number.isFinite(low) && Number.isFinite(high) && low > 0 && high >= low) {
      return { low, high };
    }
  }
  return null;
}

const SENTENCE_ANCHOR_PATTERNS = [
  /平均句长[^0-9]{0,10}(\d{1,3})(?:\s*[-~至]\s*(\d{1,3}))?/,
  /句长分布[^0-9]{0,20}平均句长[^0-9]{0,10}(\d{1,3})(?:\s*[-~至]\s*(\d{1,3}))?/,
];
const PARAGRAPH_ANCHOR_PATTERNS = [
  /段均字数[^0-9]{0,10}(\d{1,4})(?:\s*[-~至]\s*(\d{1,4}))?/,
  // 注：不把「段落节奏」当锚点——moshu-style 模板该行填的是「段落平均句数」，
  // 单位与段均字数不同，误配会产出永久假阳性（审计-V3 S2）。
];
const DIALOG_ANCHOR_PATTERNS = [/对话行占比[^0-9]{0,6}(\d{1,3})\s*%/];

function styleDriftCandidates(prose, styleText) {
  const candidates = [];
  const degraded = [];
  const sentenceAnchor = parseAnchor(styleText, SENTENCE_ANCHOR_PATTERNS);
  const paragraphAnchor = parseAnchor(styleText, PARAGRAPH_ANCHOR_PATTERNS);
  const dialogAnchor = parseAnchor(styleText, DIALOG_ANCHOR_PATTERNS);
  if (!sentenceAnchor && !paragraphAnchor && !dialogAnchor) {
    degraded.push("style_baseline_unparsed");
    return { candidates, degraded };
  }
  const han = countHan(prose);
  const sentences = prose.split(/[。！？!?…]+/).filter((part) => countHan(part) > 0);
  const paragraphs = prose.split(/\n\s*\n/).filter((part) => countHan(part) > 0);
  const lines = prose.split("\n").filter((line) => line.trim() !== "");
  const dialogLines = lines.filter((line) => /^["“「]/.test(line.trim())).length;

  const round1 = (value) => Math.round(value * 10) / 10;
  const outOfBand = (actual, anchor) =>
    actual < anchor.low * (1 - DRIFT_TOLERANCE) || actual > anchor.high * (1 + DRIFT_TOLERANCE);

  if (sentenceAnchor) {
    const actual = sentences.length ? round1(han / sentences.length) : 0;
    if (outOfBand(actual, sentenceAnchor)) {
      candidates.push({
        type: "style_drift",
        metric: "avg_sentence_len",
        actual,
        baseline: `${sentenceAnchor.low}-${sentenceAnchor.high}`,
      });
    }
  }
  if (paragraphAnchor) {
    const actual = paragraphs.length ? round1(han / paragraphs.length) : 0;
    if (outOfBand(actual, paragraphAnchor)) {
      candidates.push({
        type: "style_drift",
        metric: "avg_paragraph_chars",
        actual,
        baseline: `${paragraphAnchor.low}-${paragraphAnchor.high}`,
      });
    }
  }
  if (dialogAnchor) {
    const actual = lines.length ? round1((dialogLines * 100) / lines.length) : 0;
    if (outOfBand(actual, dialogAnchor)) {
      candidates.push({
        type: "style_drift",
        metric: "dialog_line_ratio",
        actual,
        baseline: `${dialogAnchor.low}-${dialogAnchor.high}`,
      });
    }
  }
  return { candidates, degraded };
}

function gapTouchCandidates(prose, gapsText) {
  // 解析 `追踪/信息差.md` 表格：| ID | 知情人 | 读者已知 | 关键词 | 状态 | 首次登记章 | 最近变更章 | 备注 |
  const candidates = [];
  for (const line of gapsText.split("\n")) {
    const cells = line.split("|").map((cell) => cell.trim());
    if (cells.length < 9) continue;
    const id = cells[1];
    const keywords = cells[4];
    const status = cells[5];
    if (!/^G\d{3,}$/.test(id)) continue; // 表头/分隔行/无关行
    if (status !== "登记") continue;
    for (const keyword of keywords.split(/[、,，]/).map((word) => word.trim()).filter(Boolean)) {
      if (prose.includes(keyword)) {
        candidates.push({ type: "gap_touch", gap_id: id, keyword, hint: "可标记兑现（作者确认）" });
      }
    }
  }
  return candidates;
}

function analyzeProse(proseText, styleText, gapsText, options = {}) {
  const threshold = options.threshold ?? IMAGERY_REPEAT_THRESHOLD;
  const candidates = [];
  const degraded = [];
  candidates.push(...imageryCandidates(proseText, threshold));
  if (styleText) {
    const drift = styleDriftCandidates(proseText, styleText);
    candidates.push(...drift.candidates);
    degraded.push(...drift.degraded);
  } else {
    degraded.push("style_not_provided");
  }
  if (gapsText) {
    const touched = gapTouchCandidates(proseText, gapsText);
    candidates.push(...touched);
    if (gapsText.split("\n").every((line) => !/^\|\s*G\d{3,}/.test(line))) {
      degraded.push("gaps_unparsed");
    }
  } else {
    degraded.push("gaps_not_provided");
  }
  return { candidates, degraded, blocking_count: 0 };
}

function main(argv) {
  let prosePath = null;
  let stylePath = null;
  let gapsPath = null;
  let asJson = false;
  let threshold = IMAGERY_REPEAT_THRESHOLD;
  for (let index = 0; index < argv.length; index++) {
    const argument = argv[index];
    if (argument === "--prose") prosePath = argv[++index];
    else if (argument === "--style") stylePath = argv[++index];
    else if (argument === "--gaps") gapsPath = argv[++index];
    else if (argument === "--json") asJson = true;
    else if (argument === "--threshold") threshold = parseInt(argv[++index], 10);
    else {
      process.stderr.write(`ERROR: unknown argument ${argument}\n`);
      return 2;
    }
  }
  if (!prosePath) {
    process.stderr.write("ERROR: --prose <file> is required\n");
    return 2;
  }
  if (!Number.isFinite(threshold) || threshold < 1) {
    process.stderr.write("ERROR: --threshold must be an integer >= 1\n");
    return 2;
  }
  let proseText;
  try {
    proseText = fs.readFileSync(prosePath, "utf8");
  } catch (error) {
    process.stderr.write(`ERROR: unable to read prose file: ${error.message}\n`);
    return 2;
  }
  let styleText = null;
  if (stylePath) {
    try {
      styleText = fs.readFileSync(stylePath, "utf8");
    } catch (error) {
      process.stderr.write(`ERROR: unable to read style file: ${error.message}\n`);
      return 2;
    }
  }
  let gapsText = null;
  if (gapsPath) {
    try {
      gapsText = fs.readFileSync(gapsPath, "utf8");
    } catch (error) {
      process.stderr.write(`ERROR: unable to read gaps file: ${error.message}\n`);
      return 2;
    }
  }
  const result = analyzeProse(proseText, styleText, gapsText, { threshold });
  if (asJson) {
    console.log(JSON.stringify(result, null, 2));
    return 0;
  }
  if (result.candidates.length === 0) {
    console.log("prose candidates: none");
  }
  for (const candidate of result.candidates) {
    if (candidate.type === "imagery") {
      console.log(`[imagery] "${candidate.text}" 出现 ${candidate.count} 次`);
    } else if (candidate.type === "style_drift") {
      console.log(`[style_drift] ${candidate.metric}: 实际 ${candidate.actual}, 基线 ${candidate.baseline}`);
    } else {
      console.log(`[gap_touch] ${candidate.gap_id} 关键词 "${candidate.keyword}" 命中正文（${candidate.hint}）`);
    }
  }
  for (const item of result.degraded) {
    console.log(`[degraded] ${item}`);
  }
  console.log("blocking_count: 0");
  return 0;
}

module.exports = { analyzeProse, IMAGERY_REPEAT_THRESHOLD, DRIFT_TOLERANCE };

if (require.main === module) {
  process.exitCode = main(process.argv.slice(2));
}

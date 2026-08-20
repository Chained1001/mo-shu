#!/usr/bin/env node
// 守护对象：check-prose-candidates.js 候选类机检回归。禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。
"use strict";

const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

const TOOL = path.resolve(__dirname, "../skills/moshu-write/scripts/check-prose-candidates.js");

function run(args) {
  return spawnSync(process.execPath, [TOOL, ...args], { encoding: "utf8" });
}

const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "prose-candidates-"));
try {
  // 正向：同一意象词重复出现 → imagery 命中；含登记信息差关键词 → gap_touch 命中
  const prose = path.join(tmpDir, "prose.md");
  fs.writeFileSync(
    prose,
    "灵光灵光灵光灵光灵光灵光。他凝视着那道灵光，灵光乍现又灭，灵光始终不散，灵光映在眼底，灵光落入长夜。\n",
    "utf8"
  );
  const gaps = path.join(tmpDir, "gaps.md");
  fs.writeFileSync(
    gaps,
    "| ID | 知情人 | 读者已知 | 关键词 | 状态 | 首次登记章 | 最近变更章 | 备注 |\n" +
      "|---|---|---|---|---|---|---|---|\n" +
      "| G001 | 江晨 | 未知 | 灵光、顿悟 | 登记 | 第1章 | 第1章 | 测试登记 |\n" +
      "| G002 | 钟嘉嘉 | 已知 | 军报 | 已兑现 | 第1章 | 第2章 | 已兑现不报 |\n",
    "utf8"
  );
  const forward = run(["--prose", prose, "--gaps", gaps, "--json"]);
  assert.strictEqual(forward.status, 0, forward.stderr);
  const forwardOut = JSON.parse(forward.stdout);
  assert.ok(
    forwardOut.candidates.some((candidate) => candidate.type === "imagery" && candidate.text === "灵光" && candidate.count >= 5),
    `imagery 候选缺失: ${JSON.stringify(forwardOut.candidates)}`
  );
  assert.ok(
    forwardOut.candidates.some(
      (candidate) => candidate.type === "gap_touch" && candidate.gap_id === "G001" && candidate.keyword === "灵光"
    ),
    "gap_touch 候选缺失"
  );
  assert.strictEqual(forwardOut.blocking_count, 0);
  assert.ok(forwardOut.degraded.includes("style_not_provided"), "缺 style 应降级标注");
  assert.ok(!forwardOut.degraded.includes("gaps_not_provided"));
  assert.ok(!forwardOut.degraded.includes("gaps_unparsed"));

  // 反向：干净文本 → 候选为空、blocking_count=0
  const clean = path.join(tmpDir, "clean.md");
  fs.writeFileSync(
    clean,
    "他走进院子，看见老槐树下的石桌。午后阳光穿过枝叶，落下一地斑驳。\n\n他坐下，翻开那本旧书，读了很久。\n",
    "utf8"
  );
  const reverse = run(["--prose", clean, "--json"]);
  assert.strictEqual(reverse.status, 0, reverse.stderr);
  const reverseOut = JSON.parse(reverse.stdout);
  assert.deepStrictEqual(reverseOut.candidates, []);
  assert.strictEqual(reverseOut.blocking_count, 0);
  assert.ok(reverseOut.degraded.includes("style_not_provided"));
  assert.ok(reverseOut.degraded.includes("gaps_not_provided"));

  // 降级：坏格式 gaps → gaps_unparsed 标注、退出 0
  const badGaps = path.join(tmpDir, "bad.md");
  fs.writeFileSync(badGaps, "这不是信息差表格\n", "utf8");
  const degraded = run(["--prose", clean, "--gaps", badGaps, "--json"]);
  assert.strictEqual(degraded.status, 0, degraded.stderr);
  const degradedOut = JSON.parse(degraded.stdout);
  assert.ok(degradedOut.degraded.includes("gaps_unparsed"));
  assert.strictEqual(degradedOut.blocking_count, 0);

  // 契约：moshu-style 模板逐字产出的文风文件必须能被解析出句长锚点
  // （守护 S1：模板字段名与 check-prose-candidates.js 解析锚点对齐；改任何一侧字段名此用例必红）
  const styleTemplate = path.join(tmpDir, "style-template.md");
  fs.writeFileSync(
    styleTemplate,
    "# 某书 文风\n" +
      "## 生成记录\n" +
      "- 来源：本地文件\n" +
      "- 抽样：第 1/50/120 章全文\n" +
      "- 生成时间：2026-08-21\n" +
      "- 文风可用：是\n" +
      "## 整体语感\n" +
      "- 句长分布：短<15字 66% / 中15-30 33% / 长>30 0% / ≥50字超长句 0% / 平均句长 12 字\n" +
      "- 标点习惯：逗号 50% / 句号 30% / 感叹号 5% / 问号 5% / 破折号 0% / 省略号 0%\n" +
      "- 段落节奏：段落平均句数 2.0（统计）+ 单段单动作为主\n",
    "utf8"
  );
  const styled = run(["--prose", prose, "--gaps", gaps, "--style", styleTemplate, "--json"]);
  assert.strictEqual(styled.status, 0, styled.stderr);
  const styledOut = JSON.parse(styled.stdout);
  assert.ok(
    styledOut.candidates.some((candidate) => candidate.type === "style_drift" && candidate.metric === "avg_sentence_len"),
    `按 moshu-style 模板生成的文风未解析出 avg_sentence_len 锚点: ${JSON.stringify(styledOut)}`
  );
  assert.ok(
    !styledOut.candidates.some(
      (candidate) => candidate.type === "style_drift" && candidate.metric === "avg_paragraph_chars" && candidate.baseline === "2-2"
    ),
    "段落平均句数被误当段均字数（S2 假阳性回归）"
  );
  assert.ok(!styledOut.degraded.includes("style_baseline_unparsed"), "句长锚点不得静默丢失");

  // 幂等：同输入跑两遍输出逐字节一致
  const first = run(["--prose", prose, "--gaps", gaps, "--json"]);
  const second = run(["--prose", prose, "--gaps", gaps, "--json"]);
  assert.strictEqual(first.stdout, second.stdout);

  // 错误：缺 --prose → 退出 2
  const missing = run(["--json"]);
  assert.strictEqual(missing.status, 2);

  console.log("OK: prose candidates imagery/gap-touch positives, clean negatives, degraded fallbacks, determinism, and errors");
} finally {
  fs.rmSync(tmpDir, { recursive: true, force: true });
}

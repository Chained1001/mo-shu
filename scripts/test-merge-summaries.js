#!/usr/bin/env node
/**
 * test-merge-summaries.js — merge-chapter-summaries.js 回归
 * 守护对象：merge-chapter-summaries 拼接回归。禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。
 *
 * 运行：node scripts/test-merge-summaries.js
 * 覆盖：自然排序（第2章<第10章）、拼接完整性、无损校验（P 行/概要头）、
 *       校验失败删除汇总、空目录 fail、跨平台（直接调函数，不走子进程）。
 */
const { test } = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const { mergeSummaries } = require("../skills/moshu-analyze/scripts/merge-chapter-summaries.js");

function makeDir(files) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "merge-sum-"));
  for (const [name, content] of Object.entries(files)) {
    fs.writeFileSync(path.join(dir, name), content, "utf8");
  }
  return dir;
}

test("自然排序 + 拼接完整（第2章在 第10章 前）", () => {
  const dir = makeDir({
    "第2章_摘要.md": "**概要**\n第二章内容\nP1 动作 | 白描 | 涉及甲\n",
    "第10章_摘要.md": "**概要**\n第十章内容\nP1 动作 | 白描 | 涉及乙\nP2 动作 | 白描 | 涉及丙\n",
    "第1章_摘要.md": "**概要**\n第一章内容\nP1 动作 | 白描 | 涉及甲\n",
  });
  const out = path.join(dir, "_章节摘要汇总.md");
  const r = mergeSummaries(dir, out);
  assert.ok(r.ok, r.error);
  assert.deepStrictEqual(r.files, ["第1章_摘要.md", "第2章_摘要.md", "第10章_摘要.md"]);
  assert.strictEqual(r.pMerged, 4);
  assert.strictEqual(r.summaryMerged, 3);
  const merged = fs.readFileSync(out, "utf8");
  assert.ok(merged.indexOf("第一章内容") < merged.indexOf("第二章内容"));
  assert.ok(merged.indexOf("第二章内容") < merged.indexOf("第十章内容"));
  fs.rmSync(dir, { recursive: true, force: true });
});

test("无损校验失败：删除汇总文件并返回 ok=false", () => {
  const dir = makeDir({
    // 缺 **概要** 头 → summaryMerged < files.length
    "第1章_摘要.md": "P1 动作 | 白描 | 涉及甲\n",
    "第2章_摘要.md": "**概要**\nP1 动作 | 白描 | 涉及乙\n",
  });
  const out = path.join(dir, "_章节摘要汇总.md");
  const r = mergeSummaries(dir, out);
  assert.strictEqual(r.ok, false);
  assert.match(r.error, /无损校验失败/);
  assert.ok(!fs.existsSync(out), "校验失败必须删除汇总文件");
  fs.rmSync(dir, { recursive: true, force: true });
});

test("空目录 / 无匹配文件：ok=false", () => {
  const dir = makeDir({ "readme.md": "x" });
  const r = mergeSummaries(dir, path.join(dir, "_章节摘要汇总.md"));
  assert.strictEqual(r.ok, false);
  assert.match(r.error, /没有 第N章_摘要\.md/);
  fs.rmSync(dir, { recursive: true, force: true });
});

test("目录不存在：ok=false", () => {
  const r = mergeSummaries(path.join(os.tmpdir(), "no-such-dir-xyz"), "out.md");
  assert.strictEqual(r.ok, false);
  assert.match(r.error, /目录不存在/);
});

test("CRLF 输入兼容（Windows 落盘文件）", () => {
  const dir = makeDir({
    "第1章_摘要.md": "**概要**\r\nP1 动作 | 白描 | 涉及甲\r\n",
  });
  const out = path.join(dir, "_章节摘要汇总.md");
  const r = mergeSummaries(dir, out);
  assert.ok(r.ok, r.error);
  assert.strictEqual(r.pMerged, 1);
  assert.strictEqual(r.summaryMerged, 1);
  fs.rmSync(dir, { recursive: true, force: true });
});

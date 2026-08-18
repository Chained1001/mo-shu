#!/usr/bin/env node
/**
 * test-scan-analyze.js — scan-analyze.js v2 回归（4 平台通用提取 + --dup 跨平台）
 *
 * 运行：node scripts/test-scan-analyze.js
 * fixture：tests/fixtures/scan/（4 平台最小样例，含跨平台同名书「星海征途」）
 * 说明：直接 require 解析函数断言（与 test-scan-runtime.js 同模式），不走子进程。
 */
const { test } = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");

const { detectPlatform, parseBlocks, adapt, parseDir } = require("../skills/moshu-scan/scripts/scan-analyze.js");
const FIXTURES = path.join(__dirname, "..", "tests", "fixtures", "scan");

const read = (name) => fs.readFileSync(path.join(FIXTURES, name), "utf-8");
const parse = (name) => parseBlocks(read(name)).map((b) => adapt(detectPlatform(read(name)), b));

test("平台识别：文件头自动判定 4 平台", () => {
  assert.strictEqual(detectPlatform(read("起点月票榜_20260818.md")), "起点");
  assert.strictEqual(detectPlatform(read("番茄男频阅读榜_20260818.md")), "番茄");
  assert.strictEqual(detectPlatform(read("晋江月榜_20260818.md")), "晋江");
  assert.strictEqual(detectPlatform(read("七猫男频大热榜_20260818.md")), "七猫");
});

test("起点：完整字段提取（字数/总推荐/签约/收费模式/标签/简介）", () => {
  const items = parse("起点月票榜_20260818.md");
  assert.strictEqual(items.length, 3);
  const b = items[0];
  assert.strictEqual(b.rank, 1);
  assert.strictEqual(b.title, "星海征途");
  assert.strictEqual(b.author, "林远航");
  assert.strictEqual(b.words, "320万字");
  assert.strictEqual(b.rec, "85000");
  assert.strictEqual(b.sign, "签约");
  assert.strictEqual(b.price, "VIP");
  assert.match(b.tags, /星际/);
  assert.match(b.intro, /星图/);
});

test("番茄：meta 段提取（字数/在读/题材）", () => {
  const items = parse("番茄男频阅读榜_20260818.md");
  assert.strictEqual(items.length, 3);
  const b = items[1]; // 废土拾荒者
  assert.strictEqual(b.title, "废土拾荒者");
  assert.strictEqual(b.words, "180万");
  assert.strictEqual(b.metric, "28万在读");
  assert.strictEqual(b.genre, "科幻末世");
  assert.match(b.tags, /废土/);
});

test("晋江：收藏/字数提取 + 题材平台固有缺失 [待补]", () => {
  const items = parse("晋江月榜_20260818.md");
  assert.strictEqual(items.length, 2);
  const b = items[0];
  assert.strictEqual(b.title, "月落长安");
  assert.strictEqual(b.words, "120万");
  assert.strictEqual(b.metric, "12.3万收藏");
  assert.strictEqual(b.genre, "[待补]"); // 平台固有缺失
});

test("七猫：热度/字数/题材提取", () => {
  const items = parse("七猫男频大热榜_20260818.md");
  assert.strictEqual(items.length, 3);
  const b = items[0];
  assert.strictEqual(b.title, "星海征途");
  assert.strictEqual(b.words, "320万");
  assert.strictEqual(b.metric, "8.2万热度");
  assert.strictEqual(b.genre, "科幻");
});

test("--dup 数据源：跨平台同名书可聚合", () => {
  const data = parseDir(FIXTURES);
  const byTitle = {};
  for (const { platform, items } of Object.values(data)) {
    for (const it of items) {
      if (!byTitle[it.title]) byTitle[it.title] = [];
      byTitle[it.title].push(platform);
    }
  }
  const dup = byTitle["星海征途"];
  assert.ok(dup.includes("起点") && dup.includes("番茄") && dup.includes("七猫"), `跨平台聚合缺失: ${dup}`);
  assert.ok(!byTitle["月落长安"] || byTitle["月落长安"].length === 1); // 单平台书不重复
});

test("字段归一：无单位重复（万万 bug 回归）", () => {
  const items = parse("七猫男频大热榜_20260818.md");
  assert.doesNotMatch(items[0].words, /万万/);
  assert.doesNotMatch(items[0].metric, /万万/);
  assert.doesNotMatch(parse("番茄男频阅读榜_20260818.md")[0].metric, /万万/);
});

test("CLI 兼容：require 后不自动执行 main（无副作用）", () => {
  // 通过 require 已隐式验证：模块加载不抛错、不 exit
  const mod = require("../skills/moshu-scan/scripts/scan-analyze.js");
  assert.strictEqual(typeof mod.main, "function");
});

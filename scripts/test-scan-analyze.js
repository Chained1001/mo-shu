#!/usr/bin/env node
/**
 * test-scan-analyze.js — scan-analyze.js v2 回归（4 平台通用提取 + --dup 跨平台）
 * 守护对象：scan-analyze 4 平台通用提取回归。禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。
 *
 * 运行：node scripts/test-scan-analyze.js
 * fixture：tests/fixtures/scan/（4 平台最小样例，含跨平台同名书「星海征途」）
 * 说明：直接 require 解析函数断言（与 test-scan-runtime.js 同模式），不走子进程。
 */
const { test } = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const { detectPlatform, parseBlocks, adapt, parseDir, findDuplicates } = require("../skills/moshu-scan/scripts/scan-analyze.js");
const FIXTURES = path.join(__dirname, "..", "tests", "fixtures", "scan");
const SCAN_ANALYZE = path.join(__dirname, "..", "skills", "moshu-scan", "scripts", "scan-analyze.js");

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

test("块名提取：番茄/晋江分块标注，起点无块", () => {
  const fanqie = parse("番茄男频阅读榜_20260818.md");
  assert.strictEqual(fanqie[0].block, "科幻末世");
  assert.strictEqual(fanqie[2].block, "都市脑洞");
  const jj = parse("晋江月榜_20260818.md");
  assert.strictEqual(jj[0].block, "古言");
  const qd = parse("起点月票榜_20260818.md");
  assert.strictEqual(qd[0].block, "");
});

test("--dup 联合键：同名不同作者不误报，同名同作者跨文件聚合", () => {
  const data = {
    "a.md": {
      platform: "晋江",
      items: [
        { title: "惊悚", author: "悬疑", rank: 13, block: "多元", meta: "悬疑", platform: "晋江" },
        { title: "惊悚", author: "白月光", rank: 74, block: "多元", meta: "白月光", platform: "晋江" },
      ],
    },
    "b.md": {
      platform: "起点",
      items: [{ title: "惊悚", author: "悬疑", rank: 1, block: "", meta: "", platform: "起点" }],
    },
  };
  const dups = findDuplicates(data);
  assert.strictEqual(dups.length, 1, `应只有 1 组重复（惊悚||悬疑 跨文件），实际: ${JSON.stringify(dups)}`);
  assert.strictEqual(dups[0].title, "惊悚");
  const files = dups[0].occ.map((o) => o.file);
  assert.ok(files.includes("a.md") && files.includes("b.md")); // 惊悚||悬疑 跨 a/b 聚合
  // 惊悚||白月光 仅 a#74，不构成重复
});

test("--dup 联合键：author 缺失 [待补] 时退化仅 title", () => {
  const data = {
    "a.md": { platform: "晋江", items: [{ title: "惊悚", author: "[待补]", rank: 1, block: "", meta: "", platform: "晋江" }] },
    "b.md": { platform: "晋江", items: [{ title: "惊悚", author: "[待补]", rank: 2, block: "", meta: "", platform: "晋江" }] },
  };
  const dups = findDuplicates(data);
  assert.strictEqual(dups.length, 1); // 无 author 时仍按 title 聚合
});

test("--dup 数据源：跨平台同名同作者书可聚合", () => {
  const data = parseDir(FIXTURES);
  const dups = findDuplicates(data);
  const star = dups.find((d) => d.title === "星海征途");
  assert.ok(star, "星海征途应出现在重复样本");
  const plats = star.occ.map((o) => o.platform);
  assert.ok(plats.includes("起点") && plats.includes("番茄") && plats.includes("七猫"), `跨平台聚合缺失: ${plats}`);
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

// 审计-V3 SM4：scraper 真实渲染输出 ↔ scan-analyze 适配器联合契约（此前零联合守卫，
// fixture 是手写近似样本，已与真实产出漂移——改任一 scraper 的 meta 段序/字段拼法此用例必红）
test("契约：qidian renderMarkdown 真实输出能被 detectPlatform/adapt 解析", () => {
  const { renderMarkdown } = require("../skills/moshu-scan/scripts/qidian-rank-scraper.js");
  const markdown = renderMarkdown(
    { label: "月票榜" },
    [
      {
        rank: 1,
        title: "契约书",
        author: "契约作者",
        genre: "玄幻",
        status: "连载",
        words: "320万字",
        totalRecommendations: "85000",
        signing: "签约",
        pricing: "VIP",
        url: "https://www.qidian.com/book/1/",
      },
    ],
    "https://www.qidian.com/rank/yuepiao/",
    "mobile-ssr"
  );
  assert.strictEqual(detectPlatform(markdown), "起点");
  const items = parseBlocks(markdown).map((b) => adapt("起点", b));
  assert.strictEqual(items.length, 1);
  assert.strictEqual(items[0].author, "契约作者");
  assert.ok(!items[0].genre.includes("连载"), `题材段位不得被状态污染: ${items[0].genre}`);
});

test("契约：qimao renderMarkdown 真实输出能被 detectPlatform/adapt 解析", () => {
  const { renderMarkdown } = require("../skills/moshu-scan/scripts/qimao-rank-scraper.js");
  const markdown = renderMarkdown(
    { label: "男频" },
    { label: "大热榜" },
    { label: "日榜" },
    "https://www.qimao.com/rank/1/",
    [
      {
        rank: 1,
        title: "契约书二",
        author: "契约作者二",
        genre: "都市",
        subGenre: "都市生活",
        status: "连载中",
        words: "150万字",
        heat: "100万",
        url: "https://www.qimao.com/shuku/1/",
      },
    ],
    1
  );
  assert.strictEqual(detectPlatform(markdown), "七猫");
  const items = parseBlocks(markdown).map((b) => adapt("七猫", b));
  assert.strictEqual(items.length, 1);
  assert.strictEqual(items[0].author, "契约作者二");
});

test("平台识别：无平台头文件 → 未知（C1 不静默套起点）", () => {
  assert.strictEqual(detectPlatform("# 我自己的书单\n\n## #1 测试书名\n*作者A*\n"), "未知");
  assert.strictEqual(detectPlatform("# 起点 · 月票榜\n"), "起点"); // 有头仍正常识别
});

test("字段缺失警告：缺总推荐字段的起点文件 → stderr 含「字段缺失」（C4 补回归）", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "scan-warn-"));
  try {
    fs.writeFileSync(
      path.join(dir, "起点字段缺失.md"),
      [
        "# 起点 · 测试榜",
        "- 数据质量：[OK]",
        "- 有效条目：1 / 1",
        "- 问题摘要：无",
        "",
        "---",
        "",
        "## #1 测试书名",
        "*作者A · 都市 · 连载中 · 已签约 · VIP · 100万字*",
        "",
        "[作品页](https://example.com)",
      ].join("\n"),
      "utf-8"
    );
    const r = spawnSync(process.execPath, [SCAN_ANALYZE, "--dir", dir], { encoding: "utf-8" });
    assert.match(r.stderr, /字段缺失/, "缺总推荐字段应触发字段缺失警告");
    assert.match(r.stderr, /总推荐/, "警告应点名缺失字段");
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test("平台未识别警告：无平台头文件 → stderr 含「平台未识别」且不套起点适配器（C1）", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "scan-nohdr-"));
  try {
    fs.writeFileSync(
      path.join(dir, "自定义书单.md"),
      ["# 我自己的书单", "", "## #1 测试书名", "*作者A*", "", "[作品页](https://example.com)"].join("\n"),
      "utf-8"
    );
    const r = spawnSync(process.execPath, [SCAN_ANALYZE, "--dir", dir], { encoding: "utf-8" });
    assert.match(r.stderr, /平台未识别/, "无头文件应明示平台未识别");
    assert.doesNotMatch(r.stderr, /（起点）/, "不应把未识别文件标注成起点（C1 静默降级修复）");
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

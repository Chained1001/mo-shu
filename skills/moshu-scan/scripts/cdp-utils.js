/**
 * CDP 工具函数 — 各平台采集脚本的公共依赖
 *
 * 使用方式：
 *   const { ab, sleep, evalJSON, evalJSONBase64, scrollLoad, getArg, safeStr, localDateStamp } = require("./cdp-utils");
 *
 * 前置：
 *   node <moshu-cdp skill ?>/scripts/setup-cdp-chrome.js 9222
 */

const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");

/**
 * On Windows `agent-browser` is an npm shim (agent-browser.cmd/.ps1) that
 * forwards to the real target — the native agent-browser-win32-*.exe or a
 * bundled Node CLI. Node refuses to execFile the `.cmd` without a shell
 * (CVE-2024-27980), and routing the argv array through a shell mangles it: the
 * `.cmd`'s `%*` is re-tokenized by cmd.exe (splitting on spaces, breaking on
 * & | ^), and calling the shim by bare name from powershell.exe collapses the
 * whole array into a single space-joined argument. The exact locus differs by
 * runtime, so instead of hardening any one shell path we bypass shells entirely:
 * read the `.cmd` shim, recover the real program plus its fixed leading args,
 * and execFile that target directly with the argv array — verbatim, no shell.
 */
function resolveWindowsAgentBrowser(argv) {
  const dirs = String(process.env.PATH || "").split(path.delimiter);
  let cmdPath = null;
  for (const dir of dirs) {
    if (!dir) continue;
    const candidate = path.join(dir, "agent-browser.cmd");
    if (fs.existsSync(candidate)) {
      cmdPath = candidate;
      break;
    }
  }
  if (!cmdPath) return { file: "agent-browser", args: argv };
  const dir = path.dirname(cmdPath);
  const forwardLine =
    fs
      .readFileSync(cmdPath, "utf8")
      .split(/\r?\n/)
      .find((line) => line.includes("%*")) || "";
  const tokens = [...forwardLine.matchAll(/"([^"]*)"/g)]
    .map((m) => m[1])
    .map((t) =>
      t
        .replace(/%~dp0/gi, () => dir + path.sep)
        .replace(/%dp0%/gi, () => dir + path.sep)
    );
  const jsIndex = tokens.findIndex((t) => /\.[cm]?js$/i.test(t));
  if (jsIndex >= 0) {
    return { file: process.execPath, args: [...tokens.slice(jsIndex), ...argv] };
  }
  if (tokens.length > 0) {
    return { file: tokens[0], args: [...tokens.slice(1), ...argv] };
  }
  return { file: "agent-browser", args: argv };
}

/**
 * Build a shell-free invocation. POSIX runs the native `agent-browser` binary
 * directly; Windows resolves the npm `.cmd` shim to that native target so the
 * argument array is passed verbatim, never routed through cmd.exe/PowerShell.
 */
function buildAgentBrowserInvocation(port, args, platform = process.platform) {
  const argv = ["--cdp", String(port), ...args.map(String)];
  if (platform !== "win32") {
    return { file: "agent-browser", args: argv };
  }
  return resolveWindowsAgentBrowser(argv);
}

// ---------------------------------------------------------------------------
// agent-browser 工具函数
// ---------------------------------------------------------------------------

/**
 * 调用 agent-browser CLI
 * @param {number} port - CDP 端口
 * @param  {...string} args - agent-browser 参数
 * @returns {string} stdout（trim 后）
 *
 * 注意：导航请用 openWithRetry（eval 导航），不要直接调 ab(port, "open", url)
 * ——agent-browser 的 open 等待页面"稳定"，番茄等页面永不满足会挂起并阻塞
 * daemon。此处 open 分支保留超时放宽仅为防御性（无调用方）。
 */
function ab(port, ...args) {
  const invocation = buildAgentBrowserInvocation(port, args);
  const isOpen = args[0] === "open";
  try {
    return execFileSync(
      invocation.file,
      invocation.args,
      {
        encoding: "utf-8",
        timeout: isOpen ? 40000 : 20000,
        env: {
          ...process.env,
          AGENT_BROWSER_DEFAULT_TIMEOUT: isOpen
            ? "30000"
            : process.env.AGENT_BROWSER_DEFAULT_TIMEOUT || "25000",
        },
        stdio: ["pipe", "pipe", "pipe"],
        windowsHide: true,
      }
    ).trim();
  } catch (error) {
    const stderr = error && error.stderr ? String(error.stderr).trim() : "";
    const stdout = error && error.stdout ? String(error.stdout).trim() : "";
    const detail = stderr || stdout || (error && error.message) || "unknown error";
    // ENOENT = agent-browser 未安装，或 Windows 上 npm 因文件占用留下 .DELETE 残留
    // （真实 exe 缺失）。给出可执行修复路径，避免调用方（采集脚本/agent）自行猜。
    if (error && (error.code === "ENOENT" || error.errno === "ENOENT")) {
      const hint =
        process.platform === "win32"
          ? "agent-browser 可执行文件缺失（常见原因：npm 在 Windows 文件占用时留下 .DELETE 残留）。修复：先确认无 agent-browser 进程占用（tasklist | findstr agent-browser），再 npm uninstall -g agent-browser && npm install -g agent-browser"
          : "agent-browser 未安装或不在 PATH。修复：npm install -g agent-browser";
      throw new Error(`agent-browser failed: ${detail}\n${hint}`, { cause: error });
    }
    throw new Error(`agent-browser failed: ${detail}`, { cause: error });
  }
}

/** 等待 ms 毫秒（跨平台，不依赖系统 sleep 命令） */
function sleep(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

/**
 * 打开页面（导航）。
 *
 * 不用 agent-browser 的 open 命令：它会等待页面"稳定"（load + 无持续活动），
 * 番茄等平台页面有轮询/埋点/字体加载，永不满足 → 命令挂起；且 agent-browser
 * 有常驻 daemon，挂起的 open 会阻塞后续所有命令（实测：杀 CLI 不影响 daemon，
 * 后续 eval 全部排队挂起，必须杀 daemon 才能恢复）。
 * 改用 eval 导航（location.href 赋值）：立即返回、不等待页面——页面异步加载，
 * 由调用方的 sleep + 页面状态检查（probePage 等）兜底。
 * @param {number} port - CDP 端口
 * @param {string} url - 目标 URL
 * @param {number} [attempts=2] - 最大尝试次数（eval 失败率低，保留防御）
 */
function openWithRetry(port, url, attempts = 2) {
  let lastError = null;
  for (let i = 1; i <= attempts; i++) {
    try {
      return ab(port, "eval", `location.href=${JSON.stringify(url)}`);
    } catch (error) {
      lastError = error;
      if (i < attempts) {
        process.stderr.write(
          `  ⚠ 导航第 ${i} 次失败，重试: ${String(error.message || error).split("\n")[0]}\n`,
        );
        sleep(1000);
      }
    }
  }
  throw lastError;
}

function parseJSONResult(raw) {
  if (!raw || raw === "ERR") {
    throw new Error("agent-browser returned no JSON result");
  }
  try {
    let parsed = JSON.parse(raw);
    if (typeof parsed === "string") {
      try { parsed = JSON.parse(parsed); } catch {}
    }
    return parsed;
  } catch (error) {
    throw new Error(`agent-browser returned invalid JSON: ${String(raw).slice(0, 160)}`, {
      cause: error,
    });
  }
}

/**
 * 在浏览器内执行 JS，并解析 JSON 返回值。
 * 一律走 base64（-b）：正文提取用的 JS 常含引号、反斜杠等，作为命令行参数时在 Windows 上
 * 无法逐字透传（.cmd 的 %* 与 PowerShell 都会二次解析）。base64 让参数只含 [A-Za-z0-9+/=]，
 * 和各采集脚本已在用的 evalJSONBase64 走同一条安全通道。
 */
function evalJSON(port, js) {
  return evalJSONBase64(port, js);
}

/**
 * 通过 agent-browser 的 base64 参数执行复杂 JS，避免命令行转义和参数边界问题。
 */
function evalJSONBase64(port, js) {
  const encoded = Buffer.from(String(js), "utf8").toString("base64");
  return parseJSONResult(ab(port, "eval", "-b", encoded));
}

/**
 * 安全地将值插入浏览器 eval 字符串。
 * 使用 JSON.stringify 确保值不会因特殊字符（引号、反斜杠等）破坏 eval 字符串。
 * @param {*} val - 要插入的值
 * @returns {string} JSON 字符串表示（含引号）
 */
function safeStr(val) {
  return JSON.stringify(String(val));
}

/**
 * 滚动页面加载更多内容
 * @param {number} port - CDP 端口
 * @param {number} times - 滚动次数
 * @param {number} [interval=1000] - 每次滚动间隔（ms）
 */
function scrollLoad(port, times, interval = 1000) {
  for (let i = 0; i < times; i++) {
    ab(port, "eval", "window.scrollBy(0, window.innerHeight)");
    sleep(interval);
  }
}

/** 解析 --xxx 参数 */
function getArg(args, name) {
  const i = args.indexOf(name);
  if (i >= 0) return i + 1 < args.length ? args[i + 1] : null;
  const prefix = `${name}=`;
  const inline = args.find((arg) => String(arg).startsWith(prefix));
  return inline === undefined ? null : String(inline).slice(prefix.length);
}

/**
 * 解析 --xxx 整数参数并校验范围；非法值时打印错误并退出。
 * 防止传 `--top abc` 或 `--port 99999` 时静默产出空结果/错误端口。
 * @param {string} name - 参数名（不含 --）
 * @param {string|null|undefined} raw - getArg 的原始返回值
 * @param {number} def - 缺省值（raw 为空时）
 * @param {number} min - 最小值（含）
 * @param {number} max - 最大值（含）
 * @returns {number}
 */
function requireIntArg(name, raw, def, min, max) {
  const value = raw === null || raw === undefined || raw === "" ? def : Number(raw);
  if (!Number.isInteger(value) || value < min || value > max) {
    console.error(`错误：--${name} 必须是 ${min}-${max} 的整数，收到「${raw ?? "(空)"}」`);
    process.exit(1);
  }
  return value;
}

/**
 * 输出文件名用的日期戳（YYYYMMDD），一律取**本地日历日**。
 * 不能用 new Date().toISOString().slice(0,10)：那是 UTC 日期，比 UTC+8 晚 8 小时。
 * 文件名是各采集脚本唯一的去重键（一个榜单一天一份），北京时间 00:00-08:00 之间的采集
 * 会退回「昨天」的文件名，静默覆盖前一晚采到的同名报告，且这份数据被标成前一天。
 * @param {Date} [date] - 默认当前时间
 * @returns {string} YYYYMMDD
 */
function localDateStamp(date) {
  const d = date instanceof Date ? date : new Date();
  const y = String(d.getFullYear()).padStart(4, "0");
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}${m}${day}`;
}

/**
 * 报告头「抓取时间」用的本地时间戳（YYYY-MM-DDTHH:MM:SS）。
 * 与 localDateStamp 同源取本地时区，避免报告头日期与文件名日期在北京时间 00:00-08:00 相差一天。
 */
function localTimestamp(date) {
  const d = date instanceof Date ? date : new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  );
}

/**
 * Run a scraper entrypoint and turn empty/partial output into machine-readable
 * CLI status. Legacy entrypoints may return an integer; multi-target scrapers
 * return {planned,written,failed,partial,partialReasons}.
 */
function runCli(main, label) {
  Promise.resolve()
    .then(main)
    .then((result) => {
      const outcome = Number.isInteger(result)
        ? { planned: result, written: result, failed: 0, partial: false, partialReasons: [] }
        : result;
      if (!outcome || !Number.isInteger(outcome.written) || outcome.written < 1) {
        throw new Error("no output was written");
      }
      const failed = Number.isInteger(outcome.failed) ? outcome.failed : 0;
      const planned = Number.isInteger(outcome.planned)
        ? outcome.planned
        : outcome.written + failed;
      const reasons = Array.isArray(outcome.partialReasons)
        ? outcome.partialReasons.filter(Boolean).map(String)
        : [];
      if (outcome.partial || failed > 0) {
        const details = [`wrote ${outcome.written}/${planned}`];
        if (failed > 0) details.push(`failed ${failed}`);
        details.push(...reasons);
        console.error(`${label} partial: ${details.join("; ")}`);
        process.exitCode = 2;
      }
    })
    .catch((error) => {
      const message = error && error.message ? error.message : String(error);
      console.error(`${label} failed: ${message}`);
      process.exitCode = 1;
    });
}

module.exports = {
  ab,
  sleep,
  openWithRetry,
  evalJSON,
  evalJSONBase64,
  buildAgentBrowserInvocation,
  safeStr,
  scrollLoad,
  getArg,
  requireIntArg,
  localDateStamp,
  localTimestamp,
  runCli,
};

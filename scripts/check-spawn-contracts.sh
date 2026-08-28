#!/usr/bin/env bash
# check-spawn-contracts.sh — spawn 契约单一真源守卫（B74）
# 对 scripts/spawn-contracts.json 的注册表做三查：
#   ① 注册面完备：templates/agents/ 下 8 个 agent 模板与注册条目双向一一对应；
#   ② 调用面覆盖：每个 caller 文件存在且含 must_contain 锚文本；
#   ③ 必需参数覆盖：每个 caller 锚文本 ±30 行窗口内含该 caller 的全部 required_params
#      （caller 未声明覆盖时用 agent 级 required_params）——缺失即红（阻断语义：参数缺失=调用会失败）。
# 评级口径：设计评估（注册表=机检面）与 agent 模板「被调用协议」（文档面）互补不替代，两处都保留。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PYBIN=""
for candidate in python3 python py; do
  if "$candidate" -c "" >/dev/null 2>&1; then PYBIN="$candidate"; break; fi
done
[ -z "$PYBIN" ] && { echo "FAIL: no python interpreter found" >&2; exit 1; }

exec "$PYBIN" - "--root" "$REPO_ROOT" <<'PYEOF'
import io, json, sys
from pathlib import Path

root = Path(sys.argv[sys.argv.index("--root") + 1])
manifest = root / "scripts" / "spawn-contracts.json"
tpl_dir = root / "skills" / "moshu-setup" / "references" / "templates" / "agents"

data = json.loads(manifest.read_text(encoding="utf-8"))
agents = data["agents"]

errors = []

# ── 查 1：注册面完备（模板 ↔ 注册双向）─────────────────────────────
templates = sorted(p.name for p in tpl_dir.glob("*.md")) if tpl_dir.is_dir() else []
registered = sorted(a["name"] + ".md" for a in agents)
for t in templates:
    if t not in registered:
        errors.append(f"查1 模板未注册：{t}")
for r in registered:
    if r not in templates:
        errors.append(f"查1 注册无对应模板：{r}")
if len(agents) != len({a["name"] for a in agents}):
    errors.append("查1 注册条目存在重复 agent name")

_window = 30

def window_text(path: Path, anchor: str, span: int = _window):
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if anchor in line:
            return "\n".join(lines[max(0, i - span):min(len(lines), i + span + 1)])
    return None

# ── 查 2/查 3：调用面覆盖 + 必需参数覆盖 ─────────────────────────────
total_callers = 0
for agent in agents:
    name = agent["name"]
    agent_required = agent.get("required_params", [])
    seen_callers = set()
    for caller in agent.get("callers", []):
        total_callers += 1
        rel = caller["file"]
        anchor = caller["must_contain"]
        if (rel, anchor) in seen_callers:
            errors.append(f"查2 {name} caller 重复：{rel}::{anchor}")
        seen_callers.add((rel, anchor))
        path = root / rel
        if not path.is_file():
            errors.append(f"查2 {name} caller 文件缺失：{rel}")
            continue
        text = path.read_text(encoding="utf-8")
        if anchor not in text:
            errors.append(f"查2 {name} 锚文本缺失：{rel} 不含「{anchor}」")
            continue
        required = caller.get("required_params", agent_required)
        window = window_text(path, anchor, _window)
        missing = [p for p in required if p not in window]
        if missing:
            errors.append(
                f"查3 {name} @ {rel} 锚「{anchor}」±{_window} 行内缺必需参数：{missing}"
            )

# ── 汇总 ─────────────────────────────────────────────────────────────
print(f"spawn 契约守卫：{len(agents)} 个 agent / {total_callers} 个调用点 / 模板 {len(templates)} 份")
if errors:
    for e in errors:
        print("ERROR:", e)
    sys.exit(1)
print("spawn 契约守卫通过：注册完备 / 调用面覆盖 / 必需参数覆盖（±30 行窗口）")
PYEOF

#!/usr/bin/env bash
# check-agent-template-rules.sh — agent 模板纪律静态守卫
# 规则：禁互引（格式同/同上/参照上文/见上文）· 挂载点文件存在 · 共享纪律单副本（标题不得复制进模板）。
# 扫描逻辑在 scripts/check-agent-template-rules.py。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PYBIN=""
for candidate in python3 python py; do
  if "$candidate" -c "" >/dev/null 2>&1; then PYBIN="$candidate"; break; fi
done
[ -z "$PYBIN" ] && { echo "FAIL: no python interpreter found" >&2; exit 1; }

exec "$PYBIN" "$SCRIPT_DIR/check-agent-template-rules.py" --root "$REPO_ROOT"

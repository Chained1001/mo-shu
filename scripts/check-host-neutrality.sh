#!/bin/bash
# check-host-neutrality.sh — 宿主中性守卫（B76.6）：skills/ 除 moshu-setup 适配面外
# 禁 .claude 与 CLAUDE_PROJECT_DIR 字面量（宿主布局知识收敛于 moshu-setup 单一适配面）。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PYBIN=""
for candidate in python3 python py; do
  if "$candidate" -c "" >/dev/null 2>&1; then PYBIN="$candidate"; break; fi
done
[ -z "$PYBIN" ] && { echo "FAIL: no python interpreter found" >&2; exit 1; }

exec "$PYBIN" "$SCRIPT_DIR/check-host-neutrality.py" "${1:-$REPO_ROOT}"

#!/usr/bin/env bash
# check-agents-version-sync.sh — agents_version 一致性守卫
# agents_version 被 7 个 skill 的 SKILL.md 硬编码引用，升级漏改一处即误判降级。
# 本守卫以 moshu-setup/UPGRADING.md 顶部声明为权威，校验全部一致。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PYBIN=""
for candidate in python3 python py; do
  if "$candidate" -c "" >/dev/null 2>&1; then PYBIN="$candidate"; break; fi
done
[ -z "$PYBIN" ] && { echo "FAIL: no python interpreter found" >&2; exit 1; }

exec "$PYBIN" "$SCRIPT_DIR/check-agents-version-sync.py" --root "$REPO_ROOT"

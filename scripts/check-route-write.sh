#!/usr/bin/env bash
# check-route-write.sh — 路由残留守卫（批B8）
# 扫 skills/**/*.md 表格行中第二列=moshu-write 的行，语境两级判定：
# 构建域词（开书/开写/…）→ blocking 退出 1；写作域白名单 → 过；未知语境 → candidate 退出 0。
# 扫描逻辑在 scripts/check-route-write.py；词表与理由见该文件 BLOCKING_WORDS / WHITELIST_WORDS。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PYBIN=""
for candidate in python3 python py; do
  if "$candidate" -c "" >/dev/null 2>&1; then PYBIN="$candidate"; break; fi
done
[ -z "$PYBIN" ] && { echo "FAIL: no python interpreter found" >&2; exit 1; }

exec "$PYBIN" "$SCRIPT_DIR/check-route-write.py" --root "$REPO_ROOT"

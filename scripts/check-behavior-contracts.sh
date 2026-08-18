#!/usr/bin/env bash
# check-behavior-contracts.sh — 关键行为约束静态守卫
# mo-shu 是文档驱动的 skill 包：写作行为由 SKILL.md / workflow-*.md 的约束文本承载。
# 本守卫把最关键的行为承诺固化为静态检查，约束文本被误删/弱化即失败，防止迭代导致行为漂移。
# 契约清单：scripts/behavior-contracts.json；改动契约须同步 scripts/README.md 与 test-behavior-contracts.py。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PYBIN=""
for candidate in python3 python py; do
  if "$candidate" -c "" >/dev/null 2>&1; then PYBIN="$candidate"; break; fi
done
[ -z "$PYBIN" ] && { echo "FAIL: no python interpreter found" >&2; exit 1; }

exec "$PYBIN" "$SCRIPT_DIR/check-behavior-contracts.py" \
  --root "$REPO_ROOT" \
  --contracts "$SCRIPT_DIR/behavior-contracts.json"

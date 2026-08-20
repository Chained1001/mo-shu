#!/usr/bin/env bash
# check-story-numbers.sh — 叙述性 skill 计数静态守卫
# 枚举 skills/*/SKILL.md 得 N，校验 README/README_EN/CONTRIBUTING/scripts-README/architecture
# 中「N 个 skill」/「N skills」叙述与实测一致（CHANGELOG 排除，历史条目不可改）。
# 扫描逻辑在 scripts/check-story-numbers.py；白名单见该文件顶部 ALLOWED 常量。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PYBIN=""
for candidate in python3 python py; do
  if "$candidate" -c "" >/dev/null 2>&1; then PYBIN="$candidate"; break; fi
done
[ -z "$PYBIN" ] && { echo "FAIL: no python interpreter found" >&2; exit 1; }

exec "$PYBIN" "$SCRIPT_DIR/check-story-numbers.py" --root "$REPO_ROOT"

#!/bin/bash
# check-reference-closure.sh — 引用可达性守卫（批B4，方案 A 资产宇宙）
# 断言 skills/*/references/*.md 中「资产宇宙内」的文件名提及在其所属 skill 域内可达；
# 跨域合法提及走理由白名单（check-reference-closure.py 内 ALLOWED_CROSS_DOMAIN）。
# 与 static-check 互补：static-check 扫 Markdown 链接，本守卫扫文件名文本提及。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 跨平台解释器探测（Windows 裸调 python3 会落到 Store 占位程序 exit 49）
PYBIN=""
for candidate in python3 python py; do
  "$candidate" -c "" >/dev/null 2>&1 && { PYBIN="$candidate"; break; }
done
if [ -z "$PYBIN" ]; then
  echo "FAIL: 无可用 Python 解释器（试过 python3、python、py）" >&2
  exit 1
fi

exec "$PYBIN" "$SCRIPT_DIR/check-reference-closure.py" --root "$REPO_ROOT"

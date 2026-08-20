#!/bin/bash
# check-capability-wiring.sh — 能力接线守卫（审计-V3 D1）：断言 capability-wiring.json
# 里每个能力在全部 consumer 文件中的调用点标记在位。新增能力先登记本表；删除能力同步清表。
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

exec "$PYBIN" "$SCRIPT_DIR/check-capability-wiring.py" --root "$REPO_ROOT"

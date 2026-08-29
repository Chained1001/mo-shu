#!/bin/bash
# test-host-neutrality.sh — 宿主中性守卫回归（B76.6）
# 守护对象：check-host-neutrality 宿主中性守卫——三用例=本仓全绿/违规 fixture 红/白名单（moshu-setup 适配面）绿。
# 禁：断言实现细节/真实上游/脆弱快照；fixture 放 /.tmp/tests/B76.6/ 用完即删（scripts/README.md 测试纪律）。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GUARD="$SCRIPT_DIR/check-host-neutrality.sh"
FIX_ROOT="$REPO_ROOT/.tmp/tests/B76.6"

fails=0

# ① 本仓全绿
if bash "$GUARD" >/dev/null 2>&1; then
  echo "[PASS] 本仓全绿"
else
  echo "[FAIL] 本仓守卫红（宿主字面量残留？）"
  bash "$GUARD" 2>&1 | tail -5
  fails=$((fails+1))
fi

# ② 违规 fixture 红：假技能文件含 .claude/agents/x.md
rm -rf "$FIX_ROOT"
mkdir -p "$FIX_ROOT/skills/moshu-fake/references"
echo '检查 `.claude/agents/moshu-x.md` 是否存在。' > "$FIX_ROOT/skills/moshu-fake/references/bad.md"
if bash "$GUARD" "$FIX_ROOT" >/dev/null 2>&1; then
  echo "[FAIL] 违规 fixture 应红却绿"
  fails=$((fails+1))
else
  echo "[PASS] 违规 fixture 红"
fi

# ③ 白名单绿：同一违规内容放 moshu-setup 适配面布局 → 绿（先清用例②的违规文件，独立验证豁免）
rm -rf "$FIX_ROOT/skills/moshu-fake"
mkdir -p "$FIX_ROOT/skills/moshu-setup/references/agent-references"
echo '检查 `.claude/agents/moshu-x.md` 是否存在。' > "$FIX_ROOT/skills/moshu-setup/references/agent-references/ok.md"
if bash "$GUARD" "$FIX_ROOT" >/dev/null 2>&1; then
  echo "[PASS] 白名单（moshu-setup 适配面）绿"
else
  echo "[FAIL] 白名单文件应豁免却红"
  bash "$GUARD" "$FIX_ROOT" 2>&1 | tail -5
  fails=$((fails+1))
fi

# 清理
rm -rf "$FIX_ROOT"

if [ "$fails" -ne 0 ]; then
  echo "Host-neutrality tests FAILED ($fails)."
  exit 1
fi
echo "Host-neutrality regression tests passed (3 cases)."

#!/bin/bash
# eval-prose-quality.sh — 端到端正文质量评测（确定性检测器 × 基准样本）
# 用途：检测器或写作方法论改动后，跑本脚本确认端到端质量基准没有翻转。
# 基准：evals/samples/prose-ai-flavored.md（缺陷样本）的总命中数必须显著高于
#       prose-clean.md（干净样本），且缺陷样本 blocking > 0。
# 用法：bash scripts/eval-prose-quality.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AI="$ROOT/skills/moshu-write/scripts/check-ai-patterns.js"
DEG="$ROOT/skills/moshu-write/scripts/check-degeneration.js"
SAMPLES="$ROOT/evals/samples"

# 解析检测器 --json 输出：打印 "blocking advisory"（无命中或解析失败 = "0 0"）
counts() {
  local js="$1"
  python3 - "$js" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1], encoding='utf-8'))
    f = d.get('findings', []) if isinstance(d, dict) else d
    b = sum(1 for x in f if x.get('severity') == 'blocking')
    a = sum(1 for x in f if x.get('severity') == 'advisory')
    print(b, a)
except Exception:
    print(0, 0)
PY
}

score_file() {
  # $1 = sample path ; prints "ai_b ai_a deg_b deg_a"
  local f="$1" ai_json deg_json ai_b ai_a deg_b deg_a
  ai_json="$(mktemp)"; deg_json="$(mktemp)"
  node "$AI" --check --json "$f" >"$ai_json" 2>/dev/null || true
  node "$DEG" --check --json "$f" >"$deg_json" 2>/dev/null || true
  read -r ai_b ai_a <<<"$(counts "$ai_json")"
  read -r deg_b deg_a <<<"$(counts "$deg_json")"
  rm -f "$ai_json" "$deg_json"
  printf '%s %s %s %s' "$ai_b" "$ai_a" "$deg_b" "$deg_a"
}

printf '%-28s %8s %8s %8s %8s %8s\n' '样本' 'AI-block' 'AI-adv' 'Deg-block' 'Deg-adv' '合计'
FLAV="$SAMPLES/prose-ai-flavored.md"
CLEAN="$SAMPLES/prose-clean.md"

read -r f_b f_a fd_b fd_a <<<"$(score_file "$FLAV")"
read -r c_b c_a cd_b cd_a <<<"$(score_file "$CLEAN")"
f_total=$((f_b + f_a + fd_b + fd_a))
c_total=$((c_b + c_a + cd_b + cd_a))

printf '%-28s %8d %8d %8d %8d %8d\n' "$(basename "$FLAV")" "$f_b" "$f_a" "$fd_b" "$fd_a" "$f_total"
printf '%-28s %8d %8d %8d %8d %8d\n' "$(basename "$CLEAN")" "$c_b" "$c_a" "$cd_b" "$cd_a" "$c_total"

FAIL=0
[ "$f_b" -gt 0 ] || { echo "FAIL: 缺陷样本必须至少 1 条 blocking 命中（检测器未生效或样本退化）"; FAIL=1; }
[ "$f_total" -gt "$c_total" ] || { echo "FAIL: 缺陷样本总命中（$f_total）未显著高于干净样本（$c_total）"; FAIL=1; }
# 干净样本 blocking 应为 0（blocking 规则要求真人语料命中 ≈0）
[ "$c_b" -eq 0 ] || { echo "FAIL: 干净样本出现 blocking 命中（$c_b 条）——检测器误伤自然表达"; FAIL=1; }

if [ "$FAIL" = 0 ]; then
  echo "PASS: 端到端质量基准成立（缺陷 $f_total > 干净 $c_total，干净 blocking=0）"
else
  echo "FAIL: 端到端质量基准翻转，检查最近检测器/方法论改动"
fi
exit $FAIL

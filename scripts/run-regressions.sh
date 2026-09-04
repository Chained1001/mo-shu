#!/usr/bin/env bash
# run-regressions.sh —— 本地一键全跑 CI 回归面（审计四期立案一收口，B98）
#
# 定位声明（B98 规格 B1）：本地全跑 CI 回归面的一次性入口，**不进 CI**——
# CI 保持枚举步骤不变（改 CI 为 wrapper 属另一批决策，见规格设计说明 #12）。
# 守护对象：审计四期 C2「本地验收面与 CI 回归面漂移」收口——B94-B96 本地只跑
# 守卫（check-*）没跑 test-* 回归套件导致 CI 首红（7f99404 教训）。
#
# 跑法：三类 glob——
#   scripts/test-*.py + scripts/test_*.py  python 探测链 python3→python→py（-X utf8 + PYTHONIOENCODING）
#   scripts/test-*.sh                      bash
#   scripts/test-*.js                      node（缺失时显式报缺，不静默跳过）
#
# 防假绿内建（审计法 grep 三陷阱 v1.8 + 盲区 #15）：
#   逐项打印「[i/N] 文件 … exit=码」；不得 2>/dev/null 吞 stderr（stderr 透传）；
#   任一失败 exit 1（含 node 缺失——报缺即失败，不静默）。
#
# SKIP 清单：文件顶部显式数组+每项一行原因注释；跳过项在汇总显式列出，禁止静默扩。
# step 0 内嵌 PRD 轻量 lint（C4/C6 降级版，作者裁定 2026-09-01）：grep PRD 退役词，
# 排除历史版本行（v2. 前缀）与迁移注记行（含「收口/退役/已删」）。轻量 lint 非独立
# 守卫（C4 三次辗转降级裁定 2026-09-01）——不进 CI、不配自举回归。

set -u

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$(cd "$(dirname "$0")/.." && pwd)")"
cd "$REPO_ROOT" || { echo "FATAL: 无法进入仓库根 $REPO_ROOT"; exit 2; }

# ---------- SKIP 清单（显式+带原因，新增须带原因） ----------
SKIP=(
  "test-shared-assets.py|mode-drift Windows chmod 假红（审计法 v1.3 平台假红清单第二类），CI Linux 为准"
)

# ---------- python 探测链 ----------
detect_python() {
  for cand in python3 python py; do
    if command -v "$cand" >/dev/null 2>&1; then
      # 验证可执行（py 可能是 Windows 启动器，-3 才稳定）
      if [ "$cand" = "py" ]; then
        "$cand" -3 -c "" >/dev/null 2>&1 && { echo "$cand -3"; return; }
      else
        "$cand" -c "" >/dev/null 2>&1 && { echo "$cand"; return; }
      fi
    fi
  done
  echo ""
}

PYBIN="$(detect_python)"
if [ -z "$PYBIN" ]; then
  echo "FATAL: 未找到可用 python（python3→python→py -3 全缺）——python 类 test 全部无法运行。"
  exit 2
fi
echo "python 探测链命中: $PYBIN"
echo

# ---------- 收集测试文件 ----------
tests=()
for f in scripts/test-*.py scripts/test_*.py; do
  [ -f "$f" ] && tests+=("$f")
done
for f in scripts/test-*.sh; do
  [ -f "$f" ] && tests+=("$f")
done
for f in scripts/test-*.js; do
  [ -f "$f" ] && tests+=("$f")
done

total="${#tests[@]}"
passed=0
failed=0
skipped=0
failures=""

echo "========== run-regressions.sh（本地回归全跑） =========="
echo "共 $total 个 test 文件（SKIP 清单 $(( ${#SKIP[@]} )) 项）"
echo

# ---------- step 0：PRD lint 已退役（2026-09-04 作者裁定 PRD 归档——lint 使命终结；原逻辑因归档静默假绿，故整段移除） ----------

# ---------- 逐项跑 ----------
i=0
for f in "${tests[@]}"; do
  i=$((i + 1))
  name="$(basename "$f")"

  # SKIP 判断
  skip_reason=""
  for entry in "${SKIP[@]}"; do
    sname="${entry%%|*}"
    reason="${entry#*|}"
    if [ "$name" = "$sname" ]; then
      skip_reason="$reason"
      break
    fi
  done

  if [ -n "$skip_reason" ]; then
    echo "[$i/$total] $name — SKIP（$skip_reason）"
    skipped=$((skipped + 1))
    continue
  fi

  case "$f" in
    *.py)
      # shellcheck disable=SC2086
      PYTHONIOENCODING=utf-8 $PYBIN -X utf8 "$f"
      rc=$?
      ;;
    *.sh)
      bash "$f"
      rc=$?
      ;;
    *.js)
      if command -v node >/dev/null 2>&1; then
        node "$f"
        rc=$?
      else
        echo "[$i/$total] $name — FAIL（node 缺失，未静默跳过）"
        failed=$((failed + 1))
        failures="$failures
  $name: node 缺失"
        continue
      fi
      ;;
  esac

  if [ "$rc" -eq 0 ]; then
    echo "[$i/$total] $name … exit=$rc ✓"
    passed=$((passed + 1))
  else
    echo "[$i/$total] $name … exit=$rc ✗"
    failed=$((failed + 1))
    failures="$failures
  $name: exit=$rc"
  fi
done

# ---------- 守卫段（check-*，立案一余波 B99②：本地一键=CI 的 test 面+守卫面双覆盖） ----------
echo
echo "---------- 守卫段（check-*） ----------"
check_total=0
check_passed=0
check_failed=0
check_skipped=0
check_failures=""

# 逐项 glob scripts/check-*.sh（与 CI static-guards job 对齐；check-*.py 由 .sh 包装调用）
for f in scripts/check-*.sh; do
  [ -f "$f" ] || continue
  check_total=$((check_total + 1))
  name="$(basename "$f")"

  # SKIP 判断（沿用同一 SKIP 清单——test-shared-assets 的 mode-drift 类 Windows 假红按审计法 v1.3 记原因）
  skip_reason=""
  for entry in "${SKIP[@]}"; do
    sname="${entry%%|*}"
    reason="${entry#*|}"
    if [ "$name" = "$sname" ]; then
      skip_reason="$reason"
      break
    fi
  done

  if [ -n "$skip_reason" ]; then
    echo "[$check_total/${#tests[@]}+$check_total] $name — SKIP（$skip_reason）"
    check_skipped=$((check_skipped + 1))
    continue
  fi

  bash "$f" >/tmp/guard_$name.out 2>&1
  rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "[guard $check_total] $name … exit=$rc ✓"
    check_passed=$((check_passed + 1))
  else
    echo "[guard $check_total] $name … exit=$rc ✗"
    tail -5 "/tmp/guard_$name.out"
    check_failed=$((check_failed + 1))
    check_failures="$check_failures
  $name: exit=$rc"
  fi
done

# 收编 .py 直跑守卫（无 .sh 包装、CI static-guards 直调者——消本地/CI 验收面漂移，B107 CI 红判因）
# 清单维护纪律：CI static-guards 新增直调 .py 守卫时同批在此登记（与 8.1 三处同步同性质）。
for f in scripts/check-methodology-wiring.py; do
  [ -f "$f" ] || continue
  check_total=$((check_total + 1))
  name="$(basename "$f")"
  python "$f" >/tmp/guard_$name.out 2>&1
  rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "[guard $check_total] $name … exit=$rc ✓"
    check_passed=$((check_passed + 1))
  else
    echo "[guard $check_total] $name … exit=$rc ✗"
    tail -5 "/tmp/guard_$name.out"
    check_failed=$((check_failed + 1))
    check_failures="$check_failures
  $name: exit=$rc"
  fi
done

# ---------- 汇总 ----------
echo
echo "========== 汇总 =========="
echo "test 段: 总数 $total | 通过 $passed | 失败 $failed | 跳过 $skipped"
echo "守卫段: 总数 $check_total | 通过 $check_passed | 失败 $check_failed | 跳过 $check_skipped"
if [ "$skipped" -gt 0 ] || [ "$check_skipped" -gt 0 ]; then
  echo "跳过项（显式清单）："
  for entry in "${SKIP[@]}"; do
    echo "  - ${entry%%|*}：${entry#*|}"
  done
fi
if [ -n "$failures" ] || [ -n "$check_failures" ]; then
  [ -n "$failures" ] && echo "test 失败清单：$failures"
  [ -n "$check_failures" ] && echo "守卫失败清单：$check_failures"
  exit 1
fi
echo "全部通过（exit 0）"
exit 0

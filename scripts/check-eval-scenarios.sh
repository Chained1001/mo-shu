#!/bin/bash
# check-eval-scenarios.sh — 场景剧本静态校验（不跑 LLM）
# 校验：3 个剧本 README 存在且非空；各含「断言」节；各含 ≥3 条 [机检] 标记；
# 剧本内引用的仓库脚本路径（scripts/ 或 skills/ 开头）必须存在。
# CI 只做静态校验——场景剧本是人工走查物，不在 CI 跑 LLM。
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$REPO_ROOT" ]; then
  echo "Error: not in a git repository"
  exit 1
fi

SCENARIOS=("日更一章" "开书" "审查工单")
failures=0

for scenario in "${SCENARIOS[@]}"; do
  readme="$REPO_ROOT/evals/scenarios/$scenario/README.md"
  if [ ! -f "$readme" ]; then
    echo "FAIL: evals/scenarios/$scenario/README.md 缺失"
    failures=$((failures + 1))
    continue
  fi
  if [ ! -s "$readme" ]; then
    echo "FAIL: evals/scenarios/$scenario/README.md 为空"
    failures=$((failures + 1))
    continue
  fi
  if ! grep -q '^## 断言' "$readme"; then
    echo "FAIL: evals/scenarios/$scenario/README.md 缺「## 断言」节"
    failures=$((failures + 1))
  fi
  machine_count="$(grep -c '\[机检\]' "$readme" || true)"
  if [ "$machine_count" -lt 3 ]; then
    echo "FAIL: evals/scenarios/$scenario/README.md 机检项不足 3 条（实测 $machine_count）"
    failures=$((failures + 1))
  fi
  while IFS= read -r ref; do
    [ -n "$ref" ] || continue
    if [ ! -e "$REPO_ROOT/$ref" ]; then
      echo "FAIL: evals/scenarios/$scenario/README.md 引用路径不存在: $ref"
      failures=$((failures + 1))
    fi
  done < <(grep -oE '(scripts|skills)/[A-Za-z0-9_./-]+' "$readme" | sort -u)
done

if [ "$failures" -gt 0 ]; then
  echo "eval scenarios: FAIL ($failures)"
  exit 1
fi
echo "eval scenarios: ok (${#SCENARIOS[@]} scenarios)"

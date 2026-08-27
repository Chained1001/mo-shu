#!/bin/bash
# test-writing-pipeline.sh — 零 LLM 管道契约 e2e（正式回归，非临时验证）
# 守护对象：写作→追踪→卷报告→审查工单→候选机检的确定性管道契约。禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。
# 串链：init → commit（伏笔+信息差）→ check（含 suspension_warnings）→
#       volume-report（重放 diff 为空）→ review_tickets write/resolve/list → check-prose-candidates（blocking_count=0）
# fixture 全在临时目录，trap 自清理，不留工作区残留。
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TRACKING_TOOL="$REPO_ROOT/skills/moshu-write/scripts/tracking_commit.py"
TICKETS_TOOL="$REPO_ROOT/skills/moshu-review/scripts/review_tickets.py"
PROSE_TOOL="$REPO_ROOT/skills/moshu-write/scripts/check-prose-candidates.js"

PYBIN=""
for candidate in python3 python py; do
  if "$candidate" -c "" >/dev/null 2>&1; then PYBIN="$candidate"; break; fi
done
[ -n "$PYBIN" ] || { echo "FAIL: no python interpreter found"; exit 1; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
PROJECT="$WORK/book"
mkdir -p "$PROJECT/正文" "$PROJECT/大纲"

fail() {
  echo "FAIL: $1"
  exit 1
}

# ---------- 1. init（schema_version=2，信息差域可选） ----------
cat > "$WORK/init.json" <<'EOF'
{
  "schema_version": 2,
  "book_title": "管道契约测试书",
  "last_chapter": 0,
  "context": {
    "position": {"volume": "第一卷·试炼", "volume_start_chapter": 1, "story_time": "入营第一天", "scene": "训练场"},
    "long_term_constraints": [],
    "active_character_names": [],
    "continuity_risks": [],
    "recent_chapters": [],
    "next_chapter_commitments": []
  },
  "character_snapshots": {},
  "foreshadow": [],
  "timeline_events": [],
  "information_gaps": []
}
EOF
"$PYBIN" "$TRACKING_TOOL" init --project "$PROJECT" --input "$WORK/init.json" >/dev/null 2>&1 || fail "tracking init"

# ---------- 2. commit（一章：伏笔 1 条 + 信息差 1 条） ----------
cat > "$WORK/commit.json" <<'EOF'
{
  "schema_version": 2,
  "mode": "append",
  "chapter": 1,
  "chapter_title": "初入试炼",
  "expected_state_revision": 0,
  "delta": {
    "result": "主角踏入训练场，测试伏笔与信息差登记。",
    "character_changes": [],
    "foreshadow_changes": [
      {"action": "upsert", "id": "F001", "summary": "训练场地下的秘密。", "planted_chapter": 1, "planned_resolution_chapter": 5, "status": "已埋", "importance": "中"}
    ],
    "information_gap_changes": [
      {"action": "register", "id": "G001", "knowers": ["主角"], "reader_known": "未知", "keywords": ["秘宝"], "status": "登记", "note": "主角知道秘宝存在，读者不知道。"}
    ],
    "timeline_events": [],
    "constraints": [],
    "next_chapter_commitments": ["推进训练。"]
  },
  "context": {
    "position": {"volume": "第一卷·试炼", "volume_start_chapter": 1, "story_time": "入营第一天", "scene": "训练场"},
    "long_term_constraints": [],
    "active_character_names": [],
    "continuity_risks": []
  },
  "character_snapshots": {}
}
EOF
"$PYBIN" "$TRACKING_TOOL" commit --project "$PROJECT" --input "$WORK/commit.json" >/dev/null 2>&1 || fail "tracking commit"
STATE="$PROJECT/追踪/_tracking-state.json"
SCHEMA_V="$("$PYBIN" -c 'import os,sys; sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[1]))); import tracking_commit as t; print(t.TRACKING_SCHEMA_VERSION)' "$TRACKING_TOOL")"
grep -q "\"schema_version\": $SCHEMA_V" "$STATE" || fail "state schema_version != $SCHEMA_V（版本无关断言，随工具常量）"
grep -q '"last_committed_chapter": 1' "$STATE" || fail "last_committed_chapter != 1"

# ---------- 3. check（含 suspension_warnings 候选字段） ----------
CHECK_OUT="$("$PYBIN" "$TRACKING_TOOL" check --project "$PROJECT" 2>/dev/null)" || fail "tracking check"
echo "$CHECK_OUT" | grep -q '"last_committed_chapter": 1' || fail "check 输出缺 last_committed_chapter"
echo "$CHECK_OUT" | grep -q '"suspension_warnings"' || fail "check 输出缺 suspension_warnings"

# ---------- 4. volume-report（确定性重放） ----------
"$PYBIN" "$TRACKING_TOOL" volume-report --project "$PROJECT" --from-chapter 1 --to-chapter 1 >/dev/null 2>&1 || fail "volume-report"
REPORT="$PROJECT/追踪/卷报告_第1-1章.md"
[ -s "$REPORT" ] || fail "volume-report 产物为空"
cp "$REPORT" "$WORK/report-first.md"
"$PYBIN" "$TRACKING_TOOL" volume-report --project "$PROJECT" --from-chapter 1 --to-chapter 1 >/dev/null 2>&1 || fail "volume-report 重跑"
diff -q "$WORK/report-first.md" "$REPORT" >/dev/null || fail "volume-report 重放不一致"

# ---------- 5. review_tickets write/resolve/list ----------
cat > "$WORK/findings.json" <<'EOF'
{
  "schema_version": 2,
  "chapter_range": [1, 1],
  "review_token": "p1pe8tok",
  "findings": [
    {"id": "T001", "severity": "blocking", "dimension": "consistency", "evidence": "第1章 训练场", "suggestion": "统一设定", "status": "open", "status_note": ""},
    {"id": "T002", "severity": "candidate", "dimension": "prose", "evidence": "第1章 第2段", "suggestion": "微调节奏", "status": "open", "status_note": ""}
  ]
}
EOF
"$PYBIN" "$TICKETS_TOOL" write --project "$PROJECT" --input "$WORK/findings.json" >/dev/null 2>&1 || fail "tickets write"
TICKET_FILE="$(ls "$PROJECT/.moshu-review/tickets/"tickets_*.json 2>/dev/null | head -1)"
[ -n "$TICKET_FILE" ] || fail "tickets write 未生成工单文件"
"$PYBIN" "$TICKETS_TOOL" resolve --project "$PROJECT" --ticket "$TICKET_FILE" --id T001 --status fixed --note "已按统一设定修复。" >/dev/null 2>&1 || fail "tickets resolve"
OPEN_LIST="$("$PYBIN" "$TICKETS_TOOL" list --project "$PROJECT" --status open 2>/dev/null)" || fail "tickets list"
echo "$OPEN_LIST" | grep -q '"id": "T002"' || fail "list open 应只剩 candidate T002"
echo "$OPEN_LIST" | grep -q '"id": "T001"' && fail "list open 不应含已 fixed 的 T001"

# ---------- 6. check-prose-candidates（blocking_count 恒 0，候选不拦截） ----------
cat > "$WORK/prose.md" <<'EOF'
他走进训练场，看见老槐树下的石桌。午后阳光穿过枝叶，落下一地斑驳。

他坐下，翻开那本旧书，读了很久。
EOF
PROSE_OUT="$(node "$PROSE_TOOL" --prose "$WORK/prose.md" --json 2>/dev/null)" || fail "check-prose-candidates"
echo "$PROSE_OUT" | grep -q '"blocking_count": 0' || fail "check-prose-candidates blocking_count != 0"

echo "OK: writing pipeline (init→commit→check→volume-report→tickets→prose-candidates)"

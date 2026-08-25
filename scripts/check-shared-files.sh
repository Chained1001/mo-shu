#!/bin/bash
# check-shared-files.sh — 检查跨 skill 同名文件内容一致性
# 扫描所有 skill 的 references/ 与 scripts/ 目录，找出同名文件并比较内容
# 兼容 bash 3+（macOS）
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$REPO_ROOT" ]; then
  echo "Error: not in a git repository"
  exit 1
fi

SKILLS_DIR="$REPO_ROOT/skills"
if [ ! -d "$SKILLS_DIR" ]; then
  echo "Error: skills/ not found at $SKILLS_DIR"
  exit 1
fi

# Known intentional differences (basename): these files are expected to differ across skills.
# After the short-form skills were removed, some entries below are harmless no-ops (single
# copy or no copy at all) kept to avoid churn in the guard config.
# - output-templates.md / material-decomposition.md: single-copy (moshu-analyze).
# - genre-catalog.md / genre-readers.md: previously ignored for a historical analyst-lens
#   fork; copies are now byte-identical and registered in shared-assets.json — no longer ignored.
# - quality-checklist.md: previously split writer/reviewer copies; since audit P0 it is a
#   single canonical copy (moshu-write) registered in shared-assets.json — no longer ignored.
IGNORE_NAMES="output-templates.md material-decomposition.md"

# Genre-style-divergent (basename): drop the references/genre-styles/ fork copy (if any);
# the remaining prose-card copies must stay byte-identical.
GENRE_STYLE_DIVERGENT_NAMES="双男主.md"

# （审计-V3 PM9：emotional-methods.md 已收敛为单副本——agent-references/reader-contract
# 已存在，原白名单理由失效；该文件现已登记 shared-assets.json 并字节一致，不再豁免）
LONGFORM_DIVERGENT_NAMES=""

mismatches=0
checked=0

echo "Shared File Consistency Check"
echo "=============================="

# Only inspect repository content plus non-ignored additions. Runtime state such
# as **/.omc/ may live below references/ on a developer machine, but it is not a
# skill asset and must not make this guard disagree with a clean CI checkout.
list_asset_files() {
  local asset_dir="$1"
  git -C "$REPO_ROOT" ls-files -z --cached --others --exclude-standard -- skills |
    while IFS= read -r -d '' rel_path; do
      [ -f "$REPO_ROOT/$rel_path" ] || continue
      case "$rel_path" in
        skills/*/"$asset_dir"/*) printf '%s\n' "$REPO_ROOT/$rel_path" ;;
      esac
    done
}

REFERENCE_FILES="$(list_asset_files references)"
PYTHON_BIN=""
for candidate in python3 python py; do
  if "$candidate" -c "" >/dev/null 2>&1; then
    PYTHON_BIN="$candidate"
    break
  fi
done
if [ -z "$PYTHON_BIN" ]; then
  echo "FAIL: Python 3 is required (tried python3, python, and py)" >&2
  exit 1
fi
"$PYTHON_BIN" "$REPO_ROOT/scripts/sync-shared-assets.py" check

list_reference_basenames() {
  local path
  while IFS= read -r path; do
    case "$path" in
      # .gitkeep 是目录占位符，不算共享内容文件（2026-08-25 注记：skills/ 内占位符已清，
      # 豁免保留以兼容 otherMaterials/referProject/ 等目录的既有 .gitkeep——F8 审核注记）
      */.gitkeep) ;;
      *) printf '%s\n' "${path##*/}" ;;
    esac
  done <<< "$REFERENCE_FILES"
}

# Find all reference basenames that appear in 2+ skills
dup_names="$(list_reference_basenames | sort | uniq -d)"

for base in $dup_names; do
  # Skip known intentional differences
  skip=false
  for ignore in $IGNORE_NAMES; do
    if [ "$base" = "$ignore" ]; then
      skip=true
      break
    fi
  done
  if [ "$skip" = true ]; then
    continue
  fi
  # Collect all paths for this basename
  paths=()
  while IFS= read -r fpath; do
    [ -z "$fpath" ] && continue
    [ "${fpath##*/}" = "$base" ] && paths+=("$fpath")
  done <<< "$REFERENCE_FILES"

  # Genre-style-divergent basenames: drop the references/genre-styles/ fork copy (if any);
  # the remaining prose-card copies must still be byte-identical.
  case " $GENRE_STYLE_DIVERGENT_NAMES " in
    *" $base "*)
      filtered=()
      for p in ${paths[@]+"${paths[@]}"}; do
        case "$p" in
          */genre-styles/*) ;;
          *) filtered+=("$p") ;;
        esac
      done
      paths=(${filtered[@]+"${filtered[@]}"})
      ;;
  esac

  # Longform-divergent basenames: drop the moshu-write copy (intentional
  # long-form-only fork); the remaining copies must still be byte-identical.
  case " $LONGFORM_DIVERGENT_NAMES " in
    *" $base "*)
      filtered=()
      for p in ${paths[@]+"${paths[@]}"}; do
        case "$p" in
          */moshu-write/*) ;;
          *) filtered+=("$p") ;;
        esac
      done
      paths=(${filtered[@]+"${filtered[@]}"})
      ;;
  esac

  if [ ${#paths[@]} -lt 2 ]; then
    continue
  fi

  checked=$((checked + 1))
  ref_path="${paths[0]}"
  ref_skill="$(echo "$ref_path" | sed "s|$SKILLS_DIR/||" | cut -d'/' -f1)"
  all_match=true

  for ((i = 1; i < ${#paths[@]}; i++)); do
    if ! diff -q "$ref_path" "${paths[$i]}" >/dev/null 2>&1; then
      skill_name="$(echo "${paths[$i]}" | sed "s|$SKILLS_DIR/||" | cut -d'/' -f1)"
      if [ "$all_match" = true ]; then
        echo ""
        echo "MISMATCH: $base"
        echo "  Reference: $ref_skill"
      fi
      echo "  Differs in: $skill_name"
      all_match=false
      mismatches=$((mismatches + 1))
    fi
  done
done

echo ""
echo "=============================="
echo "Reference groups checked: $checked | Mismatches: $mismatches"

if [ "$mismatches" -gt 0 ]; then
  echo ""
  echo "NOTE: Some mismatches may be intentional (skill-specific customizations)."
  echo "      Review each case before syncing."
  exit 1
fi

echo "All shared files are consistent."

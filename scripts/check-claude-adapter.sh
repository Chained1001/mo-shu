#!/usr/bin/env bash
# check-claude-adapter.sh — Claude Code marketplace/plugin compatibility checks.
# Static by default; set CLAUDE_REAL_CHECK=1 to invoke the installed Claude CLI.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MARKETPLACE="$REPO_ROOT/.claude-plugin/marketplace.json"
# Derive the expected plugin count from the marketplace itself instead of
# hard-coding it: adding/removing a skill must not require editing this script.
EXPECTED_COUNT=$(python3 -c "import json,sys; print(len(json.load(open(sys.argv[1], encoding='utf-8'))['plugins']))" "$MARKETPLACE")

fail() { echo "FAIL: $*" >&2; exit 1; }

echo "Claude Code adapter check"
echo "========================="
echo "Repo: $REPO_ROOT"

python3 - "$MARKETPLACE" "$REPO_ROOT" "$EXPECTED_COUNT" <<'PY'
import json
import re
import sys
from pathlib import Path

marketplace_path = Path(sys.argv[1])
repo_root = Path(sys.argv[2])
expected_count = int(sys.argv[3])

data = json.loads(marketplace_path.read_text(encoding="utf-8"))
plugins = data.get("plugins")
if not isinstance(plugins, list):
    raise SystemExit("FAIL: marketplace plugins must be an array")
if len(plugins) != expected_count:
    raise SystemExit(
        f"FAIL: expected {expected_count} marketplace plugins, found {len(plugins)}"
    )

expected = {path.parent.name for path in (repo_root / "skills").glob("*/SKILL.md")}
found: set[str] = set()
for plugin in plugins:
    if not isinstance(plugin, dict):
        raise SystemExit("FAIL: every marketplace plugin must be an object")
    name = plugin.get("name")
    description = plugin.get("description")
    source = plugin.get("source")
    skills = plugin.get("skills")
    version = plugin.get("version")
    if not isinstance(name, str) or not name:
        raise SystemExit("FAIL: marketplace plugin is missing name")
    if name in found:
        raise SystemExit(f"FAIL: duplicate marketplace plugin: {name}")
    if not isinstance(description, str) or not description:
        raise SystemExit(f"FAIL: {name}: missing description")
    if source != "./":
        raise SystemExit(f"FAIL: {name}: source must be './', got {source!r}")
    if skills != [f"./skills/{name}"]:
        raise SystemExit(
            f"FAIL: {name}: skills must contain only './skills/{name}', got {skills!r}"
        )
    skill_md = repo_root / "skills" / name / "SKILL.md"
    if not skill_md.is_file():
        raise SystemExit(f"FAIL: {name}: referenced SKILL.md does not exist")
    # version 必须与 SKILL.md frontmatter 一致（审计-V3 G1-b：此前只校验映射不比版本，
    # 导致 release-prep bump SKILL.md 后 marketplace 三处滞后且 CI 无感）
    if not isinstance(version, str) or not version:
        raise SystemExit(f"FAIL: {name}: missing version")
    frontmatter = skill_md.read_text(encoding="utf-8").split("---")[1]
    declared = re.search(r"^version:\s*(\S+)\s*$", frontmatter, re.MULTILINE)
    if declared is None:
        raise SystemExit(f"FAIL: {name}: SKILL.md frontmatter has no version field")
    if declared.group(1) != version:
        raise SystemExit(
            f"FAIL: {name}: marketplace version {version!r} != SKILL.md version {declared.group(1)!r}"
        )
    found.add(name)

if found != expected:
    missing = sorted(expected - found)
    extra = sorted(found - expected)
    raise SystemExit(f"FAIL: marketplace/skills mismatch; missing={missing}, extra={extra}")

print(f"  OK marketplace maps all {len(found)} skills exactly once (name+skills+version 与 SKILL.md 一致)")
PY

if [ "${CLAUDE_REAL_CHECK:-0}" = "1" ]; then
  command -v claude >/dev/null 2>&1 \
    || fail "CLAUDE_REAL_CHECK=1 but claude is not on PATH"
  TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/ohstory-claude-check.XXXXXX")"
  trap 'rm -rf "$TMP_DIR"' EXIT
  echo "  Claude: $(claude --version)"

  # Marketplace validation alone does not validate component frontmatter. Build
  # one synthetic plugin containing every skill so the official CLI parses all
  # SKILL.md files in a single strict validation pass.
  mkdir -p "$TMP_DIR/plugin/.claude-plugin" "$TMP_DIR/home" "$TMP_DIR/config"
  cp -R "$REPO_ROOT/skills" "$TMP_DIR/plugin/skills"
  python3 - "$TMP_DIR/plugin" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
names = sorted(path.parent.name for path in (root / "skills").glob("*/SKILL.md"))
manifest = {
    "name": "mo-shu-ci-bundle",
    "version": "0.0.0",
    "description": "Synthetic bundle for validating all mo-shu skill components",
    "author": {"name": "chianed1001"},
    "skills": [f"./skills/{name}" for name in names],
}
(root / ".claude-plugin/plugin.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY
  claude plugin validate --strict "$TMP_DIR/plugin"
  echo "  OK Claude CLI strict component validation (all $EXPECTED_COUNT skills)"

  claude plugin validate --strict "$REPO_ROOT"
  echo "  OK Claude CLI strict marketplace validation"

  # Exercise the real marketplace/install path without reading or writing the
  # caller's Claude configuration.
  CLAUDE_CONFIG_DIR="$TMP_DIR/config" HOME="$TMP_DIR/home" \
    claude plugin marketplace add "$REPO_ROOT" >/dev/null
  while IFS= read -r name; do
    CLAUDE_CONFIG_DIR="$TMP_DIR/config" HOME="$TMP_DIR/home" \
      claude plugin install "$name@mo-shu-skills" --scope user >/dev/null
  done < <(python3 - "$MARKETPLACE" <<'PY'
import json
import sys
from pathlib import Path

for item in json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["plugins"]:
    print(item["name"])
PY
)
  CLAUDE_CONFIG_DIR="$TMP_DIR/config" HOME="$TMP_DIR/home" \
    claude plugin list --json >"$TMP_DIR/installed.json"
  python3 - "$TMP_DIR/installed.json" "$MARKETPLACE" "$EXPECTED_COUNT" <<'PY'
import json
import sys
from pathlib import Path

installed = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
marketplace = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
expected_count = int(sys.argv[3])
expected = {f'{item["name"]}@mo-shu-skills' for item in marketplace["plugins"]}
found = {item.get("id") for item in installed}
if len(installed) != expected_count or found != expected:
    raise SystemExit(f"FAIL: installed Claude plugins mismatch; expected={sorted(expected)}, found={sorted(found)}")
for item in installed:
    name = item["id"].split("@", 1)[0]
    skill = Path(item["installPath"]) / "skills" / name / "SKILL.md"
    if not skill.is_file():
        raise SystemExit(f"FAIL: installed Claude plugin omitted {skill}")
print(f"  OK isolated Claude marketplace installed all {len(installed)} skill plugins")
PY
fi

echo "OK: Claude Code adapter checks passed"

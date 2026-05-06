#!/usr/bin/env bash
# new_session.sh — scaffold a new session JSON + acceptance YAML
# Usage: ./scripts/new_session.sh <session_id>
# Requirements: bash 3.2+, no jq/yq dependency

set -euo pipefail

SCRIPT_NAME="$(basename "$0")"

usage() {
  echo "Usage: $SCRIPT_NAME <session_id>" >&2
  echo "  session_id format: ^session-[a-zA-Z0-9_-]+\$" >&2
  echo "  Example: $SCRIPT_NAME session-200" >&2
  exit 1
}

# --- arg check ---
if [ $# -lt 1 ] || [ -z "${1:-}" ]; then
  usage
fi

SESSION_ID="$1"

# --- format check ---
if ! echo "$SESSION_ID" | grep -qE '^session-[a-zA-Z0-9_-]+$'; then
  echo "ERROR: invalid session_id format: '$SESSION_ID'" >&2
  echo "  Must match: ^session-[a-zA-Z0-9_-]+\$" >&2
  exit 1
fi

SESSION_JSON="docs/sessions/${SESSION_ID}.json"
SESSION_YAML="docs/acceptance/${SESSION_ID}.yaml"

# --- collision check ---
if [ -f "$SESSION_JSON" ]; then
  echo "ERROR: '$SESSION_JSON' already exists. Aborting to prevent overwrite." >&2
  exit 1
fi
if [ -f "$SESSION_YAML" ]; then
  echo "ERROR: '$SESSION_YAML' already exists. Aborting to prevent overwrite." >&2
  exit 1
fi

# --- ensure dirs exist ---
mkdir -p "docs/sessions" "docs/acceptance"

# --- atomic cleanup on failure ---
CLEANUP_JSON=""
CLEANUP_YAML=""
cleanup() {
  local exit_code=$?
  if [ "$exit_code" -ne 0 ]; then
    [ -n "$CLEANUP_JSON" ] && [ -f "$CLEANUP_JSON" ] && rm -f "$CLEANUP_JSON"
    [ -n "$CLEANUP_YAML" ] && [ -f "$CLEANUP_YAML" ] && rm -f "$CLEANUP_YAML"
  fi
}
trap cleanup EXIT

# --- generate session JSON ---
CLEANUP_JSON="$SESSION_JSON"
cat > "$SESSION_JSON" <<ENDJSON
{
  "session_id": "${SESSION_ID}",
  "phase_id": "TBD",
  "type": "implementation",
  "title": "TODO: fill in title",
  "goal": "TODO: fill in goal",
  "scope": [],
  "out_of_scope": [],
  "constraints": [],
  "acceptance_ref": "docs/acceptance/${SESSION_ID}.yaml",
  "allowed_changes": [],
  "allowed_changes_detail": [],
  "forbidden_changes": [],
  "completion_criteria": [
    {
      "id": "CC-${SESSION_ID}-01",
      "type": "artifact",
      "condition": "TODO: fill in condition"
    }
  ],
  "acceptance_criteria": [
    {
      "id": "AC-${SESSION_ID}-01",
      "description": "TODO: fill in description",
      "test_name": "test_placeholder"
    }
  ],
  "review_points": [
    "仕様一致（AC達成）",
    "変更範囲遵守",
    "副作用なし（既存破壊なし）",
    "検証十分性（テスト・証跡・再現性により、受入判断に足る根拠があること）"
  ],
  "failure_type": "spec_missing"
}
ENDJSON

# --- generate acceptance YAML ---
CLEANUP_YAML="$SESSION_YAML"
cat > "$SESSION_YAML" <<ENDYAML
session_id: ${SESSION_ID}
goal: "TODO: fill in goal"

scope:
  - "TODO: fill in scope"

out_of_scope:
  - "TODO: fill in out_of_scope"

acceptance:
  - id: AC-${SESSION_ID}-01
    requirement: "TODO: fill in requirement"
    test_name: test_placeholder
    type: manual
    manual_check: true
    verification:
      - "TODO: fill in verification"
ENDYAML

# --- success ---
trap - EXIT
echo "Created: $SESSION_JSON"
echo "Created: $SESSION_YAML"
echo "Done. Edit the files to fill in TODO placeholders."

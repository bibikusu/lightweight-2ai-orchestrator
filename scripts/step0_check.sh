#!/usr/bin/env bash
# step0_check.sh — Session 開始前 Step0 状態確認 (global_rules.md 項目A)
# Usage: ./scripts/step0_check.sh [expected_head_hash]
#   No args  : report state, exit 0
#   With hash: report state + verify HEAD matches, exit non-0 on mismatch
#
# Env vars:
#   STEP0_UNTRACKED_ALLOWLIST : newline-separated grep-E patterns (overrides DEFAULT)
#
# Requirements: bash 3.2+

set -euo pipefail

# --- default allowlist for untracked files ---
DEFAULT_ALLOWED_UNTRACKED=(
  "^DL/"
)

# --- resolve allowlist (env var overrides default) ---
ALLOWED_UNTRACKED=()
if [ -n "${STEP0_UNTRACKED_ALLOWLIST:-}" ]; then
  while IFS= read -r line; do
    [ -n "$line" ] && ALLOWED_UNTRACKED+=("$line")
  done <<< "$STEP0_UNTRACKED_ALLOWLIST"
else
  ALLOWED_UNTRACKED=("${DEFAULT_ALLOWED_UNTRACKED[@]}")
fi

EXPECTED_HEAD="${1:-}"

# --- collect state ---
HEAD=$(git rev-parse HEAD 2>/dev/null || echo "N/A")
ORIGIN=$(git rev-parse origin/main 2>/dev/null || echo "N/A")
BRANCH=$(git branch --show-current 2>/dev/null || echo "N/A")
STASH_COUNT=$(git stash list 2>/dev/null | wc -l | tr -d ' ')

echo "============================================"
echo "  Step0 state check"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
echo "branch      : $BRANCH"
echo "HEAD        : $HEAD"
echo "origin/main : $ORIGIN"
echo ""

# --- stash report ---
if [ "$STASH_COUNT" -gt 0 ]; then
  echo "[WARN] stash entries: $STASH_COUNT"
  git stash list 2>/dev/null | head -3 | sed 's/^/  /' || true
else
  echo "[INFO] stash: empty"
fi
echo ""

# --- HEAD drift report ---
if [ "$HEAD" != "$ORIGIN" ]; then
  echo "[WARN] HEAD != origin/main (local commits ahead or branch diverged)"
else
  echo "[INFO] HEAD == origin/main: OK"
fi
echo ""

# --- untracked files report ---
UNTRACKED_LIST=$(git status --short 2>/dev/null | grep '^??' | awk '{print $2}' || true)
if [ -n "$UNTRACKED_LIST" ]; then
  echo "[INFO] untracked files:"
  while IFS= read -r path; do
    in_allowlist=false
    for pattern in "${ALLOWED_UNTRACKED[@]}"; do
      if echo "$path" | grep -qE "$pattern"; then
        in_allowlist=true
        break
      fi
    done
    if $in_allowlist; then
      echo "  OK (allowlisted) : $path"
    else
      echo "  -- (not listed)  : $path"
    fi
  done <<< "$UNTRACKED_LIST"
else
  echo "[INFO] working tree: clean (no untracked files)"
fi
echo ""

# --- expected hash check (strict mode, only when arg provided) ---
EXIT_CODE=0
if [ -n "$EXPECTED_HEAD" ]; then
  if [ "$HEAD" = "$EXPECTED_HEAD" ]; then
    echo "[OK] HEAD matches expected hash"
  else
    echo "[FAIL] HEAD mismatch" >&2
    echo "  expected : $EXPECTED_HEAD" >&2
    echo "  actual   : $HEAD" >&2
    EXIT_CODE=1
  fi
fi

echo "============================================"
echo "  Step0 check complete. exit=$EXIT_CODE"
echo "============================================"
exit $EXIT_CODE

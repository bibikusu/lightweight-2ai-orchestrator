#!/usr/bin/env bash
# step0_check.sh — セッション開始前 Step0 状態確認（5関数版）
# Usage: SESSION_ID=<id> ./scripts/step0_check.sh
# Env:
#   SESSION_ID              : セッションID（省略時はgitブランチから導出）
#   STEP0_UNTRACKED_ALLOWLIST : 許可untrackedパターン（改行区切り grep-E パターン）

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# セッションIDをブランチ名から導出する（sandbox/session-XXX → session-XXX）
_resolve_session_id() {
  if [ -n "${SESSION_ID:-}" ]; then
    printf '%s' "$SESSION_ID"
    return
  fi
  local branch
  branch=$(git -C "$REPO_ROOT" branch --show-current 2>/dev/null || printf '')
  if printf '%s' "$branch" | grep -qE '^sandbox/(session-[a-zA-Z0-9_.-]+)$'; then
    printf '%s' "$branch" | grep -oE 'session-[a-zA-Z0-9_.-]+'
    return
  fi
  printf 'unknown'
}

SESSION_ID_RESOLVED="$(_resolve_session_id)"
ARTIFACTS_DIR="$REPO_ROOT/artifacts/$SESSION_ID_RESOLVED/step0"

# --- 5関数定義 ---

check_git_status() {
  git -C "$REPO_ROOT" status --short 2>/dev/null || true
}

check_head() {
  git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || printf 'N/A\n'
}

check_stash() {
  git -C "$REPO_ROOT" stash list 2>/dev/null || true
}

check_reflog() {
  git -C "$REPO_ROOT" reflog 2>/dev/null | head -10 || true
}

save_to_artifacts() {
  local sid="${1:-$SESSION_ID_RESOLVED}"
  mkdir -p "$ARTIFACTS_DIR"
  check_git_status > "$ARTIFACTS_DIR/${sid}_git_status.txt"
  check_head       > "$ARTIFACTS_DIR/${sid}_git_head.txt"
  check_stash      > "$ARTIFACTS_DIR/${sid}_git_stash.txt"
  check_reflog     > "$ARTIFACTS_DIR/${sid}_git_reflog.txt"
}

# --- メイン出力 ---

echo "============================================"
echo "  Step0 state check  [session: $SESSION_ID_RESOLVED]"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
echo ""
echo "[check_git_status]"
check_git_status || true
echo ""
echo "[check_head]"
check_head
echo ""
echo "[check_stash]"
check_stash || true
echo ""
echo "[check_reflog]"
check_reflog || true
echo ""

save_to_artifacts "$SESSION_ID_RESOLVED"

echo "--------------------------------------------"
echo "  artifacts: $ARTIFACTS_DIR"
echo "============================================"
echo "  Step0 check complete. exit=0"
echo "============================================"
exit 0

#!/bin/bash
# stop hook v2 proposal — session-203
# 改善点: sandbox/* と claude/* ブランチでは push 要求しない
# CLAUDE.md §4.1「git push は KUNIHIDE manual only」との衝突を解消

set -e

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

# sandbox/* または claude/* ブランチは push 要求しない
if [[ "$BRANCH" == claude/* ]] || [[ "$BRANCH" == sandbox/* ]]; then
  echo "[stop hook v2] branch '$BRANCH' is sandbox/claude — no push requirement"
  exit 0
fi

# main/master のみ未 push チェック (既存ロジック継承)
if [[ "$BRANCH" == "main" ]] || [[ "$BRANCH" == "master" ]]; then
  UNPUSHED=$(git log origin/"$BRANCH"..HEAD --oneline 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$UNPUSHED" -gt 0 ]]; then
    echo "[stop hook v2] WARNING: $UNPUSHED unpushed commit(s) on '$BRANCH'"
    echo "[stop hook v2] Push is KUNIHIDE manual only — see CLAUDE.md §4.1"
  fi
fi

exit 0

#!/usr/bin/env bash
# session-171h: post-push 検証用 Claude hook wrapper
# hook_eval_helper の判定結果を表示し、exit code をそのまま返す

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [ -x ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="python3"
fi

"$PYTHON" scripts/hook_eval_helper.py
exit $?

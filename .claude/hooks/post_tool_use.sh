#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

if [[ -x ".venv/bin/python" ]]; then
  PYBIN=".venv/bin/python"
else
  PYBIN="python3"
fi

"${PYBIN}" -m ruff check orchestration/ tests/
PYTHONPATH=. "${PYBIN}" -m pytest tests/ -q
PYTHONPATH=. "${PYBIN}" -m mypy --explicit-package-bases orchestration/ --ignore-missing-imports
"${PYBIN}" -m compileall orchestration/ >/dev/null

echo "[post_tool_use] all 4 gates passed"

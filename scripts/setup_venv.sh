#!/usr/bin/env bash
# Recreate project .venv from Git-tracked dependency files (session-backlog-05).
# Usage: bash scripts/setup_venv.sh
# Requires: Python 3.11+ recommended (matches .github/workflows/validation.yml).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "error: Python interpreter not found (set PYTHON or install python3)" >&2
  exit 1
fi

echo "Using: $($PY --version 2>&1)"

if [ -d ".venv" ]; then
  echo "Removing existing .venv"
  rm -rf .venv
fi

"$PY" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt

echo ""
echo "Done. Activate with: source .venv/bin/activate"
echo "Run 4-gate checks: bash scripts/check_env.sh"

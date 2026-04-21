#!/usr/bin/env bash
# Canonical 4-gate verification using .venv/bin only (session-backlog-05).
# Usage (from repo root): bash scripts/check_env.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

die() {
  echo "error: $*" >&2
  exit 1
}

[ -x ".venv/bin/python" ] || die ".venv/bin/python missing; run: bash scripts/setup_venv.sh"
[ -x ".venv/bin/ruff" ] || die ".venv/bin/ruff missing; run: bash scripts/setup_venv.sh"
[ -x ".venv/bin/pytest" ] || die ".venv/bin/pytest missing; run: bash scripts/setup_venv.sh"

echo "[1/4] ruff"
.venv/bin/ruff check .

echo "[2/4] pytest"
PYTHONPATH=. .venv/bin/pytest backend/tests/ -q

echo "[3/4] mypy"
PYTHONPATH=. .venv/bin/python -m mypy --explicit-package-bases orchestration --ignore-missing-imports

echo "[4/4] compileall"
PYTHONPYCACHEPREFIX="./.pycache_compileall" .venv/bin/python -m compileall -q -f orchestration backend

echo "OK: all four gates passed."

#!/usr/bin/env bash
# 標準 4-gate（ruff / pytest / mypy / compileall）をリポジトリルートで実行する。
# 正本は .github/workflows/validation.yml の各 run と同一コマンド列。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  echo "error: $ROOT/.venv/bin/python が見つかりません。先に仮想環境を作成し依存を入れてください。" >&2
  echo "  python3 -m venv .venv" >&2
  echo "  .venv/bin/pip install --upgrade pip" >&2
  echo "  .venv/bin/pip install -r requirements.txt" >&2
  echo "  .venv/bin/pip install -r requirements-dev.txt" >&2
  exit 1
fi

echo "== ruff =="
.venv/bin/ruff check .

echo "== pytest =="
PYTHONPATH=. .venv/bin/pytest backend/tests/ -q

echo "== mypy =="
PYTHONPATH=. .venv/bin/python -m mypy --explicit-package-bases orchestration --ignore-missing-imports

echo "== compileall =="
PYTHONPYCACHEPREFIX="./.pycache_compileall" .venv/bin/python -m compileall -q -f orchestration backend

echo "OK: 4-gate 完了"

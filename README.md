# lightweight-2ai-orchestrator

ローカル検証は **リポジトリルートに `.venv` を作成し、その `bin` 配下のツールだけで標準 4-gate を走らせる**ことを前提とする（`.venv/` は Git 管理外。`.gitignore` 済み）。

## 環境構築（再現手順）

Python 3.11 系を推奨（CI と同じ）。

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -r requirements-dev.txt
```

- `requirements.txt` … ランタイム依存（オーケストレータ実行向け）
- `requirements-dev.txt` … 検証用（ruff / mypy / types-PyYAML など）。CI（`.github/workflows/validation.yml`）は `requirements.txt` に加え `ruff` と `mypy` を個別インストールしており、ローカルでは上記のとおり `requirements-dev.txt` まで入れると型スタブも揃い整合しやすい。

## 標準 4-gate（`.venv/bin` ベース）

次のいずれかで実行できる。

1. **スクリプト（推奨）** — 手順の再現性が最も高い。

   ```bash
   ./scripts/run_four_gates.sh
   ```

2. **コマンド列** — `run_four_gates.sh` と同一（正本は Git 管理の `scripts/run_four_gates.sh` および `.github/workflows/validation.yml`）。

   ```bash
   .venv/bin/ruff check .
   PYTHONPATH=. .venv/bin/pytest backend/tests/ -q
   PYTHONPATH=. .venv/bin/python -m mypy --explicit-package-bases orchestration --ignore-missing-imports
   PYTHONPYCACHEPREFIX="./.pycache_compileall" .venv/bin/python -m compileall -q -f orchestration backend
   ```

セッション実行や merge 前チェックなど、その他の運用手順は `docs/` 配下の各文書を参照。

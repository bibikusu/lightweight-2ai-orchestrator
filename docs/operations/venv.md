# Python 仮想環境と 4-gate 検証（`.venv/bin` 正本）

ローカル検証は **必ずリポジトリルートの `.venv`** を使う。グローバルの `python3` / `pip` で代替すると、CI（`.github/workflows/validation.yml`）と異なる解釈になり誤判定の原因になる。

## 前提

- **Python**: 3.11 系を推奨（CI の `setup-python` と揃える）
- **作業ディレクトリ**: リポジトリルート

## `.venv` の再構築（再現手順）

依存は Git 管理下の次の 2 ファイルで固定する。

- `requirements.txt` — 実行・テスト実行に必要な依存（`pytest` を含む）
- `requirements-dev.txt` — lint / 型チェック用（`ruff`, `mypy`, `types-PyYAML`）

自動化:

```bash
bash scripts/setup_venv.sh
```

手動でも同じ内容:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
```

`pyproject.toml` の `[project.optional-dependencies] dev` は、`requirements-dev.txt` と同じ開発用依存の意味で揃えてある（`pip install .[dev]` はこのリポジトリでは必須ではない）。

## 4-gate 検証コマンド（`.venv/bin` 正本）

次の 4 つを **この順** で実行する。`PYTHONPATH=.` が必要なコマンドはそのまま使う。

| # | 内容 | コマンド |
|---|------|----------|
| 1 | Ruff | `.venv/bin/ruff check .` |
| 2 | Pytest | `PYTHONPATH=. .venv/bin/pytest backend/tests/ -q` |
| 3 | Mypy | `PYTHONPATH=. .venv/bin/python -m mypy --explicit-package-bases orchestration --ignore-missing-imports` |
| 4 | compileall | `PYTHONPYCACHEPREFIX=./.pycache_compileall .venv/bin/python -m compileall -q -f orchestration backend` |

一括実行（上表と同等）:

```bash
bash scripts/check_env.sh
```

`compileall` は **`.venv/bin/python`** で実行する（システムの `python3` ではない）。これによりインタープリタとパッケージ集合が gate 全体で一致する。

## CI との関係

GitHub Actions の validation ワークフローは `requirements.txt` に加え `ruff` と `mypy` をインストールしている。ローカルでは `requirements-dev.txt` により同じツール集合を一回で入れられる。

`.venv` ディレクトリ自体は **コミットしない**（`.gitignore` 前提）。

# Cursor 実行テンプレート: session-03

## 実行目的

`orchestration/providers` の最小実装を正本仕様に整合させる。セッションレポート自動生成および retry ループは本セッションでは扱わない。

## allowed_changes

- `orchestration/providers/__init__.py`
- `orchestration/providers/openai_client.py`
- `orchestration/providers/claude_client.py`
- `orchestration/providers/llm_json.py`

## forbidden_changes

- `orchestration/run_session.py` の変更
- セッションレポート自動生成・retry ループの追加
- `docs/master_instruction.md` / `docs/roadmap.yaml` / `docs/session_post_process.md` の変更
- `docs/sessions/session-03a.*` / `docs/templates/cursor_run_session-03a.md` の変更
- session-04 / session-05 用セッションファイルの新規作成

## 完了条件

- `docs/acceptance/session-03.yaml` の全 AC を満たす
- `changed_files` が providers 4 ファイル以内であり禁止パスを含まない
- `artifacts/reports/session-03-report.json` を保存契約どおり残せる記録が取れる

## 差戻し条件

- allowed_changes 外のファイルを変更した
- report / retry 関連のコードを本セッションに混入した
- 環境変数名または API 呼び出し形式を無断で変更した

## 実行後確認コマンド

```bash
PYTHONPATH=orchestration python3 -c "from providers.openai_client import OpenAIClientConfig, OpenAIClientWrapper; from providers.claude_client import ClaudeClientConfig, ClaudeClientWrapper; from providers.llm_json import parse_json_object"
PYTHONPYCACHEPREFIX=./.pycache_py_compile python3 -m py_compile orchestration/run_session.py
.venv/bin/python -m pytest backend/tests/test_patch_validation.py -q
```

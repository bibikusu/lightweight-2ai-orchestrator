# Cursor 実行テンプレート: session-03a

## 実行目的

session-03 の仕様を一意化し、session-04（セッションレポート自動生成）・session-05（retry 最小実装）との境界を文書で固定する。実装コードは変更しない。

## allowed_changes

- `docs/sessions/session-03.json`
- `docs/acceptance/session-03.yaml`
- `docs/templates/cursor_run_session-03.md`

## forbidden_changes

- `docs/master_instruction.md` / `docs/roadmap.yaml` / `docs/session_post_process.md` の変更
- `orchestration/**/*.py` の変更
- `docs/sessions/session-04.json` / `session-05.json` および対応 acceptance の作成
- `docs/sessions/session-03a.json` / `docs/acceptance/session-03a.yaml` / 本ファイルの変更

## 完了条件

- `session-03` の JSON / YAML が provider 最小実装のみを対象とし、report 自動生成・retry をスコープに含まない
- 保存契約 `artifacts/reports/session-XX-report.json` が session-03 文書に明示されている
- `artifacts/reports/session-03a-report.json` が生成可能な内容で手順が閉じている

## 差戻し条件

- 正本3ファイルを変更した
- session-04 / session-05 のセッションファイルを作成した
- 実装コードを変更した
- session-03 に report / retry が混入した

## 実行後確認コマンド

```bash
ls docs/sessions/session-03.json docs/acceptance/session-03.yaml
grep -E "report|retry" docs/sessions/session-03.json docs/acceptance/session-03.yaml || true
ls docs/sessions/session-04.json docs/sessions/session-05.json 2>&1
```

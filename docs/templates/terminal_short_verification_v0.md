# Terminal short verification template v0

セッション作業後に **cwd = リポジトリルート** で実行する **固定短文検証** のみを列挙する。解釈や長文判断は要求しない。

## session-196（docs-only）標準手順

1. **session 静的検証**

   ```bash
   python tools/session_validate.py docs/sessions/session-196.json
   ```

2. **必須ファイルの存在**

   ```bash
   test -f docs/sessions/session-196.json
   test -f docs/acceptance/session-196.yaml
   test -f docs/specs/next_action_artifact_contract_v0.md
   test -f docs/templates/terminal_short_verification_v0.md
   ```

3. **変更範囲の一覧（人間確認用）**

   ```bash
   git diff --name-only
   ```

上記は **そのままコピー実行可能** とし、セッションごとに文言を変えない（変更が必要ならテンプレートの **バージョン番号を上げた別ファイル** で行う）。

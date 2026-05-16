# .claude/hooks/ — ClaudeCode Hook Script 一覧

このディレクトリには ClaudeCode の Tool 実行前後に自動発火する hook script を管理する。

---

## ファイル一覧

| ファイル | 種別 | 状態 | 用途 |
|---------|------|------|------|
| `pre_tool_use.sh` | PreToolUse | **有効** | `scripts/preflight_session.sh` を呼び出す汎用ゲート |
| `post_tool_use.sh` | PostToolUse | **有効** | 4 gates (ruff / pytest / mypy / compileall) を実行 |
| `post_push.sh` | PostToolUse | **有効** | `scripts/hook_eval_helper.py` による push 後検証 |
| `preflight_session.sh.proposed` | PreToolUse | **提案中** | stash 保護 / forbidden_changes 突合 / branch チェック |
| `post_tool_use.sh.proposed` | PostToolUse | **提案中** | .env 書込検出 / read-after-write 検証 / ログ記録 |
| `test_hooks.sh.proposed` | テスト | **提案中** | 上記 2 つの proposed hook の動作確認スクリプト |

> **注意**: `.proposed` 拡張子のファイルは `settings.json` に登録されていないため有効ではない。  
> 有効化は KUNIHIDE が手動で `settings.json` に追記する。

---

## 有効な hook の動作

### pre_tool_use.sh (PreToolUse)

Tool 実行前に `scripts/preflight_session.sh` を呼び出す。

```
exit 0 → Tool 実行を許可
exit 1 → Tool 実行をブロック (エラーメッセージを表示)
```

### post_tool_use.sh (PostToolUse)

Tool 実行後に 4 gates を実行:

1. `ruff check orchestration/ tests/` — Python lint
2. `pytest tests/ -q` — ユニットテスト
3. `mypy --explicit-package-bases orchestration/ --ignore-missing-imports` — 型チェック
4. `python -m compileall orchestration/ >/dev/null` — 構文チェック

---

## proposed hook の有効化手順

> **KUNIHIDE のみが実行する。ClaudeCode は実行しない。**

### ステップ 1: proposed script を正規ファイルにコピー

```bash
cp .claude/hooks/preflight_session.sh.proposed .claude/hooks/preflight_session.sh
cp .claude/hooks/post_tool_use.sh.proposed .claude/hooks/post_tool_use.sh
chmod +x .claude/hooks/preflight_session.sh
chmod +x .claude/hooks/post_tool_use.sh
```

### ステップ 2: テストで動作確認

```bash
bash .claude/hooks/test_hooks.sh.proposed
```

全テスト PASS を確認してから次のステップへ。

### ステップ 3: settings.json に hook を登録

`settings.json` に以下を追記する (現在の `permission_mode` は保持する):

```json
{
  "permission_mode": "plan",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/preflight_session.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/post_tool_use.sh"
          }
        ]
      }
    ]
  }
}
```

### ステップ 4: Claude Code を再起動して hook を反映

---

## proposed hook の動作仕様

### preflight_session.sh.proposed — exit code

| exit | 意味 | ClaudeCode の挙動 |
|------|------|-----------------|
| 0 | 全チェック通過、実行許可 | Tool を実行する |
| 1 | 警告あり、実行は継続 | Tool を実行するが警告を表示 |
| 2 | ブロック、実行禁止 | Tool の実行を中止してエラーを表示 |

#### チェック内容

1. **untracked ファイル数** — 50 件超で警告、100 件超でブロック
2. **ブランチ保護** — main/master 上で git push/merge/reset をブロック
3. **sealed stash 保護** — stash 件数が 8 件未満でブロック
4. **forbidden_changes 突合** — Edit/Write/Bash ツールで forbidden パスへのアクセスをブロック

### post_tool_use.sh.proposed — exit code

| exit | 意味 |
|------|------|
| 0 | 全チェック通過 |
| 1 | 警告あり (main branch での作業、ファイル実体なし) |
| 2 | 危険検出 (.env / secrets/ への書込) |

#### チェック内容

1. **read-after-write verification** — git diff のファイルが実体として存在するか確認
2. **.env / secrets/ 書込検出** — ステージされた場合は危険アラート
3. **main branch 直接作業検出** — 警告を出力
4. **git diff ログ記録** — `.claude/logs/hooks.log` に記録

---

## ログファイル

```
.claude/logs/hooks.log
```

出力フォーマット:

```
[2026-05-17 10:30:00] [INFO] [tool:Edit] PreToolUse hook 開始
[2026-05-17 10:30:00] [WARN] [tool:Edit] untracked ファイルが 55 件 (警告閾値: 50)
[2026-05-17 10:30:00] [INFO] [tool:Edit] PreToolUse hook 通過 (exit 0)
[2026-05-17 10:30:01] [INFO] [post][tool:Edit] PostToolUse hook 開始
[2026-05-17 10:30:01] [INFO] [post][tool:Edit] diff (staged): src/pipeline/run_daily.sh
[2026-05-17 10:30:01] [INFO] [post][tool:Edit] exit 0
```

---

## 関連ドキュメント

- `docs/strategy/vision-and-principles.md §4` — 絶対禁則 (forbidden_changes の正本)
- `CLAUDE.md §4` — forbidden actions
- `scripts/preflight_session.sh` — セッション投入前の汎用 preflight
- `scripts/hook_eval_helper.py` — post_push hook の評価ロジック

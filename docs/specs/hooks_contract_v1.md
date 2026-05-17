# hooks 契約仕様 v1 (hooks_contract_v1)

- **session**: session-203-pre
- **type**: docs-only (契約仕様のみ。`.claude/settings.json` 変更・`.claude/hooks.bak` 復活は本セッションでは禁止)
- **status**: frozen-spec
- **作成日**: 2026-05-17
- **前提**: governance pause 中。hooks の実体有効化は本セッション対象外 (docs-only)
- **後方参照**: `docs/sessions/session-203-pre.json` / `docs/acceptance/session-203-pre.yaml`
- **関連**: `claude_md_contract_v1.md` (§3.3 禁止操作 / §4 秘密情報禁止と二重化)

---

## 0. このドキュメントの位置づけと禁止事項

### 0.1 目的

本ドキュメントは Claude Code の **hooks がどう発火し、何を強制し、
どう復活させるか** を contract として freeze する仕様書である。
hooks 実体の有効化・`.claude/settings.json` への hooks 定義の追記は
**本セッションでは行わない** (docs-only / governance pause)。

### 0.2 docs-only 制約 (本セッションで物理的に行わないこと)

- `.claude/settings.json` (32 bytes placeholder) の変更
- `.claude/hooks.bak` の復活・リネーム・有効化
- hooks スクリプトの新規実装・改変
- hooks の settings.json への登録

本契約は「どうあるべきか」を freeze するにとどめる。実体反映は別 session。

### 0.3 規定する 7 章

| 章 | 内容 |
|----|------|
| §1 | hooks の種類と各 hook の発火条件 (8 種) |
| §2 | `.claude/settings.json` の構造定義 (現状 permission_mode のみ・32bytes) |
| §3 | `.claude/hooks.bak` からの復活手順 (docs-only) |
| §4 | PreToolUse で git push をブロックする現行ロジック |
| §5 | PostToolUse での監査ログ (audit jsonl 推奨形式) |
| §6 | hooks の Python 3.9 互換要件 (PEP604 禁止) |
| §7 | 13 個の事故防止ガード一覧 |

---

## 1. hooks の種類と各 hook の発火条件 (8 種)

Claude Code は以下 8 種の hook イベントを持つ。各 hook は発火条件・
入力・期待される exit code 契約が異なる。

### 1.1 PreToolUse

- **発火条件**: 任意のツール (Bash / Write / Edit 等) が **実行される直前**。
- **用途**: 禁止操作のブロック (git push / git add . / main 直 commit 等)。
- **契約**: 非ゼロ exit でツール実行を **拒否** できる (ガードの主戦場)。
- **本リポジトリ現行**: `.claude/hooks/pre_tool_use.sh` →
  `scripts/preflight_session.sh` を呼ぶ wrapper (§4 参照)。

### 1.2 PostToolUse

- **発火条件**: ツール実行が **完了した直後**。
- **用途**: 4-gate 検証・監査ログ追記 (§5)。
- **契約**: 失敗時に後続を止める / ログを残す。
- **本リポジトリ現行**: `.claude/hooks/post_tool_use.sh` が
  ruff / pytest / mypy / compileall の 4 ゲートを実行。

### 1.3 UserPromptSubmit

- **発火条件**: ユーザ (KUNIHIDE) がプロンプトを **送信した時点**。
- **用途**: 1 chat = 1 project 規律の注入 / 文脈プリチェック。
- **契約**: プロンプトに前提を付与、または不正文脈を警告。

### 1.4 Stop

- **発火条件**: メインの応答 (turn) が **停止する時点**。
- **用途**: 完了報告の整合チェック / artifact 必須フィールド確認。
- **契約**: artifact 不備時に「完了」を阻止 (AC pass 偽装防止)。

### 1.5 SubagentStop

- **発火条件**: サブエージェント (Agent ツール) が **停止する時点**。
- **用途**: サブエージェント成果物の検証・親への引き継ぎ確認。
- **契約**: サブエージェントの自己承認を信用しない (検証必須)。

### 1.6 Notification

- **発火条件**: Claude Code が **通知を発する時点** (承認待ち等)。
- **用途**: 承認疲れ対策の集約通知 / 重要イベントの可視化。
- **契約**: 通知の抑制・整形 (Approval Fatigue 対策と連動)。

### 1.7 SessionStart

- **発火条件**: セッションが **開始する時点**。
- **用途**: sealed stash 件数確認 / branch 確認 / baseline 照合の起点。
- **契約**: 異常 (stash 件数変動・誤 branch) を起動時に検出。

### 1.8 PreCompact

- **発火条件**: 文脈圧縮 (compaction) が **行われる直前**。
- **用途**: 圧縮前に重要不変条件 (禁則・session_id) を退避・再注入。
- **契約**: 圧縮により絶対禁則が失われないことを保証。

### 1.9 発火順序の概念

```
SessionStart
  └─ UserPromptSubmit
       └─ PreToolUse → (tool 実行) → PostToolUse   ← 複数回ループ
       └─ (必要時) PreCompact
  └─ SubagentStop (Agent 使用時)
  └─ Stop (turn 終了)
```

---

## 2. `.claude/settings.json` の構造定義 (現状 permission_mode のみ・32bytes)

### 2.1 現状 (frozen placeholder)

- 現行 `.claude/settings.json` は **32 bytes** の placeholder。
- 内容は `permission_mode` キー 1 個のみ (`{ "permission_mode": "plan" }`)。
- CLAUDE.md §4.3 により **改変禁止**。本契約も変更しない (docs-only)。

### 2.2 構造定義 (契約上の論理スキーマ)

将来 KUNIHIDE が hooks を有効化する際の **論理構造** を以下に freeze する
(実体反映は別 session / KUNIHIDE manual)。

| キー | 型 | 説明 | 現状 |
|------|----|------|------|
| `permission_mode` | string | 権限モード (`plan` 等) | 設定済 (唯一のキー) |
| `permissions.allow` | string[] | 許可コマンド allowlist | 未設定 (proposed 参照) |
| `permissions.deny` | string[] | 拒否コマンド denylist | 未設定 (proposed 参照) |
| `hooks` | object | hook イベント → スクリプト割当 | **未設定 (本契約対象外)** |
| `env` | object | sandbox 環境変数 | 未設定 |

- 拡張候補は `.claude/settings.json.proposed` に既出 (KUNIHIDE manual review 後に
  リネーム採用)。本契約は `proposed` を変更しない。
- `hooks` キーは Phase A-3 で別途実装予定 (roadmap-2026.md §3.3 Step A-3)。
  本契約では論理構造の freeze にとどめ、実定義は書かない。

### 2.3 不可侵条件

- 現行 32 bytes placeholder は session-203-pre では一切変更しない。
- `hooks` キーの実体追記は KUNIHIDE manual review + PR レビュー必須。

---

## 3. `.claude/hooks.bak` からの復活手順 (docs-only)

### 3.1 前提: governance pause

hooks は governance pause 中につき **無効化済み**。`.claude/hooks.bak`
(または同等の退避物) は audit 履歴であり、CLAUDE.md の禁則上
ClaudeCode は不触 (復活操作を自走しない)。

### 3.2 復活手順 (KUNIHIDE manual only — 本契約は手順を記述するのみ)

1. **事前確認**: `git stash list | wc -l` が 8 であること (sealed stash 不変)。
2. **branch 確認**: sandbox branch 上であること (main 直は禁止)。
3. **diff レビュー**: `.claude/hooks.bak` と現行 `.claude/hooks/` の差分を
   KUNIHIDE が目視レビュー。
4. **段階有効化**: PreToolUse (ブロック系) → PostToolUse (監査系) の順で
   1 つずつ有効化し、各段で 4-gate を回す。
5. **settings.json 反映**: `hooks` キーへの登録は KUNIHIDE manual で実施。
6. **記録**: 復活は session JSON + acceptance YAML を伴って起票。

> 本セッション (session-203-pre) は上記を **実行しない**。手順の freeze のみ。

### 3.3 復活時の禁止事項

- ClaudeCode による `.claude/hooks.bak` の無断 apply / リネーム / 有効化禁止。
- レビューなしの一括復活禁止 (段階有効化必須)。
- sealed stash 件数が 8 でない状態での復活禁止 (即中断 → KUNIHIDE 報告)。

---

## 4. PreToolUse で git push をブロックする現行ロジック

### 4.1 ブロック対象 (絶対禁則と一致)

PreToolUse ガードは、ツール実行直前に以下を **拒否** する:

- `git push` (KUNIHIDE manual only — ClaudeCode は実行しない)
- `git push --force` / `git push -f`
- `git add .` / `git add -A`
- `main` ブランチへの直接 commit
- `git stash pop` / `git stash drop` / `git stash apply`
- `git reset --hard` (KUNIHIDE 確認前)

### 4.2 現行 wrapper の構造

- `.claude/hooks/pre_tool_use.sh` は `scripts/preflight_session.sh` を
  呼び出す wrapper。`CLAUDE_SESSION_ID` を引数に preflight を実行する。
- preflight が非ゼロ exit を返すとツール実行は **拒否** される。

### 4.3 ブロック判定の契約 (論理仕様)

```
入力: 実行予定コマンド文字列 cmd
判定:
  if cmd が "git push" にマッチ           -> DENY (理由: KUNIHIDE manual only)
  if cmd が "git push --force/-f" にマッチ -> DENY (理由: 不可逆・要 KUNIHIDE)
  if cmd が "git add ." / "git add -A"     -> DENY (理由: 個別指定必須)
  if 現 branch == main かつ commit 操作     -> DENY (理由: sandbox branch のみ)
  if cmd が "git stash pop/drop/apply"      -> DENY (理由: sealed stash 保護)
  else                                      -> ALLOW
exit code: DENY=非ゼロ / ALLOW=0
```

### 4.4 二重防御

- hooks 側ブロックは `claude_md_contract_v1.md §3.3` の禁止操作と
  **二重化** する (片方が無効でも他方が効く)。
- `.claude/settings.json.proposed` の `permissions.deny` にも
  `git push` 系が列挙されており、settings 層でも拒否される設計。

---

## 5. PostToolUse での監査ログ (audit jsonl 推奨形式)

### 5.1 目的

- AI 完了報告を信用しない (Gemini 全削除事故の教訓)。
- 全ツール実行を機械可読で追跡し、AC pass 偽装を検出可能にする。

### 5.2 推奨保存先

- `audit/` ディレクトリ配下に **JSON Lines (.jsonl)** で 1 行 1 イベント追記。
- 例: `audit/tool_use-YYYYMMDD.jsonl` (日次ローテーション)。
- 追記専用 (append-only)。既存行の書換・削除はしない。

### 5.3 1 行あたりの推奨フィールド

| フィールド | 型 | 説明 |
|------------|----|------|
| `ts` | string (ISO8601) | イベント時刻 |
| `session_id` | string | 実行中の session_id |
| `branch` | string | 実行時の git branch |
| `tool` | string | ツール名 (Bash / Write / Edit 等) |
| `action` | string | 実行内容の要約 (コマンド / 対象パス) |
| `decision` | string | `allow` / `deny` / `executed` |
| `gate_result` | object | 4-gate (ruff/pytest/mypy/compileall) の pass/fail |
| `exit_code` | int | ツール / gate の exit code |

### 5.4 推奨 1 行例 (形式の説明のみ)

```jsonl
{"ts":"2026-05-17T00:00:00Z","session_id":"session-203-pre","branch":"sandbox/...","tool":"Bash","action":"git status","decision":"executed","exit_code":0}
```

### 5.5 現行 PostToolUse

- `.claude/hooks/post_tool_use.sh` は ruff / pytest / mypy / compileall の
  4 ゲートを実行し、結果を出力する。
- 監査 jsonl 追記は本契約で **推奨形式を freeze** するにとどめ、
  実装の有効化は別 session (governance pause 中)。

### 5.6 監査ログの不可侵

- audit jsonl は append-only。過去行の改ざんは禁止。
- 監査ログの削除・切り詰めは KUNIHIDE 承認なしには行わない。

---

## 6. hooks の Python 3.9 互換要件 (PEP604 禁止)

### 6.1 互換ターゲット

- hooks から呼ばれる Python スクリプトは **Python 3.9 互換** を必須とする。
- 実行系が 3.9 を含むため、3.10+ 専用構文を使うと hook 自体が失敗する
  (= ガードが効かなくなる事故につながる)。

### 6.2 PEP 604 禁止 (`X | Y` 型注釈)

- **禁止**: `def f(x: int | None)` / `list[int] | None` 等の PEP 604 union 構文。
- **代替**: `from typing import Optional, Union` を用い
  `Optional[int]` / `Union[int, str]` と書く。

### 6.3 その他 3.10+ 構文の禁止

- `match` / `case` 文 (structural pattern matching) を使わない。
- `dict | dict` のマージ演算子に依存しない (3.9 では `{**a, **b}`)。
- パラメータ仕様 `ParamSpec` 等 3.10+ typing は使わない。

### 6.4 検証

- 4-gate の `python -m compileall` および mypy で 3.9 非互換を検出する。
- hooks スクリプトは shebang を `#!/usr/bin/env bash` / `python3` とし、
  3.10+ 専用ランタイムに暗黙依存しない。

---

## 7. 13 個の事故防止ガード一覧

hooks (および settings.deny / CLAUDE.md 禁則) で多重化すべき
**事故防止ガード 13 件** を以下に freeze する。各ガードは
PreToolUse / PostToolUse / SessionStart のいずれかで強制される。

| # | ガード | 強制 hook | 根拠 |
|---|--------|-----------|------|
| 1 | `git push` ブロック (KUNIHIDE manual only) | PreToolUse | CLAUDE.md §4.1 |
| 2 | `git add .` / `git add -A` ブロック | PreToolUse | CLAUDE.md §4.1 |
| 3 | `main` ブランチ直接 commit ブロック | PreToolUse | CLAUDE.md §4.1 |
| 4 | `git stash pop/drop/apply` ブロック | PreToolUse | CLAUDE.md §4.2 |
| 5 | `git push --force` / `git reset --hard` ゲート | PreToolUse | CLAUDE.md §4.1 |
| 6 | sealed stash 件数 == 8 不変チェック | SessionStart | CLAUDE.md §4.2 / §10 |
| 7 | `.claude/settings.json` 改変検出 | PreToolUse | CLAUDE.md §4.3 |
| 8 | 戦略文書 (`docs/strategy/*` 等) 改変検出 | PreToolUse | CLAUDE.md §4.4 |
| 9 | 本番 DB / production server アクセスブロック | PreToolUse | CLAUDE.md §4.5 |
| 10 | `.env` / `secrets/` 読み取りブロック | PreToolUse | CLAUDE.md §4.5 |
| 11 | `npm install` / `pip install` 承認なし実行ブロック | PreToolUse | CLAUDE.md §4.5 (Axios RAT) |
| 12 | docker image version pin 強制 (latest 禁止) | PreToolUse | lessons-learned (LiteLLM) |
| 13 | AI 完了報告の artifact 手動検証強制 | Stop / PostToolUse | lessons-learned §3.4 (Gemini 事故) |

### 7.1 ガードの多重化原則

- 各ガードは hooks 単独に依存せず、`settings.deny` および CLAUDE.md 禁則と
  **三重化** する (Approval Fatigue / 単一障害点の回避)。
- ガードを 1 つでも無効化する変更は PR レビュー必須
  (`claude_md_contract_v1.md §7.3` と連動)。

### 7.2 ガード失敗時の挙動

- ガードが DENY を返した場合、ClaudeCode は同一操作を再試行しない。
- sealed stash 件数異常 (#6) は **即中断 → KUNIHIDE 報告** (凍結審議トリガー)。

---

## 8. 本契約の受入対応 (acceptance マッピング)

検証可能条件は `docs/acceptance/session-203-pre.yaml` に 1:1 で定義。要点:

- 本ファイルが存在し 300 行以上であること。
- 8 種 hook (PreToolUse / PostToolUse / UserPromptSubmit / Stop /
  SubagentStop / Notification / SessionStart / PreCompact) が明記されていること。
- 「git push」ブロックロジック・「audit」jsonl・「Python 3.9」/「PEP604」・
  「13」事故防止ガードが本文に明記されていること。
- `.claude/settings.json` を変更しない docs-only であること。

---

## 9. 改訂履歴

| version | date | session | 変更概要 |
|---------|------|---------|----------|
| v1 | 2026-05-17 | session-203-pre | 初版 freeze (docs-only。hooks 実体有効化・settings 変更は対象外) |

---

**END OF FILE — hooks_contract_v1.md (v1, frozen-spec, docs-only)**

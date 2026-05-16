---
name: session-planner
description: |
  新しいタスクを 14 キー JSON 形式でセッション起票する。
  ユーザーが「新しいセッション起票」「session-pre 相当」「セッション定義を作って」と
  依頼したときに使う。旧 orchestrator の session-pre フェーズ相当。
allowed-tools: Read, Write, Grep, Glob, Bash(git log:*)
model: sonnet
---

# Session Planner Skill

## 目的

14 キー JSON 形式でセッションを起票する。
旧 orchestrator の `prepared_spec` (session-pre フェーズ) 相当の責務を担う。

## 旧 orchestrator での位置づけ

旧 `run_session.py` の `prepared_spec` ステージが担っていた:
- セッション JSON の構造検証
- `allowed_changes` と `forbidden_changes` の衝突チェック
- `completion_criteria.type` の canonical enum 検証
- `review_points` の固定 4 軸確認

これらをプロンプト + 規律として実行する。

---

## 14 キー仕様

| # | キー | 型 | 説明 |
|---|------|----|------|
| 1 | `session_id` | string | `git log --grep` で衝突確認済みの一意 ID |
| 2 | `phase_id` | string | roadmap-2026.md の Phase 参照 (例: `M03`, `V2-Z5`) |
| 3 | `title` | string | 1 行で目的が伝わるタイトル |
| 4 | `goal` | string | セッション完了時の達成状態を一文で |
| 5 | `scope` | list[str] | 本セッションで触る対象 (ファイル・機能・操作) |
| 6 | `out_of_scope` | list[str] | 明示的に触らないもの (次セッション以降へ) |
| 7 | `constraints` | list[str] | 実行制約・守らなければならないルール |
| 8 | `acceptance_ref` | string | acceptance YAML の repository 相対パス |
| 9 | `allowed_changes_detail` | list[str] | 変更許可ファイル + 変更内容の説明 |
| 10 | `forbidden_changes` | list[str] | 変更禁止対象 (stash + 他 session 含む) |
| 11 | `completion_criteria` | list[{id, type, condition}] | 完了基準 (canonical type 使用) |
| 12 | `acceptance_criteria` | list[{id, description, test_name}] | 検収基準 (description と test_name を 1:1) |
| 13 | `review_points` | list[str] | 固定 4 軸 (変更不可) |
| 14 | `failure_type` | string | 失敗時の分類 enum (canonical) |

---

## 固定値 (変更禁止)

### review_points (固定 4 軸)

```json
"review_points": [
  "仕様一致（AC達成）",
  "変更範囲遵守",
  "副作用なし",
  "検証十分性"
]
```

### completion_criteria.type (canonical enum)

| 値 | 用途 |
|----|------|
| `artifact` | ファイル・成果物の存在確認 |
| `non_regression` | 既存テストが壊れていないこと |
| `side_effect_free` | 変更範囲外への影響がないこと |
| `document_rule` | ドキュメント・規律への記録 |
| `state_transition_consistent` | 状態遷移の整合性 |

### failure_type (canonical enum)

`spec_drift` / `regression` / `side_effect` / `artifact_missing` /
`approval_mismatch` / `dependency_missing` / `scope_creep`

---

## 実行手順

### Step 1: session_id 衝突確認

```bash
git log --grep "<候補の session_id>" --oneline
```

ヒットしたら ID を変更する。

### Step 2: forbidden_changes に必ず含める

- `strategy/` (永久固定階層)
- sealed stash@{0} ～ stash@{7} (旧 orchestrator 凍結物)
- 他の進行中 session が触るファイル群

### Step 3: scope/out_of_scope の境界を明確化

「このセッションでは〇〇しない」を out_of_scope に列挙する。
曖昧な境界は `constraints` に注記を加える。

### Step 4: acceptance_criteria と test_name を 1:1 対応

各 acceptance criteria には対応するテスト関数名 (`test_<動詞>_<対象>`) を付ける。
テストが存在しない場合は `test_MANUAL_<説明>` とする。

### Step 5: completion_criteria で artifact を網羅

作成・変更するすべてのファイルを `artifact` 型 completion_criteria に列挙する。

---

## 出力先

```
docs/sessions/{session_id}.json
```

---

## チェックリスト (起票後に確認)

- [ ] `session_id` が git log でヒットしない
- [ ] `review_points` が固定 4 軸と完全一致
- [ ] `completion_criteria.type` が canonical enum のみ
- [ ] `forbidden_changes` に stash@{0..7} が含まれる
- [ ] `acceptance_ref` のパスが `docs/acceptance/{session_id}.yaml` 形式
- [ ] `allowed_changes_detail` が `scope` と整合している
- [ ] `acceptance_criteria` と `test_name` が 1:1 対応

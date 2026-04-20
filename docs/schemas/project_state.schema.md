# ProjectState 仕様書

**Schema file**: `docs/schemas/project_state.schema.json`
**Draft**: JSON Schema Draft-07
**対象**: session-144 (viewer v0) が読む各プロジェクトの現在状態

---

## 1. 目的

10 プロジェクト可視化ダッシュボードの入力として、各プロジェクトの「現在の状態」と「誰のボールか」を一元表現する契約を定義する。

各プロジェクトは `projects/<project_id>/state.json` にこの形式でファイルを置くことで、ダッシュボードから可視化される。

---

## 2. 必須フィールド (required: 7)

| フィールド名 | 型 | 説明 |
|---|---|---|
| `project_id` | string (non-empty) | プロジェクト一意識別子。`docs/projects.yaml` の `id` と一致必須 |
| `current_phase` | string (non-empty) | 現在のフェーズ識別子。例: `phase7-post`, `a02-phase-a` |
| `current_session_id` | string (non-empty) | 現在または直近のセッション ID。例: `session-144-pre` |
| `status` | enum | プロジェクト全体の状態(後述の 6 値) |
| `waiting_for` | enum or null | ボールの所在(後述の 7 値 + null) |
| `last_updated` | string (date-time) | 最終更新時刻(ISO 8601、例 `2026-04-20T09:00:00+09:00`) |
| `last_error` | string or null | 直近のエラーメッセージ。なければ null |

---

## 3. 推奨フィールド (optional: 2)

| フィールド名 | 型 | 説明 |
|---|---|---|
| `summary` | string | 1 行の状況説明。ダッシュボードカードに表示 |
| `next_action` | string | 人間向けの次アクション 1 行。「人間判断 OS」の中核表示 |

---

## 4. status enum (6 値)

| 値 | 意味 |
|---|---|
| `idle` | 未稼働、活動なし |
| `running` | 実行中(Cursor 実装中 / 4-gate 走行中など) |
| `waiting` | 誰かの判定・承認待ち |
| `blocked` | 進行不能、外的要因または明示不能な詰まり |
| `completed` | フェーズ完了 |
| `error` | エラー停止 |

---

## 5. waiting_for enum (7 値 + null)

| 値 | 意味 |
|---|---|
| `gpt_spec_decision` | GPT による仕様決定待ち |
| `claude_diff_analysis` | Claude 参謀の差分分析待ち |
| `cursor_implementation` | Cursor 作業部隊の実装中 |
| `gpt_acceptance` | GPT 受入判定待ち |
| `human_cherry_pick` | 人間による main 反映待ち |
| `human_external_input` | 人間の外部情報入力待ち(keyword 確定 / domain 取得等) |
| `blocked` | ボール所在が明示できない詰まり |
| `null` | 待ち状態ではない(status が running / idle / completed / error のとき) |

### status と waiting_for の役割分離

- **status**: プロジェクト「全体」の今の状態
- **waiting_for**: 「次のアクション権」が誰にあるか

両者は独立に設定する。例:
- `status=waiting`, `waiting_for=gpt_acceptance` → 正常な待ち
- `status=running`, `waiting_for=null` → Cursor 実装中など
- `status=blocked`, `waiting_for=blocked` → 明示できない詰まり
- `status=completed`, `waiting_for=null` → 完了

---

## 6. additionalProperties

このスキーマは `additionalProperties: false` で閉じている。未定義フィールドを追加したい場合は、先にスキーマを更新すること。

---

## 7. サンプル (完全版)

```json
{
  "project_id": "A02_fina",
  "current_phase": "phase7-post",
  "current_session_id": "session-144-pre",
  "status": "waiting",
  "waiting_for": "gpt_acceptance",
  "last_updated": "2026-04-20T09:00:00+09:00",
  "last_error": null,
  "summary": "session-144-pre 受入待ち",
  "next_action": "GPT 受入後に main へ cherry-pick"
}
```

## 8. サンプル (最小版、推奨フィールド省略)

```json
{
  "project_id": "A01_Card_task",
  "current_phase": "phase1",
  "current_session_id": "session-12",
  "status": "idle",
  "waiting_for": null,
  "last_updated": "2026-04-20T00:00:00+09:00",
  "last_error": null
}
```

---

## 9. 更新ルール

- state.json の生成・更新は session-144 本体以降で規定する
- 本 session (session-144-pre) はスキーマ定義のみで、各プロジェクトへの配置は行わない
- last_updated はファイル書き込み時点の時刻を ISO 8601 で記録する

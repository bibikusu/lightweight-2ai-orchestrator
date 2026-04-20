# QueueState 仕様書

**Schema file**: `docs/schemas/queue_state.schema.json`
**Draft**: JSON Schema Draft-07
**対象**: session-144 (viewer v0) が読む queue engine の現在状態

---

## 1. 目的

オーケストレーターの queue engine が現在抱えている job の状態をダッシュボードから可視化するための契約を定義する。

1 ファイルで queue 全体を表現する。プロジェクト単位の queue を分離運用する場合は、各 `projects/<project_id>/queue_state.json` に同形式で配置してよい。

---

## 2. トップレベル必須フィールド

| フィールド名 | 型 | 説明 |
|---|---|---|
| `queue_version` | string | スキーマバージョン識別子。現在は `"1.0"` 固定 |
| `last_updated` | string (date-time) | queue_state.json の最終更新時刻 (ISO 8601) |
| `jobs` | array | 管理中の job 配列。空配列を許容 |

---

## 3. jobs[] の必須フィールド

| フィールド名 | 型 | 説明 |
|---|---|---|
| `id` | string | job 一意識別子 |
| `type` | string | job 種別 (例: `session_run`, `research`, `generate`, `publish`) |
| `status` | enum | ライフサイクル状態 (後述) |
| `priority` | integer (0-100) | 優先度。既定 `50`、0=最低、100=最高 |
| `created_at` | string (date-time) | job 生成時刻 (ISO 8601) |

---

## 4. jobs[] の任意フィールド

| フィールド名 | 型 | 説明 |
|---|---|---|
| `payload` | object or null | job 固有の入力 JSON |
| `result` | object or null | COMPLETED 時の結果 JSON |
| `retry_count` | integer (>=0) | リトライ回数。既定 0、max 2 を推奨 |
| `started_at` | string (date-time) or null | 実行開始時刻 |
| `completed_at` | string (date-time) or null | 完了または失敗確定時刻 |
| `error` | string or null | FAILED / DEAD_LETTER 時のエラーメッセージ |
| `project_id` | string or null | 所属プロジェクト ID (global job は null) |

**重要**: `retry_count` / `payload` / `result` / `started_at` / `completed_at` / `error` / `project_id` は任意項目であり、viewer v0 はこれらが未定義の job であっても描画可能でなければならない。

---

## 5. job status enum (5 値)
PENDING → RUNNING → COMPLETED
→ FAILED → RETRY (max 2)
→ DEAD_LETTER

| 値 | 意味 |
|---|---|
| `PENDING` | 実行待ち |
| `RUNNING` | 実行中 |
| `COMPLETED` | 正常完了 |
| `FAILED` | 失敗 (再試行対象の可能性あり) |
| `DEAD_LETTER` | リトライ上限到達、以降再試行しない |

---

## 6. priority の意味

| 範囲 | 用途例 |
|---|---|
| 90-100 | 緊急 (メトリクス取得など) |
| 70-89 | 高 (キーワード調査、リライト判定) |
| 40-69 | 通常 (既定 50、記事生成など) |
| 10-39 | 低 (SNS 収集、バックグラウンド整理) |
| 0-9 | 最低優先 |

---

## 7. サンプル (複数 job)

```json
{
  "queue_version": "1.0",
  "last_updated": "2026-04-20T10:00:00+09:00",
  "jobs": [
    {
      "id": "job_001",
      "type": "session_run",
      "status": "PENDING",
      "priority": 50,
      "created_at": "2026-04-20T09:00:00+09:00"
    },
    {
      "id": "job_002",
      "type": "research",
      "status": "RUNNING",
      "priority": 80,
      "payload": {"scope": "all_clusters"},
      "retry_count": 0,
      "created_at": "2026-04-20T08:00:00+09:00",
      "started_at": "2026-04-20T08:05:00+09:00",
      "project_id": "A02_fina"
    }
  ]
}
```

## 8. サンプル (空 queue)

```json
{
  "queue_version": "1.0",
  "last_updated": "2026-04-20T00:00:00+09:00",
  "jobs": []
}
```

---

## 9. 更新ルール

- queue_state.json の生成・更新は queue engine (P6C) が行う
- 本 session (session-144-pre) はスキーマ定義のみ
- 実配置と書き込みは session-144 本体以降、または queue engine 側の改修で扱う

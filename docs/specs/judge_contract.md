# judge_contract v0（docs-only）

## 1. Document Identity

- Document type: spec (judge recommendation contract)
- Version: v0
- Status: canonical docs-only contract
- Session: `docs/sessions/session-200.json`
- Acceptance: `docs/acceptance/session-200.yaml`
- Realized by: `docs/sessions/session-202-pre.json`

## 2. Purpose

本書は **judge が Commander に提出する recommendation の最小契約** を正本化する。

judge は worker_report を受領し、acceptance criteria との照合結果を `judge_recommendation` として提出するが、**自律的に GO を確定する権限を持たない**。最終決定は GPT Commander に委ねる。

## 3. judge recommendation schema

judge_recommendation artifact は以下のフィールドを持つ。

| フィールド名 | 型 | 必須 | 説明 |
|---|---|---|---|
| `session_id` | string | 必須 | 対象 session の識別子 |
| `acceptance_ref` | string (path) | 必須 | 対応 acceptance YAML のパス |
| `recommendation` | string (enum) | 必須 | judge の推薦値。値は `go` / `hold` / `fail` のいずれか |
| `failure_type` | string or null | 必須 | 推薦が `hold` / `fail` の場合の失敗分類。`go` の場合は `null` |
| `cause_summary` | string | 必須 | 推薦根拠の要約 |
| `evidence_refs` | array of string (path) | 必須 | 判定根拠となるファイルパス一覧 |
| `next_action` | string | 必須 | Commander への推奨アクション（例: "proceed", "request_fix", "human_review"） |

### 3.1 additionalProperties

本 schema は `additionalProperties: false` を適用する。上記フィールド以外のトップレベルフィールドを judge_recommendation artifact に含めない。

### 3.2 recommendation の意味

| 値 | 意味 |
|---|---|
| `go` | judge は AC 達成と判断し、Commander に進行を推薦する |
| `hold` | judge は保留を推薦する（Commander の判断が必要） |
| `fail` | judge は AC 未達成と判断し、Commander に差し戻しを推薦する |

## 4. 禁止事項

### 4.1 recommendation only（judge は決定しない）

- judge は **`recommendation`** を提出するのみであり、GO / HOLD / FAIL を **確定しない**。
- judge は worker_report の評価者であるが、**最終決定権を持たない**。
- **final GO / HOLD / FAIL の決定権は GPT Commander のみに帰属する。**

### 4.2 final_decision_owner 固定

- `final_decision_owner` は **`commander`** に固定する。
- いかなる状況においても judge が `final_decision_owner` を変更・上書きすることを禁止する。

### 4.3 autonomous GO 禁止

- judge が自律的に GO を発行することを **禁止する**。
- `recommendation: "go"` は Commander への提案であり、Commander の承認なしに実行 GO に変換されない。

### 4.4 L4 autonomy 禁止

- L4 レベルの自律実行（ヒューマン承認なしの自動 GO / 自動 FAIL 確定）を **禁止する**。
- judge は人間 Commander による最終承認を必須とする。

## 5. 非スコープ

以下は本契約で要件化しない。将来の evolution を blocking しないため、本契約に含めない。

- routing の heuristic 定義（別 session へ委譲）
- telemetry の定義（別 session へ委譲）
- exact failure_type → decision mapping の freeze（別 session へ委譲）
- total deterministic function の定義（別 session へ委譲）
- failure_type ごとの自動振り分けロジック（別 session へ委譲）

## 6. 参照

- `docs/sessions/session-200.json`（本契約の起票セッション）
- `docs/acceptance/session-200.yaml`（acceptance 正本）
- `docs/specs/worker_report_contract.md`（worker report contract）
- `docs/contracts/judge_observation_contract.md`（observation contract）
- `docs/specs/pcc_display_contract.md`（PCC display contract）

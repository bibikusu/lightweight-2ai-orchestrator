# judge_observation contract v0（docs-only）

## 1. Document Identity

- Document type: contract (observation)
- Version: v0
- Status: canonical docs-only contract
- Session: `docs/sessions/session-201-pre.json`
- Acceptance: `docs/acceptance/session-201-pre.yaml`
- Upstream contracts:
  - worker_report: `docs/specs/worker_report_contract.md`（session-199 正本化予定）
  - judge_recommendation: `docs/specs/judge_contract.md`（session-200 正本化予定）
  - PCC display: `docs/specs/pcc_display_contract.md`（session-197-pre 正本化済み）

## 2. Purpose

本契約は、**worker_report** と **judge_recommendation** を PCC（Pre-Commit Check）および Commander が **read-only で観測可能な judge_observation artifact として接続する** docs-only 契約を正本化する。

本契約は **観測契約（observation contract）** であり、runtime の dispatch / queue 実行 / scheduler 割当 / dashboard 実行時 UI は本契約のスコープ外とする。

## 3. judge_observation schema（5フィールド）

judge_observation artifact は以下の5フィールドを持つ。各フィールドは宣言済みのフィールド名を正とする。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `worker_report_ref` | string (path) | worker が提出した report の参照パス（`docs/specs/worker_report_contract.md` に準拠）|
| `judge_recommendation_ref` | string (path) | judge が提出した recommendation の参照パス（`docs/specs/judge_contract.md` に準拠）|
| `observation_metadata` | object | 観測メタデータ（session_id / acceptance_ref / observed_at 等）|
| `pcc_display_fields` | object | PCC が表示に使用するフィールドセット（`docs/specs/pcc_display_contract.md` Section 6 準拠）|
| `final_decision_boundary` | string (enum) | 最終決定の境界宣言。値は `"commander_only"` に固定（自律 GO 禁止）|

### 3.1 additionalProperties

本 schema は `additionalProperties: false` を適用する。上記5フィールド以外のトップレベルフィールドを judge_observation artifact に含めない。

## 4. 禁止事項

### 4.1 worker self-approval 禁止

- worker は自身の report に対して GO/HOLD/FAIL を確定してはならない。
- worker は `status_proposal` のみを提出し、最終判定は judge を経由して Commander に委ねる。

### 4.2 autonomous GO 禁止

- judge_observation に基づく GO 発行を judge が自律的に行うことを禁止する。
- judge は `judge_recommendation` を提出するのみであり、実行 GO を確定しない。

### 4.3 L4 autonomy 禁止

- L4 レベルの自律実行（ヒューマン承認なしの自動 GO / 自動 FAIL 確定）を禁止する。

### 4.4 final_decision_boundary 固定

- `final_decision_boundary` の値は `"commander_only"` に固定する。
- **final GO / HOLD / FAIL の決定権は GPT Commander のみに帰属する。**

## 5. PCC read-only invariant（PCC 観測の不変条件）

- PCC は judge_observation artifact を **read-only** で観測する。
- PCC は judge_observation artifact を **書き換えない**。
- PCC は `pcc_display_fields` の内容を `docs/specs/pcc_display_contract.md` Section 6 の宣言順で表示する。
- PCC の観測は **filesystem-first**（リポジトリ上の正本ファイルの参照）に限定し、live queue / runtime の実行状態を primary にしない。

## 6. 上流契約との接続

| 上流 artifact | 正本パス | 正本化セッション | 現在の状態 |
|---|---|---|---|
| worker_report | `docs/specs/worker_report_contract.md` | session-199 | 未作成 |
| judge_recommendation | `docs/specs/judge_contract.md` | session-200 | 未作成 |
| PCC display | `docs/specs/pcc_display_contract.md` | session-197-pre | 作成済み |

> 上記パスのうち `docs/specs/worker_report_contract.md` および `docs/specs/judge_contract.md` は本契約起票時点で未作成である。本契約はこれら上流パスへの **forward reference（前方参照）** を宣言するにとどまり、ファイルの存在・内容の不変性を hash レベルで保証する対象に含めない。

## 7. 非スコープ

以下は本契約で要件化しない。

- routing heuristic の定義（別 session へ委譲）
- telemetry の定義（session-202 以降）
- deterministic routing freeze（session-203 以降）
- 補助 JSON schema ファイル（本 session では不作成）
- judge_observation artifact の physical storage path の freeze
- runtime dispatch / queue / scheduler / provider の挙動
- dashboard runtime および websocket / realtime sync を前提とした表示更新

## 8. 参照

- `docs/specs/pcc_display_contract.md`（session-197-pre 正本化済み）
- `docs/specs/worker_report_contract.md`（session-199 正本化予定・forward reference）
- `docs/specs/judge_contract.md`（session-200 正本化予定・forward reference）
- `docs/contracts/session_throughput_fastlane_v0.md`（運用契約・filesystem-first の根拠）

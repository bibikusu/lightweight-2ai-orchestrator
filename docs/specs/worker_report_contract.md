# worker_report contract v0（docs-only）

## 1. Document Identity

- Document type: spec (worker report contract)
- Version: v0
- Status: canonical docs-only contract
- Session: `docs/sessions/session-199.json`
- Acceptance: `docs/acceptance/session-199.yaml`
- Realized by: `docs/sessions/session-202-pre.json`

## 2. Purpose

本書は **worker が orchestrator / Commander に提出する report の最小契約** を正本化する。

worker は実行結果を `worker_report` として提出するが、**自身の report に対して GO/HOLD/FAIL を確定する権限を持たない**。最終判定は judge を経由して GPT Commander に委ねる。

## 3. worker_report schema

worker_report artifact は以下のフィールドを持つ。

| フィールド名 | 型 | 必須 | 説明 |
|---|---|---|---|
| `session_id` | string | 必須 | 対象 session の識別子（back-reference 必須） |
| `acceptance_ref` | string (path) | 必須 | 対応 acceptance YAML のパス（back-reference 必須） |
| `status_proposal` | string (enum) | 必須 | worker の状態提案。値は `pass_proposed` / `fail_proposed` / `blocked_proposed` のいずれか |
| `changed_files` | array of string | 必須 | 本 session で変更・作成したファイルのパス一覧 |
| `verification_summary` | string | 必須 | 実施した検証の要約（acceptance criteria の達成状況を記述） |
| `evidence_refs` | array of string (path) | 必須 | 検証根拠となるファイルパス一覧（filesystem 上の正本を参照） |
| `blocker_summary` | string or null | 必須 | 未解決の blocker がある場合にその要約を記述。blocker がない場合は `null` |

### 3.1 status_proposal の意味

| 値 | 意味 |
|---|---|
| `pass_proposed` | worker は AC 達成と判断。judge / Commander による最終確認待ち |
| `fail_proposed` | worker は AC 未達成と判断。judge / Commander による最終確認待ち |
| `blocked_proposed` | worker は実行ブロックを検出。blocker_summary に詳細を記述 |

## 4. 5原則

### 原則 1: worker self-approval 禁止

- worker は **自身の report に対して GO/HOLD/FAIL を確定してはならない**。
- worker は `status_proposal` のみを提出し、最終判定権を保持しない。
- **final GO / HOLD / FAIL の決定権は GPT Commander のみに帰属する。**

### 原則 2: filesystem-first reference

- worker_report の根拠とする情報は **filesystem 上の正本ファイル**（session JSON / acceptance YAML / 変更ファイル）から取得する。
- チャット本文の長文転記・LLM の都度生成テキストを `evidence_refs` の primary source にしない。
- `evidence_refs` に列挙するパスは **リポジトリ上に実在するファイルのみ** とする。

### 原則 3: status_proposal（worker は status を提案するのみ）

- worker は `status_proposal` フィールドに状態の提案値を記入する。
- worker は `status` を **確定しない**。確定は judge / Commander の責務。
- `status_proposal` は上記 3 値（`pass_proposed` / `fail_proposed` / `blocked_proposed`）のみを取る。

### 原則 4: back-reference 必須（session_id / acceptance_ref）

- worker_report には **`session_id`** および **`acceptance_ref`** を必ず含める。
- これにより judge / Commander が対応する acceptance 正本を特定できる。
- `acceptance_ref` は `docs/acceptance/<session_id>.yaml` の形式を正とする。

### 原則 5: PASS/FAIL 確定禁止

- worker は report において **PASS / FAIL を確定する語彙を使用してはならない**。
- 使用可能な語彙: `pass_proposed` / `fail_proposed` / `blocked_proposed`
- 禁止表現（例）: `"status": "PASS"` / `"result": "FAIL"` / `"final_result": "pass"` 等の確定語

## 5. 非スコープ

以下は本契約で要件化しない。

- `artifacts/` の exact path topology の freeze
- runtime storage hierarchy の確定・freeze
- execution artifact structure の確定・freeze
- orchestration / queue / scheduler / provider の挙動
- judge recommendation schema（`docs/specs/judge_contract.md` で定義）
- judge_observation schema（`docs/contracts/judge_observation_contract.md` で定義）

## 6. 参照

- `docs/sessions/session-199.json`（本契約の起票セッション）
- `docs/acceptance/session-199.yaml`（acceptance 正本）
- `docs/specs/judge_contract.md`（judge recommendation contract）
- `docs/contracts/judge_observation_contract.md`（observation contract）
- `docs/specs/pcc_display_contract.md`（PCC display contract）

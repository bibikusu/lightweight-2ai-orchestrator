# Decision Engine Complete Specification (Canonical)

本ドキュメントは Decision Engine 完成仕様の正本である。実装は本仕様に従う。
selector の上位レイヤーとして、selector_output (session-173-pre 仕様) を受け取り、queue 接続前の実行可否判断と queue_payload 生成を行う。

## 1. Responsibility

Decision Engine の責務は以下に限定する。

- selector_output (session-173-pre 仕様の output_schema) の受け取り
- queue_policy.yaml の解釈
- project_registry.json の解釈
- 実行可否の判定 (queue_route の決定)
- human_required 有無の判定
- queue_payload の生成
- decision_id および decision_reason の出力 (必須)
- 決定論的判断の保証

Decision Engine は以下を行わない。

- session の選択 (selector の責務)
- queue への enqueue 実行 (queue layer の責務)
- run_session の起動 (CLI 層 / scheduler の責務)
- Lock 取得 (Lock Manager の責務)
- Review 結果記録 (Review Engine の責務)
- Dashboard 表示 (presentation 層の責務)

## 2. Input Schema

Decision Engine は以下を入力として受け取る。

- selector_output: object
  - selected_session_id: str | null
  - execution_mode: "full_stack" | "fast_path"
  - selection_reason: str
  - candidate_sessions: list[object]
  - metadata: object
- project_registry: object (docs/config/project_registry.json)
- queue_policy: object (docs/config/queue_policy.yaml)
- current_queue_state: object (queue layer から渡される現在状態)

selector_output が selected_session_id: null の場合、Decision Engine は queue_payload を生成せず、queue_route = failed を返す。

## 3. Output Schema

Decision Engine は以下を出力する。**全フィールド必須**。

```json{
"decision_id": "string (UUID v4)",
"selected_session_id": "string | null",
"project_id": "string | null",
"execution_mode": "full_stack | fast_path",
"queue_route": "ready | blocked_human | retry_waiting | failed",
"human_required": "boolean",
"decision_reason": "string",
"queue_payload": {
"session_id": "string",
"project_id": "string",
"execution_mode": "string",
"priority_rank_value": "integer",
"scheduled_at": "string (ISO8601)"
},
"metadata": {
"selector_output_ref": "string (artifacts/selector/<timestamp>.json path)",
"policy_version": "string",
"generated_at": "string (ISO8601)"
}
}

queue_route が ready 以外の場合、queue_payload は空 object とする。

## 4. Queue Route Decision Rules

queue_route は以下の enum:

- `ready` — 即座に queue に enqueue 可能
- `blocked_human` — 人間判断が必要、enqueue を保留
- `retry_waiting` — 同一 session の retry 上限到達、再投入待機
- `failed` — 判定不能、enqueue せず失敗扱い

決定ルール (上から優先、最初に該当した条件で確定):

1. selector_output.selected_session_id が null → `failed` (理由: no_session_selected)
2. project_registry に project_id が存在しない → `failed` (理由: registry_mismatch)
3. queue_policy.human_required_conditions に該当 → `blocked_human`
4. previous_results.retry_count >= max_retries → `retry_waiting` (cooldown まで)
5. queue_policy で session_id が exclude 対象 → `failed` (理由: policy_excluded)
6. 上記以外 → `ready`

## 5. Human Required Determination

human_required = true の条件 (いずれか1つ満たせば true):

- queue_policy.yaml の human_required_conditions に session_id が一致
- session JSON の human_approval_required: true フラグが立っている
- previous_results に human_review_pending: true が記録されている
- project_registry の default_human_required: true (project 単位)

いずれにも該当しない場合は human_required = false。
human_required = true の場合、queue_route は必ず blocked_human となる。

## 6. Queue Payload Generation Contract

queue_route = ready の場合のみ、queue_payload を生成する。それ以外は空 object。

queue_payload 必須キー:

- session_id (str): selector_output.selected_session_id を継承
- project_id (str): project_registry.project_id_for_session_id() の結果
- execution_mode (str): selector_output.execution_mode を継承
- priority_rank_value (int): selector_output.candidate_sessions[i].priority_rank_value を継承
- scheduled_at (str): 現在時刻 ISO8601 (queue_policy で遅延指定があれば加算)

queue_payload は queue layer に渡される。queue layer がこの payload を受けて enqueue を実行する。Decision Engine は enqueue 自体を行わない。

## 7. Determinism Contract

Decision Engine は決定論的でなければならない。

- 同一 selector_output / 同一 project_registry / 同一 queue_policy / 同一 current_queue_state に対して、同一 (queue_route, human_required, queue_payload) を返す
- decision_id は UUID v4 (ランダム) のため決定論的でなくてよい (記録目的)
- metadata.generated_at も非決定論的でよい (記録目的)
- 上記以外のフィールドは全て決定論的とする

## 8. Output Persistence

Decision Engine の出力は以下に保存する。

- パス: artifacts/decision/<timestamp>.json
- 必須キー: decision_id / selected_session_id / project_id / execution_mode / queue_route / human_required / decision_reason / queue_payload / metadata
- timestamp は ISO8601 (例: 20260504T120100Z)

## 9. Layer Boundary

| 層 | 責務 | Decision Engine との関係 |
|---|---|---|
| selector (session-173-pre) | session 選択 | Decision Engine の入力を提供 |
| Decision Engine (本仕様) | 実行可否判断と queue_payload 生成 | 本仕様の対象 |
| queue layer | enqueue / dequeue / 状態管理 | Decision Engine の出力を消費 |
| Lock Manager (session-171) | 同時実行制御 | queue layer 内で連携 |
| Review Engine (session-172) | 結果記録 | Decision Engine の対象外 |
| run_session.py | 1 session 実行 | queue dequeue 後に起動 |
| scheduler | 定期実行 | Decision Engine を pipeline 内で呼び出す |
| Dashboard / UI | 可視化 | Decision Engine の出力を表示 |

Decision Engine は queue / run_session / scheduler / UI を直接操作しない。

## 10. Versioning

本ドキュメント v1.0 を canonical 起点とする。改訂時は metadata.policy_version をインクリメントすること。
selector_output 契約 (session-173-pre v1.0) との整合性を維持すること。selector が改訂された場合、Decision Engine も整合性確認を実施する。

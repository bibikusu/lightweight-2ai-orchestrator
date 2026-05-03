# session-174-pre 検収レポート (起票検収)

## セッション情報

- session_id: session-174-pre
- phase_id: phase-mc
- type: docs-only
- 起票日: 2026-05-04 (chat 49)
- 前提セッション: session-173-pre (selector 完成形 正本化)

## 判定

PASS (起票検収)

## Template C selfcheck 結果

| 項目 | 結果 |
|---|---|
| 必須キー 8 個 (session_id, phase_id, title, goal, scope, out_of_scope, constraints, acceptance_ref) | PASS |
| review_points 4 軸 (仕様一致 / 変更範囲遵守 / 副作用なし / 検証十分性) | PASS |
| allowed_changes_detail = list[str] | PASS |
| completion_criteria = object 配列 (id, type, condition) | PASS |
| AC / CC 1:1 対応 (補完 CC 含む、AC 11 + CC 17) | PASS |
| forbidden_changes が selector / decision / run_session 実装層を保護 | PASS |
| forbidden_changes が session-170/171/172 既存起票を保護 | PASS |
| forbidden_changes が session-173-pre 全成果物 (4 ファイル) を保護 | PASS |
| acceptance_ref = repository 相対パス | PASS |
| scope と out_of_scope が重複していない | PASS |
| allowed_changes と forbidden_changes が衝突していない | PASS |
| 5 ファイル以内 (4 ファイル新規作成) | PASS |
| 曖昧語なし | PASS |
| selector_output 契約 = session-173-pre の output_schema と整合 | PASS |

## 確認した正本性

- Decision Engine 完成仕様を docs/templates/decision_engine_complete_spec.md として正本化
- Responsibility 8 項目を明文化、selector / queue / Lock / Review / run_session / scheduler / UI との責務境界を明確化
- Input Schema (selector_output / project_registry / queue_policy / current_queue_state) を canonical 形式で定義
- Output Schema (decision_id / queue_route / queue_payload など 9 フィールド) を必須化
- queue_route の enum 4 値 (ready / blocked_human / retry_waiting / failed) を canonical 起点として固定
- Queue Route Decision Rules 6 ステップを上から優先順で明記
- human_required 判定ルール 4 条件を列挙
- queue_payload 生成契約 (ready 時のみ生成) を明文化
- Determinism Contract (decision_id / generated_at を除く全フィールド) を記述
- Layer Boundary を表形式で明記、selector / queue / run_session / scheduler / UI を直接操作しないことを契約化

## session-173-pre との整合確認

- selector_output schema (session-173-pre Section 3) ↔ Decision Engine Input Schema (本仕様 Section 2) は完全整合
- execution_mode enum (full_stack, fast_path) は両仕様で一致
- selected_session_id null 時の挙動 (selector が null 返却 → Decision Engine は queue_route = failed) は両仕様で一貫

## 結論

Decision Engine 完成仕様 正本化完了。M-C 設計フェーズ (selector + Decision Engine) の上位層が canonical として固定された。
chat 50 以降での実装フェーズ着手の前提条件を充足する。

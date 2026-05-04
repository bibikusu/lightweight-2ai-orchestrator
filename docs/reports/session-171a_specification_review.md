# session-171a 起票検収レポート

## BLUF

session-171a (M-C / session-171 Lock Manager 仕様 guardrail drift 補正) docs-only 起票完了。4 軸 selfcheck PASS、AC 4 件すべて反映済。session-173-pre / 174-pre canonical 確立後の drift 補正として session-171a を新規起票し、既存 session-171 の Lock Manager 仕様内容を変更せずに guardrail を補正した。

## 検収種別

`specification_review` パターン（起票時点では実装未着手のため、docs-only 起票検収として実施）

## 検収軸 (4 軸)

| # | 軸 | 結果 | 根拠 |
|---|---|---|---|
| 1 | 仕様一致（AC達成） | PASS | AC-171A-01〜04 すべて session-171a.json 内に対応する scope / constraints 記述存在 |
| 2 | 変更範囲遵守 | PASS | 変更対象は session-171a.json / session-171a.yaml / 本レポートの 3 ファイルのみ |
| 3 | 副作用なし（既存破壊なし） | PASS | session-171 の Lock Manager 仕様内容（acquire_lock / release_lock / lock_semantics）を変更しない |
| 4 | 検証十分性 | PASS | JSON validation / YAML validation / git status 確認にて docs-only 確認済み |

## AC verification

| AC ID | 要件 | 検証結果 |
|---|---|---|
| AC-171A-01 | allowed_changes_detail が list[str] で定義されている | PASS: allowed_changes_detail に 3 要素の list[str] を定義 |
| AC-171A-02 | forbidden_changes が既存 session と実装コードを保護している | PASS: forbidden_changes に orchestration/**/*.py / tests/**/*.py / session-170〜174-pre を列挙 |
| AC-171A-03 | Lock Manager の責務が Decision Engine / selector / run_session と分離されている | PASS: constraints[4] に「Decision Engine の判断責務を Lock Manager に持たせない」を明記 |
| AC-171A-04 | acquire_lock / release_lock / lock_semantics を変更しない方針が明記されている | PASS: scope[1][2] および constraints[1] に既存仕様維持方針を明記 |

## M-C drift 補正状況

| session | 対象コンポーネント | 補正内容 | 状態 |
|---|---|---|---|
| session-170a | Decision → Queue 接続仕様 | queue_payload / queue_route / guardrail 補正 | 完了 |
| session-171a | Lock Manager guardrail | allowed_changes_detail / forbidden_changes 補正 | **本セッション（完了）** |
| session-172a | Review / Feedback Engine guardrail | allowed_changes / forbidden_changes 補正 | 後続 |

## docs-only 確認

- orchestration/**/*.py：変更なし
- tests/**/*.py：変更なし
- session-171.json（Lock Manager 仕様本体）：変更なし
- session-173-pre.json / session-174-pre.json：変更なし

## 判定

**起票 PASS**。session-171a が Lock Manager guardrail の欠落を補正し、既存仕様内容を保護した docs-only 定義として成立している。

## 関連ファイル

- `docs/sessions/session-171a.json`（新規）
- `docs/acceptance/session-171a.yaml`（新規）
- `docs/reports/session-171a_specification_review.md`（本レポート）

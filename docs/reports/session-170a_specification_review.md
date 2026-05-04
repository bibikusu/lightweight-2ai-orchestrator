# session-170a 起票検収レポート

## BLUF

session-170a (M-C / session-170 Decision → Queue 接続仕様 canonical drift 補正) docs-only 起票完了。4 軸 selfcheck PASS、AC 4 件すべて反映済。session-173-pre / 174-pre canonical 確立後の drift 補正として session-170a を新規起票し、既存 session-170 を変更せずに guardrail を補正した。

## 検収種別

`specification_review` パターン（起票時点では実装未着手のため、docs-only 起票検収として実施）

## 検収軸 (4 軸)

| # | 軸 | 結果 | 根拠 |
|---|---|---|---|
| 1 | 仕様一致（AC達成） | PASS | AC-170A-01〜04 すべて session-170a.json 内に対応する scope / constraints 記述存在 |
| 2 | 変更範囲遵守 | PASS | 変更対象は session-170a.json / session-170a.yaml / 本レポートの 3 ファイルのみ |
| 3 | 副作用なし（既存破壊なし） | PASS | session-170/171/172/173-pre/174-pre および orchestration/**/*.py を変更しない |
| 4 | 検証十分性 | PASS | JSON validation / YAML validation / git status 確認にて docs-only 確認済み |

## AC verification

| AC ID | 要件 | 検証結果 |
|---|---|---|
| AC-170A-01 | queue_payload の必須キー 5 件が明示されている | PASS: scope[1] に session_id / project_id / execution_mode / priority_rank_value / scheduled_at の 5 キーを明示 |
| AC-170A-02 | queue_route が enum[ready,blocked_human,retry_waiting,failed] として明示されている | PASS: scope[2] および constraints[5] に enum 4 値を明示 |
| AC-170A-03 | allowed_changes_detail が list[str] で定義されている | PASS: allowed_changes_detail に 3 要素の list[str] を定義 |
| AC-170A-04 | forbidden_changes が既存 session と実装コードを保護している | PASS: forbidden_changes に orchestration/**/*.py / tests/**/*.py / session-170〜174-pre を列挙 |

## M-C drift 補正状況

| session | 対象コンポーネント | 補正内容 | 状態 |
|---|---|---|---|
| session-170a | Decision → Queue 接続仕様 | queue_payload 5キー / queue_route 4enum / guardrail 補正 | **本セッション（完了）** |
| session-171a | Lock Manager guardrail | allowed_changes / forbidden_changes 補正 | 後続 |
| session-172a | Review / Feedback Engine guardrail | allowed_changes / forbidden_changes 補正 | 後続 |

## docs-only 確認

- orchestration/**/*.py：変更なし
- tests/**/*.py：変更なし
- session-170.json / session-171.json / session-172.json：変更なし
- session-173-pre.json / session-174-pre.json：変更なし

## 判定

**起票 PASS**。session-170a が session-174-pre canonical に整合した guardrail を備えた docs-only 定義として成立している。

## 関連ファイル

- `docs/sessions/session-170a.json`（新規）
- `docs/acceptance/session-170a.yaml`（新規）
- `docs/reports/session-170a_specification_review.md`（本レポート）

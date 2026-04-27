# Project BACKLOG

軽量2AIオーケストレーター方式の未解決事項 / 改善候補を一元管理する BACKLOG 正本。

各項目は:
- ID: `BACKLOG-<CATEGORY>-NNN`
- 内容: 簡潔な説明
- 発生元: 発見セッション / 発見時期
- 優先度: high / medium / low
- 見積: 想定作業時間
- 対応予定: 対応候補セッション or "未定"

---

## Open BACKLOG(未対応)

### BACKLOG-CURSOR-COMMIT-GUARD-001

- **内容**: Cursor による untracked ファイル放置事故の再発防止
- **発生元**: session-137 / session-138(2026-04-18 〜 19)
- **状態**: session-141 のプロンプトに「事故再発防止」セクションを追加することで運用的に緩和済。Hook 側で自動化する余地あり
- **優先度**: low(運用ワークアラウンド済)
- **見積**: 20-30min
- **対応予定**: P7 Hooks 拡張(未定)

### BACKLOG-QUEUE-TEST-SPEC-MISSING-001

- **内容**: queue engine の spec_missing 明示テスト追加
- **発生元**: session-137(P6C 実装時)
- **影響**: spec_missing が human_gate に分岐するロジックは実装済だが、テストが暗黙的
- **優先度**: low
- **見積**: 10min
- **対応予定**: P7 完了後の軽量メンテ session

### BACKLOG-PATCH-001

- **内容**: `patch_apply` の fuzzy match / hunk 再解決による大型 HTML 対応
- **発生元**: Card Task session-12 / session-114
- **影響**: 2400 行超の HTML ファイルでは `patch_apply` が `context_mismatch` で失敗する構造的制約
- **優先度**: low(Cursor 直接実装で回避可能)
- **見積**: 調査含めて数時間
- **対応予定**: 本命プロジェクト(A02_fina / Card Task)の量産開始前に判断

### BACKLOG-SANDBOX-CLEANUP-001

- **内容**: 不要な sandbox ブランチ(41 本削除対象 + 17 本判定対象)の整理
- **発生元**: 運用蓄積
- **優先度**: low
- **見積**: 30-60min
- **対応予定**: 未定(P7 完了後の余裕時)

---

## Resolved BACKLOG(対応済)

### BACKLOG-PREFLIGHT-EXIT-CODE-001(解消済)

- **内容**: `scripts/preflight_session.sh` の終了コード設計を補正し、dirty worktree / branch sync NG / venv 不備 / session 定義不足で non-zero を返すようにした
- **解消セッション**: session-142
- **解消 commit**: `eb73021`
- **解消日**: 2026-04-20


### BACKLOG-DRIFT-DETECTOR-REVIEW-POINTS-001(解消済)

- **内容**: `drift_detector.py` の `EXPECTED_REVIEW_POINTS` を「実装過不足なし」から「検証十分性」に修正
- **状態**: 参謀 selfcheck により、既に正本は「検証十分性」と確認済(userMemories 2026-04-17)

---

## 管理原則

- 新規 BACKLOG は本ファイルに追記する
- 解消したら "Resolved BACKLOG" セクションに移動する(削除しない、履歴として残す)
- P7 以降はセッション作成時に本ファイルを参照し、関連項目があれば取り込みを検討する

---

### BACKLOG-RUFF-EXCLUDE-DL-001
**起票日**: 2026-04-26
**カテゴリ**: 開発環境 / lint
**優先度**: 中
**状態**: open

#### 内容
`DL/` 配下の外部ダウンロード品を `ruff check .` の対象から除外するかを、独立した production session として検討・実装する。

#### Action
- `pyproject.toml` の `[tool.ruff] exclude` に `DL` を追加する是非を独立sessionで判断する
- 実装する場合は4コマンド検証を行う
- 他の除外対象を便乗追加しない

#### chat 36 baseline 証跡
- **取得日**: 2026-04-27
- **取得元**: chat 36 / 4 command gate baseline 確認
- **実測値**:
  - `ruff check .`: exit=1 / 67 errors（うち 36 fixable）/ 全件 `DL/` 配下
  - `pytest -x --tb=line`: exit=1 / `test_aggregate_observation_reports.py::test_aggregate_reports_passes_validation_suite` 失敗（内部で ruff check を呼び出す連鎖失敗）
  - `mypy`: exit=0 / Success: no issues found in 17 source files
  - `compileall`: exit=0
- **影響範囲**: 修復セッション (session-149 / session-150) の AC を「全通過」から「baseline比較で悪化なし」に書き換える根拠となった
- **関連 commit**: 修復本体は session-150 / session-149 として完了 (chat 36)

---

### BACKLOG-ENV-PYPROJECT-001
**起票日**: 2026-04-26
**カテゴリ**: 開発環境 / pyproject
**優先度**: 低
**状態**: open

#### 内容
`pyproject.toml` の dev extras / flat-layout 前提を整理し、開発環境の再現性を高める。

#### Action
- 現在の `pyproject.toml` の依存・pytest・ruff 設定を棚卸しする
- dev環境の最小依存と任意依存を分ける
- ruff除外設定とは別sessionで扱う

---

### BACKLOG-UNTRACKED-LEFTOVERS-001
**起票日**: 2026-04-26
**カテゴリ**: Git運用 / 作業ツリー整理
**優先度**: 低
**状態**: open

#### 内容
`DL/` 配下の untracked 残存物について、保管継続・archive移動・削除候補のいずれかを判断する。

#### Action
- `DL/` の内容と由来を確認する
- repo管理対象にしない方針なら `.gitignore` / ruff exclude / archive のいずれで管理するか決める
- 本件単独で実施し、他変更と混ぜない

---

### BACKLOG-ALLOWED-CHANGES-CLARIFY-001
**起票日**: 2026-04-26
**カテゴリ**: セッション仕様 / allowed_changes_detail
**優先度**: 中
**状態**: open

#### 内容
`allowed_changes_detail` の記述規約を docs-only session と code session で分けて明文化する。

#### Action
- docs-only 用の記述例を追加する
- code session 用の記述例を追加する
- `allowed_changes` と `forbidden_changes` の衝突判定例を追加する

---

### BACKLOG-DIRECTIVE-PROPAGATION-001
**起票日**: 2026-04-27
**カテゴリ**: 規律 / 司令塔指示の伝達
**優先度**: 中
**状態**: open

#### 内容
司令塔判断を Cursor 投入ブロックへ反映する際、判断項目ごとの反映チェックリストを必須化する。chat 36 において、司令塔判断 #2 (`repair_context` フィールド削除) の Cursor投入ブロックへの反映が漏れ、追加補正タスクが必要となった事象を再発防止する。

#### Action
- 司令塔判断項目を逐条リストアップし、Cursor投入ブロック内の「実施事項」「禁止事項」のいずれかに反映されているかを確認する手順を明文化する
- 参謀selfcheckチェックリストに「司令塔判断項目の反映漏れ確認」を追加する
- chat 36 事例 (`repair_context` 削除指示反映漏れ) を再発防止学習の記録として残す

---

### BACKLOG-PUSH-STATE-DETECT-001
**起票日**: 2026-04-27
**カテゴリ**: Git運用 / push状態検出
**優先度**: 低
**状態**: open

#### 内容
`origin/<branch>` がローカル ref として存在しない場合、`git log origin/<branch>..HEAD` は stderr 抑制下で「未push数=0」のような誤解を生む出力をする。push状態の自動検出機構にフォールバックを追加し、ref不在時は判定不能を明示する。

#### Action
- `origin/<branch>` ref の存在確認を push状態判定の前段に追加する
- ref不在時は「判定不能（fetch要 or upstream未設定）」を明示する出力にする
- chat 36 Diag-A5 で初出した事例を再発防止する

---

### BACKLOG-DUPLICATE-INVOCATION-001
**起票日**: 2026-04-27
**カテゴリ**: 規律 / 実行制御
**優先度**: 高
**状態**: open

#### 内容
人間オペレーションにおいて、同一Cursor投入ブロックの再実行（コピペ再投入）が発生し、重複処理・二重commit・状態不整合のリスクがある。

chat 36 にて、同一ブロック再投入が発生しうる構造的問題を確認。

#### 原因
- chat往復による状態認識ズレ
- 「完了済みか未実行か」の判定が人間依存
- run_session に冪等性チェックが存在しない

#### Action
- session単位での「実行済み判定」仕組みの検討（state.json / completed_stages拡張）
- 同一session再実行時の自動STOP条件定義
- Cursor投入前チェックリストの制度化

---

## BACKLOG-CURSOR-AUTO-STOP-001
**status**: open
**discovered_in**: chat 38 #2
**summary**: Cursor が bash 内 non-zero exit 検知時に独断停止する挙動を確認。投入文に書かれていない `|| code=$?` を Cursor が独断追加して自己補正する例も観測。
**impact**: 4-gate 連続実行が保証されない / 投入文 drift 発生
**proposed_fix**: 投入文 template に `|| code=$?` を正本化 (BACKLOG-4GATE-IDIOM-001 と連動)、または Cursor 側に「指示外の bash 改変を禁止」する規律を明文化

## BACKLOG-DIRECTIVE-PROPAGATION-002
**status**: open
**discovered_in**: chat 38 #2
**summary**: BACKLOG-DIRECTIVE-PROPAGATION-001 の再発。司令塔承認版投入文と Cursor 実投入版が乖離 (修正1+2+3 のうち 2/3 が抜けて投入された)。
**impact**: 参謀 selfcheck を通過した投入文が経路上で改変される / 規律ガード無効化リスク
**proposed_fix**: 投入文を Cursor へ渡す経路の整合性確保 (コピペ精度 / 中間処理の有無確認)

## BACKLOG-4GATE-IDIOM-001
**status**: open
**discovered_in**: chat 38 #2 続行
**summary**: 4-gate 連続実行を保証する idiom として `; echo "exit=$?"` および `|| code=$?` を投入文 template に正本化する必要。
**impact**: 投入文ごとに idiom が揺れる / chat 38 #2 で auto-stop 誘発
**proposed_fix**: master_instruction.md または global_rules.md に 4-gate 標準 template を明記

## BACKLOG-HANDOFF-PRECISION-001
**status**: open
**discovered_in**: chat 38 Step 1-3
**summary**: chat 37 引き継ぎサマリの sandbox/session-146-pre 記述「5 commits 全件 main 反映済」が実体「10 commits / うち chat 35 残務 5件未反映」と齟齬。chat 跨ぎの引き継ぎ精度問題。
**impact**: chat 38 で sandbox 削除を試みた際に判断材料不足 / 数ターンの調査工数が発生
**proposed_fix**: chat 終了時の引き継ぎサマリ生成ルールに「sandbox / branch HEAD と main 反映状況の patch-id 検証ステップ」を組込

# PCC display contract v0（docs-only）

## 0. 目的とスコープ

本書は **PCC（Pre-Commit Check / 事前検証コンテキスト）を「表示・参照」する側の契約** を文書正本化する。  
**runtime の dispatch・queue 実行・scheduler 割当・provider 呼び出し・dashboard の実行時 UI・websocket・realtime sync は本契約のスコープ外** とし、**実装コードを定義しない**。

## 1. filesystem-first

- PCC 関連の参照対象は **リポジトリ上のファイルパス** を正とする（チャット本文の長文転送や都度生成テキストを primary source にしない）。
- 典型パス（例・非網羅）:
  - `docs/sessions/*.json`
  - `docs/acceptance/*.yaml`
  - `docs/specs/*.md`
- 表示・照会は **上記のようなパスに対する存在確認・内容読取（read）** に限定し、**実行時ストリームを前提としない**。

## 2. deterministic semantics（表示の決定性） / deterministic rendering

- **deterministic rendering**: 表示内容は **参照元ファイルの宣言値** および **本書に列挙した語・順序** からのみ導出し、チャット要約・LLM の都度生成文を **正（source of truth）にしない**。
- **表示ラベル**（例: session_id, phase_id, AC id）は **文書に列挙された語** を用い、都度の自由生成ラベルを正としない。
- **並び順**は文書または参照元ファイル内の **宣言順** を正とし、実装依存の暗黙ソートを定義しない。
- **真偽・列挙**は `pass` / `fail` / `not_applicable` 等、**別文書で定義済みの語彙**に合わせる（本書では新たな runtime 状態機械を定義しない）。
- **PCC 8 フィールド帯**の並びは **Section 6 の宣言順**（`current_session` → … → `judge_state`）を正とする。

## 3. 明示的非スコープ（禁止領域との整合）

以下は **本契約で要件化しない**（別セッションまたは実装フェーズへ委譲）。

- `orchestration/**/*.py` の挙動
- `queue/**` の runtime 動作
- `scheduler/**` の runtime 動作
- `provider/**` の実装
- **dashboard runtime**（実行中 UI の更新契約）
- **websocket** および **realtime sync** を前提とした表示更新

## 4. PCC display の最小定義

**PCC display** とは、人間またはツールが **filesystem 上の正本ファイル** を根拠として、次を **短文・反復可能** に確認できる状態を指す。

1. 対象 `session_id` の session JSON が存在する。
2. `acceptance_ref` で指された acceptance YAML が存在し、`session_id` が一致する。
3. `allowed_changes_detail` に列挙されたパスの範囲に変更が収まっている（人間または `git diff --name-only` による確認）。

## 5. read-only invariant（読み取り専用不変条件）

- PCC display における **正本への働きかけは read（存在確認・内容読取）に限定**する。
- **禁止**: 参照元ファイルの書き換え、ロック、副作用のあるコマンド実行を「表示の前提」として必須化すること（本書は docs-only / filesystem-first の閲覧契約である）。
- **runtime 更新**（queue / scheduler / websocket 等）に依存する「最新化」は本契約の primary path に含めない（Section 3 参照）。

## 6. PCC 8 フィールド（表示スロット）と出典

以下 8 名は **表示用スロット識別子** とする。値は **各出典パス上の JSON/YAML/Markdown の宣言** から取得し、無い場合は **空・`null`・`not_applicable` のいずれかを文書化済み語彙で表す**（推測補完しない）。

1. **`current_session`**
   - **出典パス**: `docs/sessions/<session_id>.json`
   - **出典決定規則**: 表示対象の `<session_id>` は呼び出し側が与える。ファイルが存在しない場合は当スロットは未解決（表示不可）。

2. **`next_action`**
   - **プロジェクト横断ビュー（例: 10 プロジェクト）の出典パス**: `docs/projects/<project_id>/state.json` の **`next_action` キー**（推奨フィールド。スキーマは `docs/schemas/project_state.schema.json`）。
   - **構造（variant / shape）の語彙正本**: `docs/schemas/next_action_v0.json`（binding・dispatch は本書で定義しない）。
   - **出典決定規則**: セッション単体ビューでは、当該 `session_id` の session JSON の `goal` / `scope` は **補助説明** に限り、**next_action artifact のファイル連鎖**（`docs/specs/next_action_artifact_contract_v0.md` 等のセッションが指す正本）が明示されている場合にのみ primary とみなす。

3. **`blocker`**
   - **出典パス（プロジェクト）**: `docs/projects/<project_id>/state.json` の **`blockers`**（キーが存在し非空配列なら、その宣言順で要素を列挙。スキーマ外キーでも **ファイル上に宣言されていれば** 表示の根拠としてよい）。
   - **出典（セッション）**: `docs/sessions/<session_id>.json` の **`failure_type`** および **`constraints` 配列の文字列**（宣言テキストのみ）。明示キーが無い場合、チャットログから blocker 文を合成しない。

4. **`waiting_human`**
   - **出典パス**: `docs/projects/<project_id>/state.json` の **`waiting_for`** / **`status`**（`docs/schemas/project_state.schema.json` の enum に準拠）。
   - **出典決定規則**: `waiting_for` が `human_cherry_pick` または `human_external_input` のとき、または `status` が `waiting` で `waiting_for` が人間系の値であるときに人間待ちを示す（**ポリシー説明の参照**として `docs/config/queue_policy.yaml` の `waiting_human` / `route_to_waiting_human_on` を読んでもよいが、**live queue の実行状態は正本にしない**）。

5. **`queue_status`**
   - **出典決定規則**: **live queue / runtime の実行状態を primary にしない**。リポジトリ内に **保存済み snapshot** として明示パスが存在する場合のみ（例: `docs/reports/**/*.json` に当該キーが記録されている）そのファイルを出典とする。該当ファイルが無い場合は **`not_applicable`**（または非表示）。

6. **`recent_failures`**
   - **出典パス（プロジェクト）**: `docs/projects/<project_id>/state.json` の **`last_error`**（必須キー。`null` でなければ直近の失敗メッセージの正）。
   - **出典決定規則**: 複数件の履歴が必要な場合、**セッションまたは acceptance が明示引用するログファイル** に限りそのパスを追加出典とする。無ければ `last_error` のみを正とする。

7. **`dependency_state`**
   - **出典パス**: `docs/projects/<project_id>/state.json` の **`current_phase`**, **`current_session_id`**, **`status`**, **`waiting_for`**, **`blockers`**（存在する場合）を **積み上げ表示の正** とする。
   - **出典決定規則**: 外部依存グラフを別ファイルで持つ場合は、**session JSON または acceptance がそのパスを明示引用しているときのみ** 併用出典とする（暗黙のグローバル探索は禁止）。

8. **`judge_state`**
   - **出典パス**: `docs/sessions/<session_id>.json` に **判定結果を表すトップレベルフィールド**（例: `failure_type`）が存在する場合はその値。
   - **出典決定規則**: 別ファイルに judge 出力が保存されている場合、**当該 session がパスを明示引用しているときのみ** そのファイルを出典とする。いずれも無い場合は **`not_applicable`**。チャット要約を judge_state の正にしない。

## 7. `test_pcc_*` の AST テスト命名規約

- **プレフィックス**: Python のテスト関数名は **`test_pcc_`** で始める（**PCC 表示契約**または **`pcc_display_contract.md`** に紐づく検証に限定）。
- **AST 照合の意図**: `docs/sessions/<session_id>.json` の `acceptance_criteria[].test_name`、または `docs/acceptance/<session_id>.yaml` の `test_name` と、テストモジュール内の `def test_pcc_...` を **同一文字列**で対応付け、静的に存在確認する（セッションごとに命名を揺らさない）。
- **推奨形**: `test_pcc_<対象>_<観点>`（snake_case）。例: `test_pcc_display_filesystem_first_primary`（本リポジトリの session-197-pre における AC と一致）。
- **禁止**: `test_pcc_` を PCC と無関係な一般回帰テストに流用しない（grep / CI の意味分解能を落とすため）。

## 8. 参照

- `docs/schemas/next_action_v0.json`（構造不変量の正本。本書では binding ロジックを定義しない）
- `docs/schemas/project_state.schema.json`（`docs/projects/*/state.json` のフィールド意味の参照）
- `docs/contracts/orchestration_contract_v0.md`（descriptive 文脈）

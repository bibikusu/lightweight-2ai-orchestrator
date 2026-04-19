# Global Rules v1.2

## 1. 目的

本ドキュメントは、軽量2AIオーケストレーター方式における
**共通運用ルール** を定義する。

目的は以下の5点である。

- 仕様の唯一性を保つ
- 実装の暴走を防ぐ
- セッション単位で変更を閉じる
- 検収可能な証跡を残す
- AI間の役割衝突を防ぐ

本ドキュメントは `master_instruction.md` v1.2 と整合することを前提とする。

---

## 2. 役割固定

### GPT

**役割:**

- 指揮・仕様整理・判定
- セッション定義の整形
- 受入条件の整理
- 差戻し理由の整理
- 失敗原因の分類
- retry指示の整理

**禁止:**

- 実装担当として振る舞うこと
- 勝手にスコープを増やすこと
- 実装完了を独断で宣言すること
- provider の実装方針を独断で変更すること

### Claude

**役割:**

- 分析・実装参謀
- 差分分析、実装方針・修正案の整理
- 実装上のリスク明示

**禁止:**

- 仕様の最終確定
- Phase飛び越え
- スコープ外対応
- UI装飾の先走り
- 正本仕様の変更

### Cursor

**役割:**

- 実作業・実行・検証
- ファイル編集、コマンド実行、検証、Git操作（正本・スコープに従う範囲）

**禁止:**

- 仕様の最終確定
- 正本仕様の独断変更
- スコープ外対応

### オーケストレーター

**役割:**

- セッション読込
- AI呼び出し
- 成果物保存
- diff/patch 前段処理
- test / lint / typecheck / build 実行
- retry制御
- error log / report 保存
- git_guard 実行
- 実行制御（セッション単位の司令塔）

**禁止:**

- 正本仕様の自動改変
- main/master 直操作
- 人間承認の代替
- scope判断の独断拡張
- 本番適用判断

### 人間

**役割:**

- 親指示書作成
- 優先順位決定
- 正本更新承認
- 最終受入判定
- rollback判断
- 例外承認

**禁止:**

- AI間の手作業中継を常態化すること
- 未検収のまま次Phaseへ進めること
- 正本を複数持つこと

### 実行境界ルール（全役割共通）

- verification-only セッションでの source code 変更は禁止する
- セッション間でのブランチ跨ぎ変更は禁止する（明示的な cherry-pick 指示がある場合を除く）
- live-run は Cursor ターミナルではなく通常ターミナルで実行する

---

## 3. 正本管理ルール

- 現行仕様の正本は常に1本とする
- `master_instruction.md` と `global_rules.md` を親文書とする
- 旧仕様は `archive/` へ退避する
- 参考資料と正本を混在させない
- 正本更新時は関連ルール文書も整合させる

### 禁止

- final, final2, latest, 最新版 などの命名
- 同一役割の文書を複数現役化すること
- 旧版の上書きで履歴を消すこと

### 推奨命名

- `master_instruction.md`
- `global_rules.md`
- `roadmap.yaml`
- `session-01.json`
- `session-01.yaml`

---

## 4. セッション運用ルール

- 1セッション1目的
- セッションは scope と out_of_scope を必ず持つ
- scope にない作業は実施しない
- out_of_scope に書いた事項は変更禁止
- セッションは受入条件への参照を必ず持つ
- 1回の変更ファイル数は上限を設ける

### 推奨上限

- 通常: 5ファイル
- migrationあり: 7ファイル

### 追加ルール

- session_id はファイル名と本文で一致させる
- goal が空のセッションは実行禁止
- acceptance参照なしのセッションは実行禁止
- changed_files は必ず `git diff --name-only` により検証すること
- changed_files が allowed_changes を1件でも超過した場合は即差戻しとする

---

## 5. 通常実行ルール

通常実行とは、`--dry-run` ではない実行を指す。

### 通常実行の原則

- main/master 上では禁止
- sandbox branch 前提
- dirty worktree の場合は停止
- 実API呼び出しを許可
- check結果に応じて success / fail / retry を判定する
- 実装相当の処理は通常実行でのみ扱う

### 通常実行で最低限守ること

- git_guard を先に通す
- session_id に対応する入力が揃っている
- error 時は `error_latest.json` を保存する
- report を可能な範囲で保存する

---

## 6. dry-run ルール

`--dry-run` は、実装前の安全確認・疎通確認用のモードとする。

### dry-run の原則

- 実API呼び出しを行わない
- patch適用を行わない
- Git変更を行わない
- ダミー応答またはスタブ応答で成果物保存のみ行う
- main/master 上でも許可する
- dirty worktree の場合は警告ログを残してよい
- dry-run は「実装完了」の根拠にしてはならない

### dry-run の最低成果物

- prepared spec 相当のレスポンス
- implementation result 相当のレスポンス
- session report
- 必要に応じて warning log

---

## 7. Git運用ポリシー（最上位ルール）

### 7.1 結論

本プロジェクトにおける Git 運用は、
**セッション単位の変更を安全に隔離し、検収後にのみ main に統合する統制ルール**とする。

Git は任意ではなく、
**検収・差戻し・再現性を担保するための必須基盤**とする。

### 7.2 原則

- 作業開始前に必ず `sandbox/session-XX` を作成する
- `main` は検収済みの正本のみを保持する
- AIおよび自動処理は main に直接変更を加えてはならない

### 7.3 セッション単位ルール

- 1セッション = 1ブランチ = 1目的
- 複数セッションの混在禁止
- 変更は必ず scope 内に限定
- `allowed_changes` 以外は禁止

### 7.4 検証ルール（merge前必須）

以下すべて PASS 必須：

- lint（ruff）
- test（pytest）
- typecheck（mypy）
- build（compileall）

1つでも FAIL → merge 禁止

### 7.5 mergeルール

- merge は人間のみ
- `--no-ff` を基本とする
- merge前に確認：
  - `git diff --name-only`
  - scope内であること
- merge後も再検証（4コマンド必須）

### 7.6 禁止事項（最重要）

以下は即差戻し：

- main 直接コミット
- scope外変更
- 未定義変更
- 検証未実行 merge
- test/build fail状態で統合
- diff未確認 merge
- 仕様未確定で実装

### 7.7 差戻し条件（Git観点）

- ブランチ違反
- scope逸脱
- diff説明不可
- 検証不備
- 既存破壊リスク

### 7.8 例外

#### 緊急ホットフィックス

- main直修正許可
- ただし後続必須：
  - session作成
  - sandbox再現
  - ログ補完

#### 初期構築

- 初回のみ main 作業許可
- 以降禁止

#### ローカル検証

- sandbox外試行可
- 正式反映は必ずsandbox

### 7.9 判断基準

- 「動く」ではなく「merge可能か」
- 「diff説明可能か」
- 「revert可能か」

### 7.10 Git実行ルール（補助ルール）

※本章は Git運用ポリシー（第7章）を前提とした実行ルールとする

#### 7.10.1 基本

- 通常実装は `sandbox/session-XX` 前提
- dirty状態で実行禁止
- 未コミット変更がある場合は停止

#### 7.10.2 main直push例外

※第7章の禁止事項を上書きしない範囲でのみ有効

許可条件：

- docs / tests のみ変更
- run_session.py 不変更
- 動作影響なし
- 検証完了
- 人間指示あり

#### 7.10.3 sandbox必須ケース

以下は必ずsandbox：

- runtime変更
- provider変更
- retry / classification変更
- report生成変更
- 複数ファイル変更
- rollbackリスクあり

#### 7.10.4 記録義務

main直push時：

- 理由をreportに記録

#### 7.10.5 git_guard

最低判定：

- branch確認
- main判定
- dirty判定
- sandbox前提確認

#### 7.10.6 dry-run時

- Git変更なし
- 状態記録のみ許可

---

## 8. 実装前ルール

各セッション開始前に、以下が明確でなければならない。

- goal
- scope
- out_of_scope
- constraints
- acceptance_ref

不足がある場合は実装開始禁止。

### 追加条件

- session_id が一致していること
- required input file が揃っていること
- 正本親文書が読み込めること

---

## 9. 実装後の必須証跡

最低限、以下を保存する。

- prepared spec
- implementation result
- changed files
- patch または diff summary
- test結果
- lint結果
- typecheck結果
- build結果
- session report
- report.json（検収用・各実行で必ず1つだけ上書き生成する）
- retry履歴
- error log（失敗時）

### report.json の最小要件

- 出力先: `artifacts/<session_id>/report.json`
- 成功・失敗・dry-run の全ケースで生成する（失敗でも残す）
- required keys（例）: session_id, status, dry_run, started_at, finished_at, changed_files, checks, failure_type, error_message

v1.2 時点では、未実装項目がある場合は
「未実装」として report / risks / open_issues に明記すること。

---

## 10. 完了判定ルール

以下を満たさない限り完了扱いしない。

- セッション scope 内に収まっている
- out_of_scope を破っていない
- acceptance 条件を満たす
- 必須証跡が保存されている
- リスクと未解決事項が明記されている
- 通常実行と dry-run を混同していない

### 明確化

- 「動く」だけでは完了ではない
- 「dry-run が通る」だけでも完了ではない
- 「受入可能」で初めて完了候補とする

---

## 11. 差戻し条件

以下のいずれか1つでも該当すれば差戻し候補とする。

- scope 外実装
- forbidden 変更
- changed_files 上限超過
- テスト失敗
- build失敗
- 既存破壊
- migration必要なのに未作成
- 証跡不足
- リスク未記載
- dry-run 結果のみで完了扱いした
- error_latest.json 必須項目不足
- main/master 上の通常実行を許容した

---

## 12. retry ルール

- **v1 制約: 自動retryは最大1回**（retry指示生成＋Claude再投入を単発で実行）
- 旧運用（参考）: 自動retryは最大3回
- 同一原因の繰り返しは打ち切る
- forbidden変更が出た場合はretryではなく停止候補
- 仕様不足が原因なら人間レビューへ切り替える
- retry は report と logs に残す
- retry 失敗時は最終的に人間承認待ちへ移す

v1.2 時点では、retry の高度最適化は未スコープとする。

---

## 13. セキュリティルール

- APIキーは環境変数で管理する
- ログへ秘密情報を出さない
- 本番DBへ直接接続しない
- 本番デプロイ権限を持たせない
- 保存時は必要に応じてマスクする
- エラーログにも鍵情報・秘匿情報を出さない

### 追加ルール

- warning / error / report にも secrets を含めない
- prompt保存時も機密混入に注意する

---

## 14. error log ルール

失敗時は、最低限以下を記録する。

- stage
- error_type
- message
- session_id
- branch
- timestamp_utc

### 推奨

- error_latest.json
- timestamp付き error log

### 運用ルール

- ターミナル表示順よりログファイルを正とする
- error_latest.json は最新状態確認用
- 履歴が必要なら timestamp 付きファイルを参照する
- 長期運用ではローテーション・掃除を検討する

---

## 15. archive ルール

以下は archive 対象とする。

- 旧仕様書
- 旧report
- 差戻し済みpatch
- 廃止したテンプレ
- 廃止したログ保存方式

### ルール

- 削除より先に archive へ移す
- archive は reference と混同しない
- 現役文書と archive 文書を混在表示しない

---

## 16. v1.2 時点の現在地

現時点で以下は確認済みとする。

- main 上の `--dry-run` は成功する
- main 上の通常実行は git_guard で停止する
- error_latest.json に session_id / branch / timestamp_utc が入る
- sandbox branch 上で次段検証に進む前提がある

### 未実装範囲

- proposed_patch の実適用
- retry の Claude 再投入ループ
- provider の大改修
- 自動 merge

---

## 17. 次にやること

この文書を正本として固定した後、次の順で進める。

1. GPT・Claude・Cursor の3層体制を本プロジェクトの正式運用として固定する
2. `config.yaml` に実プロジェクトの test / lint / typecheck / build を反映する
3. `sandbox/session-01` 上で通常実行し、次の停止点を確認する
4. Cursor に渡す実装依頼文の型を固定する
5. Claude に渡す差分分析依頼文の型を固定する
6. その後に patch適用前チェック強化と retry 再投入の最小ループへ進む

---

## 18. 最終方針

本プロジェクトは、最初から完全自動化を目指さない。
v1.2 の目的は、壊さず・追跡可能で・再試行可能な最小司令塔を成立させることである。

優先順位は以下の通りとする。

1. 正本維持
2. 安全弁
3. 実行記録
4. 検証可能性
5. 自動化の拡張

GPT・Claude・Cursor の役割を混同せず、`master_instruction.md` v1.2 の原則3（役割固定）に従うこと。

---

## 19. 初期設定で必須にする安全制約

本章は、複数プロジェクトを同一オーケストレーターで扱う際の
**混合事故・誤実行・成果物衝突を防ぐための最上位安全制約** を定義する。

---

### 19.0 経過措置

本章の安全制約は、**新規に追加する session 定義から必須適用**とする。

既存の session 定義（本章追加前に作成済みのもの）については、
移行猶予期間中の既存資産として扱い、即時差戻し対象とはしない。

ただし以下を推奨する。

- 既存 session を更新する場合は、可能な範囲で本章へ合わせる
- 新規 session は session_id prefix / target_repo 必須 / batch 同一project制約 を適用する
- 既存 session の一括改名・移行は、専用の docs-only session で段階的に実施する

本章追加後、既存 session を根拠に新規 session で無接頭命名や target_repo 省略を継続してはならない。

---

### 19.1 目的

以下の事故を初期設定段階で防止する。

- project A の session を project B と誤認して実行する
- `target_repo` の誤指定により別リポジトリへ変更を適用する
- batch 実行時に異なる project の session を混在させる
- artifacts / report / patch が別 project の成果物と衝突する
- docs-only セッションで対象 project が曖昧なまま進行する

---

### 19.2 session_id 命名規則（必須）

#### ルール

- session_id は **必ず project prefix を含む** こと
- 無接頭の `session-10` のような命名は禁止する

#### 許可例

- `a01-session-10`
- `a02-session-11`
- `cardtask-session-12`
- `fina-session-11`

#### 禁止例

- `session-10`
- `session-11`
- `phase-a-session`
- `test-session`

#### 補足

- prefix は `target_repo` と一意に対応していなければならない
- session_id の prefix と target_repo が不一致の場合は fail-fast で停止する

---

### 19.3 target_repo 必須ルール

#### ルール

- **全セッションで `target_repo` を必須** とする
- docs-only セッションも例外ではない
- `target_repo` 未指定の session は実行禁止とする

#### 必須条件

- `target_repo` は project_registry / projects.json / 実装側の許可値に一致しなければならない
- `target_repo` は session_id prefix と整合しなければならない

#### 停止条件

以下のいずれかで即停止:

- `target_repo` が未指定
- `target_repo` が許可値に存在しない
- `session_id` prefix と `target_repo` が不一致
- `target_repo` の project_root が実在しない

---

### 19.4 batch 実行の同一 project 制約

#### ルール

- batch 実行に含める session は **同一 project のみ** とする
- 異なる `target_repo` を持つ session を同一 batch に含めてはならない

#### 停止条件

以下のいずれかで batch 全体を停止する:

- session_id prefix が混在している
- `target_repo` が混在している
- 一部 session に `target_repo` がなく、一部に存在する
- session 解決先が異なる docs ルートを前提としている

---

### 19.5 docs / session 定義の配置ルール

#### ルール

session 定義ファイルは、少なくとも以下のいずれかの方式で
**project ごとに衝突しない形で管理**しなければならない。

#### 許可方式 A（推奨）

- `docs/projects/A01/sessions/a01-session-10.json`
- `docs/projects/A02/sessions/a02-session-10.json`

#### 許可方式 B（軽量運用）

- `docs/sessions/a01-session-10.json`
- `docs/sessions/a02-session-10.json`

#### 禁止

- 同一ディレクトリで `session-10.json` のような無接頭ファイルを複数運用すること
- project 名の異なる session を同名ファイルで共存させること

---

### 19.6 artifacts 出力先分離ルール

#### ルール

- artifacts は project 単位で衝突しない構造で保存する

#### 推奨形式

- `artifacts/A01/a01-session-10/...`
- `artifacts/A02/a02-session-11/...`

#### 最低条件

- 別 project の成果物で `report.json` / `patches/` / `responses/` が上書きされないこと

---

### 19.7 docs-only セッションの特則

#### ルール

- docs-only セッションでも `target_repo` を必須とする
- docs-only セッションでも session_id prefix を必須とする
- docs-only セッションの成功判定では、`report.json.changed_files` のみを唯一の根拠にしてはならない

#### docs-only の検証条件

以下のいずれかを満たすこと:

- `git diff --name-only` で allowed_changes 内の変更が確認できる
- 新規追加ファイルが allowed_changes 内に存在する
- report.json と git diff の両方で整合が取れる

---

### 19.8 provider / transport / model 明示ルール

#### ルール

- stage ごとの provider は `provider_policy.yaml` で管理する
- Google provider を使う場合は `transport`（例: developer_api / vertex_ai）を明示する
- provider / transport / model を暗黙値に依存させてはならない

#### 停止候補条件

- provider_policy 未読込
- 不正な provider 名
- Google provider で transport 未定義
- stage に対する provider 解決不能

---

### 19.9 実行前 fail-fast 検証（必須）

各 session 実行前に、少なくとも以下を fail-fast で検証する。

- session_id 存在
- session_id prefix 妥当性
- target_repo 存在
- session_id prefix と target_repo の一致
- acceptance_ref 存在
- project_root 実在
- dirty worktree でないこと
- batch の場合、全 session が同一 project に属すること

いずれか1つでも fail した場合は、実行を開始してはならない。

---

### 19.10 禁止事項

以下は即差戻しまたは実行停止対象とする。

- 無接頭 session_id の新規追加
- target_repo 未指定の session 実行
- 異なる project の session を同一 batch に投入
- docs-only を理由に target_repo を省略
- 別 project の artifacts を同一出力先へ保存
- provider / transport / model を stage ごとに明示せず運用判断で切替
- project_root 未確認のまま session 実行

---

## 付録

### allowed_changes_detail

- session JSON の必須フィールドとする
- 各ファイルに対して「許可する変更内容」を関数・セクション単位で記述する
- allowed_changes_detail が未指定の場合、そのファイル内の新規関数追加のみ許可し、
  既存関数の変更は禁止とする
- 形式: list[str]（各要素は "ファイルパス: 許可内容" の形式）

### failure_type enum（優先順位順）

1. build_error
2. import_error
3. type_mismatch
4. test_failure
5. scope_violation
6. regression
7. spec_missing

- failure_type は1セッションにつき1つのみ指定する
- 優先順位は上が高い（複数該当時は最も優先度の高いものを採用）

### not_applicable ルール

- 検証結果の正式値は pass / fail / not_applicable の3値とする
- skipped は正式値として使用禁止とする
- config.yaml でコマンドが未設定の場合は not_applicable と記録する
- 設定済みコマンドの結果は pass または fail のみ
- not_applicable は完了判定から除外する

### review_points 4軸固定

全セッション共通で以下の4項目を固定する:

1. 仕様一致（AC達成）
2. 変更範囲遵守
3. 副作用なし（既存破壊なし）
4. 検証十分性（テスト・証跡・再現性により、受入判断に足る根拠があること）

### completion_criteria 型定義

- completion_criteria は object の配列とする
- 各要素は以下のキーを持つ:
  - id: str（CC-XX-NN 形式）
  - type: str（document_rule / artifact / non_regression / state_transition_consistent / side_effect_free）
  - condition: str（判定条件の記述）
- 各 completion_criteria は少なくとも1つの acceptance_criteria 項目に紐づくこと
- コードセッションにおいては、各 acceptance は対応するテストケースを持つこと（docs-onlyセッションは除く）

### session-114 既知 warning と正本側の解消方針

- `docs/reports/session-114_completion_report.json` の risks に、当時 `completion_criteria.type` の正本一覧へ `state_transition_consistent` が未掲載であったことに起因し、自己検証等で「enum 外」と扱われる可能性が記録されている。
- 上記 **completion_criteria 型定義** の `type` 許容値に `state_transition_consistent` を正式に含めたことで、**ドキュメント正本の観点**では同値は許容 enum の一員であり、enum 外値として扱わない。
- 実行時バリデーションやセッション JSON の機械検査で同一の warning が残る場合は、検証側を本節の許容値一覧へ追随させること（runtime / selfcheck コードの変更は当該 docs セッションのスコープ外）。

### completion_status 定義

- completion_status は `usable_for_self` / `review_required` / `failed` の3値のみ許可する
- 判定条件は以下を厳密に適用する:
  1. acceptance_results に result=`fail` が1件以上ある場合は `failed`
  2. 1に該当せず、risks または open_issues が1件以上ある場合は `review_required`
  3. 1と2のいずれにも該当しない場合は `usable_for_self`
- human_review_needed は completion_status が `review_required` のときのみ true、それ以外は false

## drift detector v0.1 の適用方針

- drift detector v0.1 は session-123 で導入された。
- 現時点では temporary compatibility mode として運用する。
- temporary compatibility mode では、session JSON に `drift_check_v01: true` を持つ session のみ drift check を実行する。
- 新規に起票する session は、原則として `drift_check_v01: true` を付与する。
- 既存 session は直ちに default-on 化せず、段階移行とする。
- default-on への切替は、既存 session 群が以下の準拠状況を満たしたうえで、人間承認を経て行う。
  - required keys の充足
  - review_points の固定4軸完全一致
  - allowed_changes_detail の形式準拠
  - acceptance.test_name の必須項目充足
- temporary compatibility mode の恒久化は禁止する。後続 session で移行方針を定期的に見直すこと。

## drift detector default-on 移行条件

drift detector は以下の条件をすべて満たした場合に default-on に移行する。

### 必須条件（項目のみ定義・数値は session-126 実測後に確定）

- 全 session の required keys 充足率が閾値（session-126 で決定）を超えていること
- review_points が固定4軸に完全一致している session の比率が閾値（session-126 で決定）を超えていること
- allowed_changes_detail の形式違反率が閾値（session-126 で決定）未満であること
- acceptance.test_name 欠落が存在しないこと

### 閾値確定プロセス

- session-126 で既存 session 群の実測を行う
- 実測結果を踏まえて default-on 移行閾値の具体数値を事後追記する
- 実測前に default-on 移行判断を行わない

### 段階移行ルール

- Phase 1: 新規 session のみ原則 drift_check_v01 を付与する
- Phase 2: 準拠確認済みの既存 session に適用する
- Phase 3: 全 session に強制適用する

### fail 時の挙動

- default-on 適用後は drift fail の場合、必ず fail-fast で停止する
- override は行わない

## new / legacy session 運用ルール

### new session

- 新規 session は drift_check_v01: true を原則付与する
- review_points は canonical 固定4軸に完全一致させる
  - 第1軸: 仕様一致（AC達成）
  - 第2軸: 変更範囲遵守
  - 第3軸: 副作用なし（既存破壊なし）
  - 第4軸: 検証十分性（テスト・証跡・再現性により、受入判断に足る根拠があること）
- canonical に一致しない session は新規起案時点で採用しない

### legacy session

- 既存 session 群は legacy として扱う
- legacy session は docs/reports/legacy-session-whitelist.json により明示管理する
- legacy session は default-on 強制対象外とする
- legacy session は履歴として保持し、書き換えない
- legacy の整理は別 session で段階的に実施する(session-128 以降)

### whitelist 運用

- legacy-session-whitelist.json の初期版は session-127 で作成する
- session-128 で精査・確定する
- whitelist の追加・削除は後続 session で docs-only 形式で扱う

---

## state / resume 実行ルール

- state handoff は session 単位で扱う
- state は JSON 形式で永続化する
- 最小 state 必須キーは `session_id`, `current_stage`, `completed_stages`, `status`, `timestamp_utc` とする
- failure 時は `failure_stage`, `failure_type` を保存対象に含める
- resume は `completed_stages` を根拠に未完了地点からのみ再開する
- retry は同一 session 内の修正再投入、resume は保存 state を根拠とする再開であり、責務を混同してはならない
- state 不整合時は自動続行せず停止候補とする

### M03-pre 正本整備追加定義 (session-132-pre)

#### pipeline stage 正式リスト

run_session.py の実行単位を **pipeline stage** と呼ぶ。以下の10値を pipeline stage の正式リストとする。

1. `loading`
2. `validating`
3. `git_guard`
4. `prepared_spec`
5. `implementation`
6. `patch_apply`
7. `retry_instruction`
8. `implementation_retry`
9. `drift_check`
10. `completed`

- state.json の `current_stage` は上記正式リストのいずれかの値を取る
- state.json の `completed_stages` は上記正式リストの部分列とする
- `completed` は正常終了時に `current_stage` に記録される終端値であり、completed_stages には含めない慣例とする

#### checkpoint_failure_type enum

state 記録時の実行状態分類を表す enum として `checkpoint_failure_type` を新設する。既存の `failure_type` (session 検収・差戻し分類) とは意味論的に別物であり、混同してはならない。

現時点の checkpoint_failure_type 値:

- `DriftCheckFailed` — drift check 失敗で stage 実行が中断された場合
- `SessionFailed` — session 全体が失敗(例外以外の原因)で終了した場合
- (実装で補足的に使用される Python 例外型名 — 例えば `RuntimeError` 等 — は、session-131 実装準拠として許容する。正式値は上記2値とし、例外型名はフォールバックとして扱う)

新規の checkpoint_failure_type 値を追加する場合は、本文書を更新して正本化する。

#### failure_type と checkpoint_failure_type の役割分離

2つの enum は**用途と意味論が独立**である。

| 分類 | 用途 | 記録場所 | 値 |
|---|---|---|---|
| `failure_type` | session 検収・差戻し分類(人間・GPT が判定する際の根拠) | session report / acceptance 評価 | `build_error` / `import_error` / `type_mismatch` / `test_failure` / `scope_violation` / `regression` / `spec_missing` |
| `checkpoint_failure_type` | state 記録時の実行状態分類(checkpoint で自動記録する値) | state.json | `DriftCheckFailed` / `SessionFailed` 他 |

- 同一 session 内で両方が記録されうるが、意味論は独立
- **state.json の `failure_type` field には、checkpoint_failure_type enum の値を格納する**(field 名と enum 名が異なる点に注意)
- state.json の `failure_type` は **実行状態記録用フィールドであり、検収用 failure_type とは意味が異なる**
- session 検収結果としての failure_type は、state.json ではなく別途 report / acceptance 評価で記録する

#### completed_stages の正式定義

`completed_stages` を **「state checkpoint が正常に記録された pipeline stage の一覧」** と定義する。

- 業務的に完了した全 stage を必ずしも意味しない
- retry 早期 break(同一原因停止など)では checkpoint フックに到達しないまま session が終了するため、completed_stages が短縮されうる
- resume 判定時は completed_stages 単独ではなく、`current_stage` / `status` / `failure_stage` / state.json 内 `failure_type` field (= checkpoint_failure_type の値) を**併せて解釈する**
- completed_stages は resume 判定の補助情報であり、厳密な全完了履歴ではない

### M03 resume 正本補足 (session-133-pre)

#### resume 実行時の例外規則

- `loading` は常時実行とする。
- `validating` は常時実行とする。
- retry ループ内 2 回目以降の `patch_apply` は、`completed_stages` の単純な stage 名の列挙では表現できない。このため、**初回パイプラインにおける skip 判定の対象**とは分離して扱う（session-132 実装では、ループ内の `patch_apply` は checkpoint で `patch_apply` を重複記録せず、skip 判定との衝突を避ける）。
- 上記は session-132 実装で確認された挙動を正本化するためのものである。M03-D で `retry_history.json` を導入した後も、「`loading` / `validating` は常時実行」という原則は維持する。

#### artifact 欠損時停止規則（DP-07=A）

resume 実行で skip 対象 stage の required artifact が欠損している場合、当該実行は整合性破綻として fail-fast 停止しなければならない。state.json に `completed_stages` の記録が存在しても、対応 artifact が存在しない場合は resume 継続を許可しない。

- skip 対象 stage に required artifact が存在しない場合、resume 実行は継続してはならず、**exit code 1** で停止する。
- エラーメッセージには **欠損した artifact のファイル名** を含める。
- state.json が `completed_stages` を保持していても、required artifact が欠損している状態は **resume 前提の整合性破綻**として扱う。
- 欠損時に該当 stage を黙示的に再実行するフォールバックは禁止する。

#### retry 経路履歴の分離と `retry_history.json`（DP-08=C）

completed_stages は初回パイプラインの完了記録のみを保持し、retry 経路の履歴は `retry_history.json` に分離保存する。これにより state.json schema の互換性を維持しつつ、retry ループ内の多重 `patch_apply` 実行を明示的に表現する。

- 既存 `state.json` schema は **non-breaking** に維持する（破壊的変更を行わない）。
- `completed_stages` は **初回パイプライン**の stage 完了記録に限定する。
- retry 経路の履歴は **`retry_history.json`**へ分離保存する。
- `retry_history.json` は `state.json` の代替ではなく、**retry 経路専用の補助履歴**である。
- `retry_history.json` の不在と「retry 履歴が無い」ことの区別は設計論点であり、M03-D 実装で厳密化する。`state.json` と `retry_history.json` を混同しない。

**`retry_history.json` 最小スキーマ案（M03-D 実装時に最終確定する。実装時の微調整の余地あり）**

- `session_id` (str)
- `retry_count` (int)
- `retry_events` (list[object])

各 `retry_events` 要素の最小項目案:

- `attempt_index` (int)
- `resumed_from_stage` (str)
- `executed_stages` (list[str])
- `patch_apply_executed` (bool)
- `started_at_utc` (str)
- `finished_at_utc` (str)
- `result` (enum: `success`, `fail`)

#### skip 対象 stage の厳密定義（DP-09=C）

現行実装（session-132）の skip 対象・非対象を次表に正本化する。`loading` / `validating` の常時実行原則は上記「resume 実行時の例外規則」に従い、本表では重複定義を避ける。

| stage 名 | skip 可否 | 理由 | required artifact / state | 補足 |
|---|---|---|---|---|
| `loading` | no | 実行コンテキスト構築と state / artifact 読み込み前提を確立するため | session 定義 / acceptance / 親文書 | 常時実行（「resume 実行時の例外規則」参照） |
| `validating` | no | resume / 通常実行を問わず入力整合性確認が必要なため | loaded context | 常時実行（「resume 実行時の例外規則」参照） |
| `git_guard` | yes | 正常完了済みなら再実行不要 | `state.json` の `completed_stages` | resume skip 対象 |
| `prepared_spec` | yes | 既存 prepared_spec artifact を再利用できるため | `prepared_spec.json` | artifact 欠損時は fail-fast 停止 |
| `implementation` | yes | 既存 implementation artifact を再利用できるため | `implementation_result.json` | artifact 欠損時は fail-fast 停止 |
| `patch_apply` | yes | 初回パイプラインの `patch_apply` 完了記録は skip 可能 | `state.json` の `completed_stages` | retry ループ内の多重実行は `retry_history` 側で別管理 |
| `retry_instruction` | yes | 既存 retry_instruction artifact を再利用できるため | `retry_instruction.json` | artifact 欠損時は fail-fast 停止 |
| `implementation_retry` | yes | 既存 retry 実装 artifact を再利用できるため | `implementation_result.json`（`responses/implementation_result.json`。session-132 は implementation と同一ファイルを retry 時に上書き更新） | M03-D 実装で `retry_history` と整合 |
| `drift_check` | yes | 完了済み drift_check は再利用可能 | `state.json` の `completed_stages` | resume skip 対象 |
| `completed` | no | 終端値であり実行 stage ではないため | final state | skip 対象外 |

**AC-02 補正文言（本節の要約）:** `loading` / `validating` は常時実行とする。retry ループ 2 回目の `patch_apply` は従来 `completed_stages` の単純な記録では表現できないため、初回パイプラインの skip 判定とは切り離して扱う。

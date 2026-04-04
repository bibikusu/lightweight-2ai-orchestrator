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
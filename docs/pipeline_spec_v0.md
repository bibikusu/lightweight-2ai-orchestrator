# パイプライン仕様 v0

## 1. 文書情報

- 文書種別: pipeline_spec
- バージョン: v0
- 文書名: structured_3layer_pipeline_spec_v0
- ステータス: draft_ready_for_storage

## 2. 目的

仕様書から session JSON / acceptance YAML を生成し、現行オーケストレーター互換を保ったまま、差戻し可能な形で確定する。

## 3. スコープ

### in_scope

- 仕様書入力の事前精査
- session JSON の生成
- acceptance YAML の生成
- 生成物の構造・整合性・互換性チェック
- fail 時の差戻し
- pass 時の保存判定

### out_of_scope

- orchestrator 本体コードの変更
- Bootstrap 実装コードの追加
- 2プロジェクト目以降を前提にした共通化実装
- repository への自動保存処理
- run_session.py の挙動変更

## 4. 3層パイプライン

### Layer 1: Input Gate

- 担当: GPT またはルールベース検査
- 目的: 入力仕様の不足・曖昧さ・矛盾を検出する

#### 入力

- source specification
- phase definition
- project config

#### 出力

- spec_check_result.json

#### pass 条件

- in_scope と out_of_scope が分離されている
- phase_id が定義されている
- target_feature が1つに絞られている
- UI と logic が混在していない
- 保存先パス規約がある

#### fail 時の処理

- 不足項目を返して停止する

### Layer 2: Generate

- 担当: GPT
- 目的: session JSON と acceptance YAML を生成する

#### 入力

- validated spec
- repository context
- template A（session JSON 生成用）
- template B（acceptance YAML 生成用）

#### 出力

- session-XX.json
- session-XX.yaml

#### ルール

- 現プロジェクト専用で生成する
- 現行オーケストレーター互換を優先する
- 一発正解を前提にしない
- 差戻し可能なドラフトとして生成する

### Layer 3: Review Gate

- 担当: Claude
- 目的: 構造・整合性・互換性を検査する

#### 入力

- generated session json
- generated acceptance yaml
- repository context
- template C（セルフチェック用）

#### 出力

- review_result.json

#### 判定

- pass: 保存候補として確定
- fail: GPT へ差戻し

## 5. Review Contract

Claude の返答は以下のどちらかに限定する。

- pass
- fail_with_structured_errors

### 禁止する返答

- 感想のみ
- 曖昧な改善提案のみ
- 概ね問題ないが再確認してください
- なんとなく不自然

### fail 時の必須形式

```json
{
  "status": "fail",
  "errors": [
    {
      "id": "E-01",
      "location": "string",
      "message": "string",
      "fix": "string"
    }
  ]
}
```

## 6. 現行オーケストレーター互換ルール

### session JSON 必須キー

- session_id
- phase_id
- title
- goal
- scope
- out_of_scope
- constraints
- acceptance_ref

### session JSON 追加ルール

- session_id と session ファイル名は一致必須
- acceptance_ref は repository 相対パス
- phase_id は roadmap.yaml に存在必須

### session JSON スキーマ制約

| フィールド | 型 | 制約 |
|---|---|---|
| allowed_changes_detail | list[str] | 各要素は "path: 変更内容の説明" 形式 |
| completion_criteria | list[object] | 各要素に id / type / condition 必須 |

completion_criteria.type の許可値:

- artifact
- document_rule
- non_regression
- side_effect_free

### acceptance YAML 必須キー

#### required_by_orchestrator（実行互換）

- session_id

#### required_by_template（生成品質）

- session_id
- goal
- scope
- out_of_scope
- acceptance
- completion_checks
- change_guardrails

### acceptance YAML 補足ルール

- session_id はトップレベル必須
- 既存 acceptance YAML サンプル構造を維持する
- 独自ネスト構造を増やさない

## 7. 差戻しループ

### 起動条件

- review_result.status == fail

### フロー

1. Claude が構造化エラーを返す
2. GPT が最小差分で修正する
3. Claude が再検証する
4. pass まで繰り返す

## 8. 現プロジェクト専用 v0 固定事項

- session required keys は現行実行系準拠
- acceptance YAML は既存サンプル構造を維持
- acceptance_ref は repository 相対パス
- phase_id は roadmap.yaml に存在必須
- session_id とファイル名は一致必須

## 9. 汎用化ポリシー

### 原則

汎用化は思想として持つが、v0 では実装しない。

### 共通層候補

- required key validation
- acceptance top-level structure validation
- pass or fail review format
- ambiguity detection rules

### プロジェクト固有層候補

- phase_id list
- repository path rules
- forbidden files
- naming rules
- acceptance sample structure

### 汎用化の着手条件

- 同一プロジェクトで 3 session 以上が pass
- 差戻し理由がパターン化している
- 固有ルールと共通ルールを分類できる

## 10. REPOSITORY_CONTEXT の推奨内容

- docs/sessions の既存 JSON サンプル 1件
- docs/acceptance の既存 YAML サンプル 1件
- roadmap.yaml の phase_id 一覧
- session 保存先パス
- acceptance 保存先パス
- 命名規則

# テンプレートC：最終セルフチェック用（現行互換検査追加版）

以下の生成物を検査してください。

## 入力

### session_json

{{SESSION_JSON}}

### acceptance_yaml

{{ACCEPTANCE_YAML}}

### repository_context

{{REPOSITORY_CONTEXT}}

### session_file_path

{{SESSION_FILE_PATH}}

### acceptance_file_path

{{ACCEPTANCE_FILE_PATH}}

## 目的

session JSON と acceptance YAML の整合性、および現行オーケストレーター互換性を検査する。

## 絶対ルール

- 出力は JSON のみ
- コードフェンス禁止
- 説明文禁止
- 問題がなければ "status": "pass"
- 問題があれば "status": "fail"
- 問題は具体的に列挙する
- 修正案は最小差分で書く

## 出力スキーマ

```
{
  "status": "pass or fail",
  "errors": [
    {
      "id": "E-01",
      "location": "string",
      "message": "string",
      "fix": "string"
    }
  ],
  "warnings": [
    {
      "id": "W-01",
      "location": "string",
      "message": "string",
      "fix": "string"
    }
  ]
}
```

## 検査項目

1. session_json の必須キー欠落（session_id, phase_id, title, goal, scope, out_of_scope, constraints, acceptance_ref）
2. acceptance_yaml の必須キー欠落
3. session_id の不一致
4. acceptance requirement と session acceptance_criteria の不一致
5. test_name の欠落・重複
6. allowed_changes と forbidden_changes の衝突
7. scope と out_of_scope の重複
8. completion_criteria と completion_checks の不一致
9. 最大5ファイル制約違反
10. 曖昧語の残存
11. YAML / JSON の構文破綻
12. manual / automated の判定ミス
13. acceptance_ref のパスが repository 内の相対パスとして妥当か
14. session_id と session_file_path のファイル名一致
15. phase_id が repository_context 内の roadmap.yaml phase 一覧に存在するか

## 追加互換検査ルール

- session_json に以下の必須キーがあるか:
  session_id, phase_id, title, goal, scope, out_of_scope, constraints, acceptance_ref
- acceptance_yaml の session_id がトップレベルにあるか
- session_json.acceptance_ref と acceptance_file_path が一致するか
- session_file_path のファイル名が session_id と対応するか
- acceptance_file_path のファイル名が acceptance_ref と対応するか
- acceptance_ref が docs/ から始まる場合は repository 相対パスとして扱える形か
- acceptance_ref が絶対パスになっていないか
- phase_id が roadmap.yaml 未定義なら error にする
- repository_context に roadmap 情報がない場合は warning にする

## 判定ルール

- 実行系で落ちる可能性が高いものは error
- 実行はできるが運用事故になりやすいものは warning

## Spec Check v0 契約

以下の型・構造検査を必ず実施する。schema/type 不一致が検出された場合は `failure_type: spec_missing` を当該 error オブジェクトに付与する。

### allowed_changes_detail 型検査

- `allowed_changes_detail` が存在する場合、型が list[str] であること
- 各要素が `"path: 説明"` 形式（コロン区切り）であること
- object 形式の場合は型不一致とみなし error とする（failure_type: spec_missing）

### completion_criteria 構造検査

- `completion_criteria` が存在する場合、型が object 配列であること
- 各要素に `id` / `type` / `condition` の3キーが必須
- `type` の値が以下のいずれかであること: `artifact` / `document_rule` / `non_regression` / `side_effect_free`
- string 配列の場合は型不一致とみなし error とする（failure_type: spec_missing）

### failure_type 付与ルール

上記検査で型・構造不一致を検出した場合、errors 配列の当該要素に `failure_type` フィールドを追加する。

```
{
  "id": "E-XX",
  "location": "string",
  "message": "string",
  "fix": "string",
  "failure_type": "spec_missing"
}
```

では JSON のみを出力してください。

## drift_phase1 追加チェック (session-127 で固定)

- session JSON に `drift_check_v01: true` が含まれているか
- `review_points` が canonical 4軸(「仕様一致（AC達成）」/「変更範囲遵守」/「副作用なし（既存破壊なし）」/「検証十分性」)と完全一致しているか

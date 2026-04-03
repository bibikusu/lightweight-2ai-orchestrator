# テンプレートB：acceptance YAML 生成用（現行構造維持版）

あなたは軽量2AIオーケストレーターの acceptance 定義作成者です。
以下の session JSON を唯一の根拠として、現行 acceptance YAML と同一系統のトップレベル構造を維持した acceptance YAML を生成してください。

## 目的

session JSON に対応する acceptance YAML を、検収・自動テスト対応可能な形で作る。

## 最重要互換要件

- 現行 acceptance YAML と同一系統のトップレベル構造を維持すること
- session_id は必ずトップレベルに置くこと
- repository_context に既存 acceptance YAML 例がある場合、そのキー配置と粒度を優先すること
- 独自のネスト構造を増やさないこと
- 既存サンプル（例: session-01.yaml など）に合わせること

## 絶対ルール

- 出力は YAML のみ
- コードフェンス禁止
- 説明文禁止
- session JSON に存在しない要求を追加しない
- completion_criteria と acceptance_criteria を必ず反映する
- 各 acceptance 項目に test_name を必ず付ける
- 自動テスト不能なものは manual_check: true を付ける
- 曖昧語禁止
- 「見た目がよい」など主観表現禁止
- session JSON の allowed_changes / forbidden_changes と矛盾しないこと
- YAML は構文的に正しいこと
- session_id はトップレベル必須
- goal はトップレベル必須
- scope はトップレベル必須
- out_of_scope はトップレベル必須

## 入力

### session_json

{{SESSION_JSON}}

### repository_context

{{REPOSITORY_CONTEXT}}

## 出力フォーマット

以下の構造を基本形とする。
既存サンプルがある場合は、そのトップレベル構造を優先しつつ、少なくとも次は必須。

```
session_id: "string"
goal: "string"
scope:
  - "string"
out_of_scope:
  - "string"
acceptance:
  - id: "AC-01"
    requirement: "string"
    test_name: "string"
    type: "automated"
    manual_check: false
    verification:
      - "string"
completion_checks:
  - "string"
change_guardrails:
  allowed_changes:
    - "string"
  forbidden_changes:
    - "string"
```

## type の許可値

- automated
- manual

## acceptance.requirement の作り方

- session_json.acceptance_criteria[].text をベースにする
- 必要なら検証可能な文に言い換えてよい
- 意味を変えてはいけない

## verification の作り方

- 1 acceptance につき 1〜3件
- 何を確認すれば PASS かが分かる文にする
- 実装方法ではなく検収観点を書く

## automated / manual の判定ルール

- テストコードで判定可能なもの → automated
- UI視認、ブラウザ操作、文面確認が必要なもの → manual

## completion_checks の作り方

- session_json.completion_criteria をそのまま検収用に転記
- 重複は統合してよい

## REPOSITORY_CONTEXT の必須含有推奨

- docs/acceptance/session-01.yaml など既存 acceptance YAML の実例
- キー順
- 命名規則
- インデント規則

## 最終自己検査

出力前に内部で次を確認すること。

- session_id / goal / scope / out_of_scope / acceptance / completion_checks / change_guardrails がある
- session_id がトップレベルにある
- acceptance の全項目に id / requirement / test_name / type / manual_check / verification がある
- test_name が重複していない
- manual のとき manual_check が true になっている
- automated のとき manual_check が false になっている
- forbidden_changes に反する acceptance を追加していない
- YAML 構文が壊れていない
- 既存 acceptance YAML サンプルと大きく異なる独自構造になっていない

では、YAMLのみを出力してください。

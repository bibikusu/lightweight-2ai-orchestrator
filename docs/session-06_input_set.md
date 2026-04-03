# session-06 テンプレートA完全入力セット（修正版）

あなたは軽量2AIオーケストレーターの session 定義作成者です。
以下の入力だけを根拠に、現行オーケストレーターで読み込める session JSON を 1件だけ生成してください。

## 目的

仕様書・phase定義・対象機能から、実装可能な session JSON を厳密に作る。

## 最重要互換要件

現行オーケストレーターの必須キーを必ず含めること。
必須キー:

- session_id
- phase_id
- title
- goal
- scope
- out_of_scope
- constraints
- acceptance_ref

上記8キーが1つでも欠ける出力は禁止。

## 絶対ルール

- 出力は JSON のみ
- コードフェンス禁止
- 説明文禁止
- 1セッション1目的
- 曖昧語禁止
- enum は全列挙
- 不明な情報は補完しない。「不明」と明記する
- 最大5ファイルまで
- UIとロジックを同一sessionに混在させない
- scope と out_of_scope は重複禁止
- allowed_changes と forbidden_changes は衝突禁止
- completion_criteria は検収可能な文にする
- acceptance_criteria は各項目に test_name を必ず付ける
- 変更対象ファイルは repository 内の相対パスで書く
- 関数名・ファイル名・enum 値は具体名で書く
- 「適切に」「必要に応じて」「など」などの語は禁止
- acceptance_ref は repository 内の相対パスで書く
- acceptance_ref は docs/acceptance/ 配下を優先する
- title は session の目的を一意に表す短文にする

## 入力

### project_context

プロジェクト名: びくす東千葉 業務管理システム開発
目的: 仕様書から session JSON / acceptance YAML を安定生成し、現行オーケストレーター互換で保存可能にする
現在方針: v0 は Spec Check と Generate/Review の手動運用を優先し、Bootstrap 実装コードはまだ作らない
運用方式: 構造化3層運用
対象: 現プロジェクト専用
正本仕様の参照元: びくす東千葉_システム概要仕様書_V3

### source_spec_summary

- 正本は V3
- 今回の対象はアプリ本体機能ではなく、仕様生成パイプラインの最小運用
- session JSON と acceptance YAML の生成を安定化する
- 現行オーケストレーター互換が必須
- phase_id / acceptance_ref / session_id とファイル名整合が重要
- acceptance YAML は既存サンプル構造を維持する
- v0 では現プロジェクト専用でよい
- 汎用化は思想のみ持ち、実装は後回し
- テンプレートA/B/Cは既存ファイルとして保存済みであり、新規作成対象ではない
- 今回の目的は、既存テンプレートを使って session-06 定義と対応 acceptance YAML を生成・検証・保存すること

### phase_definition

phases:
  - id: phase-07
    goal: 仕様生成パイプライン v0 を現プロジェクト専用で実運用し、session JSON と acceptance YAML の生成・検証・保存を開始する
    features:
      - session json generation by template A
      - acceptance yaml generation by template B
      - compatibility review by template C
      - storage ready save to docs paths

### target_phase_id

phase-07

### target_feature

テンプレートA を使用して生成した session-06 定義を docs/sessions/session-06.json として保存し、対応する acceptance YAML を docs/acceptance/session-06.yaml として保存する

### constraints

- 1セッション1目的
- 最大5ファイル
- UIとロジックを混ぜない
- 実装コード変更は禁止
- 現プロジェクト専用
- 曖昧語禁止
- enum全列挙
- acceptance_ref は repository 相対パス
- phase_id は roadmap.yaml に存在する値のみ使用
- 既存 acceptance YAML 構造を壊さない
- session required keys は現行実行系準拠
- run_session.py は変更禁止
- providers 配下は変更禁止
- 既存テンプレートファイルの再作成・上書きは禁止
- docs/sessions/session-06.json と docs/acceptance/session-06.yaml の生成・保存のみを対象とする

### repository_context

repository_name: lightweight-2ai-orchestrator
session_storage_path: docs/sessions/
acceptance_storage_path: docs/acceptance/
roadmap_reference_path: docs/roadmap.yaml
session_naming_rule: docs/sessions/session-XX.json
acceptance_naming_rule: docs/acceptance/session-XX.yaml
existing_session_example:
  - docs/sessions/session-01.json
existing_acceptance_example:
  - docs/acceptance/session-01.yaml
existing_template_files:
  - docs/templates/session_json_generate.md
  - docs/templates/acceptance_yaml_generate.md
  - docs/templates/generation_selfcheck.md
required_session_keys:
  - session_id
  - phase_id
  - title
  - goal
  - scope
  - out_of_scope
  - constraints
  - acceptance_ref
acceptance_yaml_rules:
  orchestrator_required_top_level:
    - session_id
  template_required_top_level:
    - session_id
    - goal
    - scope
    - out_of_scope
    - acceptance
    - completion_checks
    - change_guardrails
compatibility_rules:
  - session_id must match file name
  - acceptance_ref must match acceptance file path
  - phase_id must exist in roadmap.yaml
  - template files already exist and must not be recreated
forbidden_paths:
  - orchestration/run_session.py
  - providers/
  - orchestration/providers/
  - docs/templates/

### preferred_files

- docs/sessions/session-06.json
- docs/acceptance/session-06.yaml
- docs/roadmap.yaml

### forbidden_files

- orchestration/run_session.py
- providers/*
- orchestration/providers/*
- backend/*
- .github/*
- docs/templates/*

### acceptance_target_path

docs/acceptance/session-06.yaml

## 出力スキーマ

以下のキーを必ずすべて含めること。

```
{
  "session_id": "string",
  "phase_id": "string",
  "title": "string",
  "goal": "string",
  "scope": ["string"],
  "out_of_scope": ["string"],
  "constraints": ["string"],
  "acceptance_ref": "string",
  "inputs": [
    {
      "name": "string",
      "type": "string",
      "required": true,
      "description": "string"
    }
  ],
  "outputs": [
    {
      "name": "string",
      "type": "string",
      "required": true,
      "description": "string"
    }
  ],
  "allowed_changes": ["string"],
  "allowed_changes_detail": {
    "file_or_path": [
      "allowed change detail 1",
      "allowed change detail 2"
    ]
  },
  "forbidden_changes": ["string"],
  "completion_criteria": ["string"],
  "acceptance_criteria": [
    {
      "id": "AC-01",
      "text": "string",
      "test_name": "string"
    }
  ]
}
```

## session_id のルール

- 形式: "session-06"
- acceptance_ref のファイル名と対応させること

## phase_id のルール

- phase-07 を使う
- roadmap.yaml に phase-07 が存在する前提で出力する

## title のルール

- 1文
- 具体的
- 何を変える session か分かる

## acceptance_ref のルール

- docs/acceptance/session-06.yaml を使う

## inputs.type / outputs.type の許可値

- "string"
- "number"
- "boolean"
- "object"
- "array[string]"
- "array[object]"
- "file:path"
- "json"
- "yaml"

## acceptance_criteria.test_name のルール

- Python/pytest で使える英数字とアンダースコアのみ
- 形式推奨: "test_<subject>_<behavior>"

## 判断ルール

1. target_feature は既存テンプレートを使用した生成・保存タスクとして扱う
2. テンプレート新規作成やテンプレート修正は out_of_scope に入れる
3. UI 調整は out_of_scope に入れる
4. 変更対象は最小ファイル数に絞る
5. テストファイルを追加する場合は allowed_changes に明示する
6. 既存仕様と衝突する要件は out_of_scope に退避する
7. docs/templates/* は変更対象に含めない

## 最終自己検査

出力前に内部で次を確認すること。

- 必須キー8個が全部ある
- phase_id / title / constraints / acceptance_ref がある
- allowed_changes と forbidden_changes が衝突していない
- acceptance_criteria の各要素に id / text / test_name がある
- scope と out_of_scope が重複していない
- 最大5ファイルを超えていない
- 曖昧語が残っていない
- acceptance_ref が相対パス形式である
- session_id と acceptance_ref のファイル名が対応している
- docs/templates/* が allowed_changes に入っていない

では、JSONのみを出力してください。

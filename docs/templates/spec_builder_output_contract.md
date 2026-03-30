# Spec Builder Output Contract

## 目的

Spec Builder が生成する成果物の品質と構造を固定する。

---

## 出力対象

- master_instruction.md
- roadmap.yaml
- sessions/session-01.json
- acceptance/session-01.yaml

---

## 共通ルール

- 全ファイルは完全構造で出力する
- 不完全なフィールドは禁止
- 推測での補完は禁止
- 曖昧語は禁止

---

## session-01.json 要件

### 必須フィールド

- session_id: str
- objective: str
- inputs: list[object]
- outputs: list[object]
- allowed_changes: list[str]
- forbidden_changes: list[str]
- completion_criteria: list[str]
- acceptance_criteria: list[object]
- review_points: list[str]

---

### acceptance_criteria 要件

各要素:

- id: str
- description: str
- test_function: str

制約:

- description は検証可能な内容のみ
- test_function は必ず存在する関数名

---

## roadmap.yaml 要件

- phases: list
- 各phaseは以下を含む:
  - phase_id
  - objective
  - sessions

---

## master_instruction.md 要件

- セクション分割必須
- 以下を含む:
  - システム目的
  - スコープ
  - 制約
  - 成功条件
  - 禁止事項

---

## 禁止事項

- run_session.py に依存する記述
- 未定義フィールド
- 曖昧な成功条件
- テスト不能なAC

---

## 合格条件

- 4ファイルすべてが生成されている
- 各ファイルが構造的に破綻していない
- acceptance と test_function が1対1

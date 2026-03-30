# Spec Reviewer Output Contract

## 目的

Spec Reviewer の出力形式を固定し、判定ぶれを防ぐ。

---

## 出力形式

Reviewer は以下のどちらかのみを返す。

1. pass JSON
2. rejection JSON

---

## pass JSON 必須フィールド

- session_id: str
- status: enum[pass]
- summary: str
- confirmed_facts: list[str]
- risks: list[str]
- open_issues: list[str]
- next_action: str

---

## rejection JSON 必須フィールド

- session_id: str
- status: enum[reject]
- failure_type: enum[scope_violation,acceptance_invalid,forbidden_weakness,phase_split_invalid,spec_missing]
- cause_summary: str
- fix_instructions: list[str]
- do_not_change: list[str]

---

## 共通ルール

- 曖昧語禁止
- confirmed_facts と interpretation を混同しない
- fix_instructions は実行可能な単位で書く
- do_not_change は具体的に書く
- session_id は入力対象と一致している必要がある

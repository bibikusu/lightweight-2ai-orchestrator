# Spec Generation Flow

## 目的
最小入力から仕様叩き台を生成し、構造化レビューを通して、人間が最終承認できる状態まで運ぶ標準フローを固定する。

---

## 全体フロー

1. 人間が `spec_builder_input_sheet.yaml` を埋める
2. Spec Builder が以下を生成する
   - master_instruction.md
   - roadmap.yaml
   - sessions/session-XX.json
   - acceptance/session-XX.yaml
3. Spec Reviewer が生成物を検査する
4. Reviewer は `pass JSON` または `rejection JSON` のいずれかを返す
5. 人間が最終承認する
6. 承認後にのみ session execution に進む

---

## 役割分離

### 人間
- project の目的を決める
- 今回やることを決める
- やらないことを決める
- 最終承認を行う

### Spec Builder
- 最小入力を構造化する
- 親仕様 / roadmap / session / acceptance の叩き台を生成する
- 推測でスコープを膨らませない

### Spec Reviewer
- session が 1目的に収まっているか確認する
- acceptance が検収可能か確認する
- forbidden_changes が弱くないか確認する
- out_of_scope が不足していないか確認する
- pass または reject を構造化出力する

---

## 入力

必須入力:

- `docs/templates/spec_builder_input_sheet.yaml`
- `docs/templates/spec_builder_prompt.md`
- `docs/templates/spec_builder_output_contract.md`
- `docs/templates/spec_reviewer_prompt.md`
- `docs/templates/spec_reviewer_output_contract.md`
- `docs/templates/spec_reviewer_rejection_format.json`

---

## Builder 出力

Builder は以下を生成する。

- `master_instruction.md`
- `roadmap.yaml`
- `sessions/session-XX.json`
- `acceptance/session-XX.yaml`

制約:

- 1セッション1目的
- 曖昧語禁止
- acceptance と test_function を 1 対 1 対応
- forbidden_changes を具体化
- out_of_scope を明示

---

## Reviewer 判定

Reviewer は以下のどちらかを返す。

### pass
- `docs/templates/spec_pass_format.json` に従う

### reject
- `docs/templates/spec_reviewer_rejection_format.json` に従う

---

## pass 時の流れ

1. Reviewer が pass JSON を返す
2. 人間が内容を確認する
3. 問題がなければ session を確定する
4. Cursor 実行または docs-only 実行へ進む

---

## reject 時の流れ

1. Reviewer が rejection JSON を返す
2. 人間は `failure_type` と `fix_instructions` を確認する
3. Builder へ再入力または最小修正を行う
4. Reviewer に再投入する

---

## 停止条件

以下のいずれかなら session execution に進まない。

- session objective が複数ある
- acceptance が曖昧
- forbidden_changes が弱い
- allowed_changes が抽象的
- out_of_scope が不足している
- phase 分解が飛んでいる

---

## 実行記録テンプレ

### Confirmed facts
- 

### Interpretation
- 

### Risks
- 

### Open issues
- 

### Final approval
- approved / rejected

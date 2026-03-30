# Session Review Checklist

## 目的
検収時に「動いた」ではなく、「受入可能か」で判定する。

---

## 1. 仕様一致

- [ ] objective を達成している
- [ ] acceptance_criteria を満たしている
- [ ] review_points を満たしている
- [ ] 事実と解釈が混同されていない

---

## 2. 変更範囲遵守

- [ ] changed_files が allowed_changes 内のみ
- [ ] forbidden_changes に触れていない
- [ ] scope 外変更がない
- [ ] 別セッションに切るべき変更が混ざっていない

---

## 3. 副作用なし

- [ ] 既存挙動を壊していない
- [ ] 既存テストが通っている
- [ ] runtime に不要な変更がない
- [ ] docs-only なら code を触っていない
- [ ] code セッションなら docs 混入がない

---

## 4. 実装過不足なし

- [ ] 必要なものだけを実装している
- [ ] 過剰な抽象化がない
- [ ] 将来保守性を悪化させていない
- [ ] 重複実装になっていない

---

## 5. failure_type 判定

最初に該当したもののみ採用する。

1. build_error
2. import_error
3. type_mismatch
4. test_failure
5. scope_violation
6. regression
7. spec_missing
8. not_applicable

---

## 6. 最終判定

### pass 条件
- [ ] acceptance 全達成
- [ ] scope_check = pass
- [ ] side_effect_check = pass
- [ ] implementation_sufficiency_check = pass

### fail / blocked 条件
- [ ] acceptance 未達
- [ ] allowed_changes 外変更
- [ ] 既存破壊
- [ ] 前提不足
- [ ] 同一セッションで補ってはいけない変更が混入

---

## 7. レビューテンプレ

### Confirmed facts
- 

### Interpretation
- 

### Risks
- 

### Open issues
- 

### Final decision
- pass / fail / blocked

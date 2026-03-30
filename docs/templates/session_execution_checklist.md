# Session Execution Checklist

## 目的
セッション実行中に scope 拡大・前提補完・不要変更が混ざるのを防ぐ。

---

## 1. 実装開始前

- [ ] pre-flight checklist を完了した
- [ ] target branch prerequisite が必要か判断した
- [ ] allowed_changes を再確認した
- [ ] forbidden_changes を再確認した
- [ ] 停止条件を確認した

---

## 2. 実装中

- [ ] 変更は allowed_changes の範囲内のみ
- [ ] 新規ファイルは session 定義に含まれている
- [ ] 既存テスト変更が禁止なら触れていない
- [ ] docs-only セッションで code を触っていない
- [ ] code セッションで docs を混ぜていない
- [ ] prerequisite 不足を同一セッションで補っていない

---

## 3. 検証

- [ ] pytest を実行した
- [ ] lint を実行した
- [ ] typecheck を実行した
- [ ] build / compileall を実行した
- [ ] 失敗時は failure_type を 1 つに絞った
- [ ] 同一原因の再試行を繰り返していない

---

## 4. 差分確認

- [ ] `git diff --stat` を確認した
- [ ] changed_files が allowed_changes に一致している
- [ ] 想定外の差分がない
- [ ] 未追跡ファイルを混ぜていない

---

## 5. レポート

- [ ] changed_files を記録した
- [ ] implementation_summary を記録した
- [ ] risks を記録した
- [ ] open_issues を記録した
- [ ] acceptance_results を記録した
- [ ] scope_check / side_effect_check / implementation_sufficiency_check を記録した

---

## 6. 停止条件

- [ ] allowed_changes 外修正が必要になった
- [ ] prerequisite 不足が見つかった
- [ ] 既存テストと重複が発覚した
- [ ] 4本の検証が通らない
- [ ] 修正が複数目的に広がった

---

## 7. 実行記録テンプレ

### changed_files
- 

### validation_results
- pytest:
- lint:
- typecheck:
- build:

### risks
- 

### open_issues
- 

### final_judgement
- completed / blocked / fail

# Pre-flight / Prerequisite Checklist

## 目的
実装開始前に、前提不足・スコープ不一致・重複作業を検出し、同一セッション内での事故を防ぐ。

---

## 1. セッション基本確認

- [ ] session_id が確定している
- [ ] objective が 1 つに限定されている
- [ ] allowed_changes が定義されている
- [ ] forbidden_changes が定義されている
- [ ] acceptance_criteria が定義されている
- [ ] review_points が定義されている

---

## 2. ワークツリー確認

- [ ] `git status --short` を実行した
- [ ] scope 外の未コミット変更がない
- [ ] 未追跡ファイルの扱いを確認した
- [ ] 今回のセッションに無関係なファイルを混ぜないと確認した

---

## 3. prerequisite file 確認

- [ ] セッションが前提とする file 一覧を洗い出した
- [ ] 各 prerequisite file が tracked file であることを確認した
- [ ] 各 prerequisite file が実在することを確認した
- [ ] prerequisite file が current branch 上でも存在することを確認した
- [ ] prerequisite file 不足を同一セッションで補わないと確認した

---

## 4. scope / path 確認

- [ ] allowed_changes のパスが実リポジトリと一致している
- [ ] 存在しないファイルを allowed_changes に含めていない
- [ ] 実際の対象ファイル数が変更上限内である
- [ ] docs-only セッションか code セッションかを明確にした

---

## 5. 重複確認

- [ ] 既存テストと目的が重複していないことを確認した
- [ ] 既存テンプレートと競合しないことを確認した
- [ ] 既存 helper / utility で置き換え可能か確認した
- [ ] 新規作成より追記・共通化が適切か確認した

---

## 6. 検収可能性確認

- [ ] acceptance_criteria と test / review 観点が対応している
- [ ] 正常系の完了条件が明確
- [ ] 異常系または停止条件が明確
- [ ] 副作用なしを確認できる方法がある
- [ ] rollback 可能性がある

---

## 7. 停止条件

以下のいずれかに該当したら実装を開始しない。

- [ ] prerequisite file が tracked でない
- [ ] prerequisite file が存在しない
- [ ] allowed_changes に存在しない対象ファイル修正が必要
- [ ] 既存テストと重複する
- [ ] acceptance_criteria が曖昧
- [ ] session objective が複数ある

---

## 8. 記録テンプレ

### Confirmed facts
- 

### Interpretation
- 

### Open issues
- 

### Decision
- proceed / stop

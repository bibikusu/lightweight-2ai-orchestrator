# Target Branch Prerequisite Checklist

## 目的
sandbox ではなく、最終反映先 branch 上で prerequisite artifact と前提状態を確認し、merge / cherry-pick 時の事故を防ぐ。

---

## 1. 対象 branch 確認

- [ ] target branch 名を確認した
- [ ] 現在 checkout 中の branch を確認した
- [ ] merge / cherry-pick / rebase のどれで反映するか決めた

---

## 2. prerequisite artifact 確認

- [ ] target branch 上で prerequisite artifact 一覧を確認した
- [ ] prerequisite artifact が tracked file である
- [ ] prerequisite artifact が存在する
- [ ] prerequisite artifact のパスが session 前提と一致する
- [ ] sandbox 側だけに存在して main 側にないファイルがない

---

## 3. target branch 差分確認

- [ ] target branch と sandbox branch の差分前提を確認した
- [ ] sandbox で通っても target branch で落ちる要因がないか確認した
- [ ] prerequisite file の欠落を別コミットで混ぜないと確認した

---

## 4. 実行前チェック

- [ ] `git ls-files <path>` で tracked を確認した
- [ ] `test -f <path>` で存在確認した
- [ ] target branch 上で必要最小限の検証コマンドを回す準備ができている

---

## 5. merge / cherry-pick 後チェック

- [ ] allowed_changes 外の変更が混入していない
- [ ] target branch 上で pytest を実行した
- [ ] target branch 上で lint を実行した
- [ ] target branch 上で typecheck を実行した
- [ ] target branch 上で build / compileall を実行した

---

## 6. 停止条件

以下のいずれかなら反映を止める。

- [ ] target branch に prerequisite artifact がない
- [ ] tracked でない prerequisite file がある
- [ ] allowed_changes 外修正が必要
- [ ] target branch 上で検証が落ちる
- [ ] sandbox と target branch の前提差分が解消されていない

---

## 7. 記録テンプレ

### Target branch
- 

### Prerequisite artifacts checked
- 

### Confirmed facts
- 

### Interpretation
- 

### Decision
- merge / cherry-pick / stop

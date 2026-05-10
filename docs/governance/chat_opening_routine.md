# Chat Opening Routine (canonical)

## 目的

chat 冒頭の状態確認を固定し chat 跨ぎ復元コストと寝起き誤操作を削減する。
本 doc は **commander 操作の routine** 限定。参謀応答テンプレ / ClaudeCode invocation rules は別 doc とする。

## commander 初動 5 コマンド

```bash
git rev-parse HEAD
git rev-parse origin/main
git rev-list --left-right --count origin/main...HEAD
git status --short
git stash list | head -5
```

## 健全状態の判定基準

- HEAD == origin/main (base_commit 一致)
- divergence: 0 / 0
- stash@{0} は sealed
- tracked 変更なし (`??` は許容)

## STOP 条件 (作業着手前に解消必須)

1. **HEAD ≠ origin/main** → STOP (commander manual push / rebase 完了まで。自走 push / rebase 禁止)
2. **committed-but-not-pushed** (右側 divergence > 0) → STOP (commander manual push 完了まで。自走 push 禁止)
3. **stash 汚染検出** (stash@{0} が sealed 以外に変化) → STOP (commander 確認・手動解消まで)
4. **tracked 変更あり** (modified / deleted が存在) → STOP (新 session 起票せず commander へ報告。自走復旧禁止)

## base_commit 確認手順

新 session 開始前に以下を確認する:

1. 起票文の `base_commit` フィールドを読む
2. `git rev-parse origin/main` の出力と完全一致を確認する
3. 不一致なら STOP (起票文が古い可能性 → commander へ報告)

## stash 取扱原則

stash@{0} は sealed。`git stash` 家族コマンド (push / pop / apply / drop / clear) は commander manual only。
詳細は canonical governance docs (memory_role / global_rules / master_instruction の canonical) を参照。

## 参照

- memory_role canonical (NEW-MEMO で確定)
- global_rules canonical (review_points 4 軸 / forbidden_changes / 完了判定)
- master_instruction canonical (3 層役割固定)

## (Appendix / optional) compact handoff 最小形

chat 冒頭で commander が任意採用できる最小フォーマット:

```
=== handoff v0-min ===
base_commit: <full sha>
wave_now:    <fraction>
next:        <session_id>
open_q:      <list | なし>
=== /handoff ===
```

完全版 (v1-normal / full) は別 session で canonical 化予定。

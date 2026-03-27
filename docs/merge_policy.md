# Merge Policy（main 統合ルール）

## 目的

本ドキュメントは、軽量2AIオーケストレーターにおける  
**sandbox ブランチ → main ブランチへの統合ルール**を定義する。

目的は以下：

- 正本（source of truth）を一意に保つ
- conflict 時の判断を迷わない状態にする
- セッション単位の成果物を安全に main に反映する
- 実務投入時の事故（破壊・逸脱）を防ぐ

---

## 原則（最重要）

### 1. main が唯一の正本

- main に存在する状態のみが正しい
- sandbox の状態は「未確定」
- 正式な仕様・実装・挙動は main を参照する

---

### 2. セッション単位で統合する

- 1セッション = 1変更単位
- 複数セッションをまとめて統合しない
- commit メッセージで session_id を必ず追跡可能にする

例：

```
session-13: auto-judge acceptance results from executed tests
```

---

### 3. 合格したセッションのみ統合

以下を満たさないものは main に入れない：

- acceptance 全達成
- pytest PASS
- typecheck PASS
- build PASS
- changed_files が制約内
- review 済み

---

## 統合手順（標準フロー）

### 推奨：cherry-pick

```bash
git switch main
git pull origin main
git cherry-pick <commit_sha>
PYTHONPATH=. .venv/bin/pytest backend/tests/ -q
git push origin main
```

**統合前の全体テスト（必須）:** cherry-pick 完了後（conflict 解消を含む）、**push の前に**リポジトリルートで上記 `pytest` を実行する。conflict 解消でコードが壊れていてもローカルでは気づけないためである（session-13 ではテスト確認なしで push し、今回は問題なかったが再発防止のため手順に明記する）。

### 手順の意味

| ステップ | 意味 |
|----------|------|
| switch main | 正本に移動 |
| pull | 最新状態取得 |
| cherry-pick | 単一セッションだけ適用 |
| pytest（backend/tests 全体） | 統合直前の正しさ確認（**push 前に必須**） |
| push | 正本更新 |

---

## merge / cherry-pick の使い分け

### cherry-pick（標準）

**使用条件：**

- セッション単位の変更
- 単一 commit で完結
- 安全に反映したい場合

**理由：**

- 差分が明確
- 不要変更を持ち込まない
- rollback しやすい

### merge（例外）

**使用条件：**

- 複数コミットが一体不可分
- 大規模変更
- migration を含む構造変更

**注意：**

- 必ず事前レビュー
- squash merge を推奨

---

## conflict 解決ルール（最重要）

### 基本ルール

- **新しい仕様（後発セッション）を正とする**

### 優先順位

1. acceptance を満たしている側
2. 新しいセッション
3. 仕様書（global_rules.md）
4. 過去実装

### 禁止事項

- 両方のロジックを混ぜる
- 意図不明の折衷
- テストだけ合わせてロジックを壊す

### 正しい解決方法

- session 側の意図を理解する
- 不要な旧ロジックを削除する
- テストを新仕様に合わせる

### 判断基準

- **acceptance を満たしている方が正**

### 禁止事項（統合時）

以下は絶対に行わない：

- 未検収セッションの統合
- scope 外変更の混入
- 複数セッションの同時統合
- main 直接編集
- テストを無理やり PASS にする修正

---

## 具体例（session-13）

### 発生した問題

- acceptance_results が not_applicable 前提の旧テスト
- 新仕様は passed / failed 自動判定

### 解決

- session-13 の仕様を採用
- not_applicable 前提ロジックを削除
- 新しいテストに統一

---

## ロール別責務

| ロール | 責務 |
|--------|------|
| Spec Commander（GPT） | 正本仕様の維持、conflict 判断の最終決定、acceptance の整合性保証 |
| Implementation（Claude） | 指定 scope のみ実装、既存破壊を避ける、テストを満たす |
| Orchestrator（Python） | セッション実行制御、checks 実行、report 出力 |
| Human | 最終承認、main 統合実行、conflict 解決判断 |

---

## 成功条件

以下が満たされた状態：

- main が常に動作可能
- すべての変更が session 単位で追跡可能
- conflict 解決がルールに従って再現可能
- 誰がやっても同じ結果になる

---

## 補足：なぜこのルールが必要か

session-13 にて：

- conflict 発生
- 正本判断が曖昧
- 手順が一時的に属人化

この経験を踏まえ、ルールを固定する。

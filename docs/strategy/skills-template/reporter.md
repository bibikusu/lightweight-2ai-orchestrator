---
name: reporter
description: |
  セッション完了後の実装結果報告と artifact を生成する。
  ユーザーが「完了報告を作って」「セッションレポート」「検収レポート起票」と依頼したときに使う。
  旧 orchestrator の worker_report / observation フェーズ相当。
allowed-tools: Read, Write, Grep, Glob, Bash(git log:*, git diff:*, git show:*)
model: sonnet
---

# Reporter Skill

## 目的

Worker の実装と Judge の判定結果をまとめ、**検収レポート** と
**Early Warning Sign** チェックリストを生成する。
旧 orchestrator の `worker_report` + `observation` ステージ相当の責務を担う。

## 旧 orchestrator での位置づけ

旧 `run_session.py` のレポート生成 (`reports/` への `report.json` 出力) と、
`observation_builder.py` のメタ観測が担っていた:
- `implementation_result.json` からの完了サマリー生成
- artifact のファイル一覧・行数・diff 統計
- Early Warning Sign の兆候チェック
- 次セッションへの引き継ぎ情報

これらをプロンプト + 読み取り操作で実行する。

---

## 検収レポートの命名規則

| 種別 | ファイル名パターン | 用途 |
|------|----------------|------|
| `spec_review` | `docs/acceptance/{session_id}_spec_review.yaml` | 起票段階の検収 |
| `implementation_review` | `docs/acceptance/{session_id}_implementation_review.yaml` | 実装段階の検収 |

---

## 実行手順

### Step 1: 実装情報の収集

```bash
git log --oneline -5                    # 直近 commit 確認
git diff --name-only HEAD~1 HEAD        # 変更ファイルリスト
git diff --stat HEAD~1 HEAD             # 変更行数統計
cat docs/sessions/{session_id}.json    # セッション定義
```

### Step 2: implementation_review YAML 生成

`docs/acceptance/{session_id}_implementation_review.yaml` を生成する。

```yaml
session_id: {session_id}
review_type: implementation_review
date: {YYYY-MM-DD}
verdict: {pass / conditional_pass / fail}
failure_type: {failure_type または null}

acceptance_criteria_results:
  - id: AC-{id}
    description: "{description}"
    test_name: "{test_name}"
    result: pass / fail
    note: "{備考}"

completion_criteria_results:
  - id: CC-{id}
    type: {artifact / non_regression / side_effect_free / document_rule / state_transition_consistent}
    condition: "{condition}"
    result: pass / fail

changed_files:
  - path: "{ファイルパス}"
    lines_added: {N}
    lines_removed: {N}

summary: |
  {3 行以内で何を実装したか / 達成状況の要約}

next_session_hint: |
  {次セッションで着手すべきこと。session-plan.yaml の depends_on を参照}
```

### Step 3: Early Warning Sign チェック

以下の 8 カテゴリを確認し、各カテゴリを 緑/黄/赤 で評価する:

| カテゴリ | チェック内容 | 赤の条件 |
|---------|------------|---------|
| **実装速度** | 想定 session 数に対する完了数 | 計画比 50% 未満 |
| **変更範囲** | 1 session あたりの変更ファイル数 | 10 ファイル超 |
| **テスト通過率** | pytest pass / total | 90% 未満 |
| **forbidden_changes 違反** | 違反 commit 数 | 1 件以上 |
| **Day 14 Hard Gate** | hard_gate_date までの残日数 | 3 日以下で未達成 |
| **承認回数** | session あたりの KUNIHIDE 判断要求数 | 5 回超 |
| **凍結禁句** | 「もう少しで動く」等の禁句発生 | 1 回でも発生 |
| **スコープクリープ** | out_of_scope への侵食 | 1 件以上 |

赤が 3 項目以上 → 凍結審議トリガーを KUNIHIDE に報告する。

### Step 4: session-plan.yaml の status 更新提案

```yaml
# 更新対象
- id: {session_id}
  status: ✅completed
  commit: "{commit_hash}"
  date: "{YYYY-MM-DD}"
```

この変更を `docs/sessions/` コミット時に合わせて提案する
(実際の更新は KUNIHIDE 判断で行う)。

---

## 完了報告フォーマット

```
=== Reporter 完了報告 ===
session_id: {session_id}
review_type: implementation_review
verdict: pass / conditional_pass / fail

artifact:
  - docs/acceptance/{session_id}_implementation_review.yaml ({N}行)

Early Warning Sign:
  実装速度: 緑/黄/赤
  変更範囲: 緑/黄/赤
  テスト通過率: 緑/黄/赤
  forbidden_changes 違反: 緑/黄/赤
  Day 14 Hard Gate: 緑/黄/赤 (残 N 日)
  承認回数: 緑/黄/赤
  凍結禁句: 緑/黄/赤
  スコープクリープ: 緑/黄/赤

赤カウント: {N}件 {N >= 3 ? → 凍結審議トリガー : → 継続}

next_session_hint:
  {次セッション ID または「session-plan.yaml で次の pending を確認してください」}
```

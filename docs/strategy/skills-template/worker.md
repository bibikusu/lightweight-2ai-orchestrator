---
name: worker
description: |
  セッション JSON に基づいてsandbox 内で実装を行い、artifact を生成する。
  ユーザーが「このセッションを実装して」「sandbox で実行して」と依頼したときに使う。
  旧 orchestrator の implementation フェーズ相当。
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet
---

# Worker Skill

## 目的

セッション JSON (`docs/sessions/{session_id}.json`) の `scope` と
`allowed_changes_detail` に従い、**sandbox branch 内のみ**で実装を完遂する。
旧 orchestrator の `implementation` / `patch_apply` ステージ相当の責務を担う。

## 旧 orchestrator での位置づけ

旧 `run_session.py` の `implementation` → `patch_apply` ステージが担っていた:
- `allowed_changes_detail` に基づくファイル変更
- `forbidden_changes` の遵守確認
- `completion_criteria` の達成状況記録
- `implementation_result.json` (変更ファイルリスト・サマリー) の生成

これらを ClaudeCode の直接ツール操作 + 規律で実行する。

---

## Sandbox-First 原則 (絶対遵守)

```
git branch で現在のブランチが sandbox/* であることを確認してから着手する。
main / master への直接変更は禁止。
```

確認コマンド:
```bash
git branch --show-current
# 出力が sandbox/* でなければ即停止
```

---

## 実行手順

### Step 0: セッション JSON 読込

```bash
cat docs/sessions/{session_id}.json
```

以下のキーを必ず確認する:
- `allowed_changes_detail`: 変更許可ファイルと内容
- `forbidden_changes`: 変更禁止対象
- `completion_criteria`: 完了基準
- `constraints`: 制約事項

### Step 1: forbidden_changes の確認

`forbidden_changes` に列挙されたファイル・ディレクトリには一切触れない。
変更前に `git diff --name-only` でドリフトを確認する。

### Step 2: 変更実施

`allowed_changes_detail` のみを対象に変更を行う。
1 ファイルずつ変更し、意図しない変更が混入していないか確認する。

### Step 3: completion_criteria の達成確認

各 `completion_criteria` の `condition` を満たしているか確認する:
- `artifact`: 対象ファイルが存在するか (`ls` / `Read` で確認)
- `non_regression`: テストが pass するか (`pytest` / 検証コマンド実行)
- `side_effect_free`: `git diff --name-only` が allowed のみか確認
- `document_rule`: ドキュメントへの記載が完了しているか
- `state_transition_consistent`: 状態遷移が仕様通りか確認

### Step 4: artifact 生成

実装完了後、以下の情報を記録する:

```
変更ファイル: [ファイルパスのリスト]
変更サマリー: [何を変更したか 3 行以内]
completion_criteria 達成状況: [各 CC の pass/fail]
```

### Step 5: git commit

```bash
git add <変更したファイルのみ (git add . / -A 禁止)>
git commit -m "<session_id>: <タイトル>\n\n<変更サマリー>"
```

**禁止**:
- `git add .` / `git add -A`
- `git push` (KUNIHIDE 個人作業)
- `--no-verify`

---

## 変更範囲チェック (完了前必須)

```bash
git diff --name-only HEAD~1 HEAD
```

出力が `allowed_changes_detail` に列挙されたファイルのみであることを確認する。
1 ファイルでも allowed 外が含まれていた場合は `git restore` で即戻す。

---

## 完了報告フォーマット

```
=== Worker 完了報告 ===
session_id: {session_id}
branch: {branch名}
commit: {hash}
変更ファイル:
  - {ファイル1}
  - {ファイル2}
completion_criteria:
  CC-01: pass / fail (理由)
  CC-02: pass / fail (理由)
forbidden_changes: 不触確認 OK / NG (NGの場合は詳細)
```

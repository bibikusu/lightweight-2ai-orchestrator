---
name: judge-4axis
description: |
  実装結果を 4 軸 review_points で検証し、pass / conditional_pass / fail を判定する。
  ユーザーが「検証して」「4 軸レビューして」「AC を確認して」と依頼したときに使う。
  旧 orchestrator の judge フェーズ相当。
allowed-tools: Read, Bash, Grep, Glob
model: sonnet
---

# Judge 4-Axis Skill

## 目的

Worker が生成した実装結果を、固定 4 軸 `review_points` で検証する。
旧 orchestrator の `drift_check` / judge ステージ相当の責務を担う。

## 旧 orchestrator での位置づけ

旧 `run_session.py` の `drift_check` ステージ + 判定ロジックが担っていた:
- `allowed_changes` と `forbidden_changes` の逸脱確認 (scope_violation 検出)
- `acceptance_criteria` の達成確認
- `completion_criteria` の type 別検証
- `verdict` (pass / conditional_pass / fail) の確定と `failure_type` の分類

これらを ClaudeCode の読み取り操作 + 判定ロジックで実行する。

---

## 固定 4 軸 (変更不可)

| 軸 | 検証内容 |
|----|---------|
| **軸 1: 仕様一致（AC達成）** | `acceptance_criteria` の全 `description` が満たされているか |
| **軸 2: 変更範囲遵守** | 変更ファイルが `allowed_changes_detail` のみか。`forbidden_changes` に違反がないか |
| **軸 3: 副作用なし** | 既存テスト (pytest / ruff / mypy / compileall) が全 pass か。想定外の副作用がないか |
| **軸 4: 検証十分性** | `completion_criteria` が全 AC をカバーしているか。抜け穴がないか |

---

## 実行手順

### Step 1: セッション JSON と実装 diff を読込

```bash
cat docs/sessions/{session_id}.json
git diff --name-only HEAD~1 HEAD  # 変更ファイルリスト
git diff HEAD~1 HEAD              # 変更内容全文
```

### Step 2: 軸 1 — 仕様一致（AC達成）

`acceptance_criteria` の各 `description` について:
1. 対応する `test_name` 関数が存在するか確認 (`grep -r "{test_name}"`)
2. テストが pass しているか確認 (`pytest -k "{test_name}" -v`)
3. MANUAL テストの場合は実装内容を読んで条件充足を判定

**判定**: AC が 1 つでも未達 → **fail**

### Step 3: 軸 2 — 変更範囲遵守

```bash
git diff --name-only HEAD~1 HEAD
```

変更ファイルを `allowed_changes_detail` と突合:
- allowed 外ファイルが含まれる → `scope_violation` で **fail**
- `forbidden_changes` に含まれるファイルが変更されている → `scope_violation` で **fail**

**stash@{0..7} 確認**:
```bash
git stash list | head -10
# stash 内容が変更されていないか確認
```

### Step 4: 軸 3 — 副作用なし

```bash
# 可能な場合に実行
python -m pytest --tb=short -q
python -m ruff check .
python -m mypy . --ignore-missing-imports
python -m compileall . -q
```

テスト失敗 → `regression` で **fail**

### Step 5: 軸 4 — 検証十分性

`completion_criteria` の各 `id` が `acceptance_criteria` をカバーしているか確認:
- AC に対応する CC がない場合 → `artifact_missing` で **conditional_pass** (警告)
- `completion_criteria.type` が canonical enum 外 → **fail**

---

## 判定結果の定義

| verdict | 意味 | 条件 |
|---------|------|------|
| `pass` | 全 4 軸クリア | 軸 1-4 すべて問題なし |
| `conditional_pass` | 軽微な不備あり | 軸 4 に警告のみ、軸 1-3 クリア |
| `fail` | 要修正 | 軸 1-3 のいずれかで違反・未達 |

---

## failure_type の分類

| failure_type | 判定基準 |
|-------------|---------|
| `spec_drift` | 実装が仕様 JSON の goal/scope から逸脱している |
| `regression` | 既存テストが壊れた |
| `side_effect` | allowed 外ファイルへの副作用 |
| `artifact_missing` | 必須ファイルが存在しない |
| `approval_mismatch` | acceptance_criteria の description が実装と不一致 |
| `dependency_missing` | depends_on が未完了のまま着手 |
| `scope_creep` | out_of_scope に列挙された機能が実装に含まれる |

---

## 完了報告フォーマット

```
=== Judge 4-Axis 判定結果 ===
session_id: {session_id}
verdict: pass / conditional_pass / fail
failure_type: {failure_type または null}

軸 1 仕様一致（AC達成）: OK / NG
  - AC-{id}: pass / fail (理由)

軸 2 変更範囲遵守: OK / NG
  - 変更ファイル: {リスト}
  - 逸脱: なし / あり (詳細)

軸 3 副作用なし: OK / NG
  - pytest: pass / fail
  - ruff: clean / {エラー}
  - forbidden_changes 違反: なし / あり

軸 4 検証十分性: OK / WARN
  - CC カバレッジ: {カバー数}/{AC総数}
  - 未カバー: なし / {AC-id リスト}

次アクション: なし / Worker 再実行 ({理由})
```

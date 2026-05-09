# ClaudeCode Completion Report Schema v1

**status**: canonical (locked from this version)
**target**: ClaudeCode session 完了報告
**scope**: ClaudeCode が session を完了する際に必ず生成する `completion_report.yaml` の構造定義
**applies_to**: 本 schema canonical 化以降の全 session
**non_applies_to**: GPT / ClaudeWeb の報告(本 schema は ClaudeCode のみ対象)

---

## 1. 目的

ClaudeCode 完了報告の schema を固定し、以下の運用問題を構造的に防ぐ:

- **AC pass 偽装**(事故#4): fail を黙る・空欄で誤魔化す誘惑の構造的排除
- **完了報告曖昧**: 「どこまでやった?」「本当に pass?」「何が fail?」が commander から再質問される運用負荷
- **証跡欠落**: 検収可能性が報告だけでは確認できない状態

本 schema は完了報告を「読めば判断可能な状態」にすることが唯一の責務である。実装・自動生成・他 schema との連動は本 schema の対象外。

---

## 2. 必須フィールド一覧

ClaudeCode が session 完了時に生成する `artifacts/<sid>/completion_report.yaml` は以下の **全フィールドを必須** とする。フィールド欠落は schema 違反として扱う。

| フィールド | 型 | 必須 | 空欄/空配列の扱い |
|---|---|---|---|
| `session_id` | string | ✅ | 空欄禁止 |
| `status` | enum | ✅ | 空欄禁止 |
| `gates_passed` | array<string> | ✅ | 空配列でも明示記載必須 |
| `gates_failed` | array<string> | ✅ | **空配列でも明示記載必須(空欄禁止)** |
| `failure_type` | enum | ✅ | **空欄禁止(`not_applicable` を明示)** |
| `failure_detail` | string | ✅ | **空欄禁止(`not_applicable` 時は `none` を明示)** |
| `artifacts_produced` | array<string> | ✅ | **最低 1 件必須(空配列禁止)** |
| `commit_sha` | string \| null | ✅ | commit 未実施時は明示的に `null` |
| `timestamp` | string (ISO8601) | ✅ | 空欄禁止 |

### 2.1. `session_id`

- 形式: 起票 JSON の `session_id` と完全一致
- 例: `NEW-D`, `session-178-pre`

### 2.2. `status` (enum)

| 値 | 意味 |
|---|---|
| `completed` | 全 completion_criteria 達成・全 acceptance_criteria 達成・gates 全 pass |
| `failed` | gates fail / acceptance fail / scope 違反 |
| `partial` | scope 一部達成・残部は別 session に分離 |

### 2.3. `gates_passed` / `gates_failed`

4-gate(`ruff` / `pytest` / `mypy` / `compileall`)の実行結果を明示。

- `gates_passed`: pass した gate 名の配列(例: `["ruff", "compileall"]`)
- `gates_failed`: **fail した gate 名の配列。pass 全件時でも `[]` を明示記載**

**重要**: docs-only session で pytest / mypy が適用範囲外の場合、その gate は `gates_passed` にも `gates_failed` にも含めない。代わりに「適用範囲外」を `failure_detail` 等で明示する選択肢があるが、本 schema では **実行した gate のみ列挙** し、未実行 gate を黙示するのは許容しない。未実行 gate は `failure_detail` に記載すること。

### 2.4. `failure_type` (enum)

| 値 | 意味 |
|---|---|
| `not_applicable` | failure なし(`status: completed` の場合の標準値) |
| `scope_violation` | 起票 scope を逸脱した変更が発生 |
| `gate_failure` | 4-gate のいずれかが fail |
| `ac_partial` | acceptance_criteria の一部のみ達成 |
| `other` | 上記以外(`failure_detail` で詳細必須) |

**空欄禁止**: `status: completed` でも `failure_type: not_applicable` を必ず明示記載。

### 2.5. `failure_detail`

- 文字列(複数行可)
- `failure_type: not_applicable` のとき: `none` を明示記載(空欄禁止)
- `failure_type: not_applicable` 以外のとき: 何が起きたか・どこで止まったか・次にどうすべきか を1段落以上で記述

### 2.6. `artifacts_produced`

session が生成した artifact の path 配列。**最低 1 件必須**(空配列禁止)。

- 標準的に含むもの: `artifacts/<sid>/run_log.txt`, `artifacts/<sid>/diff_summary.json`, `artifacts/<sid>/completion_report.yaml`
- session 固有の成果物がある場合は追加

### 2.7. `commit_sha` / `timestamp`

- `commit_sha`: 本 session の commit SHA。commit 未実施時は `null` を明示。
- `timestamp`: ISO8601 形式(例: `2026-05-09T19:16:00Z`)。

---

## 3. 事故#4(AC pass 偽装)再発防止メカニズム

本 schema は以下の構造で AC pass 偽装を防ぐ:

### 3.1. 「黙って隠す」誘惑の排除

`gates_failed: []` を **空配列でも明示記載必須** とすることで、fail を黙って報告から省く動作を schema 違反として検出可能にする。

```
[偽装パターン] gates_failed フィールド自体を省略
[防止メカニズム] フィールド必須化により欠落 = schema 違反
```

### 3.2. 「空欄で誤魔化す」誘惑の排除

`failure_type` を **空欄禁止・enum 値必須** とすることで、「何が起きたか言わない」動作を schema 違反として検出可能にする。

```
[偽装パターン] failure_type を空欄にして判断を曖昧化
[防止メカニズム] 空欄禁止・enum 必須により曖昧化 = schema 違反
```

### 3.3. 「成功扱いで failure を消す」誘惑の排除

`failure_detail` を **必須・`not_applicable` 時は `none` 明示** とすることで、「failure があったのに status: completed にする」誘惑を抑止する。

```
[偽装パターン] failure があるのに status: completed
[防止メカニズム] failure_type と status の整合を読み手が機械的に検証可能
                (status: completed なら failure_type: not_applicable が論理必然)
```

### 3.4. 「証跡なし完了報告」の排除

`artifacts_produced` を **最低 1 件必須** とすることで、検証不能な完了報告を schema 違反として検出可能にする。

```
[偽装パターン] artifacts なしで「完了した」と報告
[防止メカニズム] artifacts_produced 空配列禁止により証跡なし = schema 違反
```

---

## 4. artifacts/<sid>/ 添付必須ルール

完了報告と併せて、ClaudeCode は session 毎に `artifacts/<sid>/` ディレクトリを生成し、以下を最低限含める:

| ファイル | 内容 |
|---|---|
| `artifacts/<sid>/run_log.txt` | session 実行中の主要操作ログ |
| `artifacts/<sid>/diff_summary.json` | git diff 要約(変更ファイル一覧・追加削除行数) |
| `artifacts/<sid>/completion_report.yaml` | 本 schema に従った完了報告 |

**ルール**:

- artifacts 配下は session 完了時に **同時生成**(事前生成禁止)
- session 固有成果物は同 dir 内に追加可
- artifacts への path は `completion_report.yaml` の `artifacts_produced` と完全一致

---

## 5. 記入例

### 5.1. 成功 case(全 gate pass)

```yaml
session_id: NEW-D
status: completed
gates_passed:
  - ruff
  - compileall
gates_failed: []
failure_type: not_applicable
failure_detail: none
artifacts_produced:
  - artifacts/NEW-D/run_log.txt
  - artifacts/NEW-D/diff_summary.json
  - artifacts/NEW-D/completion_report.yaml
commit_sha: 1a2b3c4d5e6f7890
timestamp: 2026-05-09T19:30:00Z
```

### 5.2. 失敗 case(gate fail)

```yaml
session_id: example-failed-session
status: failed
gates_passed:
  - ruff
gates_failed:
  - pytest
failure_type: gate_failure
failure_detail: |
  test_xxx で AssertionError 発生。
  期待値と実装の差異を解析中。
  詳細は artifacts/example-failed-session/run_log.txt 参照。
artifacts_produced:
  - artifacts/example-failed-session/run_log.txt
  - artifacts/example-failed-session/diff_summary.json
  - artifacts/example-failed-session/completion_report.yaml
commit_sha: null
timestamp: 2026-05-09T20:00:00Z
```

### 5.3. 部分達成 case

```yaml
session_id: example-partial-session
status: partial
gates_passed:
  - ruff
  - compileall
gates_failed: []
failure_type: ac_partial
failure_detail: |
  ac1 / ac2 達成。
  ac3 は scope 外の dependency が必要と判明したため、別 session に分離申請。
  本 session は ac1 / ac2 までで commit 済。
artifacts_produced:
  - artifacts/example-partial-session/run_log.txt
  - artifacts/example-partial-session/diff_summary.json
  - artifacts/example-partial-session/completion_report.yaml
commit_sha: 9f8e7d6c5b4a3210
timestamp: 2026-05-09T21:00:00Z
```

---

## 6. 検証観点(commander / GPT 用)

完了報告を検収する際、以下を機械的に確認できる:

| 観点 | 確認方法 |
|---|---|
| schema 違反検出 | YAML の必須フィールド存在チェック |
| `gates_failed` 明示 | フィールドが存在し配列であること |
| `failure_type` 妥当性 | enum 値のいずれかであること |
| `failure_detail` 整合 | `not_applicable` 時に `none` 明示・それ以外時に空欄でないこと |
| 証跡有無 | `artifacts_produced` が最低 1 件・実 file 存在 |
| `status` と `failure_type` 整合 | `completed` なら `not_applicable` / それ以外なら適切な enum |

---

## 7. 本 schema の境界(明示的な非対象)

以下は本 schema の対象外。混同しないこと:

- **GPT / ClaudeWeb の報告** — 本 schema は ClaudeCode のみ対象
- **handoff_artifact** — 完了報告と handoff は別概念(本 schema は完了報告のみ)
- **current_state.json** — 状態 projection は別 schema(連動なし)
- **next_action 自動生成** — schema は schema・engine は別話
- **completion_report の自動 validation 実装** — schema 確定のみ・実装は別 session

---

## 8. 改版ルール

本 schema は本 session(NEW-D)で canonical 化される。以後の改版は:

- 必須フィールドの **追加** は影響大のため別 session で起票
- 必須フィールドの **削除** は事故#4 再発防止メカニズムを破壊するため禁止方向
- 既存フィールドの **意味変更** は破壊的変更として禁止方向
- enum 値の **追加** は許容(`failure_type` の選択肢追加など)

---

## 9. 関連既知事故(memory 由来)

本 schema が直接対象とする事故:

- **事故#4(AC pass 偽装)**: ClaudeCode 完了報告後に artifact 手動 grep で発覚 → 本 schema で構造的予防

本 schema が対象としない事故:

- 事故#1(正本盲信) — 別途 docs/repo 現物確認ルールで対処
- 事故#2(ID 衝突) — 起票前 `git log --grep` で対処
- 事故#3(Sealed 露出) — `git stash` 家族 commander manual only で対処
- 事故#5(参謀越権) — role 定義側で対処

---

**END OF SCHEMA SPECIFICATION**

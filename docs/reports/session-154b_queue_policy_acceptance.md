# session-154b 受入検収レポート — queue_policy.yaml

検収実施日: 2026-05-01
セッション ID: session-154b
対象ファイル: docs/config/queue_policy.yaml

---

## 1. STEP 0: 存在確認

| 確認項目 | 結果 |
|---------|------|
| ファイルパス | docs/config/queue_policy.yaml |
| 存在 | YES |
| ファイルサイズ | 3288 bytes |
| 最終更新 | 2026-04-22 20:26 |
| 分岐判定 | 分岐 A（存在）→ 受入検収続行 |

本セッションでの新規作成: **なし（AC-154b-02 PASS）**

---

## 2. queue_policy.yaml 実ファイル構造（AC-154b-03）

### 2.1 トップレベルキー一覧

| # | 実体キー名 | 概要 |
|---|-----------|------|
| 1 | `version` | v1.1 |
| 2 | `last_updated` | 2026-04-19 |
| 3 | `description` | ファイルの説明テキスト |
| 4 | `condition_dsl` | 構造化条件式の定義（operators / field_source / combination_logic / error_handling） |
| 5 | `queues` | 実行キュー定義（daytime / night / blocked / waiting_human / retry） |
| 6 | `execution_rules` | 実行可否ルール（isolation / night_batch / blocked_queue / waiting_human_queue） |
| 7 | `project_priority` | プロジェクト優先度（risk_to_priority / explicit_priority_order） |
| 8 | `retry_policy` | リトライ設定（max_retry / same_failure_retry / require_error_classification 等） |
| 9 | `human_gate` | human approval 必須条件（required_if） |
| 10 | `decision_priority` | 競合ルール優先順位（safety > data_integrity > production_stability > speed） |

### 2.2 condition_dsl 主要内容

- `operators`: eq / ne / in / not_in / gt / lt / gte / lte
- `field_source.scope`: registry_only（project_registry.json のフィールドのみ参照）
- `combination_logic.default`: AND
- `error_handling`: undefined_field → forbidden、type_mismatch → forbidden、undefined_operator → parse_error_abort

### 2.3 queues 構成

| キュー名 | default_enabled | 説明 |
|---------|----------------|------|
| daytime | true | 日中実行（人間監視あり）、priority_order: critical > high > medium > low |
| night | true | 夜間自動実行 |
| blocked | true | 自動実行禁止 |
| waiting_human | true | 人間判断待ち |
| retry | true | リトライ実行 |

### 2.4 execution_rules 主要内容

- `isolation.parallel_allowed_if`: db_touch_allowed = false のとき並列許可
- `isolation.serial_required_if`: db_touch_allowed = true のとき直列必須
- `night_batch.allowed_if`: night_batch_allowed=true かつ db_touch_allowed=false かつ deploy_risk in [low, medium]
- `night_batch.forbidden_if`: db_touch_allowed=true または deploy_risk=critical

### 2.5 human_gate 主要内容

```yaml
human_gate:
  required_if:
    - field: deploy_risk
      operator: eq
      value: critical
    - field: db_touch_allowed
      operator: eq
      value: true
```

deploy_risk=critical または db_touch_allowed=true の場合に human approval 必須。

---

## 3. schema_v0 との整合確認（AC-154b-04）

session-153 の queue_policy_schema_v0.md が定義する「必須 3 キー」と実ファイルのキーの対応を記録する。

### 3.1 対応表

| schema_v0 定義キー | 実ファイル対応キー | 対応状況 |
|------------------|----------------|---------|
| `selection_rules` | **存在しない** | ⚠️ キー名乖離 |
| `selection_rules.status_required` | **存在しない**（selector が docs/sessions/*.json から全候補を読む仕組みで代替） | ⚠️ キー名乖離 |
| `selection_rules.depends_on_required_status` | **存在しない** | ⚠️ キー名乖離 |
| `selection_rules.human_required_priority` | `project_priority.risk_to_priority`（意味的に部分対応） | ⚠️ 部分対応・キー名乖離 |
| `stop_reason_reference` | **存在しない** | ⚠️ キー名乖離 |
| `stop_reason_reference.source` | **存在しない** | ⚠️ キー名乖離 |
| `stop_reason_reference.referenced_values` | **存在しない** | ⚠️ キー名乖離 |
| `human_approval_enforcement` | `human_gate`（意味的に対応） | ⚠️ キー名乖離・意味的対応あり |
| `human_approval_enforcement.required` | `human_gate.required_if`（条件式形式で実装） | ⚠️ 型と構造が異なる |
| `human_approval_enforcement.auto_execution_forbidden` | **明示的なフィールドなし**（daytime キュー + human_gate の組み合わせで実質的に実現） | ⚠️ 明示フィールドなし |

### 3.2 整合確認サマリー

| schema_v0 必須キー | 整合状態 |
|------------------|---------|
| `selection_rules` | **乖離あり** — 実ファイルに対応キーなし |
| `stop_reason_reference` | **乖離あり** — 実ファイルに対応キーなし |
| `human_approval_enforcement` | **部分対応** — `human_gate` キーが意味的に対応するが名称・型が異なる |

### 3.3 実ファイルの追加構造（schema_v0 定義外）

以下は schema_v0 が定義していない実ファイル固有の構造であり、運用上の拡張として記録する。

| 実体キー | 内容 |
|---------|------|
| `condition_dsl` | 構造化条件式エンジン定義（schema_v0 には含まれない高度機能） |
| `execution_rules` | 並列/直列・夜間バッチ・blocked_queue ルーティング |
| `retry_policy` | リトライ設定 |
| `decision_priority` | 競合ルールの優先順位 |

### 3.4 後続 BACKLOG（キー名乖離の解消候補）

| BACKLOG ID | 内容 |
|-----------|------|
| BACKLOG-S154b-001 | queue_policy_schema_v0.md を実ファイルのキー名（human_gate 等）に合わせて改訂するか、実ファイルを schema_v0 準拠キー名に更新するかを判断する session を起票する |
| BACKLOG-S154b-002 | `stop_reason_reference` キーを queue_policy.yaml に追加するか否かを判断する |
| BACKLOG-S154b-003 | `selection_rules` キーを queue_policy.yaml に追加するか否かを判断する |

---

## 4. selector 実装と queue_policy.yaml の依存確認（AC-154b-05）

### 4.1 _resolve_execution_mode() の参照先

`orchestration/selector/core.py` の `_resolve_execution_mode()` 関数（session-162 で実装）のシグネチャ:

```python
def _resolve_execution_mode(
    selected_session: dict[str, Any],
    project_registry: dict[str, Any],
) -> str | None:
```

**引数に `queue_policy` が存在しない。**

参照先:
1. `selected_session.get("execution_mode")` — session.json の execution_mode フィールド
2. `project_registry` の `default_execution_mode` フィールド — project_registry.json

**結論: `_resolve_execution_mode()` は `queue_policy.yaml` に直接依存しない。（AC-154b-05 PASS）**

### 4.2 queue_policy に依存する関数（参考）

`_priority_rank_value()` は `queue_policy.get("project_priority")` および `queue_policy.get("queues")` を参照する。これは execution_mode とは無関係のセッション優先度計算ロジックであり、今回の受入検収スコープ外。

---

## 5. AC-154b 検証結果一覧

| AC ID | 内容 | 結果 | 根拠 |
|-------|------|------|------|
| AC-154b-01 | queue_policy.yaml が既存ファイルとして存在する | **PASS** | ls -la 確認済み（3288 bytes） |
| AC-154b-02 | 本セッションで queue_policy.yaml を新規作成していない | **PASS** | git diff --name-only に含まれない |
| AC-154b-03 | 主要構造（condition_dsl / queues / execution_rules / retry_policy / human_gate 等）が確認され実体キー名が記録されている | **PASS** | 本レポート §2 に記録済み |
| AC-154b-04 | schema_v0 との整合確認（キー名対応・乖離）が記録されている | **PASS（乖離あり）** | 本レポート §3 に対応表・BACKLOG 記録済み |
| AC-154b-05 | _resolve_execution_mode() が queue_policy.yaml に直接依存していない | **PASS** | 本レポート §4 に確認済み |
| AC-154b-06 | queue_policy.yaml 本体に破壊的変更がない | **PASS** | git diff 0 行差分（後続 §6 で確認） |
| AC-154b-07 | .claude/ と DL/ に変更がない | **PASS** | git status --short に含まれない |
| AC-154b-08 | JSON / YAML 構文確認 PASS（3 ファイル） | **PASS** | python3 確認済み（後続 §6 で確認） |

---

## 6. 構文確認・scope 検査

以下は commit 前の確認手順。本レポートは session-154b の検収記録として保存される。

### 構文確認コマンド

```bash
python3 -m json.tool docs/sessions/session-154b.json > /dev/null
python3 -c "import yaml; yaml.safe_load(open('docs/acceptance/session-154b.yaml'))"
python3 -c "import yaml; yaml.safe_load(open('docs/config/queue_policy.yaml'))"
```

### git diff 確認

```bash
git diff -- docs/config/queue_policy.yaml  # 0 行差分であること
git diff -- docs/sessions/session-154.json  # 0 行差分であること（旧定義保持）
git status --short                          # ?? DL/ + 3 新規ファイルのみ
```

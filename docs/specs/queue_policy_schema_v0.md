# queue_policy.yaml schema v0 (docs-only)

## 1. 目的

本文書は、session-152 で定義した next-session selector が参照する `queue_policy.yaml` の最小項目を schema として定義するものである。本文書は schema 仕様のみを扱い、実値・実データインスタンスは含めない。

## 2. 範囲と非範囲

### 2.1 本文書が定義するもの

- `queue_policy.yaml` の最小項目 schema (型 / 必須 / 取り得る値)
- selector が policy を読む契約 (load → validate → apply)
- session-152 入出力契約との対応関係

### 2.2 本文書が定義しないもの

- `queue_policy.yaml` の実ファイルおよび実値 (= session-154 以降の対象)
- `project_registry.json` の schema (= session-155 以降の対象)
- selector の Python 実装 (= session-156 以降の対象)
- queue engine / scheduler / 自動実行の仕様

## 3. session-152 入出力契約との対応

session-152 (next-session selector) は次の入出力契約を持つ。

- 入力: pending_sessions が session_id / status / depends_on / human_required を持つ list[object]
- 出力: next_session_candidate / human_required_flag / stop_reason
- 選択 policy: status=open かつ depends_on 全件 done / human_required=false 優先
- 停止条件 stop_reason enum: no_candidates / all_blocked_by_dependency / only_human_required_left
- 自動実行禁止 / human approval 必須

本文書はこの contract のうち「選択 policy」「停止条件 enum 参照」「human approval 強制」の 3 点を `queue_policy.yaml` の schema として外部化する。

## 4. queue_policy.yaml schema (最小項目)

### 4.1 トップレベル構造

| キー | 型 | 必須 | 概要 |
|---|---|---|---|
| `selection_rules` | object | yes | selector が候補 session を絞り込むためのルール群 |
| `stop_reason_reference` | object | yes | session-152 で正本定義された stop_reason 3 enum を policy から参照可能化する項目 |
| `human_approval_enforcement` | object | yes | human approval 必須を policy レベルで強制する項目 |

### 4.2 selection_rules

selector が候補 session を絞り込むためのルール群。次の 3 サブキーを必須とする。

#### 4.2.1 selection_rules.status_required

- 型: string
- 必須: yes
- 取り得る値: pending_sessions[].status の取り得る値の部分集合 (例として `"open"`)
- 役割: 選択候補となる session の status を限定する。

#### 4.2.2 selection_rules.depends_on_required_status

- 型: string
- 必須: yes
- 取り得る値: pending_sessions[].status の取り得る値の部分集合 (例として `"done"`)
- 役割: 候補 session の depends_on に列挙された全 session が当該 status であることを要件化する。

#### 4.2.3 selection_rules.human_required_priority

- 型: string (enum)
- 必須: yes
- 取り得る値: `"false_first"` / `"true_first"` / `"no_priority"`
- 役割: human_required=false の session を優先するか、true を優先するか、優先順を持たないかを policy として宣言する。

### 4.3 stop_reason_reference

session-152 で正本定義された stop_reason 3 enum を policy 側から参照可能とする項目。本 schema は enum 値を **再定義せず**、session-152 を正本として参照する旨のみを規定する。

| サブキー | 型 | 必須 | 概要 |
|---|---|---|---|
| `source` | string | yes | enum 正本の所在 (許容値: `"session-152"` のみ) |
| `referenced_values` | list[string] | yes | session-152 で定義された enum 値を文字列として列挙 (no_candidates / all_blocked_by_dependency / only_human_required_left)。本 schema での新規追加・変更は禁止。 |

### 4.4 human_approval_enforcement

human approval 必須を policy レベルで強制する項目。

| サブキー | 型 | 必須 | 概要 |
|---|---|---|---|
| `required` | bool | yes | human approval を必須とするか。許容値: `true` のみ (本 schema は false を許容しない)。 |
| `auto_execution_forbidden` | bool | yes | selector の出力に基づく自動実行を policy レベルで禁止するか。許容値: `true` のみ。 |

## 5. selector が policy を読む契約 (load → validate → apply)

selector は次の 3 ステップで policy を扱う。本契約は schema レベルで義務化する。

### 5.1 load

- 入力: `queue_policy.yaml` のファイルパス
- 出力: 構造化されたメモリ上の policy オブジェクト
- 失敗時の挙動: ファイル不在・YAML 構文エラーは selector を停止させ、stop_reason として返さず、上位への error として扱う。

### 5.2 validate

- 入力: load で得られた policy オブジェクト
- 出力: schema 適合性の判定結果 (適合 / 非適合)
- 必須検査:
  - トップレベルに `selection_rules` / `stop_reason_reference` / `human_approval_enforcement` の 3 キーが存在すること。
  - `selection_rules` 配下に `status_required` / `depends_on_required_status` / `human_required_priority` の 3 キーが存在すること。
  - `stop_reason_reference.source` が `"session-152"` であること。
  - `stop_reason_reference.referenced_values` が session-152 で定義された 3 enum 値の集合と一致すること。
  - `human_approval_enforcement.required` が `true` であること。
  - `human_approval_enforcement.auto_execution_forbidden` が `true` であること。
- 非適合時: selector を停止させ、上位への error として扱う。stop_reason は返さない。

### 5.3 apply

- 入力: validate を通過した policy オブジェクトと session-152 入力契約に従う pending_sessions
- 出力: session-152 出力契約に従う next_session_candidate / human_required_flag / stop_reason
- 適用順:
  1. `selection_rules.status_required` で候補を絞り込む。
  2. `selection_rules.depends_on_required_status` で候補をさらに絞り込む。
  3. 残候補が空なら、stop_reason を session-152 の出力契約に従って no_candidates / all_blocked_by_dependency / only_human_required_left のいずれかとして返す。
  4. 残候補がある場合、`selection_rules.human_required_priority` に従って候補を並べ替え、先頭を next_session_candidate として返す。
  5. `human_approval_enforcement.required = true` および `auto_execution_forbidden = true` のため、selector は推薦のみを行い、自動実行はしない。

## 6. 本文書の制約

- 本文書は schema 定義のみであり、`queue_policy.yaml` の実値・実データインスタンスを含まない。
- stop_reason enum は session-152 を正本とし、本文書内で再定義しない。
- 本文書は docs-only であり、Python 実装・queue engine・scheduler・自動実行の仕様を含まない。
- `queue_policy.yaml` 実ファイルは session-154 以降で別途定義する。
- `project_registry.json` は session-155 以降で別途定義する。
- selector の Python 実装は session-156 以降で別途定義する。

## 7. 参照

- session-152: next-session selector の入出力契約 (正本)
- BACKLOG-NEXT-SESSION-SELECTOR-001: session-152 の起票 backlog
- BACKLOG-QUEUE-POLICY-SCHEMA-001: 本セッションの起票 backlog

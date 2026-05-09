# compact_context_pack.v0 — 仕様概要

**正本**: `compact_context_pack_v0.json`  
**補助**: `compact_context_pack_v0.yaml`（human review 用）  
**schema_version**: `compact_context_pack.v0`

---

## 目的

GPT（司令塔）→ ClaudeCode（現場責任者）への handoff artifact 実行時に注入する  
**minimal context** の境界を定義する。

AI の hallucination / context pollution を防ぐため、許可フィールドを明示的に列挙し、  
それ以外を forbidden とする allowlist 設計を採用する。

---

## Allowlist（注入許可フィールド）

| フィールド | 必須 | 制約 |
|---|---|---|
| `session_id` | ✓ | max 64 chars |
| `phase_id` | ✓ | max 16 chars |
| `goal` | ✓ | max 512 chars |
| `scope` | ✓ | max 16 items × 256 chars |
| `base_commit` | ✓ | full SHA (40 hex chars) |
| `required_prior_session` | ✓ | max 64 chars |
| `constraints` | — | max 16 items × 512 chars |
| `acceptance_ref` | ✓ | max 256 chars |
| `allowed_changes_detail` | ✓ | max 32 items、`パス:内容` 形式 |
| `forbidden_changes` | ✓ | max 64 items |

---

## Forbidden Context（注入禁止）

| カテゴリ | 理由 |
|---|---|
| full_file_contents | token budget 超過・不要情報混入 |
| git_log_history | session 実行に不要。base_commit SHA のみ許可 |
| test_output_logs | 合否結果のみ acceptance_ref で参照 |
| runtime_state_snapshots | state.json / PID / lock は再現性を損なう |
| prior_session_full_artifacts | required_prior_session ID のみ参照 |
| unrelated_project_context | EC-CUBE / WordPress / fina 等は scope 外 |
| credentials_and_secrets | セキュリティ上の理由により絶対禁止 |

---

## Size Budget

- **max_total_tokens**: 2048
- **max_total_chars**: 8192
- **overflow_policy**: `fail_and_report`（budget 超過時はエラー）

---

## Canonical Decisions

| 項目 | 値 |
|---|---|
| canonical_format | JSON |
| secondary_format_allowed | false |
| deterministic_ordering | MUST |
| machine_readable | primary |
| validation_mode | strict |
| unknown_required_missing | fail |
| unknown_extra_fields | warn |
| injection_point | handoff_artifact_only |

---

## v0 スコープ外

- injection engine 実装
- validator 実装
- token counter 実装
- schema migration (v1 以降)
- multi-agent context sharing
- context compression algorithm

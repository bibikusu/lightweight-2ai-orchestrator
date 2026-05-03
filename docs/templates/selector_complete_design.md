# Selector Complete Design (Canonical)

本ドキュメントは selector 完成形の正本仕様である。実装は本仕様に従う。

## 1. Responsibility

selector の責務は以下に限定する。

- candidate sessions の収集
- 実行不可 session の skip 判定
- priority_rank_value による順位付け
- selected_session_id の決定 (1 件 または null)
- selection_reason の出力 (必須)
- skipped_sessions の記録 (必須、silent skip 禁止)
- execution_mode の決定 (full_stack または fast_path)

selector は queue 接続、scheduler 起動、UI 表示、Decision Engine 上位判断は行わない。

## 2. Input Schema

selector は以下を入力として受け取る。

- sessions: list[session_json] — docs/sessions/*.json から読み込んだ session 定義
- acceptance: list[acceptance_yaml] — docs/acceptance/*.yaml から読み込んだ acceptance 定義
- project_registry: object — docs/config/project_registry.json の内容
- queue_policy: object — docs/config/queue_policy.yaml の内容
- previous_results: list[state] — artifacts/session-*/state.json の集約

## 3. Output Schema

selector は以下を出力する。**全フィールド必須**、欠落は契約違反とする。

```json
{
  "selected_session_id": "string | null",
  "execution_mode": "full_stack | fast_path",
  "selection_reason": "string",
  "candidate_sessions": [
    {
      "session_id": "string",
      "priority_rank_value": "integer",
      "eligible": "boolean"
    }
  ],
  "metadata": {
    "skipped_sessions": [
      {
        "session_id": "string",
        "path": "string",
        "skip_reason": "string"
      }
    ],
    "policy_version": "string",
    "generated_at": "string (ISO8601)"
  }
}
```

selected_session_id は必ず 1 件、または `null` を明示的に返す。空文字列は禁止。

## 4. Priority Evaluation

- priority_rank_value は整数 (integer)
- 値が小さいほど優先度高
- score (連続値) は使用禁止
- queue_policy.yaml の priority ルールに準拠
- 同一値の場合は session_id の辞書順で安定ソート (決定論性確保)

## 5. Skip Conditions

selector は以下の条件で session を skip する。**silent skip 禁止**。
全ての skip は metadata.skipped_sessions に path と skip_reason 付きで記録する。

許可される skip_reason 標準値:

- `json_parse_error` — session JSON の parse に失敗
- `acceptance_mismatch` — acceptance YAML が存在しない、または acceptance_ref と不一致
- `forbidden_scope` — forbidden_changes が現在の git 状態に違反する
- `dependency_unresolved` — 依存 session が completed でない
- `already_completed` — 当該 session が完了済み
- `policy_excluded` — queue_policy により除外対象
- `registry_mismatch` — project_registry に project_id が存在しない

上記以外の skip_reason は禁止。新規追加は queue_policy.yaml 改訂を伴うこと。

## 6. Execution Mode

execution_mode は以下の enum:

- `full_stack` — 通常実行 (git_guard → prepared_spec → implementation → patch_apply → checks → report)
- `fast_path` — 軽量実行 (docs-only / 検収再実行 / acceptance-only review)

決定ルール:

- session JSON に `type: docs-only` がある場合 → `fast_path`
- それ以外 → `full_stack`
- project_registry の `execution_mode_default` が定義されている場合は registry が優先

## 7. Determinism Contract

selector は決定論的でなければならない。

- 同一入力 (sessions / acceptance / registry / policy / previous_results が完全に同一) に対して、同一出力を保証する
- 乱数、現在時刻、外部 API 呼び出しを selection ロジックに含めない
- metadata.generated_at のみ非決定論的でよい (記録目的)

## 8. Output Persistence

selector の出力は以下に保存する。

- パス: `artifacts/selector/<timestamp>.json`
- 必須キー: `selected_session_id`, `execution_mode`, `selection_reason`, `candidate_sessions`, `metadata`
- timestamp は ISO8601 (例: `20260504T120000Z`)

## 9. Boundary

本仕様は selector 単体の完成形である。以下は本仕様の対象外:

- queue への enqueue (Decision Engine の責務)
- run_session.py の subprocess 呼び出し (CLI 層の責務)
- scheduler / cron 連携 (運用層の責務)
- Dashboard / UI 表示 (presentation 層の責務)

## 10. Versioning

本ドキュメント v1.0 を canonical 起点とする。改訂時は metadata.policy_version をインクリメントすること。

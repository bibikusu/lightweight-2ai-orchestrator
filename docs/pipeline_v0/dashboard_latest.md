# 観測ダッシュボード（artifacts 集計）

## Summary

- generated_at: `2026-04-04T13:35:24.739640+00:00`
- artifacts_root: `/Users/kunihideyamane/AI_Team/軽量2AIオーケストレーター方式/artifacts`
- sessions_scanned: 35
- sessions_with_report: 33
- success_rate: **0.3939393939393939**
- success_count: 13
- failed_count: 18
- other_status_count: 2

### failure_type_distribution

（`status` が `failed` のセッションのみを集計。成功セッションは含めない。 `failure_type` が未設定の失敗は `__missing_failure_type__` に分類。`__success__` キーは使わない。）

- `patch_apply_failure`: 7
- `test_failure`: 6
- `spec_missing`: 3
- `__missing_failure_type__`: 1
- `type_mismatch`: 1

### retry_stats

- sessions_with_retry_state_file: 14
- total_retry_count: 10
- avg_retry_count: 0.30303
- max_retry_count: 1
- retry_histogram: `{'0': 23, '1': 10}`

### changed_files_stats

- empty_count: 13
- nonempty_count: 20
- avg_files_per_session: 0.818182

## Sessions

| session_id | status | failure_type | completion_status | retry_count | changed_files_count |
| --- | --- | --- | --- | ---: | ---: |
| live-run-safe-04 | success | None | review_required | 0 | 0 |
| phase2-real-02 | success | None | review_required | 0 | 1 |
| real-run-safe-01 | failed | patch_apply_failure | stopped | 1 | 0 |
| real-run-safe-02 | failed | type_mismatch | failed | 1 | 1 |
| session-01 | dry_run | None | conditional_pass | 0 | 0 |
| session-02a | completed | None | None | 0 | 2 |
| session-101 | failed | patch_apply_failure | stopped | 1 | 0 |
| session-102 | failed | patch_apply_failure | stopped | 1 | 0 |
| session-106 | success | None | review_required | 0 | 0 |
| session-107b | success | None | review_required | 0 | 1 |
| session-11-duration | success | None | review_required | 0 | 2 |
| session-114 | failed | patch_apply_failure | stopped | 1 | 0 |
| session-114-preflight | failed | test_failure | stopped | 0 | 0 |
| session-115 | success | None | review_required | 0 | 1 |
| session-116 | failed | patch_apply_failure | stopped | 1 | 0 |
| session-12 | success | None | review_required | 0 | 1 |
| session-12 | failed | spec_missing | stopped | 0 | 1 |
| session-12 | failed | spec_missing | stopped | 0 | 1 |
| session-14 | failed | spec_missing | stopped | 0 | 0 |
| session-57 | success | None | review_required | 0 | 1 |
| session-57 | failed | None | stopped | 0 | 1 |
| session-81 | failed | test_failure | stopped | 1 | 1 |
| session-81a | success | None | review_required | 0 | 1 |
| session-81」 | failed | test_failure | stopped | 0 | 0 |
| session-88 | failed | patch_apply_failure | stopped | 1 | 0 |
| session-92 | failed | test_failure | stopped | 0 | 2 |
| session-93 | success | None | review_required | 0 | 3 |
| session-94 | failed | test_failure | stopped | 0 | 2 |
| session-95 | success | None | review_required | 0 | 1 |
| session-96 | success | None | conditional_pass | 0 | 1 |
| session-97 | success | None | review_required | 0 | 1 |
| session-canary-01 | failed | test_failure | stopped | 1 | 2 |
| session-canary-01 | failed | patch_apply_failure | stopped | 1 | 0 |

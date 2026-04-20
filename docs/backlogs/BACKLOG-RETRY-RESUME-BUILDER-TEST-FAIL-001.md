# BACKLOG-RETRY-RESUME-BUILDER-TEST-FAIL-001

## 優先度
中

## 発覚日
2026-04-21 (session-125a-v2 sandbox 4-gate 検証時、整合修正レーン作業中)

## 内容
main 基準で以下の 30 test が fail している。今回の review_points / docs-only / dashboard / A02 research 系の変更とは無関係で、既存ベースライン fail と判定。

### fail 原因グルーピング (粗)
- assert 1 == 0 (main / 戻り値不整合系): 18 件
- assert 0 == 1 (件数・呼び出し回数不一致): 4 件
- FileNotFoundError (retry_instruction.json 未生成): 3 件
- assert None is True / assert False is True (期待フラグ未設定): 4 件
- サブプロセス pytest 戻り値不一致: 1 件

### 該当 test 一覧 (30 件)
- backend/tests/test_aggregate_observation_reports.py::test_aggregate_reports_passes_validation_suite
- backend/tests/test_report_generation.py::test_report_json_is_generated_on_success
- backend/tests/test_resume_execution_rules.py (3 件)
- backend/tests/test_retry_cause_deduplication.py (5 件)
- backend/tests/test_retry_count_control.py (4 件)
- backend/tests/test_retry_loop_execution.py (5 件)
- backend/tests/test_run_session_builder_integration.py (2 件)
- backend/tests/test_run_session_reviewer_retry_integration.py (1 件)
- backend/tests/test_session_state_checkpoint.py (4 件)
- backend/tests/test_session_state_resume.py (3 件)
- backend/tests/test_single_retry_limit.py (1 件)

## 次アクション
別レーンで原因をグルーピングし、修正 session を起票する。着手は session-145b / a02-design-01 完了後を想定。

## 関連
- 発覚元: session-125a-v2 (sandbox) 4-gate 検証、2026-04-21
- 他 BACKLOG との関係: 独立 (SANDBOX-CLEANUP-001 / PATCH-001 / AUTH-REQUIREMENTS-SEPARATION-001 とは無関係)

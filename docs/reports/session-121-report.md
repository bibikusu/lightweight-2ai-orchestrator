# session-121 report (M02 sequential executor)

## diagnosis
- 判定: パターンB（M02 実装が M01 前提を破壊）
- 根拠:
  - `backend/tests/test_run_plan_loader_validation.py::test_existing_checks_pass_for_m01` の4コマンド目
    `python3 orchestration/run_plan.py --plan-id plan-01` が非dry-runで実セッション実行に入るようになっていた。
  - M01 では同コマンドが成功する前提（AC-M01-08）があり、ここで `run_session.py` 実行結果に依存して失敗していた。

## implementation_summary
- `orchestration/run_plan.py` に `--execute` フラグを追加し、モード分離を実施:
  - `--dry-run`: M01同様、構造検証のみ
  - フラグなし非dry-run: 構造検証のみ（実行スキップ、M01互換）
  - `--execute`: M02 sequential executor を起動
- `backend/tests/test_run_plan_sequential_executor.py` を更新:
  - AC-M02-08 の4コマンド検証は非dry-run時に `--execute` を明示する形に変更
  - `--execute` なし非dry-runで `execute_sessions` が走らないことを検証する回帰テストを追加
- `run_session.py` / `plan_schema.py` / registry 系には変更なし

## changed_files
- `orchestration/run_plan.py`
- `backend/tests/test_run_plan_sequential_executor.py`
- `docs/reports/session-121-report.md`

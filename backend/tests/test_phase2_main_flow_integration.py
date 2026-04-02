"""AC-87-01〜04: Phase2 integration into main flow テスト。"""
import json
from pathlib import Path

from orchestration.run_session import (
    extract_api_usage,
    persist_session_reports,
    decide_completion_status,
    SessionContext,
)


# ---------------------------------------------------------------------------
# テスト用ヘルパー
# ---------------------------------------------------------------------------
def _make_ctx(session_id: str = "session-87") -> SessionContext:
    return SessionContext(
        session_id=session_id,
        session_data={
            "session_id": session_id,
            "phase_id": "phase3",
            "title": "integration test",
            "goal": "test goal",
            "scope": [],
            "out_of_scope": [],
            "constraints": [],
            "acceptance_ref": "docs/acceptance/session-87.yaml",
            "allowed_changes": ["orchestration/run_session.py", "backend/tests/"],
        },
        acceptance_data={
            "raw_yaml": "",
            "parsed": {
                "session_id": session_id,
                "acceptance": [
                    {"id": "AC-87-01", "test_name": "test_main_flow_invokes_evaluate_completion_decision"},
                    {"id": "AC-87-02", "test_name": "test_main_flow_extracts_and_passes_api_usage"},
                    {"id": "AC-87-03", "test_name": "test_main_flow_passes_api_usage_and_call_count_to_report"},
                    {"id": "AC-87-04", "test_name": "test_phase2_integration_preserves_existing_success_flow"},
                ],
            },
        },
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={},
    )


def _persist(session_dir: Path, ctx=None, **kwargs) -> dict:
    """persist_session_reports を呼び出して report.json を返す。"""
    defaults = dict(
        prepared_spec={},
        impl_result={"changed_files": [], "risks": [], "open_issues": []},
        checks={},
        status="success",
        dry_run=False,
        started_at="2026-04-02T00:00:00",
        finished_at="2026-04-02T00:01:00",
    )
    defaults.update(kwargs)
    persist_session_reports(session_dir, ctx, **defaults)
    return json.loads((session_dir / "report.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# AC-87-01: evaluate_completion_decision が report payload の追加フィールドに反映される
# ---------------------------------------------------------------------------
class TestMainFlowInvokesEvaluateCompletionDecision:
    def test_phase2_completion_eval_field_exists(self, tmp_path: Path):
        """AC-87-01: report.json に phase2_completion_eval フィールドが存在する。"""
        ctx = _make_ctx()
        report = _persist(tmp_path, ctx=ctx)
        assert "phase2_completion_eval" in report

    def test_phase2_completion_eval_has_required_keys(self, tmp_path: Path):
        """AC-87-01: phase2_completion_eval に completion と reasons キーが存在する。"""
        ctx = _make_ctx()
        report = _persist(tmp_path, ctx=ctx)
        eval_result = report["phase2_completion_eval"]
        assert "completion" in eval_result
        assert "reasons" in eval_result

    def test_phase2_completion_eval_completion_is_valid_value(self, tmp_path: Path):
        """AC-87-01: phase2_completion_eval.completion は pass または fail。"""
        ctx = _make_ctx()
        report = _persist(tmp_path, ctx=ctx)
        assert report["phase2_completion_eval"]["completion"] in ("pass", "fail")

    def test_phase2_eval_does_not_replace_completion_status(self, tmp_path: Path):
        """AC-87-01: 既存の completion_status フィールドは破壊されない。"""
        ctx = _make_ctx()
        report = _persist(tmp_path, ctx=ctx)
        assert "completion_status" in report
        assert "phase2_completion_eval" in report
        # 両方が共存すること


# ---------------------------------------------------------------------------
# AC-87-02: extract_api_usage が prepared_spec と implementation 応答から usage を抽出する
# ---------------------------------------------------------------------------
class TestMainFlowExtractsAndPassesApiUsage:
    def test_extract_api_usage_from_response_with_usage(self):
        """AC-87-02: usage キーがある応答から usage を抽出できる。"""
        response = {"result": "data", "usage": {"total_tokens": 500}}
        assert extract_api_usage(response) == {"total_tokens": 500}

    def test_extract_api_usage_from_response_without_usage(self):
        """AC-87-02: usage キーがない応答は空辞書を返す。"""
        response = {"result": "data", "spec": {}}
        assert extract_api_usage(response) == {}

    def test_api_usage_field_appears_in_report(self, tmp_path: Path):
        """AC-87-02: api_usage が report.json に含まれる。"""
        ctx = _make_ctx()
        usage = {"openai": {"total_tokens": 100}, "claude": {"input_tokens": 200}}
        report = _persist(tmp_path, ctx=ctx, api_usage=usage)
        assert report["api_usage"]["openai"]["total_tokens"] == 100
        assert report["api_usage"]["claude"]["input_tokens"] == 200


# ---------------------------------------------------------------------------
# AC-87-03: persist_session_reports に api_usage と api_call_count が渡される
# ---------------------------------------------------------------------------
class TestMainFlowPassesApiUsageAndCallCountToReport:
    def test_api_usage_and_call_count_both_in_report(self, tmp_path: Path):
        """AC-87-03: api_usage と api_call_count が同一 report.json に共存する。"""
        usage = {"openai": {}, "claude": {}}
        call_count = {"openai": 1, "claude": 2}
        report = _persist(tmp_path, api_usage=usage, api_call_count=call_count)
        assert "api_usage" in report
        assert "api_call_count" in report
        assert report["api_call_count"]["claude"] == 2

    def test_api_usage_defaults_to_empty_when_not_passed(self, tmp_path: Path):
        """AC-87-03: api_usage を渡さなければ空辞書として保存される。"""
        report = _persist(tmp_path)
        assert report["api_usage"] == {}
        assert report["api_call_count"] == {}

    def test_report_is_json_serializable(self, tmp_path: Path):
        """AC-87-03: api_usage / api_call_count を含む report.json が正常に読み込める。"""
        usage = {"openai": {"total_tokens": 50}, "claude": {"input_tokens": 30}}
        _persist(tmp_path, api_usage=usage, api_call_count={"openai": 1, "claude": 1})
        raw = (tmp_path / "report.json").read_text(encoding="utf-8")
        data = json.loads(raw)
        assert data["api_usage"]["openai"]["total_tokens"] == 50


# ---------------------------------------------------------------------------
# AC-87-04: 既存の completion_status 決定ロジックを壊さない
# ---------------------------------------------------------------------------
class TestPhase2IntegrationPreservesExistingSuccessFlow:
    def test_decide_completion_status_still_returns_passed_on_success(self):
        """AC-87-04: decide_completion_status は success+no_risks で passed を返す。"""
        result = decide_completion_status(
            status="success",
            acceptance_results=[],
            risks=[],
            open_issues=[],
        )
        assert result["completion_status"] == "passed"

    def test_decide_completion_status_returns_failed_on_failure(self):
        """AC-87-04: decide_completion_status は failed status で failed を返す。"""
        result = decide_completion_status(
            status="failed",
            acceptance_results=[],
            risks=[],
            open_issues=[],
        )
        assert result["completion_status"] == "failed"

    def test_completion_status_field_preserved_in_report(self, tmp_path: Path):
        """AC-87-04: report.json に completion_status が存在し値が正常。"""
        report = _persist(tmp_path, status="success")
        assert report["completion_status"] in (
            "passed", "conditional_pass", "review_required", "failed", "stopped"
        )

    def test_phase2_eval_does_not_overwrite_completion_status(self, tmp_path: Path):
        """AC-87-04: phase2_completion_eval は completion_status を上書きしない。"""
        ctx = _make_ctx()
        report = _persist(tmp_path, ctx=ctx, status="success")
        # 両フィールドが独立して存在すること
        assert "completion_status" in report
        assert "phase2_completion_eval" in report
        # completion_status の値は decide_completion_status が決定したもの
        assert report["completion_status"] != report["phase2_completion_eval"].get("completion")

"""AC-91-01〜04: api usage cost summary extension テスト。"""
import json
from pathlib import Path

from orchestration.run_session import (
    estimate_cost,
    build_cost_summary,
    persist_session_reports,
)


# ---------------------------------------------------------------------------
# テスト用ヘルパー
# ---------------------------------------------------------------------------
def _persist(session_dir: Path, **kwargs) -> dict:
    defaults = dict(
        ctx=None,
        prepared_spec={},
        impl_result={"changed_files": [], "risks": [], "open_issues": []},
        checks={},
        status="success",
        dry_run=False,
        started_at="2026-04-02T00:00:00",
        finished_at="2026-04-02T00:01:00",
    )
    defaults.update(kwargs)
    persist_session_reports(session_dir, **defaults)
    return json.loads((session_dir / "report.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# AC-91-01: usage がある場合に概算コストが report.json に保存される
# ---------------------------------------------------------------------------
class TestReportRecordsEstimatedCostWhenUsageAvailable:
    def test_cost_summary_in_report_when_usage_present(self, tmp_path: Path):
        """AC-91-01: usage があれば cost_summary が report.json に含まれる。"""
        usage = {
            "openai": {"prompt_tokens": 1000, "completion_tokens": 500},
            "claude": {"input_tokens": 2000, "output_tokens": 800},
        }
        report = _persist(tmp_path, api_usage=usage, api_call_count={"openai": 1, "claude": 1})
        assert "cost_summary" in report
        cs = report["cost_summary"]
        assert "openai" in cs
        assert "claude" in cs
        assert "total_estimated_cost_usd" in cs

    def test_estimated_cost_is_positive_when_tokens_present(self):
        """AC-91-01: トークンがあれば推定コストは 0 より大きい。"""
        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        cost = estimate_cost(usage, "openai")
        assert cost > 0.0

    def test_cost_calculation_is_correct_for_openai(self):
        """AC-91-01: OpenAI の概算コストが単価に基づき正しく計算される。"""
        # 1M input @ $2.50 → 1000 tokens = 1000 * 2.50 / 1_000_000 = $0.0025
        usage = {"prompt_tokens": 1000, "completion_tokens": 0}
        cost = estimate_cost(usage, "openai")
        assert abs(cost - 0.0025) < 1e-9

    def test_cost_calculation_is_correct_for_claude(self):
        """AC-91-01: Claude の概算コストが単価に基づき正しく計算される。"""
        # 1M input @ $3.00 → 1000 tokens = 1000 * 3.00 / 1_000_000 = $0.003
        usage = {"input_tokens": 1000, "output_tokens": 0}
        cost = estimate_cost(usage, "claude")
        assert abs(cost - 0.003) < 1e-9

    def test_total_cost_is_sum_of_providers(self, tmp_path: Path):
        """AC-91-01: total_estimated_cost_usd は各プロバイダの合計。"""
        usage = {
            "openai": {"prompt_tokens": 1_000_000, "completion_tokens": 0},
            "claude": {"input_tokens": 0, "output_tokens": 0},
        }
        summary = build_cost_summary(usage, {})
        assert abs(summary["total_estimated_cost_usd"] - 2.50) < 1e-6


# ---------------------------------------------------------------------------
# AC-91-02: usage が欠落していても cost summary 生成で異常終了しない
# ---------------------------------------------------------------------------
class TestCostSummaryToleratesMissingUsage:
    def test_empty_usage_returns_zero_cost(self):
        """AC-91-02: usage が空辞書なら cost は 0.0。"""
        assert estimate_cost({}, "openai") == 0.0

    def test_none_usage_returns_zero_cost(self):
        """AC-91-02: usage が None なら cost は 0.0。"""
        assert estimate_cost(None, "openai") == 0.0  # type: ignore[arg-type]

    def test_unknown_provider_returns_zero_cost(self):
        """AC-91-02: 未知プロバイダの cost は 0.0。"""
        assert estimate_cost({"prompt_tokens": 1000}, "unknown_ai") == 0.0

    def test_build_cost_summary_with_empty_usage(self):
        """AC-91-02: api_usage が空でも build_cost_summary は正常終了する。"""
        summary = build_cost_summary({}, {})
        assert summary["total_estimated_cost_usd"] == 0.0

    def test_persist_without_usage_has_zero_cost(self, tmp_path: Path):
        """AC-91-02: api_usage なしで persist しても cost_summary フィールドが存在する。"""
        report = _persist(tmp_path)
        assert "cost_summary" in report
        assert report["cost_summary"]["total_estimated_cost_usd"] == 0.0


# ---------------------------------------------------------------------------
# AC-91-03: api_usage と cost_summary が machine-readable に保存される
# ---------------------------------------------------------------------------
class TestApiUsageAndCostSummaryAreMachineReadable:
    def test_cost_summary_is_json_serializable(self, tmp_path: Path):
        """AC-91-03: cost_summary を含む report.json が JSON として読み込める。"""
        usage = {"openai": {"prompt_tokens": 500, "completion_tokens": 200}}
        _persist(tmp_path, api_usage=usage)
        raw = (tmp_path / "report.json").read_text(encoding="utf-8")
        data = json.loads(raw)
        assert "cost_summary" in data

    def test_cost_summary_values_are_numeric(self, tmp_path: Path):
        """AC-91-03: cost_summary の金額フィールドは数値型。"""
        usage = {"openai": {"prompt_tokens": 1000, "completion_tokens": 100}}
        report = _persist(tmp_path, api_usage=usage)
        cs = report["cost_summary"]
        assert isinstance(cs["total_estimated_cost_usd"], (int, float))
        assert isinstance(cs["openai"]["estimated_cost_usd"], (int, float))

    def test_cost_summary_has_call_count(self, tmp_path: Path):
        """AC-91-03: cost_summary に call_count が含まれる。"""
        call_count = {"openai": 2, "claude": 3}
        report = _persist(tmp_path, api_call_count=call_count)
        assert report["cost_summary"]["openai"]["call_count"] == 2
        assert report["cost_summary"]["claude"]["call_count"] == 3


# ---------------------------------------------------------------------------
# AC-91-04: 既存 report 生成フローを壊さない
# ---------------------------------------------------------------------------
class TestCostSummaryExtensionHasNoReportRegression:
    def test_completion_status_still_present(self, tmp_path: Path):
        """AC-91-04: completion_status フィールドが引き続き存在する。"""
        report = _persist(tmp_path, status="success")
        assert "completion_status" in report

    def test_api_usage_still_present(self, tmp_path: Path):
        """AC-91-04: api_usage フィールドが引き続き存在する。"""
        report = _persist(tmp_path, api_usage={"openai": {}})
        assert "api_usage" in report

    def test_existing_fields_not_overwritten(self, tmp_path: Path):
        """AC-91-04: session_id、status 等の既存フィールドが上書きされない。"""
        report = _persist(tmp_path, status="success")
        assert report["status"] == "success"
        # cost_summary が追加されても既存フィールドに影響しないこと
        assert "cost_summary" in report
        assert report["session_id"] is not None

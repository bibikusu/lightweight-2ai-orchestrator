"""AC-86-01〜04: API usage and cost recording テスト。"""
import json
from pathlib import Path

from orchestration.run_session import (
    extract_api_usage,
    persist_session_reports,
    SessionContext,
)


# ---------------------------------------------------------------------------
# テスト用ヘルパー
# ---------------------------------------------------------------------------
def _make_ctx(session_id: str = "session-86") -> SessionContext:
    return SessionContext(
        session_id=session_id,
        session_data={
            "session_id": session_id,
            "phase_id": "phase-1",
            "title": "api usage test",
            "goal": "record usage",
            "scope": [],
            "out_of_scope": [],
            "constraints": [],
            "acceptance_ref": "docs/acceptance/session-86.yaml",
        },
        acceptance_data={"raw_yaml": "", "parsed": {}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={},
    )


def _persist(session_dir: Path, **kwargs) -> dict:
    """persist_session_reports を呼び出して report.json を返す。"""
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
# AC-86-01: OpenAI usage が report に記録される
# ---------------------------------------------------------------------------
class TestOpenAIUsageRecordedInReport:
    def test_openai_usage_appears_in_report(self, tmp_path: Path):
        """AC-86-01: api_usage に openai キーがあれば report.json に保存される。"""
        usage = {"openai": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300}}
        report = _persist(tmp_path, api_usage=usage)
        assert report["api_usage"]["openai"]["total_tokens"] == 300

    def test_extract_api_usage_from_openai_response(self):
        """AC-86-01: extract_api_usage は usage キーを正しく抽出する。"""
        response = {
            "result": "some spec",
            "usage": {"prompt_tokens": 50, "completion_tokens": 80},
        }
        extracted = extract_api_usage(response)
        assert extracted["prompt_tokens"] == 50
        assert extracted["completion_tokens"] == 80


# ---------------------------------------------------------------------------
# AC-86-02: Claude usage が report に記録される
# ---------------------------------------------------------------------------
class TestClaudeUsageRecordedInReport:
    def test_claude_usage_appears_in_report(self, tmp_path: Path):
        """AC-86-02: api_usage に claude キーがあれば report.json に保存される。"""
        usage = {"claude": {"input_tokens": 400, "output_tokens": 600}}
        report = _persist(tmp_path, api_usage=usage)
        assert report["api_usage"]["claude"]["input_tokens"] == 400

    def test_extract_api_usage_from_claude_response(self):
        """AC-86-02: Claude レスポンス形式の usage を抽出できる。"""
        response = {
            "implementation": "code here",
            "usage": {"input_tokens": 300, "output_tokens": 500},
        }
        extracted = extract_api_usage(response)
        assert extracted["input_tokens"] == 300
        assert extracted["output_tokens"] == 500


# ---------------------------------------------------------------------------
# AC-86-03: usage データがなくてもセッション実行が壊れない
# ---------------------------------------------------------------------------
class TestMissingUsageDataDoesNotBreakExecution:
    def test_no_usage_key_returns_empty_dict(self):
        """AC-86-03: usage キーがないレスポンスは空辞書を返す。"""
        response = {"result": "some data"}
        assert extract_api_usage(response) == {}

    def test_non_dict_response_returns_empty_dict(self):
        """AC-86-03: レスポンスが dict でない場合も空辞書を返す。"""
        assert extract_api_usage(None) == {}  # type: ignore[arg-type]
        assert extract_api_usage("string") == {}  # type: ignore[arg-type]
        assert extract_api_usage([]) == {}  # type: ignore[arg-type]

    def test_usage_is_non_dict_returns_empty(self):
        """AC-86-03: usage フィールドが dict 以外なら空辞書を返す。"""
        assert extract_api_usage({"usage": None}) == {}
        assert extract_api_usage({"usage": "string"}) == {}
        assert extract_api_usage({"usage": 123}) == {}

    def test_persist_without_usage_does_not_fail(self, tmp_path: Path):
        """AC-86-03: api_usage を渡さなくてもレポートが正常生成される。"""
        report = _persist(tmp_path)  # api_usage なし
        assert "api_usage" in report
        assert report["api_usage"] == {}
        assert report["api_call_count"] == {}


# ---------------------------------------------------------------------------
# AC-86-04: api_call_count と api_usage が machine-readable JSON で保存される
# ---------------------------------------------------------------------------
class TestApiCallCountAndUsageSavedMachineReadably:
    def test_api_call_count_appears_in_report(self, tmp_path: Path):
        """AC-86-04: api_call_count が report.json に含まれる。"""
        call_count = {"openai": 1, "claude": 2}
        report = _persist(tmp_path, api_call_count=call_count)
        assert report["api_call_count"]["openai"] == 1
        assert report["api_call_count"]["claude"] == 2

    def test_report_is_json_serializable(self, tmp_path: Path):
        """AC-86-04: report.json は JSON として読み込める（machine-readable）。"""
        usage = {"openai": {"total_tokens": 999}, "claude": {"input_tokens": 500}}
        call_count = {"openai": 2, "claude": 1}
        _persist(tmp_path, api_usage=usage, api_call_count=call_count)
        raw = (tmp_path / "report.json").read_text(encoding="utf-8")
        data = json.loads(raw)
        assert data["api_usage"]["openai"]["total_tokens"] == 999
        assert data["api_call_count"]["claude"] == 1

    def test_combined_usage_and_count_in_same_report(self, tmp_path: Path):
        """AC-86-04: api_usage と api_call_count が同一 report.json に共存する。"""
        report = _persist(
            tmp_path,
            api_usage={"openai": {"total_tokens": 100}},
            api_call_count={"openai": 1},
        )
        assert "api_usage" in report
        assert "api_call_count" in report

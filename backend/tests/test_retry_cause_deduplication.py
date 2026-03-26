# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import orchestration.run_session as rs
from orchestration.run_session import (
    SessionContext,
    call_chatgpt_for_retry_instruction,
    _compute_retry_cause_fingerprint,
    main,
)


def _ctx() -> SessionContext:
    return SessionContext(
        session_id="session-05a-dedup",
        session_data={"phase_id": "p", "title": "t", "goal": "g"},
        acceptance_data={"raw_yaml": "", "parsed": {}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={"providers": {"openai": {"model": "gpt-test", "timeout_sec": 1}}},
    )


def _sample_check_results() -> dict:
    return {
        "test": {"status": "failed", "command": "pytest", "returncode": 1, "stderr": "AssertionError", "stdout": ""},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": False,
    }


def _success_check_results() -> dict:
    return {
        "test": {"status": "passed", "command": "pytest", "returncode": 0, "stderr": "", "stdout": ""},
        "lint": {"status": "skipped"},
        "typecheck": {"status": "skipped"},
        "build": {"status": "skipped"},
        "success": True,
    }


def _session_data_for_main(session_id: str) -> dict:
    return {
        "session_id": session_id,
        "phase_id": "p",
        "title": "t",
        "goal": "g",
        "scope": [],
        "out_of_scope": [],
        "constraints": [],
        "acceptance_ref": "acceptance/session-01.yaml",
    }


def _main_ctx(session_id: str, *, max_retries: int = 5) -> SessionContext:
    return SessionContext(
        session_id=session_id,
        session_data=_session_data_for_main(session_id),
        acceptance_data={"raw_yaml": "", "parsed": {"acceptance": []}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={
            "limits": {"max_retries": max_retries, "max_changed_files": 5},
            "providers": {"openai": {"model": "gpt-test", "timeout_sec": 1}},
        },
    )


def _patch_main_happy_path(
    monkeypatch,
    tmp_path,
    session_id: str,
    *,
    max_retries: int = 5,
    checks_factory=_sample_check_results,
):
    """main を進める（Git / 実 API / 実チェックは差し替え）。checks_factory で結果を切り替え。"""
    ctx = _main_ctx(session_id, max_retries=max_retries)
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(rs, "load_session_context", lambda _sid: ctx)
    monkeypatch.setattr(rs, "enforce_git_sandbox_branch", lambda _sid: None)
    monkeypatch.setattr(
        rs,
        "call_chatgpt_for_prepared_spec",
        lambda _c: {"objective": "obj", "forbidden_changes": []},
    )
    monkeypatch.setattr(
        rs,
        "call_claude_for_implementation",
        lambda _ps, _c, _ri=None: {
            "changed_files": ["src/x.py"],
            "implementation_summary": [],
            "risks": [],
            "open_issues": [],
            "proposed_patch": "",
        },
    )
    monkeypatch.setattr(
        rs,
        "run_local_checks",
        lambda _c, skip_build=False: checks_factory(),
    )
    return ctx


def _read_retry_count(session_dir: Path) -> int:
    p = session_dir / "responses" / "retry_state.json"
    if not p.is_file():
        return 0
    try:
        return int(json.loads(p.read_text(encoding="utf-8")).get("retry_count", 0))
    except (TypeError, ValueError, json.JSONDecodeError):
        return 0


def _prime_retry_state(session_dir: Path, n: int) -> None:
    rdir = session_dir / "responses"
    rdir.mkdir(parents=True, exist_ok=True)
    (rdir / "retry_state.json").write_text(
        json.dumps({"retry_count": n}, ensure_ascii=False),
        encoding="utf-8",
    )


def _prime_same_cause_file(session_dir: Path, fingerprint: str) -> None:
    rdir = session_dir / "responses"
    rdir.mkdir(parents=True, exist_ok=True)
    (rdir / "retry_instruction.json").write_text(
        json.dumps({"cause_fingerprint": fingerprint}, ensure_ascii=False),
        encoding="utf-8",
    )


def test_retry_same_cause_is_not_repeated(monkeypatch, tmp_path):
    """AC-04: 同一 cause_fingerprint では API を呼ばず抑止する"""
    monkeypatch.setattr(rs, "ARTIFACTS_DIR", tmp_path / "artifacts")
    ctx = _ctx()
    checks = _sample_check_results()
    fp = _compute_retry_cause_fingerprint(checks)

    resp_dir = tmp_path / "artifacts" / ctx.session_id / "responses"
    resp_dir.mkdir(parents=True, exist_ok=True)
    prev_path = resp_dir / "retry_instruction.json"
    prev_path.write_text(
        json.dumps({"cause_fingerprint": fp, "session_id": ctx.session_id}, ensure_ascii=False),
        encoding="utf-8",
    )

    prepared_spec: dict = {"objective": "o"}
    impl_result: dict = {"changed_files": ["a.py"]}

    def _boom(*_a, **_k):
        raise AssertionError("OpenAI client must not be constructed for same-cause dedup")

    with patch("orchestration.providers.openai_client.OpenAIClientWrapper", side_effect=_boom):
        out = call_chatgpt_for_retry_instruction(ctx, prepared_spec, impl_result, checks)

    assert out.get("retry_skipped_same_cause") is True
    assert out.get("cause_fingerprint") == fp
    assert out.get("failure_type") == "test_failure"
    assert isinstance(out.get("fix_instructions"), list)
    assert len(out["fix_instructions"]) >= 1


def test_retry_same_cause_stops_in_main(monkeypatch, tmp_path, capsys):
    """AC-01: main で同一原因時は max_retries 回回さず打ち切る"""
    sid = "session-05b-stop"
    _patch_main_happy_path(monkeypatch, tmp_path, sid, max_retries=5)
    fp = _compute_retry_cause_fingerprint(_sample_check_results())
    _prime_same_cause_file(tmp_path / "artifacts" / sid, fp)

    calls: list[int] = []
    orig = rs.call_chatgpt_for_retry_instruction

    def _wrap(*a, **k):
        calls.append(1)
        return orig(*a, **k)

    monkeypatch.setattr(rs, "call_chatgpt_for_retry_instruction", _wrap)

    def _boom(*_a, **_k):
        raise AssertionError("OpenAI は同一原因では呼ばれない")

    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    with patch("orchestration.providers.openai_client.OpenAIClientWrapper", side_effect=_boom):
        code = main()

    assert code == 1
    assert len(calls) == 1
    out = capsys.readouterr().out
    assert "リトライ試行を停止" in out
    assert _read_retry_count(tmp_path / "artifacts" / sid) == 0


def test_retry_same_cause_does_not_reinvoke_model(monkeypatch, tmp_path):
    """AC-02: 同一原因経路で OpenAI クライアントを構築しない（main 経由）"""
    sid = "session-05b-nomodel"
    _patch_main_happy_path(monkeypatch, tmp_path, sid, max_retries=3)
    fp = _compute_retry_cause_fingerprint(_sample_check_results())
    _prime_same_cause_file(tmp_path / "artifacts" / sid, fp)

    def _boom(*_a, **_k):
        raise AssertionError("OpenAIClientWrapper は同一原因では不要")

    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    with patch("orchestration.providers.openai_client.OpenAIClientWrapper", side_effect=_boom):
        assert main() == 1


def test_retry_instruction_is_still_saved_consistently(monkeypatch, tmp_path):
    """AC-03: 同一原因でも retry_instruction.json とレポート Markdown が整合する"""
    sid = "session-05b-save"
    _patch_main_happy_path(monkeypatch, tmp_path, sid, max_retries=2)
    fp = _compute_retry_cause_fingerprint(_sample_check_results())
    _prime_same_cause_file(tmp_path / "artifacts" / sid, fp)

    def _boom(*_a, **_k):
        raise AssertionError("API 不要")

    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    with patch("orchestration.providers.openai_client.OpenAIClientWrapper", side_effect=_boom):
        assert main() == 1

    session_dir = tmp_path / "artifacts" / sid
    rj = json.loads((session_dir / "responses" / "retry_instruction.json").read_text(encoding="utf-8"))
    md = (session_dir / "reports" / "session_report.md").read_text(encoding="utf-8")

    assert rj.get("retry_skipped_same_cause") is True
    assert rj.get("cause_fingerprint") == fp
    assert "## Retry Instruction" in md
    ft = rj.get("failure_type")
    assert ft is not None and str(ft) in md
    assert _read_retry_count(session_dir) == 0


def test_existing_retry_flow_not_broken(monkeypatch, tmp_path):
    """AC-04: リトライ API→ループ後の成果物とレポート必須要素が維持される（終了コード1）"""
    sid = "session-05b-normal"
    _patch_main_happy_path(monkeypatch, tmp_path, sid, max_retries=1)

    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    with patch("orchestration.providers.openai_client.OpenAIClientWrapper") as mock_inst:
        mock_inst.return_value.request_retry_instruction.return_value = {}
        assert main() == 1

    session_dir = tmp_path / "artifacts" / sid
    rj = json.loads((session_dir / "responses" / "retry_instruction.json").read_text(encoding="utf-8"))
    # 初回 API 後にループで Claude+checks が走り、同一原因なら同一原因抑止になり得る
    assert rj.get("failure_type") == "test_failure"
    md = (session_dir / "reports" / "session_report.md").read_text(encoding="utf-8")
    assert "## Retry Instruction" in md
    assert rj.get("retry_count") == 1
    assert rj.get("max_retries") == 1
    assert _read_retry_count(session_dir) == 1
    assert rj.get("retry_skipped_same_cause") is True
    rep = json.loads((session_dir / "reports" / "session_report.json").read_text(encoding="utf-8"))
    assert rep.get("retry_stopped_same_cause") is True


def test_retry_exhausted_skips_openai(monkeypatch, tmp_path):
    """retry_count >= max_retries では OpenAI を呼ばず retry_exhausted を保存する"""
    sid = "session-retry-exhausted"
    _patch_main_happy_path(monkeypatch, tmp_path, sid, max_retries=2)
    _prime_retry_state(tmp_path / "artifacts" / sid, 2)

    def _boom(*_a, **_k):
        raise AssertionError("上限到達後は OpenAI 不要")

    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    with patch("orchestration.providers.openai_client.OpenAIClientWrapper", side_effect=_boom):
        assert main() == 1

    session_dir = tmp_path / "artifacts" / sid
    rj = json.loads((session_dir / "responses" / "retry_instruction.json").read_text(encoding="utf-8"))
    assert rj.get("retry_exhausted") is True
    assert rj.get("retry_count") == 2
    assert rj.get("max_retries") == 2
    assert _read_retry_count(session_dir) == 2


def test_retry_count_resets_on_success(monkeypatch, tmp_path):
    """チェック成功時に retry_count を 0 に戻す"""
    sid = "session-retry-reset-ok"
    _patch_main_happy_path(
        monkeypatch,
        tmp_path,
        sid,
        max_retries=3,
        checks_factory=_success_check_results,
    )
    _prime_retry_state(tmp_path / "artifacts" / sid, 2)

    monkeypatch.setattr(sys, "argv", ["run_session.py", "--session-id", sid])
    assert main() == 0
    assert _read_retry_count(tmp_path / "artifacts" / sid) == 0

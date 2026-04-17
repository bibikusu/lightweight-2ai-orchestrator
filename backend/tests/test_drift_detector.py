"""Drift detector (session / acceptance) fail-fast validation tests."""

from __future__ import annotations

import json
from pathlib import Path

from orchestration.drift_detector import EXPECTED_REVIEW_POINTS, run_drift_check

REPO_ROOT = Path(__file__).resolve().parents[2]

_MINIMAL_ACCEPTANCE_YAML = """session_id: tmp-session
acceptance:
  - id: AC-01
    description: desc
    test_name: test_one
"""


def _minimal_session(overrides: dict | None = None) -> dict:
    base = {
        "session_id": "tmp-session",
        "phase_id": "phase1",
        "title": "title",
        "goal": "goal",
        "scope": ["one"],
        "out_of_scope": ["a"],
        "constraints": [],
        "acceptance_ref": "docs/acceptance/tmp.yaml",
        "allowed_changes": ["src/a.py"],
        "allowed_changes_detail": ["src/a.py: change allowed"],
        "forbidden_changes": [],
        "review_points": list(EXPECTED_REVIEW_POINTS),
        "completion_criteria": [
            {"id": "CC-1", "type": "artifact", "condition": "non-empty"},
        ],
    }
    if overrides:
        base.update(overrides)
    return base


def _write_session_acceptance(tmp_path: Path, session: dict, acceptance_yaml: str) -> tuple[str, str]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    sj = tmp_path / "session.json"
    ay = tmp_path / "acceptance.yaml"
    sj.write_text(json.dumps(session, ensure_ascii=False), encoding="utf-8")
    ay.write_text(acceptance_yaml, encoding="utf-8")
    return str(sj.resolve()), str(ay.resolve())


def test_required_keys_missing_reported_all_at_once(tmp_path: Path) -> None:
    """欠落キーが複数あるとき、ソートされた全キーが violations に含まれる。"""
    session = _minimal_session()
    del session["goal"]
    del session["constraints"]
    del session["allowed_changes_detail"]
    sp, ap = _write_session_acceptance(tmp_path, session, _MINIMAL_ACCEPTANCE_YAML)
    result = run_drift_check(sp, ap)
    assert result["ok"] is False
    codes_paths = {(v["code"], v["path"]) for v in result["violations"]}
    assert ("SESSION_REQUIRED_KEY", "session.allowed_changes_detail") in codes_paths
    assert ("SESSION_REQUIRED_KEY", "session.constraints") in codes_paths
    assert ("SESSION_REQUIRED_KEY", "session.goal") in codes_paths
    missing_msgs = [v for v in result["violations"] if v["code"] == "SESSION_REQUIRED_KEY"]
    keys_reported = sorted(m["path"].removeprefix("session.") for m in missing_msgs)
    assert keys_reported == sorted(["allowed_changes_detail", "constraints", "goal"])


def test_review_points_must_match_fixed_four_axes(tmp_path: Path) -> None:
    """review_points が固定4軸と異なる場合は fail。誤表現「検証十分性」も検出する。"""
    bad = list(EXPECTED_REVIEW_POINTS)
    bad[0] = "wrong axis"
    session = _minimal_session({"review_points": bad})
    sp, ap = _write_session_acceptance(tmp_path, session, _MINIMAL_ACCEPTANCE_YAML)
    r1 = run_drift_check(sp, ap)
    assert r1["ok"] is False
    assert any(v["code"] == "REVIEW_POINTS_MISMATCH" for v in r1["violations"])

    confused = list(EXPECTED_REVIEW_POINTS)
    confused[3] = "検証十分性"
    session2 = _minimal_session({"review_points": confused})
    sp2, ap2 = _write_session_acceptance(tmp_path / "sub", session2, _MINIMAL_ACCEPTANCE_YAML)
    r2 = run_drift_check(sp2, ap2)
    assert r2["ok"] is False
    assert any(v["code"] == "REVIEW_POINTS_MISMATCH" for v in r2["violations"])


def test_allowed_changes_detail_is_required_and_mapped(tmp_path: Path) -> None:
    """detail 欠落・コロンなし・allowed_changes 未対応で fail。"""
    s1 = _minimal_session()
    del s1["allowed_changes_detail"]
    p1, a1 = _write_session_acceptance(tmp_path / "a", s1, _MINIMAL_ACCEPTANCE_YAML)
    r1 = run_drift_check(p1, a1)
    assert r1["ok"] is False
    assert any(v["code"] == "SESSION_REQUIRED_KEY" for v in r1["violations"])

    s2 = _minimal_session({"allowed_changes_detail": ["no-colon-here"]})
    p2, a2 = _write_session_acceptance(tmp_path / "b", s2, _MINIMAL_ACCEPTANCE_YAML)
    r2 = run_drift_check(p2, a2)
    assert r2["ok"] is False
    assert any(v["code"] == "ALLOWED_CHANGES_DETAIL_FORMAT" for v in r2["violations"])

    s3 = _minimal_session(
        {
            "allowed_changes": ["src/a.py", "src/b.py"],
            "allowed_changes_detail": ["src/a.py: only one mapped"],
        }
    )
    p3, a3 = _write_session_acceptance(tmp_path / "c", s3, _MINIMAL_ACCEPTANCE_YAML)
    r3 = run_drift_check(p3, a3)
    assert r3["ok"] is False
    assert any(v["code"] == "ALLOWED_CHANGES_UNMAPPED" for v in r3["violations"])
    assert r3["failure_type"] == "scope_violation"


def test_acceptance_items_require_test_name_for_code_session(tmp_path: Path) -> None:
    """acceptance 項目に test_name がない場合は fail。"""
    session = _minimal_session()
    bad_yaml = """session_id: tmp-session
acceptance:
  - id: AC-01
    description: desc
"""
    sp, ap = _write_session_acceptance(tmp_path, session, bad_yaml)
    result = run_drift_check(sp, ap)
    assert result["ok"] is False
    assert any(v["code"] == "ACCEPTANCE_FIELD_MISSING" for v in result["violations"])


def test_valid_session_and_acceptance_pass_drift_check() -> None:
    """リポジトリ正本の session-123 定義と acceptance が drift を通過する。"""
    session_path = str(REPO_ROOT / "docs/sessions/session-123.json")
    acceptance_path = str(REPO_ROOT / "docs/acceptance/session-123.yaml")
    result = run_drift_check(session_path, acceptance_path)
    assert result["ok"] is True
    assert result["failure_type"] is None
    assert result["violations"] == []

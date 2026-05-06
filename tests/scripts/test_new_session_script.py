from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "new_session.sh"

REQUIRED_KEYS = [
    "session_id",
    "phase_id",
    "title",
    "goal",
    "scope",
    "out_of_scope",
    "constraints",
    "acceptance_ref",
    "allowed_changes_detail",
    "forbidden_changes",
    "completion_criteria",
    "acceptance_criteria",
    "review_points",
    "failure_type",
]


def _setup_dirs(base: Path) -> None:
    (base / "docs" / "sessions").mkdir(parents=True, exist_ok=True)
    (base / "docs" / "acceptance").mkdir(parents=True, exist_ok=True)


def _run(session_id: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    _setup_dirs(cwd)
    return subprocess.run(
        [str(SCRIPT), session_id],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def test_new_session_script_creates_json_and_yaml(tmp_path: Path) -> None:
    sid = "session-test-9999"
    result = _run(sid, tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert (tmp_path / f"docs/sessions/{sid}.json").exists()
    assert (tmp_path / f"docs/acceptance/{sid}.yaml").exists()


def test_new_session_script_rejects_existing_session_id(tmp_path: Path) -> None:
    sid = "session-existing-001"
    _setup_dirs(tmp_path)
    (tmp_path / f"docs/sessions/{sid}.json").write_text("{}", encoding="utf-8")
    result = _run(sid, tmp_path)
    assert result.returncode != 0, "expected non-zero exit for existing session_id"
    assert not (tmp_path / f"docs/acceptance/{sid}.yaml").exists(), \
        "YAML must not be created when JSON already exists"


def test_new_session_script_outputs_required_session_keys(tmp_path: Path) -> None:
    sid = "session-test-keys-001"
    result = _run(sid, tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(
        (tmp_path / f"docs/sessions/{sid}.json").read_text(encoding="utf-8")
    )
    missing = [k for k in REQUIRED_KEYS if k not in data]
    assert not missing, f"missing keys in generated JSON: {missing}"


def test_new_session_script_acceptance_ref_matches_yaml_path(tmp_path: Path) -> None:
    sid = "session-test-ref-001"
    result = _run(sid, tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(
        (tmp_path / f"docs/sessions/{sid}.json").read_text(encoding="utf-8")
    )
    expected_ref = f"docs/acceptance/{sid}.yaml"
    assert data["acceptance_ref"] == expected_ref, \
        f"acceptance_ref mismatch: {data['acceptance_ref']} != {expected_ref}"
    assert (tmp_path / expected_ref).exists(), \
        f"YAML not found at: {tmp_path / expected_ref}"

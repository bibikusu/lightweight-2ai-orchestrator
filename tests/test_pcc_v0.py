"""PCC v0 受入テスト AC-172DI-01〜18。"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from glob import glob
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Set

_REPO_ROOT = Path(__file__).parent.parent
_REGISTRY_PATH = _REPO_ROOT / "docs" / "config" / "project_registry.json"
_STATIC_DIR = _REPO_ROOT / "backend" / "pcc" / "static"
_SCRIPTS_PCC = _REPO_ROOT / "scripts" / "pcc"

_GIT_STATUS_VALID: Set[str] = {"clean", "dirty", "unmanaged", "detached", "unknown"}

_PROTECTED_BASELINES: Dict[str, str] = {
    "orchestration/run_session.py": "4de6affffb9297cdf02b3136e8f55172",
    "orchestration/selector/core.py": "9b19e2cbe3487d3090096c5343c88611",
    "orchestration/selector/loader.py": "959db533bf086f83765d8f6f16fbbe7b",
    "orchestration/selector/writer.py": "aaf7e28e0e9c52d12d30c8d3349cf982",
}

_ALLOWED_CHANGES = {
    "backend/pcc/__init__.py",
    "backend/pcc/pcc_v0.py",
    "backend/pcc/static/index.html",
    "backend/pcc/static/style.css",
    "backend/pcc/static/app.js",
    "backend/pcc/server.py",
    "scripts/pcc",
    "tests/test_pcc_v0.py",
    "docs/sessions/session-172d-impl.json",
    "docs/acceptance/session-172d-impl.yaml",
}


def _md5(path: str) -> str:
    return hashlib.md5(open(path, "rb").read()).hexdigest()


# ─────────────────────────────────────────────
# AC-172DI-01: import 可能性
# ─────────────────────────────────────────────


def test_pcc_v0_module_importable() -> None:
    """backend.pcc から aggregate_projects が取得できる。"""
    from backend.pcc import aggregate_projects  # noqa: F401

    assert callable(aggregate_projects)


# ─────────────────────────────────────────────
# AC-172DI-02: 戻り値件数 = registry 件数
# ─────────────────────────────────────────────


def test_aggregate_returns_one_card_per_registered_project() -> None:
    """戻り値の長さが project_registry.json の件数と一致する。"""
    from backend.pcc import aggregate_projects

    registry: Dict = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    expected_count: int = len(registry["projects"])

    result: List[Dict] = aggregate_projects()
    assert len(result) == expected_count


# ─────────────────────────────────────────────
# AC-172DI-03: project_registry.json を正本参照
# ─────────────────────────────────────────────


def test_aggregate_uses_project_registry_as_source_of_truth(tmp_path: Path) -> None:
    """monkeypatch でレジストリを切替え、戻り値が切替先と一致する。"""
    from backend.pcc.pcc_v0 import aggregate_projects

    fake_registry: Dict = {
        "projects": [
            {"project_id": "FAKE_001", "repo_path": str(tmp_path / "fake1")},
            {"project_id": "FAKE_002", "repo_path": str(tmp_path / "fake2")},
        ]
    }
    registry_file = tmp_path / "project_registry.json"
    registry_file.write_text(json.dumps(fake_registry), encoding="utf-8")

    result = aggregate_projects(
        registry_path=registry_file,
        projects_dir=tmp_path / "projects",
        queue_state_path=tmp_path / "nonexistent_queue.json",
    )

    assert [r["project_id"] for r in result] == ["FAKE_001", "FAKE_002"]


# ─────────────────────────────────────────────
# AC-172DI-04: state.json を読み込む
# ─────────────────────────────────────────────


def test_aggregate_reads_state_json_for_each_project(tmp_path: Path) -> None:
    """state.json が存在すれば latest_session / failure_type 等に反映される。"""
    from backend.pcc.pcc_v0 import aggregate_projects

    project_id = "TEST_STATE"
    registry: Dict = {
        "projects": [{"project_id": project_id, "repo_path": str(tmp_path / project_id)}]
    }
    registry_file = tmp_path / "project_registry.json"
    registry_file.write_text(json.dumps(registry), encoding="utf-8")

    projects_dir = tmp_path / "projects"
    state_dir = projects_dir / project_id
    state_dir.mkdir(parents=True)
    state: Dict = {
        "last_session": "session-test-01",
        "failure_type": "TIMEOUT",
        "human_gate": "required",
        "artifacts": "report.md",
    }
    (state_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    result = aggregate_projects(
        registry_path=registry_file,
        projects_dir=projects_dir,
        queue_state_path=tmp_path / "nonexistent_queue.json",
    )

    assert len(result) == 1
    card = result[0]
    assert card["latest_session"] == "session-test-01"
    assert card["failure_type"] == "TIMEOUT"
    assert card["human_gate"] == "required"
    assert card["artifacts"] == "report.md"


# ─────────────────────────────────────────────
# AC-172DI-05: git 未管理プロジェクトを gracefully 処理
# ─────────────────────────────────────────────


def test_aggregate_handles_missing_git_directory_gracefully(tmp_path: Path) -> None:
    """.git が存在しないプロジェクトに git_status='unmanaged' を付与する。"""
    from backend.pcc.pcc_v0 import aggregate_projects

    project_id = "NO_GIT"
    proj_path = tmp_path / project_id
    proj_path.mkdir()

    registry: Dict = {
        "projects": [{"project_id": project_id, "repo_path": str(proj_path)}]
    }
    registry_file = tmp_path / "project_registry.json"
    registry_file.write_text(json.dumps(registry), encoding="utf-8")

    result = aggregate_projects(
        registry_path=registry_file,
        projects_dir=tmp_path / "projects",
        queue_state_path=tmp_path / "nonexistent_queue.json",
    )

    assert result[0]["git_status"] == "unmanaged"


# ─────────────────────────────────────────────
# AC-172DI-06: queue_state.json 不在時は not_configured
# ─────────────────────────────────────────────


def test_aggregate_handles_missing_queue_state_gracefully(tmp_path: Path) -> None:
    """queue_state.json が存在しない場合 queue_summary='not_configured' を付与する。"""
    from backend.pcc.pcc_v0 import aggregate_projects

    project_id = "TEST_QUEUE"
    registry: Dict = {
        "projects": [{"project_id": project_id, "repo_path": str(tmp_path / project_id)}]
    }
    registry_file = tmp_path / "project_registry.json"
    registry_file.write_text(json.dumps(registry), encoding="utf-8")

    result = aggregate_projects(
        registry_path=registry_file,
        projects_dir=tmp_path / "projects",
        queue_state_path=tmp_path / "nonexistent_queue.json",
    )

    assert result[0]["queue_summary"] == "not_configured"


# ─────────────────────────────────────────────
# AC-172DI-07: 書込なし確認（md5 不変）
# ─────────────────────────────────────────────


def test_aggregate_does_not_write_to_any_source_file() -> None:
    """aggregate_projects 実行前後で source ファイルの md5 が変化しない。"""
    from backend.pcc import aggregate_projects

    targets: Dict[str, str] = {}
    reg = str(_REGISTRY_PATH)
    if os.path.exists(reg):
        targets[reg] = _md5(reg)
    for f in glob(str(_REPO_ROOT / "docs" / "projects" / "**" / "state.json"), recursive=True):
        targets[f] = _md5(f)

    aggregate_projects()

    for path, before in targets.items():
        assert _md5(path) == before, f"write detected: {path}"


# ─────────────────────────────────────────────
# AC-172DI-08: HTML のカード数 = registry 件数
# ─────────────────────────────────────────────


class _CardCountParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.card_count: int = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "article":
            attrs_dict = dict(attrs)
            if attrs_dict.get("class") == "project-card":
                self.card_count += 1


def test_html_renders_card_per_registered_project() -> None:
    """index.html の <article class='project-card'> 数が registry 件数と一致する。"""
    html = (_STATIC_DIR / "index.html").read_text(encoding="utf-8")
    parser = _CardCountParser()
    parser.feed(html)

    registry: Dict = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    assert parser.card_count == len(registry["projects"])


# ─────────────────────────────────────────────
# AC-172DI-09: 10 data-field + manual-refresh ボタン
# ─────────────────────────────────────────────


class _FieldParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.data_fields: Set[str] = set()
        self.manual_refresh_count: int = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attrs_dict = dict(attrs)
        if "data-field" in attrs_dict:
            self.data_fields.add(attrs_dict["data-field"])
        if tag == "button" and attrs_dict.get("id") == "manual-refresh":
            self.manual_refresh_count += 1


def test_html_contains_all_11_card_fields() -> None:
    """10 data-field の種類集合が仕様と一致し、manual-refresh ボタンが 1 個存在する。"""
    html = (_STATIC_DIR / "index.html").read_text(encoding="utf-8")
    parser = _FieldParser()
    parser.feed(html)

    required_fields = {
        "project_id",
        "repo_path",
        "branch",
        "HEAD",
        "git_status",
        "latest_session",
        "four_gate",
        "failure_type",
        "human_gate",
        "artifacts",
    }
    assert parser.data_fields == required_fields, (
        f"data-field mismatch: got {parser.data_fields}"
    )
    assert parser.manual_refresh_count == 1, (
        f"manual-refresh button count: {parser.manual_refresh_count}"
    )


# ─────────────────────────────────────────────
# AC-172DI-10: 実行制御要素が存在しない
# ─────────────────────────────────────────────


def test_html_has_no_execution_control_elements() -> None:
    """index.html と app.js に実行制御要素（form/submit/execute/approve/retry）が存在しない。"""
    html = (_STATIC_DIR / "index.html").read_text(encoding="utf-8")
    app_js = (_STATIC_DIR / "app.js").read_text(encoding="utf-8")

    for content, label in [(html, "index.html"), (app_js, "app.js")]:
        assert "<form" not in content, f"<form> found in {label}"
        assert 'type="submit"' not in content, f'type="submit" found in {label}'
        assert "type='submit'" not in content, f"type='submit' found in {label}"

    # onclick による実行制御ボタンが存在しない
    import re

    control_pattern = re.compile(
        r'onclick\s*=\s*["\']?\s*(execute|approve|retry)\b', re.IGNORECASE
    )
    assert not control_pattern.search(html), "execute/approve/retry onclick found in index.html"
    assert not control_pattern.search(app_js), "execute/approve/retry onclick found in app.js"


# ─────────────────────────────────────────────
# AC-172DI-11: scripts/pcc start が定義・実行可能
# ─────────────────────────────────────────────


def test_pcc_start_command_exists_and_executable() -> None:
    """scripts/pcc が実行可能で start サブコマンドが定義されている。"""
    assert _SCRIPTS_PCC.exists(), "scripts/pcc not found"
    assert os.access(str(_SCRIPTS_PCC), os.X_OK), "scripts/pcc is not executable"

    result = subprocess.run(["bash", "-n", str(_SCRIPTS_PCC)], capture_output=True)
    assert result.returncode == 0, "bash -n scripts/pcc failed"

    content = _SCRIPTS_PCC.read_text(encoding="utf-8")
    import re
    assert re.search(r"\bstart\)", content), "start) not found in scripts/pcc"


# ─────────────────────────────────────────────
# AC-172DI-12: scripts/pcc stop が定義・実行可能
# ─────────────────────────────────────────────


def test_pcc_stop_command_exists_and_executable() -> None:
    """scripts/pcc に stop サブコマンドが定義されている。"""
    content = _SCRIPTS_PCC.read_text(encoding="utf-8")
    import re
    assert re.search(r"\bstop\)", content), "stop) not found in scripts/pcc"


# ─────────────────────────────────────────────
# AC-172DI-13: scripts/pcc status が定義・実行可能
# ─────────────────────────────────────────────


def test_pcc_status_command_exists_and_executable() -> None:
    """scripts/pcc に status サブコマンドが定義されている。"""
    content = _SCRIPTS_PCC.read_text(encoding="utf-8")
    import re
    assert re.search(r"\bstatus\)", content), "status) not found in scripts/pcc"


# ─────────────────────────────────────────────
# AC-172DI-14: protected_baselines md5 不変
# ─────────────────────────────────────────────


def test_protected_baselines_md5_unchanged() -> None:
    """protected_baselines 4ファイルの md5 が基準値と一致する。"""
    for rel_path, expected_md5 in _PROTECTED_BASELINES.items():
        full_path = str(_REPO_ROOT / rel_path)
        assert os.path.exists(full_path), f"baseline file missing: {rel_path}"
        actual = _md5(full_path)
        assert actual == expected_md5, f"{rel_path}: expected {expected_md5}, got {actual}"


# ─────────────────────────────────────────────
# AC-172DI-15: aggregation 中に state.json への書込なし
# ─────────────────────────────────────────────


def test_no_writes_to_state_json_during_aggregation() -> None:
    """aggregate_projects 実行前後で docs/projects/**/state.json の md5 が変化しない。"""
    from backend.pcc import aggregate_projects

    state_files = glob(str(_REPO_ROOT / "docs" / "projects" / "**" / "state.json"), recursive=True)
    before = {f: _md5(f) for f in state_files}

    aggregate_projects()

    for path, md5_before in before.items():
        assert _md5(path) == md5_before, f"state.json was written: {path}"


# ─────────────────────────────────────────────
# AC-172DI-16: aggregation 中に project_registry.json への書込なし
# ─────────────────────────────────────────────


def test_no_writes_to_project_registry_during_aggregation() -> None:
    """aggregate_projects 実行前後で project_registry.json の md5 が変化しない。"""
    from backend.pcc import aggregate_projects

    before = _md5(str(_REGISTRY_PATH))
    aggregate_projects()
    assert _md5(str(_REGISTRY_PATH)) == before


# ─────────────────────────────────────────────
# AC-172DI-17: diff scope が allowed_changes 以内（commit/push 後に PASS）
# ─────────────────────────────────────────────


def test_session_172d_impl_diff_scope_only_allowed_files() -> None:
    """git diff --name-only origin/main の変更ファイルが allowed_changes 以内に収まる。
    pre-commit 状態では FAIL してよい（exception_keywords に記載）。
    """
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main"],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )
    changed = {f for f in result.stdout.strip().split("\n") if f}
    violations = changed - _ALLOWED_CHANGES
    assert not violations, f"scope violation: {violations}"


# ─────────────────────────────────────────────
# AC-172DI-18: git_status が 5値 enum のいずれか
# ─────────────────────────────────────────────


def test_aggregate_git_status_returns_one_of_five_canonical_values() -> None:
    """aggregate_projects() の各カードの git_status が 5 値 enum に含まれる。"""
    from backend.pcc import aggregate_projects

    result = aggregate_projects()
    for card in result:
        assert card["git_status"] in _GIT_STATUS_VALID, (
            f"{card['project_id']}: invalid git_status '{card['git_status']}'"
        )

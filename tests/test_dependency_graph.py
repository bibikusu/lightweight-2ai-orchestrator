"""Dependency graph テスト scaffold (session-194-pre)。

全テストは @pytest.mark.skip 付き。
session-194 で orchestration.dependency_graph.graph.build_dependency_graph を実装後に有効化する。
"""

import json
import pathlib
import tempfile

def test_build_valid_minimal_graph() -> None:
    from orchestration.dependency_graph.graph import build_dependency_graph  # noqa: F401

    _fixture = pathlib.Path("tests/fixtures/dependency_graph/dep_graph_valid_minimal.json")
    # AC-194-01 準拠: 単一 session の最小 valid graph を build し success=True を返す
    data = json.loads(_fixture.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = pathlib.Path(tmp)
        sessions_dir = repo_root / "docs" / "sessions"
        sessions_dir.mkdir(parents=True)
        for session in data["sessions"]:
            sid = session["session_id"]
            (sessions_dir / f"{sid}.json").write_text(
                json.dumps(session), encoding="utf-8"
            )
        result = build_dependency_graph(data["input"]["session_ids"], repo_root)
        expected = data["expected"]
        assert result.success == expected["success"]
        assert result.nodes == expected["nodes"]
        assert result.edges == expected["edges"]
        assert result.metadata == expected["metadata"]
        assert result.errors == expected["errors"]
        artifact = repo_root / "artifacts" / "session-190" / "dependency_graph" / "graph.json"
        assert artifact.exists()
        loaded = json.loads(artifact.read_text(encoding="utf-8"))
        assert loaded["success"] is True


def test_build_valid_chained_graph() -> None:
    from orchestration.dependency_graph.graph import build_dependency_graph  # noqa: F401

    _fixture = pathlib.Path("tests/fixtures/dependency_graph/dep_graph_valid_chained.json")
    # AC-194-02 準拠: depends_on 連鎖 (A→B→C) build success および session_id 昇順 ordering を確認
    data = json.loads(_fixture.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = pathlib.Path(tmp)
        sessions_dir = repo_root / "docs" / "sessions"
        sessions_dir.mkdir(parents=True)
        for session in data["sessions"]:
            sid = session["session_id"]
            (sessions_dir / f"{sid}.json").write_text(
                json.dumps(session), encoding="utf-8"
            )
        result = build_dependency_graph(data["input"]["session_ids"], repo_root)
        expected = data["expected"]
        assert result.success == expected["success"]
        assert result.edges == expected["edges"]
        assert result.metadata == expected["metadata"]
        assert result.errors == expected["errors"]
        assert [n["id"] for n in result.nodes] == expected["ordering"]


def test_cycle_returns_failure_result() -> None:
    from orchestration.dependency_graph.graph import build_dependency_graph  # noqa: F401

    _fixture = pathlib.Path("tests/fixtures/dependency_graph/dep_graph_invalid_cycle.json")
    # AC-194-08 準拠: cycle (A→B→A) 時 result.success=False / failure_type='spec_missing'
    data = json.loads(_fixture.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = pathlib.Path(tmp)
        sessions_dir = repo_root / "docs" / "sessions"
        sessions_dir.mkdir(parents=True)
        for session in data["sessions"]:
            sid = session["session_id"]
            (sessions_dir / f"{sid}.json").write_text(
                json.dumps(session), encoding="utf-8"
            )
        result = build_dependency_graph(data["input"]["session_ids"], repo_root)
        expected = data["expected"]
        assert result.success == expected["success"]
        assert result.failure_type == expected["failure_type"]
        assert len(result.errors) > 0
        assert result.errors == expected["errors"]


def test_dangling_ref_returns_failure_result() -> None:
    from orchestration.dependency_graph.graph import build_dependency_graph  # noqa: F401

    _fixture = pathlib.Path("tests/fixtures/dependency_graph/dep_graph_invalid_dangling.json")
    # AC-194-09 準拠: dangling depends_on (A depends_on X / X 未定義) 時 result.success=False
    data = json.loads(_fixture.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = pathlib.Path(tmp)
        sessions_dir = repo_root / "docs" / "sessions"
        sessions_dir.mkdir(parents=True)
        for session in data["sessions"]:
            sid = session["session_id"]
            (sessions_dir / f"{sid}.json").write_text(
                json.dumps(session), encoding="utf-8"
            )
        result = build_dependency_graph(data["input"]["session_ids"], repo_root)
        expected = data["expected"]
        assert result.success == expected["success"]
        assert result.failure_type == expected["failure_type"]
        assert len(result.errors) > 0
        assert result.errors == expected["errors"]


def test_deterministic_ordering() -> None:
    from orchestration.dependency_graph.graph import build_dependency_graph  # noqa: F401

    # AC-194-06 準拠: session_id 昇順 + input order 保存の deterministic ordering を確認
    sessions_data = [
        {"session_id": "session-A", "phase_id": "P1", "depends_on": [], "blocks": []},
        {"session_id": "session-B", "phase_id": "P1", "depends_on": [], "blocks": []},
        {"session_id": "session-C", "phase_id": "P1", "depends_on": [], "blocks": []},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = pathlib.Path(tmp)
        sessions_dir = repo_root / "docs" / "sessions"
        sessions_dir.mkdir(parents=True)
        for session in sessions_data:
            sid = session["session_id"]
            (sessions_dir / f"{sid}.json").write_text(
                json.dumps(session), encoding="utf-8"
            )
        result_normal = build_dependency_graph(
            ["session-A", "session-B", "session-C"], repo_root
        )
        result_reversed = build_dependency_graph(
            ["session-C", "session-B", "session-A"], repo_root
        )
        normal_ids = [n["id"] for n in result_normal.nodes]
        reversed_ids = [n["id"] for n in result_reversed.nodes]
        assert normal_ids == reversed_ids
        assert normal_ids == sorted(["session-A", "session-B", "session-C"])

"""Dependency graph テスト scaffold (session-194-pre)。

全テストは @pytest.mark.skip 付き。
session-194 で orchestration.dependency_graph.graph.build_dependency_graph を実装後に有効化する。
"""

from __future__ import annotations

import pathlib

import pytest


@pytest.mark.skip(reason="implementation pending session-194")
def test_build_valid_minimal_graph() -> None:
    from orchestration.dependency_graph.graph import build_dependency_graph  # noqa: F401

    _fixture = pathlib.Path("tests/fixtures/dependency_graph/dep_graph_valid_minimal.json")
    # AC-194-01 準拠: 単一 session の最小 valid graph を build し success=True を返す
    ...


@pytest.mark.skip(reason="implementation pending session-194")
def test_build_valid_chained_graph() -> None:
    from orchestration.dependency_graph.graph import build_dependency_graph  # noqa: F401

    _fixture = pathlib.Path("tests/fixtures/dependency_graph/dep_graph_valid_chained.json")
    # AC-194-02 準拠: depends_on 連鎖 (A→B→C) build success および session_id 昇順 ordering を確認
    ...


@pytest.mark.skip(reason="implementation pending session-194")
def test_cycle_returns_failure_result() -> None:
    from orchestration.dependency_graph.graph import build_dependency_graph  # noqa: F401

    _fixture = pathlib.Path("tests/fixtures/dependency_graph/dep_graph_invalid_cycle.json")
    # AC-194-08 準拠: cycle (A→B→A) 時 result.success=False / failure_type='spec_missing'
    ...


@pytest.mark.skip(reason="implementation pending session-194")
def test_dangling_ref_returns_failure_result() -> None:
    from orchestration.dependency_graph.graph import build_dependency_graph  # noqa: F401

    _fixture = pathlib.Path("tests/fixtures/dependency_graph/dep_graph_invalid_dangling.json")
    # AC-194-09 準拠: dangling depends_on (A depends_on X / X 未定義) 時 result.success=False
    ...


@pytest.mark.skip(reason="implementation pending session-194")
def test_deterministic_ordering() -> None:
    from orchestration.dependency_graph.graph import build_dependency_graph  # noqa: F401

    # AC-194-06 準拠: session_id 昇順 + input order 保存の deterministic ordering を確認
    ...

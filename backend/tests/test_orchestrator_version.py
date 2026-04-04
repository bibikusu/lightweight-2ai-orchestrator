# -*- coding: utf-8 -*-
"""Test orchestrator_version function for canary test session."""

from orchestration.run_session import orchestrator_version


def test_orchestrator_version_returns_string() -> None:
    assert orchestrator_version() == "1.0.0"
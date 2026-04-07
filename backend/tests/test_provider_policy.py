# -*- coding: utf-8 -*-
"""provider_policy 読込と stage 解決のテスト。"""

from __future__ import annotations

from pathlib import Path

import orchestration.run_session as rs


def _ctx() -> rs.SessionContext:
    runtime_config = {
        "providers": {
            "openai": {"model": "gpt-4o", "timeout_sec": 120, "max_output_tokens": 4000},
            "claude": {"model": "claude-sonnet-4-20250514", "timeout_sec": 180, "max_output_tokens": 6000},
        }
    }
    return rs.SessionContext(
        session_id="session-19a",
        session_data={},
        acceptance_data={},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config=runtime_config,
    )


def test_provider_policy_loads_stage_provider_transport_model(tmp_path: Path) -> None:
    """AC-19A-01: provider_policy.yaml から stage別 provider/transport/model が読み込まれる"""
    orch_dir = tmp_path / "orchestration"
    orch_dir.mkdir(parents=True, exist_ok=True)
    (orch_dir / "provider_policy.yaml").write_text(
        "providers:\n"
        "  validation:\n"
        "    primary:\n"
        "      provider: google\n"
        "      transport: developer_api\n"
        "      model: gemini-3.1-pro-preview\n",
        encoding="utf-8",
    )
    rs.set_active_repo_root(tmp_path)
    try:
        loaded = rs.load_provider_policy()
    finally:
        rs.set_active_repo_root(rs.ROOT_DIR)
    assert loaded["providers"]["validation"]["primary"]["provider"] == "google"
    assert loaded["providers"]["validation"]["primary"]["transport"] == "developer_api"
    assert loaded["providers"]["validation"]["primary"]["model"] == "gemini-3.1-pro-preview"


def test_prepared_spec_stage_uses_openai_model_from_policy(monkeypatch) -> None:
    """AC-19A-02: prepared_spec stage は policy に従って openai と指定modelを選択する"""
    monkeypatch.setattr(
        rs,
        "load_provider_policy",
        lambda: {
            "providers": {
                "prepared_spec": {
                    "primary": {"provider": "openai", "model": "gpt-4o-mini"},
                    "fallback": None,
                }
            }
        },
    )
    resolved = rs.resolve_stage_provider_transport_model(_ctx(), "prepared_spec")
    assert resolved == {"provider": "openai", "model": "gpt-4o-mini", "transport": None}


def test_implementation_stage_uses_anthropic_model_from_policy(monkeypatch) -> None:
    """AC-19A-03: implementation stage は policy に従って anthropic と指定modelを選択する"""
    monkeypatch.setattr(
        rs,
        "load_provider_policy",
        lambda: {
            "providers": {
                "implementation": {
                    "primary": {"provider": "anthropic", "model": "claude-sonnet"},
                    "fallback": {"provider": "google", "transport": "developer_api", "model": "gemini-x"},
                }
            }
        },
    )
    resolved = rs.resolve_stage_provider_transport_model(_ctx(), "implementation")
    assert resolved == {"provider": "claude", "model": "claude-sonnet", "transport": None}


def test_validation_stage_uses_google_transport_and_model_from_policy(monkeypatch) -> None:
    """AC-19A-04: validation stage は policy に従って google provider と指定transport/modelを選択できる"""
    monkeypatch.setattr(
        rs,
        "load_provider_policy",
        lambda: {
            "providers": {
                "validation": {
                    "primary": {
                        "provider": "google",
                        "transport": "vertex_ai",
                        "model": "gemini-3.1-pro-preview",
                    },
                    "fallback": None,
                }
            }
        },
    )
    resolved = rs.resolve_stage_provider_transport_model(_ctx(), "validation")
    assert resolved == {
        "provider": "google",
        "transport": "vertex_ai",
        "model": "gemini-3.1-pro-preview",
    }


def test_provider_policy_falls_back_to_legacy_provider_and_model(monkeypatch) -> None:
    """AC-19A-05: provider policy 未設定または読込失敗時は既存デフォルト provider/model にフォールバックする"""
    monkeypatch.setattr(rs, "load_provider_policy", lambda: {})
    prepared = rs.resolve_stage_provider_transport_model(_ctx(), "prepared_spec")
    implementation = rs.resolve_stage_provider_transport_model(_ctx(), "implementation")
    retry = rs.resolve_stage_provider_transport_model(_ctx(), "retry_instruction")

    assert prepared["provider"] == "openai"
    assert prepared["model"] == "gpt-4o"
    assert implementation["provider"] == "claude"
    assert implementation["model"] == "claude-sonnet-4-20250514"
    assert retry["provider"] == "openai"
    assert retry["model"] == "gpt-4o"

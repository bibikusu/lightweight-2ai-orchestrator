# -*- coding: utf-8 -*-
"""Google provider transport 切替テスト。"""

from __future__ import annotations

from unittest.mock import patch

from orchestration.providers.google_client import GoogleClientConfig, GoogleClientWrapper


def test_google_client_switches_transport_by_policy() -> None:
    """AC-19A-06: Google provider は transport=developer_api と transport=vertex_ai を切替できる"""
    with patch.dict("os.environ", {"GEMINI_API_KEY": "dummy-key"}, clear=False):
        developer_client = GoogleClientWrapper(
            GoogleClientConfig(model="gemini-3.1-pro-preview", transport="developer_api")
        )
        result_dev = developer_client.request_json("sys", "usr")
    assert result_dev["transport"] == "developer_api"
    assert result_dev["model"] == "gemini-3.1-pro-preview"

    with patch.dict(
        "os.environ",
        {"GOOGLE_CLOUD_PROJECT": "demo-project", "GOOGLE_CLOUD_LOCATION": "asia-northeast1"},
        clear=False,
    ):
        vertex_client = GoogleClientWrapper(
            GoogleClientConfig(model="gemini-3.1-pro-preview", transport="vertex_ai")
        )
        result_vertex = vertex_client.request_json("sys", "usr")
    assert result_vertex["transport"] == "vertex_ai"
    assert result_vertex["model"] == "gemini-3.1-pro-preview"

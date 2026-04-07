# -*- coding: utf-8 -*-
"""Google provider 最小クライアント。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict

from .llm_json import parse_json_object


@dataclass
class GoogleClientConfig:
    """Google クライアント設定。"""

    model: str
    transport: str = "developer_api"
    timeout_sec: int = 120


class GoogleClientWrapper:
    """Gemini Developer API / Vertex AI の最小ルーティング。"""

    def __init__(self, config: GoogleClientConfig) -> None:
        self._config = config
        transport = str(config.transport or "").strip().lower()
        if transport not in {"developer_api", "vertex_ai"}:
            raise ValueError(f"unsupported google transport: {config.transport}")
        self._transport = transport

    def _build_request_payload(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        return {
            "transport": self._transport,
            "model": self._config.model,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        }

    def _invoke_developer_api(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        # 本 session では最小実装のみ。実接続は後続 session で拡張する。
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("環境変数 GEMINI_API_KEY が設定されていません。")
        _ = self._build_request_payload(system_prompt, user_prompt)
        return {"ok": True, "transport": "developer_api", "model": self._config.model}

    def _invoke_vertex_ai(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        # 本 session では切替可能性の確認を優先し、実接続は行わない。
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION")
        if not project or not location:
            raise RuntimeError(
                "環境変数 GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION が設定されていません。"
            )
        _ = self._build_request_payload(system_prompt, user_prompt)
        return {"ok": True, "transport": "vertex_ai", "model": self._config.model}

    def request_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        if self._transport == "developer_api":
            return self._invoke_developer_api(system_prompt, user_prompt)
        return self._invoke_vertex_ai(system_prompt, user_prompt)

    def parse_json_text(self, text: str) -> Dict[str, Any]:
        """JSON 文字列応答を辞書へ変換する補助関数。"""
        return parse_json_object(text)

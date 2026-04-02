# -*- coding: utf-8 -*-
"""Anthropic Messages API ラッパー（実装依頼用）。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict

from anthropic import Anthropic

from .llm_json import parse_json_object


@dataclass
class ClaudeClientConfig:
    """Claude クライアント設定。"""

    model: str
    timeout_sec: int = 180
    max_output_tokens: int = 6000


def _message_text_content(message: Any) -> str:
    """Message のテキストブロックを連結する。"""
    parts: list[str] = []
    for block in message.content:
        if getattr(block, "type", None) == "text" and hasattr(block, "text"):
            parts.append(block.text)
    return "".join(parts)


class ClaudeClientWrapper:
    """Messages API で JSON 応答を得る。"""

    def __init__(self, config: ClaudeClientConfig) -> None:
        self._config = config
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("環境変数 ANTHROPIC_API_KEY が設定されていません。")
        self._client = Anthropic(
            api_key=api_key,
            timeout=float(config.timeout_sec),
            max_retries=2,
        )

    def request_implementation(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        print("[INFO] Claude Messages API 呼び出し直前（同期待ち）", flush=True)
        message = self._client.messages.create(
            model=self._config.model,
            max_tokens=self._config.max_output_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = _message_text_content(message)
        # デバッグ: 生レスポンスの先頭200文字を出力
        print(f"[DEBUG] Claude raw response (first 200 chars): {repr(text[:200])}", flush=True)
        if not text.strip():
            raise RuntimeError("Claude Messages API から空の出力でした。")

        parsed_data = parse_json_object(text)

        # Add usage information if available from the response
        if hasattr(message, 'usage') and message.usage:
            parsed_data['usage'] = {
                'input_tokens': getattr(message.usage, 'input_tokens', None),
                'output_tokens': getattr(message.usage, 'output_tokens', None),
                'total_tokens': getattr(message.usage, 'input_tokens', 0) + getattr(message.usage, 'output_tokens', 0) if hasattr(message.usage, 'input_tokens') and hasattr(message.usage, 'output_tokens') else None
            }

        return parsed_data

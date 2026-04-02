# -*- coding: utf-8 -*-
"""OpenAI Responses API ラッパー（仕様整形・リトライ指示用）。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict

from openai import OpenAI

from .llm_json import parse_json_object


@dataclass
class OpenAIClientConfig:
    """OpenAI クライアント設定。"""

    model: str
    timeout_sec: int = 120
    max_output_tokens: int = 4000


class OpenAIClientWrapper:
    """Responses API で JSON 応答を得る。"""

    def __init__(self, config: OpenAIClientConfig) -> None:
        self._config = config
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("環境変数 OPENAI_API_KEY が設定されていません。")
        self._client = OpenAI(
            api_key=api_key,
            timeout=float(config.timeout_sec),
            max_retries=2,
        )

    def _responses_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        print("[INFO] OpenAI Responses API 呼び出し直前（同期待ち）", flush=True)
        response = self._client.responses.create(
            model=self._config.model,
            instructions=system_prompt,
            input=user_prompt,
            max_output_tokens=self._config.max_output_tokens,
        )
        text = response.output_text
        if not text or not text.strip():
            raise RuntimeError("OpenAI Responses API から空の出力でした。")

        parsed_data = parse_json_object(text)

        # Add usage information if available from the response
        if hasattr(response, 'usage') and response.usage:
            parsed_data['usage'] = {
                'input_tokens': getattr(response.usage, 'input_tokens', None),
                'output_tokens': getattr(response.usage, 'output_tokens', None),
                'total_tokens': getattr(response.usage, 'total_tokens', None)
            }

        return parsed_data

    def request_prepared_spec(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        return self._responses_json(system_prompt, user_prompt)

    def request_retry_instruction(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        data = self._responses_json(system_prompt, user_prompt)
        fix = data.get("fix_instructions")
        if isinstance(fix, str):
            data["fix_instructions"] = [fix]
        elif fix is None:
            data["fix_instructions"] = []
        return data

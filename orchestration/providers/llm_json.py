# -*- coding: utf-8 -*-
"""LLM 応答から JSON オブジェクトを取り出す。"""

from __future__ import annotations

import json
import re
from typing import Any, Dict


def parse_json_object(text: str) -> Dict[str, Any]:
    """モデル出力を JSON オブジェクトとして解釈する。

    JSON の前に説明文が付いている場合（リトライ時など）も対応する。
    """
    s = text.strip()

    # コードフェンスを先頭または文中から探す
    fence_match = re.search(r"```(?:json)?\s*\n?", s)
    if fence_match:
        s = s[fence_match.end():]
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3].rstrip()

    return json.loads(s)

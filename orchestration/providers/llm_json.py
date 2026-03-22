# -*- coding: utf-8 -*-
"""LLM 応答から JSON オブジェクトを取り出す。"""

from __future__ import annotations

import json
import re
from typing import Any, Dict


def parse_json_object(text: str) -> Dict[str, Any]:
    """モデル出力を JSON オブジェクトとして解釈する。"""
    s = text.strip()
    fence = re.match(r"^```(?:json)?\s*\n?", s)
    if fence:
        s = s[fence.end() :]
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3].rstrip()

    return json.loads(s)

# -*- coding: utf-8 -*-
"""parse_json_object の LLM 由来の壊れ JSON 耐性テスト。"""

import json

import pytest

from orchestration.providers.llm_json import parse_json_object


def test_parse_plain_object():
    raw = '{"ok": true, "n": 1}'
    assert parse_json_object(raw) == {"ok": True, "n": 1}


def test_parse_fenced_json():
    raw = """説明文があります\n```json\n{"x": "y"}\n```\n末尾"""
    assert parse_json_object(raw) == {"x": "y"}


def test_parse_invalid_control_character_in_string_repaired():
    # 標準 JSON では文字列内の生改行は不可。diff をそのまま入れるモデル出力向け。
    raw = (
        "{\n"
        '  "session_id": "s",\n'
        '  "proposed_patch": "--- a\n+++ b\n@@ -1,1 +1,2 @@\n+x",\n'
        '  "patch_status": "ok"\n'
        "}"
    )
    with pytest.raises(json.JSONDecodeError):
        json.loads(raw)
    out = parse_json_object(raw)
    assert out["session_id"] == "s"
    assert "--- a\n+++ b" in out["proposed_patch"]
    assert out["patch_status"] == "ok"


def test_parse_truncated_unterminated_string_repaired():
    """Claude の途中打ち切り等で implementation_summary が閉じないケース。"""
    raw = (
        "{\n"
        '  "session_id": "session-12",\n'
        '  "changed_files": ["index.html"],\n'
        '  "implementation_summary": "Implemented consiste'
    )
    with pytest.raises(json.JSONDecodeError):
        json.loads(raw)
    out = parse_json_object(raw)
    assert out["session_id"] == "session-12"
    assert out["changed_files"] == ["index.html"]
    assert out["implementation_summary"] == "Implemented consiste"


def test_parse_balanced_extraction_with_preamble():
    raw = '先にテキスト {"a": 1, "b": 2} 後ろもある'
    assert parse_json_object(raw) == {"a": 1, "b": 2}


def test_top_level_array_rejected():
    with pytest.raises(TypeError):
        parse_json_object("[1, 2]")

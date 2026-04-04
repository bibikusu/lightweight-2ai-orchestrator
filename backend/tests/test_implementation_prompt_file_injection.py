"""build_implementation_prompt_file_context_block の注入仕様テスト（session-114）。"""
import orchestration.run_session as rs
from orchestration.run_session import build_implementation_prompt_file_context_block


def test_small_file_injected_as_whole():
    """200 行規模・改行数が閾値以下なら [current file: path] に全文が載る。"""
    body = "\n".join(f"row{i}" for i in range(200))
    content = "HEAD_MARK\n" + body + "\nTAIL_MARK\n"
    assert content.count("\n") <= rs.IMPLEMENTATION_PROMPT_FULL_FILE_MAX_NEWLINES
    block = build_implementation_prompt_file_context_block("rel/small.txt", content)
    assert "\n\n[current file: rel/small.txt]\n" in block
    assert "HEAD_MARK" in block and "TAIL_MARK" in block
    assert "omitted" not in block.lower()


def test_large_file_section_extracted():
    """300 行超かつ section_hint で <section id> 内のみが注入される。"""
    pad = "\n".join(f"PADDING{i}" for i in range(500))
    inner = "ONLY_IN_SECTION_TOP\n" + "\n".join(f"inner{i}" for i in range(40))
    inner += "\nONLY_IN_SECTION_BOTTOM\n"
    content = (
        f"{pad}\n<section id=\"task-management\">\n{inner}\n</section>\nONLY_OUTSIDE\n"
    )
    assert content.count("\n") > rs.IMPLEMENTATION_PROMPT_FULL_FILE_MAX_NEWLINES
    block = build_implementation_prompt_file_context_block(
        "sec.html",
        content,
        section_hint="task-management",
    )
    assert "ONLY_IN_SECTION_TOP" in block and "ONLY_IN_SECTION_BOTTOM" in block
    assert "PADDING0" not in block
    assert "ONLY_OUTSIDE" not in block
    assert "extracted" in block and "task-management" in block


def test_large_file_fallback_head_tail():
    """section_hint なし、または id 未検出時は先頭50+末尾20と omitted。"""
    lines = [f"line{i:04d}" for i in range(500)]
    lines[0] = "UNIQUE_HEAD_FB"
    lines[250] = "UNIQUE_MIDDLE_OMIT"
    lines[-1] = "UNIQUE_TAIL_FB"
    content = "\n".join(lines) + "\n"
    assert content.count("\n") > rs.IMPLEMENTATION_PROMPT_FULL_FILE_MAX_NEWLINES

    block_none = build_implementation_prompt_file_context_block(
        "a.txt", content, section_hint=None
    )
    assert "UNIQUE_HEAD_FB" in block_none
    assert "UNIQUE_TAIL_FB" in block_none
    assert "UNIQUE_MIDDLE_OMIT" not in block_none
    assert "omitted" in block_none.lower()

    block_bad = build_implementation_prompt_file_context_block(
        "a.txt", content, section_hint="nosuchid"
    )
    assert "not found" in block_bad.lower()
    assert "UNIQUE_HEAD_FB" in block_bad
    assert "UNIQUE_TAIL_FB" in block_bad


def test_extracted_section_truncated_if_too_long():
    """section 抽出結果が 1000 行超なら切り詰め注記が付く。"""
    pad = "\n".join(f"PX{i}" for i in range(304))
    inner = "\n".join(f"SECROW{i}" for i in range(1500))
    content = f"{pad}\n<section id=\"huge\">\n{inner}\n</section>\n"
    assert content.count("\n") > rs.IMPLEMENTATION_PROMPT_FULL_FILE_MAX_NEWLINES
    block = build_implementation_prompt_file_context_block(
        "big.txt", content, section_hint="huge"
    )
    assert "truncated" in block.lower()
    assert "SECROW0" in block
    assert "SECROW1499" not in block
    assert "SECROW999" in block

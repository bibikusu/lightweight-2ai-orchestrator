"""large-file handling の境界ケース検証（AC-01〜AC-05）。"""
from orchestration.run_session import (
    _get_head_tail_fallback,
    _truncate_lines,
    build_implementation_prompt_file_context_block,
)


def test_ac_01_nested_section_is_extracted_without_outer_noise():
    """AC-01: ネスト section でも対象 section の内側のみを抽出できる。"""
    pad = "\n".join(f"pad{i}" for i in range(350))
    content = (
        f"{pad}\n"
        "<section id=\"outer\">\n"
        "OUTER_HEAD\n"
        "<section id=\"target\">\n"
        "TARGET_TOP\n"
        "<section id=\"inner\">INNER_BODY</section>\n"
        "TARGET_BOTTOM\n"
        "</section>\n"
        "OUTER_TAIL\n"
        "</section>\n"
    )
    block = build_implementation_prompt_file_context_block(
        "nested.html", content, section_hint="target"
    )
    assert "TARGET_TOP" in block
    assert "TARGET_BOTTOM" in block
    assert "INNER_BODY" in block
    assert "OUTER_HEAD" not in block
    assert "OUTER_TAIL" not in block


def test_ac_02_duplicate_function_hints_are_deduplicated():
    """AC-02: 重複した function hint は1回だけ扱う。"""
    lines = [f"pad{i}" for i in range(360)]
    lines.extend(
        [
            "function renderCard() {",
            "  return 1;",
            "}",
            "TAIL_MARK",
        ]
    )
    content = "\n".join(lines) + "\n"
    block = build_implementation_prompt_file_context_block(
        "ui.js",
        content,
        function_hints=["renderCard", "renderCard", "renderCard"],
    )
    assert "functions [renderCard] extracted" in block
    assert block.count("function renderCard() {") == 1
    assert "... [between functions] ..." not in block


def test_ac_03_head_tail_fallback_returns_whole_for_short_input():
    """AC-03: fallback を短いファイルへ適用しても omitted にならず全文になる。"""
    content = "L0\nL1\nL2\n"
    out = _get_head_tail_fallback(content, total_lines=3, head_n=50, tail_n=20)
    assert out == content
    assert "omitted" not in out.lower()


def test_ac_04_truncate_boundary_plus_minus_one():
    """AC-04: truncate 境界値 max_lines±1 で挙動が安定する。"""
    max_lines = 4
    just_fit = "".join(f"a{i}\n" for i in range(max_lines))
    over_by_one = "".join(f"b{i}\n" for i in range(max_lines + 1))

    out_fit = _truncate_lines(just_fit, max_lines=max_lines)
    out_over = _truncate_lines(over_by_one, max_lines=max_lines)

    assert out_fit == just_fit
    assert "truncated:" not in out_fit
    assert "truncated:" in out_over
    assert "b3" in out_over
    assert "b4" not in out_over


def test_ac_05_fallback_reason_includes_section_and_function_miss():
    """AC-05: section 未検出 + function 未一致の両理由がヘッダに残る。"""
    lines = [f"line{i}" for i in range(380)]
    lines[0] = "HEAD_MARK"
    lines[-1] = "TAIL_MARK"
    content = "\n".join(lines) + "\n"

    block = build_implementation_prompt_file_context_block(
        "a.txt",
        content,
        section_hint="missing-section",
        function_hints=["notFoundFn"],
    )
    assert "section id='missing-section' not found" in block
    assert "function hints not matched in source" in block
    assert "HEAD_MARK" in block
    assert "TAIL_MARK" in block
    assert "omitted" in block.lower()

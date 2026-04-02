"""実装プロンプトへの allowed_changes ファイルコンテキスト注入のテスト（session-113）。"""
import orchestration.run_session as rs
from orchestration.run_session import SessionContext, build_implementation_prompts


def _ctx_with_detail(session_id: str, detail: list, **extra_session) -> SessionContext:
    base = {
        "session_id": session_id,
        "phase_id": "phase3",
        "title": "context injection test",
        "goal": "test",
        "scope": [],
        "out_of_scope": [],
        "constraints": [],
        "acceptance_ref": "docs/acceptance/session-89.yaml",
        "allowed_changes": ["orchestration/run_session.py"],
    }
    base.update(extra_session)
    if detail is not None:
        base["allowed_changes_detail"] = detail
    return SessionContext(
        session_id=session_id,
        session_data=base,
        acceptance_data={"raw_yaml": "", "parsed": {}},
        master_instruction="",
        global_rules="",
        roadmap_text="",
        runtime_config={},
    )


def test_small_file_context_is_included_fully(tmp_path, monkeypatch):
    """300 行以下（改行数基準）は従来どおり全文が注入される。"""
    monkeypatch.setattr(rs, "ROOT_DIR", tmp_path)
    rel = "small_ctx.txt"
    (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
    # 改行 300 以下 → 全文（先頭・末尾の目印の両方がプロンプトに載る）
    body = "\n".join(f"line{i}" for i in range(50))
    content = "UNIQUE_HEAD_SMALL_CTX\n" + body + "\nUNIQUE_TAIL_SMALL_CTX\n"
    assert content.count("\n") <= rs.IMPLEMENTATION_PROMPT_FULL_FILE_MAX_NEWLINES
    (tmp_path / rel).write_text(content, encoding="utf-8")

    ctx = _ctx_with_detail("session-113-small", [f"{rel}: test"])
    _, user = build_implementation_prompts({"objective": "x"}, ctx)
    assert "UNIQUE_HEAD_SMALL_CTX" in user
    assert "UNIQUE_TAIL_SMALL_CTX" in user
    assert f"[current file: {rel}]" in user
    assert "partial tail only" not in user


def test_large_file_uses_partial_tail_context(tmp_path, monkeypatch):
    """300 行超（改行数基準）は末尾断片のみ注入される。"""
    monkeypatch.setattr(rs, "ROOT_DIR", tmp_path)
    rel = "large_ctx.txt"
    (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
    # 改行を 301 以上にする（先頭だけ別行、あとは短い行を足す）
    lines = ["UNIQUE_HEAD_LARGE_SHOULD_NOT_APPEAR"]
    lines.extend([f"x{i}" for i in range(350)])
    lines.append("UNIQUE_TAIL_LARGE_SHOULD_APPEAR")
    content = "\n".join(lines) + "\n"
    assert content.count("\n") > rs.IMPLEMENTATION_PROMPT_FULL_FILE_MAX_NEWLINES
    (tmp_path / rel).write_text(content, encoding="utf-8")

    ctx = _ctx_with_detail("session-113-large", [f"{rel}: test"])
    _, user = build_implementation_prompts({"objective": "x"}, ctx)
    assert "partial tail only" in user
    assert "UNIQUE_TAIL_LARGE_SHOULD_APPEAR" in user
    assert "UNIQUE_HEAD_LARGE_SHOULD_NOT_APPEAR" not in user


def test_missing_allowed_change_file_is_skipped_safely(tmp_path, monkeypatch):
    """存在しないパスは例外なくスキップされ、current file ブロックが増えない。"""
    monkeypatch.setattr(rs, "ROOT_DIR", tmp_path)
    rel = "definitely_missing_file_113.txt"
    ctx = _ctx_with_detail("session-113-missing", [f"{rel}: test"])
    _, user = build_implementation_prompts({"objective": "x"}, ctx)
    # session_json にパス文字列は載るが、ファイル本文の current file ブロックは付与しない
    assert f"\n\n[current file: {rel}]\n" not in user
    assert f"lines): {rel}]\n" not in user  # partial tail 形式のヘッダも付けない


def test_context_injection_is_limited_to_allowed_changes(tmp_path, monkeypatch):
    """allowed_changes_detail がある場合はそこに列挙されたファイルだけ注入する。"""
    monkeypatch.setattr(rs, "ROOT_DIR", tmp_path)
    in_rel = "in_scope_113.txt"
    out_rel = "out_scope_113.txt"
    (tmp_path / in_rel).write_text("ONLY_IN_SCOPE_MARKER\n", encoding="utf-8")
    (tmp_path / out_rel).write_text("ONLY_OUT_OF_SCOPE_MARKER\n", encoding="utf-8")

    ctx = _ctx_with_detail(
        "session-113-scope",
        [f"{in_rel}: in"],
    )
    prepared = {
        "objective": "x",
        "allowed_changes": [in_rel, out_rel],
    }
    _, user = build_implementation_prompts(prepared, ctx)
    assert "ONLY_IN_SCOPE_MARKER" in user
    assert "ONLY_OUT_OF_SCOPE_MARKER" not in user

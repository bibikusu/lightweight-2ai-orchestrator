"""
AC-163-01〜06 対応テスト: run_session.py の --use-selector flag
AC-167-01〜07 対応テスト: execution_mode 接続・正規化
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))


# ---------------------------------------------------------------------------
# AC-163-01: parse_args() に --use-selector flag が存在する
# ---------------------------------------------------------------------------

def test_parse_args_has_use_selector_flag():
    """parse_args() が --use-selector を受け付け args.use_selector 属性を返す。"""
    from orchestration.run_session import parse_args

    with patch("sys.argv", ["run_session.py", "--use-selector"]):
        args = parse_args()
    assert hasattr(args, "use_selector")
    assert args.use_selector is True


def test_parse_args_use_selector_default_false():
    """--use-selector 未指定時は False。"""
    from orchestration.run_session import parse_args

    with patch("sys.argv", ["run_session.py", "--session-id", "session-01"]):
        args = parse_args()
    assert hasattr(args, "use_selector")
    assert args.use_selector is False


# ---------------------------------------------------------------------------
# AC-163-02 (修正版): _run_selector_subprocess() が SelectorResult を返す
# ---------------------------------------------------------------------------

def test_run_selector_subprocess_returns_session_id():
    """正常系: selected_session_id を SelectorResult.selected_session_id で返す。"""
    from orchestration.run_session import _run_selector_subprocess, SelectorResult

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = json.dumps({"selected_session_id": "session-99", "candidate_sessions": []})

    with patch("subprocess.run", return_value=mock_proc) as mock_run:
        result = _run_selector_subprocess()

    assert isinstance(result, SelectorResult)
    assert result.selected_session_id == "session-99"
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert "select_next.py" in " ".join(call_args)
    assert "--dry-run" in call_args


def test_run_selector_subprocess_exits_on_nonzero():
    """非ゼロ終了コード → sys.exit(1)。"""
    from orchestration.run_session import _run_selector_subprocess

    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stderr = "selector error"

    with patch("subprocess.run", return_value=mock_proc):
        with pytest.raises(SystemExit) as exc_info:
            _run_selector_subprocess()
    assert exc_info.value.code == 1


def test_run_selector_subprocess_exits_on_bad_json():
    """stdout が JSON でない → sys.exit(1)。"""
    from orchestration.run_session import _run_selector_subprocess

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "not-json"

    with patch("subprocess.run", return_value=mock_proc):
        with pytest.raises(SystemExit) as exc_info:
            _run_selector_subprocess()
    assert exc_info.value.code == 1


def test_run_selector_subprocess_exits_on_missing_session_id():
    """selected_session_id キーがない → sys.exit(1)。"""
    from orchestration.run_session import _run_selector_subprocess

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = json.dumps({"candidate_sessions": []})

    with patch("subprocess.run", return_value=mock_proc):
        with pytest.raises(SystemExit) as exc_info:
            _run_selector_subprocess()
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# AC-163-03 (修正版): selected_session_id と execution_mode が args に反映される
# ---------------------------------------------------------------------------

def test_main_use_selector_sets_session_id_and_calls_impl():
    """--use-selector 指定時に session_id と execution_mode が args にセットされ _run_single_session_impl が呼ばれる。"""
    from orchestration import run_session

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = json.dumps({"selected_session_id": "session-42", "candidate_sessions": []})

    captured_args = {}

    def fake_impl(args):
        captured_args["session_id"] = args.session_id
        captured_args["execution_mode"] = args.execution_mode
        return 0

    with patch("sys.argv", ["run_session.py", "--use-selector"]), \
         patch("subprocess.run", return_value=mock_proc), \
         patch.object(run_session, "_run_single_session_impl", side_effect=fake_impl), \
         patch.object(run_session, "_ensure_repo_root_on_sys_path"), \
         patch.object(run_session, "set_active_repo_root"):
        result = run_session.main()

    assert result == 0
    assert captured_args.get("session_id") == "session-42"
    assert captured_args.get("execution_mode") == "full_stack"


# ---------------------------------------------------------------------------
# AC-163-04: orchestration.selector の直接 import が存在しない
# ---------------------------------------------------------------------------

def test_no_direct_selector_import_in_run_session():
    """run_session.py に 'from orchestration.selector' / 'import orchestration.selector' が含まれない。"""
    run_session_path = ROOT_DIR / "orchestration" / "run_session.py"
    source = run_session_path.read_text(encoding="utf-8")
    assert "from orchestration.selector" not in source
    assert "import orchestration.selector" not in source


# ---------------------------------------------------------------------------
# AC-163-05: import 可能性確認（regression 補助）
# ---------------------------------------------------------------------------

def test_run_session_importable():
    """orchestration.run_session が import できる。"""
    import importlib
    mod = importlib.import_module("orchestration.run_session")
    assert mod is not None


# ---------------------------------------------------------------------------
# AC-163-06: mutually exclusive — --use-selector / --session-id / --batch
# ---------------------------------------------------------------------------

def test_use_selector_and_session_id_mutually_exclusive():
    """--use-selector と --session-id の同時指定は SystemExit を発生させる。"""
    from orchestration.run_session import parse_args

    with patch("sys.argv", ["run_session.py", "--use-selector", "--session-id", "session-01"]):
        with pytest.raises(SystemExit):
            parse_args()


def test_use_selector_and_batch_mutually_exclusive():
    """--use-selector と --batch の同時指定は SystemExit を発生させる。"""
    from orchestration.run_session import parse_args

    with patch("sys.argv", ["run_session.py", "--use-selector", "--batch", "session-01,session-02"]):
        with pytest.raises(SystemExit):
            parse_args()


# ---------------------------------------------------------------------------
# AC-167-01: SelectorResult NamedTuple の構造確認
# ---------------------------------------------------------------------------

def test_selector_result_namedtuple_has_session_id_and_execution_mode():
    """SelectorResult NamedTuple が selected_session_id と execution_mode を持つ。"""
    from orchestration.run_session import SelectorResult

    result = SelectorResult(selected_session_id="session-119", execution_mode="full_stack")
    assert result.selected_session_id == "session-119"
    assert result.execution_mode == "full_stack"
    assert hasattr(result, "selected_session_id")
    assert hasattr(result, "execution_mode")


# ---------------------------------------------------------------------------
# AC-167-02: _run_selector_subprocess() が SelectorResult を返す
# ---------------------------------------------------------------------------

def test_run_selector_subprocess_returns_selector_result():
    """_run_selector_subprocess() の戻り値が SelectorResult 型である。"""
    from orchestration.run_session import _run_selector_subprocess, SelectorResult

    fake_stdout = json.dumps({
        "selected_session_id": "session-119",
        "execution_mode": "full_stack",
    })
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = fake_stdout

    with patch("subprocess.run", return_value=mock_proc):
        result = _run_selector_subprocess()

    assert isinstance(result, SelectorResult)
    assert result.selected_session_id == "session-119"
    assert result.execution_mode == "full_stack"


# ---------------------------------------------------------------------------
# AC-167-03: execution_mode 欠損 → full_stack に正規化
# ---------------------------------------------------------------------------

def test_run_selector_subprocess_defaults_missing_execution_mode_to_full_stack():
    """execution_mode キーが欠損している場合 full_stack に正規化される。"""
    from orchestration.run_session import _run_selector_subprocess

    fake_stdout = json.dumps({"selected_session_id": "session-119"})
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = fake_stdout

    with patch("subprocess.run", return_value=mock_proc):
        result = _run_selector_subprocess()

    assert result.execution_mode == "full_stack"


# ---------------------------------------------------------------------------
# AC-167-04: execution_mode が null → full_stack に正規化
# ---------------------------------------------------------------------------

def test_run_selector_subprocess_defaults_null_execution_mode_to_full_stack():
    """execution_mode が null の場合 full_stack に正規化される。"""
    from orchestration.run_session import _run_selector_subprocess

    fake_stdout = json.dumps({"selected_session_id": "session-119", "execution_mode": None})
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = fake_stdout

    with patch("subprocess.run", return_value=mock_proc):
        result = _run_selector_subprocess()

    assert result.execution_mode == "full_stack"


# ---------------------------------------------------------------------------
# AC-167-05: execution_mode が full_stack / fast_path → そのまま維持
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", ["full_stack", "fast_path"])
def test_run_selector_subprocess_accepts_valid_execution_mode(mode):
    """execution_mode が full_stack または fast_path の場合そのまま維持される。"""
    from orchestration.run_session import _run_selector_subprocess

    fake_stdout = json.dumps({"selected_session_id": "session-119", "execution_mode": mode})
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = fake_stdout

    with patch("subprocess.run", return_value=mock_proc):
        result = _run_selector_subprocess()

    assert result.execution_mode == mode


# ---------------------------------------------------------------------------
# AC-167-06: execution_mode が不正値 → stderr エラー + exit 1
# ---------------------------------------------------------------------------

def test_run_selector_subprocess_exits_on_invalid_execution_mode(capsys):
    """execution_mode が不正値の場合 stderr エラー + exit 1。"""
    from orchestration.run_session import _run_selector_subprocess

    fake_stdout = json.dumps({
        "selected_session_id": "session-119",
        "execution_mode": "invalid_mode_xyz",
    })
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = fake_stdout

    with patch("subprocess.run", return_value=mock_proc):
        with pytest.raises(SystemExit) as exc_info:
            _run_selector_subprocess()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "execution_mode" in captured.err
    assert "invalid_mode_xyz" in captured.err


# ---------------------------------------------------------------------------
# AC-167-07: --use-selector 実行時に args.session_id と args.execution_mode が設定される
# ---------------------------------------------------------------------------

def test_main_use_selector_sets_session_id_and_execution_mode():
    """--use-selector 実行時に args.session_id と args.execution_mode が SelectorResult から設定される。"""
    from orchestration import run_session

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = json.dumps({
        "selected_session_id": "session-88",
        "execution_mode": "fast_path",
    })

    captured_args = {}

    def fake_impl(args):
        captured_args["session_id"] = args.session_id
        captured_args["execution_mode"] = args.execution_mode
        return 0

    with patch("sys.argv", ["run_session.py", "--use-selector"]), \
         patch("subprocess.run", return_value=mock_proc), \
         patch.object(run_session, "_run_single_session_impl", side_effect=fake_impl), \
         patch.object(run_session, "_ensure_repo_root_on_sys_path"), \
         patch.object(run_session, "set_active_repo_root"):
        result = run_session.main()

    assert result == 0
    assert captured_args.get("session_id") == "session-88"
    assert captured_args.get("execution_mode") == "fast_path"

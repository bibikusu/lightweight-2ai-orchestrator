#!/usr/bin/env bats
# tests/test_step0_check.sh — bats 単体テスト for scripts/step0_check.sh
# テスト対象AC: AC-01〜AC-04 (session-177)
# 実行方法: bats tests/test_step0_check.sh

SCRIPT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)/scripts/step0_check.sh"
REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"

# AC-01: step0_check.sh 単独実行で4種のチェックがすべて出力される
@test "test_step0_check_runs_four_checks" {
  SESSION_ID="test-ac01-$$" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  [[ "$output" == *"check_git_status"* ]]
  [[ "$output" == *"check_head"* ]]
  [[ "$output" == *"check_stash"* ]]
  [[ "$output" == *"check_reflog"* ]]
  # クリーンアップ
  rm -rf "$REPO_ROOT/artifacts/test-ac01-$$"
}

# AC-02: 出力先ディレクトリが存在しない場合に自動作成される
@test "test_step0_check_creates_output_dir" {
  local sid="test-ac02-$$"
  local out_dir="$REPO_ROOT/artifacts/$sid/step0"
  rm -rf "$REPO_ROOT/artifacts/$sid"
  SESSION_ID="$sid" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  [ -d "$out_dir" ]
  # クリーンアップ
  rm -rf "$REPO_ROOT/artifacts/$sid"
}

# AC-03: git stash list が空でも非エラー終了する
@test "test_step0_check_empty_stash_ok" {
  local sid="test-ac03-$$"
  # 一時的に git stash list を空返しするモック環境で実行
  local mock_dir
  mock_dir="$(mktemp -d)"
  # git モック: stash list は空を返す、それ以外は本物に委譲
  cat > "$mock_dir/git" <<'EOF'
#!/usr/bin/env bash
if [ "${1:-}" = "stash" ] && [ "${2:-}" = "list" ]; then
  exit 0
fi
exec /usr/bin/git "$@"
EOF
  chmod +x "$mock_dir/git"
  SESSION_ID="$sid" PATH="$mock_dir:$PATH" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  # クリーンアップ
  rm -rf "$mock_dir" "$REPO_ROOT/artifacts/$sid"
}

# AC-04: 出力ファイル名に session_id を含み、上書きで衝突しない
@test "test_step0_check_filename_includes_session_id" {
  local sid="test-ac04-$$"
  local out_dir="$REPO_ROOT/artifacts/$sid/step0"
  SESSION_ID="$sid" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  # ファイル名に session_id が含まれていること
  [ -f "$out_dir/${sid}_git_status.txt" ]
  [ -f "$out_dir/${sid}_git_head.txt" ]
  [ -f "$out_dir/${sid}_git_stash.txt" ]
  [ -f "$out_dir/${sid}_git_reflog.txt" ]
  # 同じ session_id で再実行しても衝突しない（上書き成功）
  SESSION_ID="$sid" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  [ -f "$out_dir/${sid}_git_head.txt" ]
  # クリーンアップ
  rm -rf "$REPO_ROOT/artifacts/$sid"
}

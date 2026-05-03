# session-167 起票検収レポート

## 概要
- session_id: session-167
- 種別: docs-only (起票)
- main HEAD (commit): 0f4611b
- 前 HEAD: 7632569 (session-166 完了時点)
- 起票日: 2026-05-03 (chat 54)
- マイルストーン: M-B step 3 実装仕様起票
- 判定: PASS

---

## 検収結果サマリ

| 軸 | 結果 |
|---|---|
| AC-167-01〜09 | 9/9 PASS (構造検証済) |
| CC-167-01〜05 | 5/5 PASS |
| 司令塔判定 3 件反映 | 3/3 反映済 |

---

## 司令塔判定 3 件の反映確認 (chat 54 内、参謀提示)

| 論点 | 内容 | 反映先 | 結果 |
|---|---|---|---|
| 論点1 | AC-167-08 verification の論理エラー修正 (案A) | yaml L76 | ✅ `git diff 7632569..HEAD` 範囲指定に修正 |
| 論点2 | existing_tests_to_preserve フィールド追加 (案γ) | json L132 | ✅ |
| 論点3 | BACKLOG-PYPATH-001 起票 (案Q) | json L147 backlog_candidates | ✅ |

---

## session-166 仕様との整合性 (依存関係)

session-167 は session-166 で固定した仕様 (HEAD 7632569) に完全準拠:

| session-166 で固定 | session-167 反映先 | 整合 |
|---|---|---|
| SelectorResult NamedTuple | AC-167-01 | ✅ |
| selected_session_id: str / execution_mode: str | AC-167-01 | ✅ |
| 正規化責任 = run_session.py 側 | scope + AC-167-03〜06 | ✅ |
| missing_key/null → full_stack | AC-167-03/04 | ✅ |
| 正常値はそのまま | AC-167-05 | ✅ |
| invalid_value → exit 1 + stderr | AC-167-06 | ✅ |
| 起動時 1 回確定 | CC-167-03 | ✅ |
| 同一 session 内 fallback 禁止 | out_of_scope | ✅ |

→ session-166 の relation_to_next_session で固定した範囲を完全網羅。

---

## review_points (4軸)

- 仕様一致 (AC達成): pass
- 変更範囲遵守: pass (2 ファイルのみ、git diff stat で確認済)
- 副作用なし (既存破壊なし): pass (docs-only、コード非接触)
- 検証十分性: pass (JSON/YAML 構文 + grep 3 件 + 司令塔判定反映確認)

---

## 構文検証結果

- python3 -m json.tool: PASS
- python3 -c "yaml.safe_load(...)": PASS

---

## 副次発見 (chat 54 累計、memory 反映候補)

1. **AC verification コマンドの実行タイミング論理エラーパターン** (#21): `git diff --name-only` は unstaged のみ参照、commit 後の検収では機能しない。`git diff <baseline>..HEAD` 範囲指定が必須。
2. **既存テスト regression 検証分離パターン** (#22): existing_tests_to_preserve フィールドで事前明示。
3. **プロジェクト全体規律 vs session 局所規律の正本化先分離** (#23): PYTHONPATH=. 必須化は session 起票文で初明文化せず BACKLOG として全体正本化へ。

---

## 関連 commit

- 0f4611b docs: session-167 起票 (run_session selector execution_mode 接続実装)
- 7632569 session-166: docs-only acceptance PASS and review report added
- 985700f docs: session-165 起票検収レポート

---

## 次セッション (実装フェーズ)

session-167 実装は別フェーズで実行:
1. Claude Code Plan Mode (Shift+Tab 2回) 必須
2. preflight_session.sh フック通過必須
3. 4-gate 全 PASS 必須 (PYTHONPATH=. 付き)
4. sandbox/session-167 ブランチ作成 → 実装 → 4-gate → cherry-pick to main
5. 実装後の検収レポートは別途作成


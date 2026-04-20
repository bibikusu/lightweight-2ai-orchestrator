# BACKLOG-AUTH-REQUIREMENTS-SEPARATION-001

## 優先度
中

## 発覚日
2026-04-21 (session-145a 作業中、作業ツリーに別レーン変更が混入していたことが判明)

## 内容
`auth/` ディレクトリと `requirements.txt` の変更が 125a / 145a / a02-research-01 レーン作業中の作業ツリーに混在していた。これらは review_points / dashboard / A02 Research の各 session とは無関係の変更で、混入したまま 4-gate 実行すると scan 対象によっては fail を誘発する環境ノイズ源。

## 経緯
- session-145a Phase 2 の 4-gate を scan 対象 `.` (全体) で実行した際、auth/routes/auth.py の未使用 import / fastapi 依存不足 などで FAIL
- KUNIHIDE 判定 B (2026-04-21) により、auth/ と requirements.txt を `git stash push -u -m "temp-separate-auth-and-requirements-before-145a-validation"` で退避 (stash@{0})
- 退避後に 4-gate を Phase 1 同条件 (.venv/bin/ prefix + scan 対象絞り込み) で再実行 → 全 pass
- 以降、145a / a02-research-01 の作業中は stash@{0} 保持を継続

## 分離方針
現在 stash@{0} に退避されている auth/ と requirements.txt を、以下のいずれかで別レーンに正式化する。

1. 内容確認 → 認証機能の実装レーンとして新規 session 起票 (例: `session-auth-01`)
2. 内容が不要・実験残渣なら `git stash drop stash@{0}`
3. 内容が別プロジェクトの作業なら別 branch に移す

## 次アクション
1. `git stash show -p stash@{0}` で内容詳細確認
2. requirements.txt の diff と auth/ 配下のファイル一覧を KUNIHIDE が確認
3. 用途判定後、上記 1-3 いずれかの方針で session 起票 or 破棄

## 関連
- 発覚元: session-145a 作業、2026-04-21
- 他 BACKLOG との関係: 独立 (RETRY-RESUME-BUILDER-TEST-FAIL-001 とは無関係)
- stash 位置: `stash@{0}: On sandbox/session-145a: temp-separate-auth-and-requirements-before-145a-validation`

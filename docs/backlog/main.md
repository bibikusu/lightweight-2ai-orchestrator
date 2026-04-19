# Project BACKLOG

軽量2AIオーケストレーター方式の未解決事項 / 改善候補を一元管理する BACKLOG 正本。

各項目は:
- ID: `BACKLOG-<CATEGORY>-NNN`
- 内容: 簡潔な説明
- 発生元: 発見セッション / 発見時期
- 優先度: high / medium / low
- 見積: 想定作業時間
- 対応予定: 対応候補セッション or "未定"

---

## Open BACKLOG(未対応)

### BACKLOG-PREFLIGHT-EXIT-CODE-001

- **内容**: `scripts/preflight_session.sh` が dirty worktree 等でも `exit 0` を返し得る既存仕様を見直す
- **発生元**: session-141 risk R-1(2026-04-19)
- **影響**: P7 Hooks 運用時の fail-fast 品質に影響。PreToolUse hook が preflight の exit code を伝播する設計のため、preflight 側が甘いと Hook 全体のガード強度が下がる
- **優先度**: medium
- **見積**: 10-20min
- **対応予定**: P7 運用開始前の別セッション(候補: session-142 or 143)

### BACKLOG-CURSOR-COMMIT-GUARD-001

- **内容**: Cursor による untracked ファイル放置事故の再発防止
- **発生元**: session-137 / session-138(2026-04-18 〜 19)
- **状態**: session-141 のプロンプトに「事故再発防止」セクションを追加することで運用的に緩和済。Hook 側で自動化する余地あり
- **優先度**: low(運用ワークアラウンド済)
- **見積**: 20-30min
- **対応予定**: P7 Hooks 拡張(未定)

### BACKLOG-QUEUE-TEST-SPEC-MISSING-001

- **内容**: queue engine の spec_missing 明示テスト追加
- **発生元**: session-137(P6C 実装時)
- **影響**: spec_missing が human_gate に分岐するロジックは実装済だが、テストが暗黙的
- **優先度**: low
- **見積**: 10min
- **対応予定**: P7 完了後の軽量メンテ session

### BACKLOG-PATCH-001

- **内容**: `patch_apply` の fuzzy match / hunk 再解決による大型 HTML 対応
- **発生元**: Card Task session-12 / session-114
- **影響**: 2400 行超の HTML ファイルでは `patch_apply` が `context_mismatch` で失敗する構造的制約
- **優先度**: low(Cursor 直接実装で回避可能)
- **見積**: 調査含めて数時間
- **対応予定**: 本命プロジェクト(A02_fina / Card Task)の量産開始前に判断

### BACKLOG-SANDBOX-CLEANUP-001

- **内容**: 不要な sandbox ブランチ(41 本削除対象 + 17 本判定対象)の整理
- **発生元**: 運用蓄積
- **優先度**: low
- **見積**: 30-60min
- **対応予定**: 未定(P7 完了後の余裕時)

---

## Resolved BACKLOG(対応済)

### BACKLOG-DRIFT-DETECTOR-REVIEW-POINTS-001(解消済)

- **内容**: `drift_detector.py` の `EXPECTED_REVIEW_POINTS` を「実装過不足なし」から「検証十分性」に修正
- **状態**: 参謀 selfcheck により、既に正本は「検証十分性」と確認済(userMemories 2026-04-17)

---

## 管理原則

- 新規 BACKLOG は本ファイルに追記する
- 解消したら "Resolved BACKLOG" セクションに移動する(削除しない、履歴として残す)
- P7 以降はセッション作成時に本ファイルを参照し、関連項目があれば取り込みを検討する

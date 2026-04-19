# P7-pre Responsibility Canonicalization

## Claude Code Hooks + MCP Integration Boundary Specification

**Phase**: P7-pre
**Status**: draft for canonicalization
**Purpose**: Claude Code Hooks / MCP / preflight / commit / 4-gate / human の責務境界を固定し、人間コピペを排除する自動実行基盤の設計前提を確定する。

---

## 1. 目的

P6 で完成した実行基盤(run_session / queue / scheduler)の上に、P7 では Claude Code Hooks と MCP を用いた自動化レイヤーを追加する。

本書の目的は、P7 本体実装の前に以下を固定することにある。

- Claude Code Hooks の責務
- MCP の責務
- preflight の責務
- commit の責務
- 4-gate の責務
- human の責務
- 自動化対象と人間判断対象の境界
- Custom Slash Commands を Phase 7-B として分離する方針

---

## 2. P7-pre で扱う責務一覧

本セッションで固定する責務は以下の 6 つとする。

1. Claude Code Hooks
2. MCP
3. preflight
4. commit
5. 4-gate
6. human

Custom Slash Commands は本セッションでは実装対象に含めず、**Phase 7-B 扱いで scope 外**とする。

---

## 3. 責務境界

### 3.1 Claude Code Hooks の責務

Claude Code Hooks は、Claude Code 実行前後のガードと補助的自動処理を担う。

担当範囲:

- 実行前の preflight 呼び出し
- 実行後の 4-gate 呼び出し
- commit 前の最終ガード
- docs-only / code-change の種別に応じた補助判定
- 失敗時の停止とログ出力

やらないこと:

- 仕様の決定
- acceptance の最終判定
- run_session.py の直接置換
- queue / scheduler の内部ロジック変更
- main への自動 push

### 3.2 MCP の責務

MCP は外部ツール・外部システムとの接続境界を担う。

担当範囲:

- GitHub など外部システムとの接続
- リポジトリ状態の読取
- 将来の PR / issue / deploy 接続の入口
- Claude Code が安全に参照できる外部文脈の提供

やらないこと:

- 仕様の正本化
- commit 判定
- acceptance 判定
- queue 実行そのもの

### 3.3 preflight の責務

preflight は、実装着手前の安全確認を担う。

担当範囲:

- worktree clean 確認
- branch sync 確認
- venv 健康確認
- session 定義ファイル存在確認
- 事前条件不足時の fail-fast

やらないこと:

- 実装
- commit
- acceptance 判定
- main 反映

### 3.4 commit の責務

commit は、変更内容を履歴として確定する責務を持つ。

担当範囲:

- allowed_changes 範囲内の変更を履歴化
- docs-only / code-change の区別
- sandbox branch 上の成果物確定
- cherry-pick 前の単位整理

やらないこと:

- acceptance 判定
- 自動 merge
- scope 逸脱の自己正当化
- main への無条件反映

### 3.5 4-gate の責務

4-gate は、最小の機械検証を担う。

対象:

- ruff
- pytest
- mypy
- compileall

担当範囲:

- コード品質確認
- 型整合確認
- テスト整合確認
- import / compile の最低限確認

やらないこと:

- 業務仕様の妥当性判定
- acceptance そのものの代替
- 人間レビューの代替

### 3.6 human の責務

human は、最終承認と例外判断を担う。

担当範囲:

- 最終受入判定
- 例外対応
- 方針変更
- スコープ変更の承認
- rollback 判断

やらないこと:

- AI 間の手作業コピペ中継の常態化
- 未検収状態でのフェーズ進行
- 曖昧な判断の放置

---

## 4. 自動化対象と人間判断対象

### 4.1 自動化対象

以下は P7 以降で自動化対象とする。

- preflight 実行
- 4-gate 実行
- docs-only / code-change の分類補助
- sandbox 上の commit 補助
- GitHub / MCP を介した補助的参照
- Hooks による fail-fast

### 4.2 人間判断対象

以下は人間判断対象として残す。

- 仕様の最終確定
- acceptance の最終判定
- main 反映可否
- 例外処理
- 本番有効化
- スコープ追加 / 変更

---

## 5. P7-B へ分離するもの

Custom Slash Commands は本セッションの scope 外とする。

理由:

- Hooks / MCP / preflight / commit / 4-gate の責務固定を優先するため
- Slash Commands は操作導線であり、責務境界より後段の UI / UX レイヤーに近いため
- P7-B として独立管理した方が責務が混ざらないため

P7-B 候補:

- /session-draft
- /spec-review
- /cursor-run

---

## 6. P7 本体に進むための入力条件

P7 本体実装に進むための前提は以下とする。

- P6 completion report が main に存在する
- QueueEngine 公開 API が固定済みである
- scheduler の責務が固定済みである
- run_session.py の CLI 契約が固定済みである
- Hooks / MCP / preflight / commit / 4-gate / human の責務境界が明文化済みである
- Slash Commands は別フェーズで扱うと明示されている

---

## 7. P7 本体で扱う対象(予告)

P7 本体では以下を候補とする。

- Claude Code Hooks 実装
- MCP 接続の最小導入
- preflight / 4-gate / commit guard の自動呼び出し
- 人間コピペ削減のための接続基盤

本書は実装仕様ではなく、**責務固定の正本**である。

---

## 8. 最終判断

P7-pre の完了条件は、Hooks / MCP / preflight / commit / 4-gate / human の責務境界が固定され、P7 本体実装に進める状態になることである。

この時点では、まだ Hooks や MCP の実装は行わない。

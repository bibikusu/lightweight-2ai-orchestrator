# Project Command Center v0 仕様正本

## 1. 本文書の位置づけ

本文書は **read-only aggregation layer** としての Project Command Center v0 の仕様正本である。

**本システムは状態可視化UIであり、実行制御システムではない。**

- 本 UI は ClaudeCode / run_session.py / queue engine の実行責務に一切踏み込まない。
- 判断責務（何を実行するか・いつ実行するか）は GPT 司令塔および Human が担う。
- 本 UI が行うことは、既存の静的ファイルを読み取り、状態をカード形式で表示することのみである。

---

## 2. 設計目的

ClaudeCode 多窓運用において、10プロジェクトの現在状態を一覧で把握できるようにする。

- 各プロジェクトの git 状態・最新 session・4-gate 状態・failure_type・human gate を一目で確認できる。
- 次に何をすべきかを Human / GPT が判断するための情報基盤を提供する。
- 実行ボタン・操作ボタン・キュー操作は一切持たない。

---

## 3. Source of Truth（情報源の固定）

本 UI が参照できる情報源は以下の6種に限定する。

| # | 情報源 | 用途 |
|---|--------|------|
| 1 | `git rev-parse HEAD` | 各リポジトリの HEAD コミット取得 |
| 2 | `git status --short` | 各リポジトリのワーキングツリー変更状態 |
| 3 | `docs/sessions/` | session 定義の読み取り（最新 session 特定） |
| 4 | `docs/acceptance/` | acceptance 定義の読み取り（4-gate 状態参照） |
| 5 | `artifacts/reports/` | 実行レポートの読み取り（artifacts 有無確認） |
| 6 | `queue_state.json`（read-only） | キュー状態の読み取り |

### 禁止事項（情報源制約）

- **DB禁止**: データベースへの直接接続・クエリ実行は禁止
- **daemon禁止**: バックグラウンドデーモンプロセスの起動は禁止
- **background watcher禁止**: ファイルシステム監視プロセス・WebSocket・SSE・push 通知の導入は禁止

---

## 4. プロジェクトカード仕様

### 4.1 カードの件数

カードは `project_registry.json` を source of truth として動的に生成する。ハードコードしない。

**初期表示は最大10件**とする。10件を超えるプロジェクトがある場合はページングまたはスクロールで対応する。

### 4.2 カード表示項目（11項目）

| # | フィールド名 | 内容 | 情報源 |
|---|------------|------|--------|
| 1 | `project_id` | プロジェクト識別子 | `project_registry.json` |
| 2 | `repo_path` | リポジトリの物理パス | `project_registry.json` |
| 3 | `branch` | 現在の git ブランチ名 | `git rev-parse --abbrev-ref HEAD` |
| 4 | `HEAD` | 直近コミットハッシュ（短縮形） | `git rev-parse HEAD` |
| 5 | `git status` | ワーキングツリーの変更状態（clean / dirty） | `git status --short` |
| 6 | `最新 session` | 最後に起票された session_id | `docs/sessions/` 最新ファイル |
| 7 | `4-gate` | 4-gate の通過状態（passed / failed / pending） | `docs/acceptance/` 対応 YAML |
| 8 | `failure_type` | 直近失敗の種別（failure_type enum 値） | `artifacts/reports/` 直近レポート |
| 9 | `human gate` | Human による承認待ち状態（waiting / cleared） | `queue_state.json` |
| 10 | `artifacts` | 最新 session の成果物有無 | `artifacts/reports/` |
| 11 | `手動更新` | 最終手動更新日時（UI上で表示） | ローカルキャッシュまたは手動入力 |

---

## 5. やらないこと（明示的禁止事項）

本 v0 では以下を実装しない。

1. **ClaudeCode を置き換えない**: 本 UI は ClaudeCode の代替・代理として動作しない。ClaudeCode は引き続き唯一の実行エンジンである。
2. **SDK自作オーケストレーター**: Anthropic SDK を用いた自作オーケストレーターの設計・実装・PoC は本スコープ外。
3. **stash@{0} の参照・解放**: stash@{0}（WIP: scheduler/batch/queue, chat51）は封印継続。本 UI から参照・解放しない。
4. **queue / scheduler の機能拡張**: queue エンジン・スケジューラーの機能追加・変更は行わない。先行肥大化禁止。

---

## 6. ClaudeWeb / ClaudeCode 投入方針

本 UI の仕様正本化・実装・検証における各 AI エージェントおよび Human の作業責任分担を以下に示す。

| 作業フェーズ | 責任主体 | 具体的作業 |
|------------|---------|----------|
| 仕様起票・正本化 | **GPT**（司令塔） | session JSON / acceptance YAML の起票・検収 |
| 仕様レビュー・参謀 | **ClaudeWeb**（参謀） | 仕様の整合性確認・リスク指摘・代替案提示 |
| 実装・ファイル生成 | **ClaudeCode**（現場知能） | docs 生成・後続の UI 実装コード作成 |
| 施工・差分適用 | **ClaudeCode** / **Cursor**（施工） | ファイル書き込み・git 操作 |
| 最終受入判定 | **Human**（最終意思決定者） | 4-gate 通過確認・GPT 検収後の承認 |

### 投入方針の補足

- ClaudeWeb は仕様の参謀として機能し、実装には踏み込まない。
- ClaudeCode は実装の現場知能として機能し、仕様の変更判断は行わない。
- GPT は司令塔として session の起票・検収・依存順序の管理を担う。
- Human はすべての破壊的変更・依存順序の逸脱・gate 承認において最終意思決定権を持つ。

---

## 7. 依存順序と実装制約

本 v0 spec の後続実装（session-172d 無印）は以下の順序が完了してから着手する。

```
179系（VCER/RB 昇格）close ✓ 完了
    ↓
役割再定義 pivot（180-pre → 180 → 181-pre → 181）
    ↓
本 session の後続実装 session-172d（無印）
```

この依存順序を逸脱した実装着手は禁止する。

---

## 8. 保護ファイル一覧

以下のファイルは本 v0 仕様化セッションで変更しない。

| ファイル | md5 baseline |
|--------|-------------|
| `orchestration/run_session.py` | `4de6affffb9297cdf02b3136e8f55172` |
| `orchestration/selector/core.py` | `9b19e2cbe3487d3090096c5343c88611` |
| `orchestration/selector/loader.py` | `959db533bf086f83765d8f6f16fbbe7b` |
| `orchestration/selector/writer.py` | `aaf7e28e0e9c52d12d30c8d3349cf982` |

---

## 9. v1 以降への拡張候補（v0 スコープ外）

以下は v1 以降で検討する。本 v0 では一切実装しない。

- WebSocket / SSE によるリアルタイム更新
- Human Gate Panel（承認・差戻し操作 UI）
- Session Queue View（queue_state の可視化）
- Roadmap Builder（Phase / 依存関係の管理）
- 認証・権限・ログイン機構
- DB 直接参照によるレポート集計
- バックグラウンドデーモンによる自動更新

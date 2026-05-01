# execution_mode 仕様 v0

## 1. 定義

execution_mode は、session 実行時の AI 投入パターンを示す enum である。

execution_mode:
  type: enum[full_stack, fast_path]

## 2. enum 値

### 2.1 full_stack

投入順:
GPT → Claude → ClaudeCode

用途:
- 新規仕様
- UI設計
- 複数 project 横断
- DB 変更あり
- deploy_risk が high または critical
- acceptance 未確定
- failure_type 発生後の再実行 session

性質:
安全モード。分析を挟む。

### 2.2 fast_path

投入順:
GPT → ClaudeCode

用途:
- docs-only
- JSON/YAML 修復
- 明確な lint 修正
- acceptance 既存
- deploy_risk が low

性質:
高速モード。低リスク作業向け。

## 3. 優先順位

execution_mode は以下の優先順位で決定する。

1. session.json の execution_mode 明示値
2. project default

session.json に execution_mode がある場合、それを正とする。
session.json に execution_mode がない場合、project default を参照する。

## 4. fallback ポリシー

v0 では同一 session 内の自動切替は禁止する。

禁止:
fast_path → full_stack の同一 session 内自動昇格

許可:
failure_type 発生後、次 session 起票時に推奨 execution_mode を full_stack にする

つまり fallback は「次 session 起票時の推奨変更」であり、現在実行中 session の AI 構成を自動変更するものではない。

## 5. selector 連携方針

将来、selector output に execution_mode を含める。

想定形式:
{
  "selected_session_id": "session-XXX",
  "selection_reason": "...",
  "execution_mode": "fast_path",
  "candidate_sessions": [],
  "metadata": {}
}

v0 では設計のみで、selector 実装は変更しない。

## 6. api_route との関係

execution_mode は戦略レイヤーである。
api_route は execution_mode から派生する実装詳細である。

3 層関係:
execution_mode
↓
api_route
↓
provider

意味:

| レイヤー | 役割 |
|---|---|
| execution_mode | どのAI体制で進めるか |
| api_route | どのAPI経路で呼ぶか |
| provider | 実際にどのモデル・事業者で実行するか |

## 7. 責任レイヤー

execution_mode の選択は意思決定レイヤーに属する。

| 役割 | 責務 |
|---|---|
| 人間 / GPT司令塔 | execution_mode を決める |
| オーケストレーター | 決定された execution_mode を実行に渡す |
| Claude / ClaudeCode | execution_mode を勝手に変更しない |

## 8. v0 人間選択ルール

v0 では UI 上で人間が明示選択する。
自動判定ロジックは実装しない。

禁止例:
if scope == docs-only:
    execution_mode = fast_path

これは v1 以降の検討事項とする。

## 9. 既存 session JSON への適用

既存 session JSON への execution_mode 一括追記は本仕様の scope 外。
必要に応じて後続 session で段階適用する。

## 10. 後続 session 候補

### session-161 候補

selector output に execution_mode を追加する設計・実装。

### session-162 候補

Project Command Center v2 UI 実装の最小 read-only 版。

### session-163 候補

事務所 LLM サーバーを軽量作業部隊として接続する PoC。

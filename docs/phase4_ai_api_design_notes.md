# Phase4 AI API Design Notes

## 目的
Phase4 では、AI API の設定を大量に実装するのではなく、
実案件投入と provider usage 実データ取得を優先する。

設定案は本ファイルに設計メモとして保存し、
実装は Phase5 で実データを見てから行う。

---

## Phase4 で実装しない理由

### 1. 実データ不足
- provider が usage を安定して返していない
- session_max_estimated_cost_usd の閾値を今決めても根拠が弱い

### 2. 既存実装と重複
- preflight fail で API 呼び出し前停止
- sandbox branch 強制
- dirty worktree 拒否
- patch 未適用時 checks スキップ

これらは既に run_session.py の現行実装で実現している。

### 3. 設定を増やすと分岐とテストが増える
Phase4 は 5 セッションに絞っているため、
config.yaml に大量設定を追加すると本筋を圧迫する。

---

## 将来の設定候補（Phase5以降）

### ai_runtime
```yaml
ai_runtime:
  session_max_api_calls: 6
  session_max_estimated_cost_usd: 1.50
  retry_max_api_calls: 2
  retry_same_cause_block: true
  save_raw_responses: true
  save_normalized_responses: true
  save_response_summaries: true
```

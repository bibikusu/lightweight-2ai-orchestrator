# memory_role.md — memory は補助記憶 / canonical は repo

## 1. 原則

本リポジトリの軽量2AIオーケストレーター運用において、以下を canonical として固定する。

1. **memory は補助記憶である** — session を跨いだ context 復元のために用いるが、repo 上の実ファイルを上書きする権限を持たない。
2. **canonical = repo** — 正本はすべて git HEAD 上の実ファイルである。
3. **矛盾時は repo 現物確認を優先する** — memory の内容と repo 現物が食い違う場合、memory を疑い、repo 現物を正として判断する。

## 2. 解決優先順序

情報源が複数存在する場合、以下の優先順序で判断する:

1. **repo 現物**（git HEAD 上の実ファイル）
2. **プロジェクト知識アップロード**（chat に添付されたスナップショット）
3. **memory**（補助記憶として参照）

memory のみを根拠に正本系（global_rules.md / master_instruction.md / canonical 14 keys / review_points 4軸 等）の判定を行ってはならない。

## 3. 適用範囲

本ルールは以下の判断において常に適用される:

- canonical session 仕様（14 keys / review_points 4軸 / acceptance_criteria.description 等）の確認
- selector md5 baseline の確認
- session_id 衝突確認
- 既存資産（保持 / frozen / 破棄）の判定
- handoff_artifact / completion_report の schema 確認

## 4. 本ルールが対象としないもの

以下は本ルールの対象外である:

- memory 操作 API / SDK の実装
- memory 自動同期 / watcher / daemon
- memory DB / state cache / runtime memory
- 運用上の context 圧縮方針の設計（future_proposal で別扱い）
- memo ファイル / スナップショットの自動生成・更新

# Cluster Check Rules（Phase A 最小仕様）

## 1. 目的
- 本仕様は、A02_fina の Phase A において blueprint 同士の検索意図衝突（カニバリ）を防ぐための最小チェックルールを定義する。
- 自動化は行わず、手動チェックのみを対象とする。

## 2. 検索意図分類（search_intent）
新規 blueprint は `search_intent` を以下のいずれかに分類する。

- `informational`: 情報収集・理解を目的とする検索意図。
- `transactional`: 申込み・購入・問い合わせなど行動実行を目的とする検索意図。
- `navigational`: 特定サービス名・ページ名・ブランドへの到達を目的とする検索意図。
- `local`: 地域名やエリア条件を含み、地域起点の比較・来訪・問い合わせを目的とする検索意図。

## 3. 重複判定ルール（最小）
既存 blueprint と比較し、以下を判定する。

1. 同一 `target_keyword` は禁止（新規作成しない）。
2. 類似キーワード（表記ゆれ・語尾違い・同義に近い語）は `search_intent` で判定する。
3. `search_intent` が同一で、かつ `heading_structure` が類似する場合は重複扱い（NG）とする。

## 4. blueprint_spec との関係
- 判定時は `docs/blueprint_spec.md` の `search_intent` を必須入力として使用する。
- 競合回避は `heading_structure` の差別化を基本とする。
- 最終確認では `cta` の誘導目的が既存 blueprint と衝突しないことを確認する。

## 5. 手動チェック手順（Phase A）
新規 blueprint 作成時に、以下を順に実施する。

1. 新規案の `target_keyword` と `search_intent` を記入する。
2. 既存 blueprint 一覧から同一または類似 `target_keyword` を抽出する。
3. 対象候補ごとに `search_intent` を比較する。
4. `heading_structure` を比較し、同一intentで構造が近い場合は新規案を修正または作成中止とする。
5. `cta` の誘導目的を比較し、同一導線への競合があれば差別化する。
6. 重複なしと判断できた場合のみ、当該 blueprint を採用する。

## 6. 適用範囲
- 本仕様は session-03 の範囲に限定する。
- DB設計、API設計、実装自動化、スコアリング高度化には拡張しない。

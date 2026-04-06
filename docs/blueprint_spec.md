# Blueprint Spec（Phase A）

## 1. Purpose
- 本仕様の目的は、SEO記事生成前段で利用する `blueprint` の最小要件を定義すること。
- `blueprint` は、検索意図からタイトル・見出し構造・CTA・構造化データ前提を整理し、後続の人手編集とHTML反映を安定化するための仕様書である。
- 本仕様は Phase A 専用とし、実装ロジックや本文自動生成は対象外とする。

## 2. Inputs
- `search_intent`（必須）: 検索ユーザーが解決したい課題・意図。
- `target_keyword`（必須）: 主対象キーワード。
- `persona`（任意）: 想定読者の属性・前提知識・利用シーン。
- `constraints`（必須）: YMYL 配慮、禁止表現、対象 publish target（`primary`）などの制約条件。

## 3. Outputs
- `title`（必須）: 記事タイトル案。
- `description`（必須）: メタディスクリプション案。
- `heading_structure`（必須）: `h2` / `h3` の階層構造。
- `cta`（必須）: 主CTA文言と誘導先の意図。
- `slug`（必須）: URL想定の文字列。
- `jsonld_type`（必須）: `article` または `faq`。

## 4. Required Fields（必須項目定義）
- `search_intent`: 問題解決意図が1文以上で定義されていること。
- `title`: 検索意図と主キーワードに整合すること。
- `heading_structure`: `h2` / `h3` の親子関係が明確で、見出しのみで全体像を把握できること。
- `cta`: 誘導目的（問い合わせ、比較、資料請求など）が明記されていること。
- `canonical前提`: 正規URLを前提に管理することを明記すること。
- `ogp前提`: OGPタイトル・説明文との整合を前提にすること。
- `jsonld前提`: `jsonld_type` に基づく JSON-LD 実装を前提にすること。

## 5. Optional Fields（任意項目）
- `persona`: 読者像が必要な場合のみ追加する。
- `tone`: 文体方針（丁寧、簡潔、専門寄りなど）を指定する。
- `internal_links`: 関連する内部導線候補。
- `external_references`: 参照候補となる外部情報源。

## 6. HTML Mapping（重要）
- session-01a の HTML構造への対応:
  - `title` はページタイトル要素と本文冒頭の見出し設計に反映する。
  - `description` は head メタ記述前提として利用する。
  - `heading_structure` は本文セクションの `h2` / `h3` 構造に1対1で対応させる。
  - `cta` は本文末尾または指定CTA領域に対応させる。
- session-01b の head（OGP / JSON-LD）との接続:
  - `title` / `description` は OGP 系メタ情報との整合を取る。
  - `slug` と `canonical前提` を canonical URL 管理の入力前提にする。
  - `jsonld_type` は JSON-LD テンプレート種別選択の前提値として扱う。

## 7. Phase Constraints
- Phase A では本文生成を行わない。
- 本文は人間が作成・編集する前提とする。
- publish target は `primary` のみを対象とする。
- 本仕様は blueprint 定義に限定し、DB/API/実装設計へ拡張しない。

## 8. YMYL Policy（重要）
- 事実確認: 数値・制度・医療/金融/法律関連情報は公開前に確認する。
- 出典確認: 参照元の一次性・更新日・信頼性を確認する。
- 誇張・断定禁止: 根拠のない断定、過度な効果保証、誤認を招く表現を禁止する。
- 免責前提: 本文・CTAを含む全体で「法的助言ではない」等の前提を明確化する。

## 9. Usage Flow
- `blueprint` 作成
- 人間による本文編集
- HTMLテンプレートへ反映（session-01a / session-01b 構造に接続）
- publish

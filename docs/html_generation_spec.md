# HTML Generation Spec（Phase A）

## 1. Purpose
- 本仕様は、`blueprint` を `base.html` ベースの静的HTML1ページへ反映するための最小生成ルールを定義する。
- session-01a のHTML/CSS構造、session-01b のhead metadata構造へ接続し、Phase A の `primary` 公開前提に合わせる。
- 本仕様は手動運用を前提とし、自動生成ロジックの実装は対象外とする。

## 2. Inputs
- `blueprint`（`search_intent`, `title`, `description`, `heading_structure`, `cta`, `slug`, `jsonld_type`）
- `base.html`（唯一のテンプレート）
- `jsonld snippets`（`article` / `faq` の選択肢）
- `publish target = primary`

## 3. Outputs
- static HTML page（単一ページ）
- page title
- meta description
- heading sections（`h2` / `h3`）
- CTA block
- canonical placeholder
- OGP placeholder
- JSON-LD type selection

## 4. Required Mapping
- `title` → `<head><title>` / `<main>` 内の主見出し
- `description` → `<meta name="description">` またはページ要約領域
- `heading_structure` → `<main>` の本文セクション構造（`h2` / `h3`）
- `cta` → CTAブロック（本文末尾または指定CTA領域）
- `slug` → ファイル名またはURL想定値（canonical設計の入力）
- `jsonld_type` → `article` / `faq` のJSON-LD選択

## 5. Template Rules
- `base.html` を唯一のテンプレートとして使用する。
- `header` / `main` / `footer` の骨格を維持する。
- session-01a のCSS前提を崩さない。
- session-01b のhead metadata前提（canonical / OGP / JSON-LD）を維持する。

## 6. Generation Flow
1. blueprint review（必須項目の充足確認）
2. human body writing（本文は人間が作成）
3. HTML mapping（`base.html` へ各項目を反映）
4. metadata review（title / description / canonical / OGP / JSON-LD確認）
5. publish（`primary` 対象のみ）

## 7. Phase Constraints
- Phase A では本文自動生成を行わない。
- 1ページずつ手動生成する。
- 対象は `primary` のみとする。
- 最終確認は人間の手動チェックを前提とする。

## 8. YMYL Policy
- 事実確認: 数値・制度・医療/金融/法律関連情報は公開前に確認する。
- 出典確認: 一次情報または信頼できる情報源を確認する。
- 誇張禁止: 根拠のない断定・過度な効果保証を禁止する。
- 法的助言ではない前提: 記事およびCTA全体で免責観点を維持する。

## 9. Example Mapping
- 例（1件のみ）
  - `title`: 「千葉のキャスト派遣サービス比較ガイド」
  - `description`: 「目的別に比較ポイントを整理し、問い合わせ前に確認すべき条件を解説」
  - `heading_structure`: `h2: 比較軸` / `h2: よくある失敗` / `h2: 依頼前チェック`
  - `cta`: 「無料相談はこちら」
  - `slug`: `chiba-cast-haken-guide`
  - `jsonld_type`: `faq`
  - 出力先: `<title>`, `<meta name="description">`, `<main>` 見出し群, CTA領域, canonical想定URL, FAQ JSON-LD

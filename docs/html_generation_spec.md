# HTML Generation Spec（Phase A）

## 1. Purpose
- 本仕様は、`cluster_check` 通過済み `blueprint` を受け取り、静的HTML1ページへ反映する実行仕様を固定する。
- 入力チェーンは `blueprint -> cluster_check -> html_generation` で固定する。
- 対象は docs-only の仕様明文化であり、実装コード変更は対象外とする。

## 2. Input Preconditions（入力前提）
- `html_generation` は `cluster_check` の判定結果が `採用可` の `blueprint` のみを受け取る。
- 受領する `blueprint` は `docs/blueprint_spec.md` の固定出力契約（`search_intent`, `target_keyword`, `title`, `description`, `heading_structure`, `cta`, `slug`, `jsonld_type`）を満たしていることを前提とする。
- 受領必須項目は `title`, `description`, `heading_structure`, `cta`, `slug`, `jsonld_type` とする。
- `blueprint` の再設計、`cluster_check` の再判定は `html_generation` の責務外とする。
- テンプレートは `base.html` を前提とし、出力対象は静的HTML1ページのみとする。

## 3. Required Mapping（必須マッピング項目）
- `title` -> `<title>`
- `description` -> `<meta name="description">`
- `heading_structure` -> `<main>` 見出し群（`h2` / `h3`）
- `cta` -> CTA領域
- `slug` -> canonical 想定URL
- `jsonld_type` -> FAQ JSON-LD または対応 JSON-LD 領域

## 4. Output Target（出力先）
- 出力物は静的HTML1ページ（単一ファイル）とする。
- head 領域の反映先は `<title>` と `<meta name="description">` とする。
- body 領域の反映先は `<main>` 見出し群と CTA領域とする。
- URL系の反映先は canonical 想定URL とする。
- 構造化データの反映先は FAQ JSON-LD または対応 JSON-LD 領域とする。

## 5. Forbidden（禁止事項）
- `blueprint` の再設計を行わない。
- `cluster_check` の再判定を行わない。
- SEO本文生成ルールの追加を行わない。
- `docs/blueprint_spec.md` と `docs/cluster_check_rules.md` を変更しない。
- `run_session.py` や `providers` 配下を変更しない。
- 新機能追加を行わない。

## 6. Completion Conditions（完了条件）
- 必須マッピング6項目の反映が完了していること。
- Phase A 制約（手動運用・静的HTML1ページ・docs-only）に準拠していること。
- 手動 review が完了していること。
- session-05 / session-06 / session-08 で固定された input chain と受領条件に矛盾しないこと。

## 7. Review Points（review 観点）
- 仕様一致（AC達成）
- 変更範囲遵守
- 副作用なし（既存破壊なし）
- 実装過不足なし

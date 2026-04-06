# A02_fina 親仕様書（凍結版）

## 文書管理

- 文書ID: master_spec_a02_fina
- バージョン: v1.0（凍結版）
- 正本: 本ファイルのみ
- 上位文書: global_rules.md（オーケストレーター共通ルール）
- 変更手順: GPT提案 → Claude差分分析 → 人間承認 → 反映

---

## 1. 定義

A02_fina は、検索意図・クラスター・エンティティを基盤に、AIが観測・判断・提案・生成を行い、人間が承認・例外判断を担いながら、長期的に可視性と収益を積み上げるSEO運用OSである。

### 1-1. 名称

- プロジェクト名: A02_fina
- システム種別: 自動運用型SEO運用OS
- 構造名: SEO運用OS 3+1層構造

### 1-2. 目的

- Google検索上位表示によるアフィリエイト収益の獲得
- AI検索（ChatGPT, Perplexity等）からの引用・可視性の獲得
- 5年10年運用に耐える自動改善型システムの構築

### 1-3. vertical

- 対象業種: 消費者金融 × 弁護士（債務整理アフィリエイト）
- YMYL該当: あり
- リスク区分: 高（法務・金融領域）

---

## 2. 4部隊体制

### GPT

- 役割: 仕様確定・判定・session定義生成
- 禁止: 実装担当として振る舞うこと、スコープ拡大

### Claude

- 役割: 分析参謀・差分分析・selfcheck
- 禁止: 仕様の最終確定、スコープ外対応

### Cursor

- 役割: 実装・実行・検証
- 禁止: 仕様の独断変更

### 人間

- 役割: 最終承認・優先順位判断・例外判断・knowledge_base への知見投入
- 禁止: 未検収のまま次Phaseに進めること

---

## 3. 3+1層構造

### レイヤー1: 生成OS

- キーワード入力
- 軽量クラスター確認
- blueprint生成
- テンプレート選択
- HTML生成
- 公開キュー投入
- knowledge_base からの独自視点注入（Phase C）
- content_inspector による品質ゲート（Phase C）

### レイヤー2: 運用OS

- Search Console分析
- CTR改善候補抽出
- リライト候補抽出（rewrite_triggers）
- 鮮度管理
- カニバリ監視
- 公開順制御

### レイヤー3: 観測OS

- 業界情報の定期取得
- 競合新着検知
- トレンド変動検知
- 影響判定
- 緊急リライト判定
- 新記事提案
- 新クラスター提案

### レイヤー4: 自己進化（拡張層）

- 勝ちテンプレート学習
- 勝ちコンテンツ形式学習
- 収益化しやすいクラスター学習
- 改善施策の効果学習
- SERP面の優先学習

---

## 4. 自動の定義

A02_finaにおける「自動」は以下で固定する。

- 自動観測
- 自動判定
- 自動提案
- 自動生成
- 自動キュー投入
- 公開は人間承認または条件付き自動

### 4-1. 人間承認

- queueに積まれた公開候補を一括承認可能にする
- 承認前にblueprint / metadata / JSON-LD / 公開先を確認可能にする

### 4-2. 条件付き自動承認

以下の条件を全て満たす場合のみ許可対象とする。

- 既存承認済みテンプレートと一致
- リスク区分が低い
- YMYL非該当
- 既存ページと重複しない
- 法務チェック不要
- 構造化データ要件を満たす

---

## 5. 本文ポリシー

### 5-1. Phase A〜B

- 本文生成なし
- 生成対象は blueprint / 見出し構造 / FAQ構造 / 比較表構造 / metadata / JSON-LD下書きまで
- Phase Aの5記事は人間が本文を書く（AI本文生成の対象外）

### 5-2. Phase C

- AI本文生成を有効化
- 人間が必要箇所のみ補正・承認
- 目的は量産ではなく、人の役に立つ高評価コンテンツの生成

### 5-3. 品質原則

- 独自性のない一般論の量産は禁止
- 既存ページの焼き直し禁止
- 読了価値・滞在価値・比較価値を重視する

---

## 6. publish_targets

公開先は以下の3層で定義する。

### 6-1. primary

- 本体サイト（独自ドメイン）
- Phase A から運用

### 6-2. platforms

- 外部プロフィール（note, はてなブログ, Zenn等）
- Phase B から追加

### 6-3. satellites

- 関連メディアサイト群（独自ドメイン × 別サーバー × 独自デザイン × 独自コンテンツ）
- Phase C から追加

### 6-4. 設計原則

- publish_targetはplugin方式で追加可能にする
- 各targetは独自テンプレート・独自デザインを持つ
- コンテンツの使い回しは禁止し、ターゲットごとに再構成する
- リンクは自然な文脈内リンクのみとする（フッター羅列禁止）
- satellitesは独自ドメイン・独自Cloudflareアカウント・独自Analyticsプロパティ・Whois privacy有効を前提とする

### 6-5. 解釈

satellitesは「リンク目的の空サイト」ではなく、独自価値を持つ関連メディアと定義する。中身のない量産サイトや同一テンプレート横展開は許可しない。

---

## 7. テクニカル要件

### 7-1. 必須技術

- Cloudflare Pages対応（Phase Aから）
- JSON-LD必須化: FAQ schema, Article schema, BreadcrumbList
- IndexNow対応（Phase Bから補助導入）

### 7-2. ホスティング方針

- Phase A: XserverまたはCloudflare Pagesのどちらでも可
- Phase B以降: Cloudflare Pages推奨（無料・帯域無制限・CDN最速）
- satellites: Cloudflare Pages無料枠で別プロジェクト運用

### 7-3. 技術設計原則

- 静的HTMLを基本とする
- 軽量CSS / 軽量JSを優先
- 構造化データは生成工程で差し込み可能にする
- CDN配信・高速表示を前提にする
- DBは使用しない
- localStorageは使用しない
- サーバーサイドレンダリングは行わない

---

## 8. 成功条件

### 8-1. 従来SEO

- Google検索での上位表示
- CTR改善
- 滞在時間改善
- リライト後の順位改善

### 8-2. GEO（Generative Engine Optimization）

- AI検索（ChatGPT, Perplexity等）からの引用
- AI検索上の可視性
- AI Overviewへの表示機会拡大

### 8-3. 対応方針

- JSON-LDによりAIが読みやすい構造を提供する
- FAQ構造でAI Overview掲載を狙う
- 独自データ（比較表・計算ツール・統計まとめ）を持つ
- 参照価値のある情報設計を優先する

### 8-4. GEO計測方針

- GEO引用獲得率はPhase B以降で計測手段が確立した時点で有効化
- Phase Aでは計測対象外
- 当面は手動でAI検索に自サイト名を入れて確認する運用

---

## 9. 軽量クラスター確認

### 9-1. Phase A

- キーワード重複確認
- 既存ページ重複確認

### 9-2. Phase C

- 本格クラスター運用
- キーワードマップ運用
- エンティティ単位の再編成

---

## 10. Phase定義

### Phase 0: Bootstrap

- A02_finaリポジトリのクリーン化
- 制御面（オーケストレーター側）/ 実装面（A02_fina側）の分離確定
- patch_apply対象パス検証
- --skip-checks運用確認
- 完了条件: session-01aのdry-run成功 + live-run最小検証成功

### Phase A: MVP静的公開

- 静的HTML 5本以上公開済み
- Search Console接続済み
- blueprint → HTML出力パイプラインが2回以上再現成功
- primaryのみ運用
- 人間が本文を書く（AI本文生成なし）

### Phase B: 運用強化

- Search Consoleデータ30日以上蓄積
- CTR / 順位データに基づくリライト候補抽出が1回以上実行済み
- カニバリ監視が稼働中
- platforms追加
- IndexNow導入

### Phase C: 拡張・自動生成

- CTR改善ループ稼働
- AI本文生成有効化
- 自動提案稼働
- satellites追加
- knowledge_base注入有効化
- content_inspector有効化

### 移行条件

- 各Phaseの完了条件を全て満たした状態で、人間が移行承認を出すこと

---

## 11. 重要指標

- 検索順位
- CTR
- 滞在時間
- スクロール率
- CTA到達率
- 引用獲得率（Phase B以降）
- クラスター単位の収益性
- リライト改善率

---

## 12. 静的サイトジェネレーター導入判断

### 12-1. Phase A

- 手書き静的HTMLを基本とする
- 50ページ以下なら十分

### 12-2. Phase B

- 100ページを超えたらHugo導入を判断する

### 12-3. 判断基準

- ページ数、管理コスト、ビルド速度、公開更新頻度、テンプレート分岐数

### 12-4. Hugo選定理由

- Go製でビルドが高速
- Markdown対応
- 大量ページに強い
- Cloudflare Pagesと接続しやすい

### 12-5. 補足

- Phase Aではgenerator導入を前提にしない
- 公開開始を優先し、管理コストが実際に増えた時点で移行判断する

---

## 13. 被リンク獲得戦略

### 13-1. 基本方針

被リンクは「リンクを作る」ではなく、引用される価値を作ることを基本とする。

### 13-2. tier1_immediate（システム実装対象外、運用マニュアルとして整理）

- Googleビジネスプロフィール登録
- 外部プロフィールサイト（note, はてな等）に専門記事投稿
- 業界ディレクトリ登録

### 13-3. tier2_midterm

- 独自比較表
- 計算ツール
- 統計まとめ
- HARO / Qwoted経由のメディア被リンク

### 13-4. tier3_longterm

- 関連メディアサイト運営（satellites）
- 各メディアが独自の価値を持つ運営

### 13-5. 禁止事項

- 中身のないリンク目的サイトの作成
- 同一テンプレート・同一コンテンツの横展開
- フッターリンク羅列
- 同一Analytics / Whoisの使い回し
- PBN的な量産リンク設計

---

## 14. knowledge_base

### 14-1. 目的

- 独自視点・体験談・業界知見・独自主張をテキストとして蓄積する
- AI生成コンテンツの差別化ソースとする

### 14-2. 動作

- Phase CのAI本文生成時に関連エピソードを自動抽出して注入する
- 使用回数を記録し、同一ネタの過剰再利用を防ぐ

### 14-3. Phase方針

- Phase A〜B: 人間が手動で本文へ反映
- Phase C: 自動注入を有効化

---

## 15. content_inspector

### 15-1. 目的

- 公開キュー投入前の自動品質チェック

### 15-2. チェック項目

- 一般論に終始していないか
- 独自視点が含まれているか
- 構造化データが正しいか

### 15-3. 動作

- 閾値未満なら再生成
- 公開判定の代替ではなく前段フィルター（人間承認の手前）

### 15-4. パイプライン上の位置

```
生成 → content_inspector → 公開キュー → 人間承認 → 公開
```

### 15-5. Phase方針

- Phase A〜B: 無効
- Phase C: 有効
- スコア閾値はPhase C開始時に調整（親仕様では固定しない）

---

## 16. rewrite_triggers

### 16-1. rank_drop

- 条件: 直近7日の平均順位が前月比3位以上下落
- アクション: 本文追記・改善候補抽出

### 16-2. low_ctr

- 条件: 順位5位以内でCTR3%未満
- アクション: タイトル・ディスクリプション再生成

### 16-3. cannibalization

- 条件: 同一クエリに自サイト2URL以上
- アクション: 主従判定 → 統合 → 301リダイレクト

### 16-4. freshness

- 条件: 外部ソースで新事実を検出
- アクション: 該当セクション追記
- ソース選定ルールはPhase B実装時に別途定義

### 16-5. 安全弁

- 1位記事は原則リライトしない（順位下落リスク回避）
- 表示回数急増中の記事は2週間静観（Googleテスト中の可能性）

### 16-6. Phase方針

- Phase A: 無効
- Phase B: 有効

---

## 17. リスク

### 17-1. 確認済みの事実

- 完全自動化ではなく人間承認を残す方針は、オーケストレーターの安全弁思想と整合する
- 静的ホスティングとの相性は高い

### 17-2. 事実から導ける解釈

- Phase Aではgenerator非導入の方が早く公開できる
- satellitesは中長期施策であり、Phase Aに入れるとスコープが膨張する
- JSON-LDとFAQ構造の早期導入はGEO対応の土台になる

### 17-3. 不確実な点

- GEOの具体的評価ロジックは外部検索事業者依存で変化し得る
- IndexNowの実運用効果は分野・サイト構造により差がある
- satellites運用の費用対効果は実際のコンテンツ供給能力に依存する
- patch_applyがA02_finaリポジトリへ正しく当たるかはPhase 0で検証必要

---

## 18. 禁止事項

- AI量産による低品質コンテンツの公開
- YMYL領域での無根拠な断定
- 法的助言と誤解される表現
- 完全自動公開（人間承認バイパス）
- 正本の複数化
- scope外の実装

---

## 19. リポジトリ構成と配置方針

### 19-1. 制御面（オーケストレーター側）

- docs/sessions/session-*.json
- docs/acceptance/session-*.yaml
- artifacts/session-*/

### 19-2. 実装面（A02_fina側）

- src/templates/ — HTMLテンプレート
- src/pages/ — 生成された記事ページ
- src/assets/css/ — 共通スタイル
- src/snippets/ — JSON-LD等の部品
- docs/roadmap.yaml — Phase定義

### 19-3. 原則

- session定義・acceptance・artifactsはオーケストレーター側に集約する
- A02_fina側にはsrc/配下の生成物とroadmapのみ置く
- 二重配置による正本分裂を防止する

---

## 20. 検証方針

### 20-1. Phase A

- Python 4コマンド（ruff/pytest/mypy/compileall）は不適用
- --skip-checksでchecksステージをスキップする
- 手動検証: HTMLバリデーション、JSON-LDチェック、ブラウザ確認

### 20-2. Phase B以降

- HTMLバリデーション自動化を検討
- Lighthouse CLI導入を検討
- リンク切れチェック導入を検討

---

## 21. session方針

### 21-1. Phase 0（Bootstrap）

- session-bootstrap: patch_apply対象パス検証 + --skip-checks動作確認

### 21-2. Phase A（MVP）

- session-01a: HTML骨格 + CSS + モバイル対応
- session-01b: JSON-LD + OGP + canonical + sitemap方針
- session-02: blueprint生成仕様
- session-03: 軽量クラスター確認
- session-04: HTML出力
- session-05: 公開（デプロイ）

### 21-3. Phase B（運用）

- session-06: Search Console接続仕様
- session-07: rewrite_triggers実装
- session-08: platforms publish target対応
- session-09: title/meta再生成ループ
- session-10: cannibalization判定ルール

### 21-4. Phase C（拡張）

- session-11: knowledge_base定義
- session-12: content_inspector
- session-13: AI本文生成
- session-14: satellites publish
- session-15: freshness trigger

---

## 22. 最終固定事項

以下は本仕様書内で変更しない限り固定とする。

- 3+1層構造
- Phase 0 → A → B → C 移行条件
- session依存順
- 自動の定義6段階
- 本文ポリシー
- 4部隊体制（GPT / Claude / Cursor / 人間）
- publish_targets 3層構造
- リポジトリ配置方針（制御面 / 実装面の分離）

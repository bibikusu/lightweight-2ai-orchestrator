# 6 ヶ月ロードマップ 2026 Q2-Q3

**最終更新**: 2026-05-16
**次回見直し**: 2026-08-16 (四半期)
**用途**: Phase 0-F の月別マイルストーン / 投入時間試算 / 予算規律 / Early Warning Sign 運用
**正本性**: 四半期見直し可、Phase 構造は半年見直しで判定

---

## 0. このファイルの目的

KUNIHIDE 個人事業主 / びくす合同会社が、12 プロジェクト並行運用を達成するための**6 ヶ月実行計画**。

vision-and-principles.md の 4 原則を土台に、月別タイムライン / 投入時間 / AI 自走比率 / 予算規律を具体化する。

**「ブレずに進めたい」**を実現するため、各 Phase の完了条件・Day 14 Hard Gate・凍結審議トリガーを明文化。

---

## 1. 全体構造

### 1.1 Phase 0-F 概要
Month 1 (2026-05-16 〜 2026-06-15)
├─ Phase 0 (Week 1, 2026-05-16 〜 2026-05-22): 凍結処理
└─ Phase A (Week 2-3, 2026-05-23 〜 2026-06-08): 基盤構築
Month 1 後半-2 (2026-06-09 〜 2026-07-15)
└─ Phase B (Week 4-6, 2026-06-09 〜 2026-06-29): A02 深耕
Month 2-3 (2026-06-30 〜 2026-08-15)
└─ Phase C: 3 プロジェクト並行
Month 4 (2026-08-16 〜 2026-09-15)
└─ Phase D: NSFW 共通基盤 + パイロット 1 本
Month 5-6 (2026-09-16 〜 2026-11-15)
└─ Phase E: 12 プロジェクト並行監督業移行
Month 7-12 (2026-11-16 〜 2027-05-15)
└─ Phase F: 安定運用 + 余剰時間で新機能

### 1.2 投入時間と AI 自走比率の推移

| Phase | 期間 | 週投入時間 | 累計時間 | AI 自走比率 | KUNIHIDE 役割 |
|------|------|----------|--------|----------|------------|
| Phase 0 | Week 1 | 20h | 20h | 0% → 10% | 凍結処理 + 規律明文化 |
| Phase A | Week 2-3 | 25h | 70h | 10% → 30% | 基盤構築 + Skills 移植 |
| Phase B | Week 4-6 | 20h | 130h | 30% → 50% | A02 量産パイロット |
| Phase C | Month 2-3 | 20h | 290h | 50% → 70% | 3 並行運用 + A03 dashboard |
| Phase D | Month 4 | 15h | 350h | 70% → 80% | NSFW 共通基盤 + パイロット |
| Phase E | Month 5-6 | 15h | 470h | 80% → 90% | 12 並行監督業 |
| Phase F | Month 7-12 | 8h | 670h | 90% → 95% | 安定運用 + 余剰 |

**累計 670 時間 / 12 ヶ月**。週上限規律: Phase 0-A は 25h まで許容、Phase B 以降は 20h、Phase E 以降は 15h、Phase F は 8h。

---

## 2. Phase 0: 凍結処理 (Week 1, 2026-05-16 〜 2026-05-22)

### 2.1 目的

旧自作 orchestrator (`run_session.py` 227KB) を完全凍結し、新体制 v3 への移行準備を完了する。Z2-Z4 セッションで untracked 整理 + 物理 archive 退避 + 戦略文書正本化を完了。

### 2.2 投入時間: 20h

### 2.3 セッション

| Session | 状態 | 内容 | commit |
|---------|------|------|--------|
| V2-Z0-FREEZE | ✅完了 (2026-05-15) | 旧 orchestrator 凍結 + 判定待ち 4 件打ち切り | 2e7ab36 |
| V2-Z1-A03-ARCH | ✅完了 (2026-05-15) | A03 アーキ確定 + 疎結合契約 | 9cfd281 |
| V2-Z2-INVENTORY | pending | untracked 38 ファイル棚卸し、docs/projects/A01-A10/ 既存中身確認 | - |
| V2-Z3-ARCHIVE | pending | 物理 archive 退避 (orchestrator-frozen-2026-05 ブランチ) | - |
| V2-Z4-STRATEGY-LOCK | pending (本セッション) | 戦略文書 4 ファイル正本化 (vision/roadmap/session-plan/lessons) | - |
| V2-Z5-SKILLS-MIGRATION | pending | 旧 5 層分離を `~/.claude/skills/` に移植 | - |

### 2.4 完了条件

- 旧 `run_session.py` が **7 日連続 touch されない**
- `~/.claude/CLAUDE.md` 新規作成、4 原則明記
- 旧 5 層分離 (session-pre/worker/judge/observation) の責務が Skills に移植完了

### 2.5 Day 14 Hard Gate (2026-05-29)

- 戦略文書 4 ファイル commit/push 完了
- untracked 38 ファイルの分類完了 (削除/archive/継承の 3 区分)
- Skills 移植が完了し、ClaudeCode で 1 セッション自走テストが PASS

### 2.6 凍結審議トリガー

- 旧 orchestrator のソースに何らかの変更が入る
- 「もう少しで orchestrator が動く」発言が出る
- Z2 棚卸しが完了せず Z3-Z5 に進めない状態が 5 日続く

---

## 3. Phase A: 基盤構築 (Week 2-3, 2026-05-23 〜 2026-06-08)

### 3.1 目的

事務所 LLM サーバー (`desktop-s7afe9q` / 100.75.209.57) 上に既製 OSS スタック (n8n + LiteLLM + Directus + PostgreSQL + Ollama) を起動。Claude Code Max 20x 契約、worktree + Builder + Validator パターン確立。

### 3.2 投入時間: 25h (上限規律内)

### 3.3 セッション・タスク

| Step | 内容 | 所要 | 担当 |
|------|------|------|------|
| A-0 | 事務所サーバー SSH 接続診断 (Tailscale 経由 ssh bikus@100.75.209.57) | 1h | KUNIHIDE + ClaudeCode 委任 |
| A-1 | Claude Code Max 20x ($200/月) 契約 | 0.5h | KUNIHIDE |
| A-2 | Cursor Pro ($20) + Copilot Pro ($10) 追加 | 0.5h | KUNIHIDE |
| A-3 | WSL2 `.wslconfig` 設定 (memory=64GB, processors=10) | 1h | ClaudeCode |
| A-4 | docker-compose.yml で n8n + LiteLLM + Directus + PG + Redis + Ollama 起動 | 4h | ClaudeCode |
| A-5 | Ollama に Qwen2.5-Coder-14B Q4_K_M pull、30+ tok/s 確認 | 1h | ClaudeCode |
| A-6 | LiteLLM ルート登録 (commander / advisor / lightweight / nsfw-safe-text) | 2h | ClaudeCode |
| A-7 | LiteLLM fallback 設定 (claude-sonnet → gpt-4o → qwen-coder-local) | 1h | ClaudeCode |
| A-8 | LiteLLM budget 設定 (月上限 $200 / 各ルート $50) | 1h | ClaudeCode |
| A-9 | Directus に 4 collection (projects / sessions / artifacts / early_warning) 作成 | 2h | ClaudeCode |
| A-10 | `~/.claude/CLAUDE.md` + `~/.claude/settings.json` 整備 | 2h | ClaudeCode |
| A-11 | `~/.claude/skills/{session-planner,worker,judge-4axis,reporter}/SKILL.md` 整備 | 3h | ClaudeCode |
| A-12 | `~/.claude/agents/{builder,validator}.md` 整備 | 2h | ClaudeCode |
| A-13 | A02 リポジトリに `.claude/{CLAUDE.md, settings.json, hooks/}` 配備 | 2h | ClaudeCode |
| A-14 | Builder + Validator 3 並列 (tmux + worktree) 試行 | 2h | KUNIHIDE + ClaudeCode |

### 3.4 完了条件

- 事務所サーバーで Docker サンドボックス起動、Tailscale 経由でブラウザから:
  - n8n UI: http://100.75.209.57:5678
  - Directus UI: http://100.75.209.57:8055
  - LiteLLM proxy: http://100.75.209.57:4000
  - Ollama API: http://100.75.209.57:11434
- A02 リポジトリで `claude` 起動 → CLAUDE.md 自動読込 → 1 セッション完走

### 3.5 Day 14 Hard Gate (2026-06-08)

- A02 で sandbox 内 auto-allow + PR review が動く
- Builder + Validator 3 並列で 1 タスク完走
- 承認回数 1 日 30 回以下に下がる (Phase 0 比 70% 削減)

### 3.6 凍結審議トリガー

- 事務所サーバー接続が 3 日確立しない
- Docker 起動が 1 週間達成しない
- Claude Max 20x の月額コストが想定を大幅超過
- LiteLLM budget が 1 週間で $50 超過 (API 暴走兆候)

### 3.7 予算規律

- 月予算上限 ¥40,000
  - Claude Max 20x: $200 (¥30,000)
  - Cursor Pro: $20 (¥3,000)
  - Copilot Pro: $10 (¥1,500)
  - 電気代追加: ¥3,000
  - Backblaze B2: ¥100
  - 合計: 約 ¥37,600
- LiteLLM budget で各ルート月上限自動停止
- 月末に Directus collection でコスト集計

---

## 4. Phase B: A02 深耕 (Week 4-6, 2026-06-09 〜 2026-06-29)

### 4.1 目的

A02_fina (SEO 自動化、最高優先) で動く記事を WordPress 公開し、Builder + Validator パターンで承認 70% 削減を実証する。

### 4.2 投入時間: 20h

### 4.3 セッション (A02 ロードマップ 17 + α)

#### サイト本体 + SEO ツール導入

| Step | 内容 | 所要 |
|------|------|------|
| B-1 | WordPress + Rank Math プラグイン整備 (Xserver 既存) | 2h |
| B-2 | SerpBear Docker 起動、A02 ターゲットキーワード登録 | 2h |
| B-3 | Greenflare Docker 起動 (技術 SEO crawler) | 1h |
| B-4 | GSC Bulk Data Downloader + GA4/Search Console 連携 | 2h |
| B-5 | seomachine (TheCraigHewitt) を A02 用 Skills に fork | 3h |
| B-6 | Ubersuggest MCP 経由のキーワードリサーチ自動化 | 2h |

#### A02 ロードマップ実装

| Session | テーマ | 担当 Skill | 自動化レベル |
|---------|--------|----------|------------|
| A02-04 | 量産 (一括生成) | article-generate | L3 自動 |
| A02-05 | 導線 (投稿用整形) | article-format-wp | L3 自動 |
| A02-06 | vertical 切替 | vertical-template | L2 通知 |
| A02-07 | キーワードマップ + クラスター設計 | keyword-cluster + Ubersuggest MCP | L2 通知 |
| A02-08 | カニバリチェック + 公開順序 | canibalize-check | L3 自動 |
| A02-09 | URL 設計 + ディレクトリ構造 | url-design | **L1 必須承認** |

### 4.4 完了条件

- A02 で動く記事 **1 本** が WordPress に公開、Google Search Console で index 確認
- 承認回数 1 日 20 回以下 (Phase A 比 50% 削減)
- Day 14 Hard Gate クリア

### 4.5 Day 14 Hard Gate (2026-06-22)

- WordPress 公開記事 1 本
- Builder + Validator パターン稼働
- Friday public post に「動く output: YES」初記録

### 4.6 凍結審議トリガー

- Day 14 で記事 1 本も公開できない
- 承認回数が Phase A レベルから減らない
- A02 ロードマップが session-04 で止まる

---

## 5. Phase C: 3 プロジェクト並行 (Month 2-3, 2026-06-30 〜 2026-08-15)

### 5.1 目的

A01 (Card_task SaaS 化) + A02 (記事量産継続) + A03 (dashboard 拡張) の 3 プロジェクト並行運用を確立。A03 dashboard で 12 プロジェクト状態の一覧表示を実現。

### 5.2 投入時間: 20h/週

### 5.3 セッション

#### A02 継続 (session-10 〜 17)

| Session | テーマ | 担当 Skill | 自動化レベル |
|---------|--------|----------|------------|
| A02-10 | 記事ページ HTML 生成 (blueprint から) | article-to-html | L3 自動 |
| A02-11 | E-E-A-T 表記 + 構造化データ + 更新日管理 | eeat-markup + schema-org | L3 自動 |
| A02-12 | sitemap.xml + robots.txt + canonical + OGP | sitemap-generate | L3 自動 |
| A02-13 | Xserver デプロイ + deploy 自動化 | deploy-xserver | **L1 必須承認** |
| A02-14 | GA4 + Search Console 連携 (設定画面) | analytics-setup | **L1 必須承認** |
| A02-15 | リライトスケジュール + 改善優先度判定 | seo-rewrite (定期実行) | L3 自動 |
| A02-16 | AI API 設定基盤 (LiteLLM 経由) | api-config | **L1 必須承認** |
| A02-17 | キュー + スケジューラ (n8n workflow) | scheduler-setup | **L1 必須承認** |
| A02-18 | A02-A03 疎結合接続契約 (API/MCP 仕様) | api-contract | **L1 必須承認** |

#### A01 着手 (別 chat で並行)

| Session | テーマ | 所要 |
|---------|--------|------|
| A01-P0 | validateAppState / showHealthWarning / exportBackupNow | 各 1-2h |
| A01-P1 | rotateBackup / maybeAutoBackup / 5 世代リング | 各 1-2h |
| A01-multi-tenant | 業種別テンプレ抽出、デリヘル/ラーメン屋/不動産で同基盤 | 4-6h |
| A01-saas-skeleton | 課金・認証・サブドメイン分離 | 6-8h |

#### A03 拡張

| Session | テーマ | 所要 |
|---------|--------|------|
| A03-portal | 案A ポータル基本実装 | 4h |
| A03-dashboard-v1 | 12 プロジェクト状態の集約表示 | 6h |
| A03-alerts | 失敗通知 + リソース監視 + コスト集計 | 4h |

### 5.4 完了条件

- A02 記事 5-10 本公開、PV / impressions 計測開始
- A01 P0/P1 完了、SaaS 化への布石完成
- A03 dashboard で 12 プロジェクト一覧表示稼働

### 5.5 Day 14 Hard Gate (各 sprint で設定)

- A02 月間記事数 5+ 本
- A01 で動く feature 2+
- A03 dashboard が KUNIHIDE 自身に役立つ

### 5.6 凍結審議トリガー

- 3 並行が同時に止まる
- A01 マルチテナント設計で 2 週間以上進まない
- 承認回数が Phase B レベルから増える

---

## 6. Phase D: NSFW 共通基盤 + パイロット 1 本 (Month 4, 2026-08-16 〜 2026-09-15)

### 6.1 目的

NSFW 6 プロジェクト (A04/A05/A06/A07/A11/A12) の**共通基盤を物理隔離環境で構築**し、最初のパイロット 1 本 (A05 CAST_PRO 模倣) を着手する。

**修正点**: 元計画「NSFW 6 本立ち上げ」は楽観的すぎる (参謀リサーチ点検結果)。本 Phase は共通基盤 + パイロット 1 本に縮小、残り 5 本は Phase E に分散。

### 6.2 投入時間: 15h/週

### 6.3 セッション

#### NSFW 共通基盤

| Session | テーマ | 所要 |
|---------|--------|------|
| NSFW-D1 | docker-compose.nsfw.yml で物理隔離 network 構築 | 3h |
| NSFW-D2 | 別 Ollama instance + Qwen2.5-Coder-14B 配置 | 2h |
| NSFW-D3 | LiteLLM nsfw-safe-text ルート設定 (Anthropic/OpenAI deny) | 2h |
| NSFW-D4 | 別 PostgreSQL instance + Directus schema 分離 | 3h |
| NSFW-D5 | Tailscale ACL で tag:nsfw を Funnel 不可に | 1h |
| NSFW-D6 | NSFW 共通 CLAUDE.md 雛形 (Anthropic/OpenAI 禁止明記) | 2h |

#### A05 パイロット

| Session | テーマ | 所要 |
|---------|--------|------|
| A05-01 | キャスト管理 DB schema 設計 | 4h |
| A05-02 | UI 雛形 (PHP/MySQL 既存パターン) | 6h |
| A05-03 | キャスト出退勤管理機能 | 6h |
| A05-04 | パイロット動作確認 | 2h |

### 6.4 完了条件

- NSFW 6 プロジェクトすべてが**同じ共通基盤**で動く準備完了
- A05 パイロットで Anthropic/OpenAI 経由 **0 回**
- Qwen フォールバックチェーン実証

### 6.5 Day 14 Hard Gate (2026-08-30)

- NSFW 共通基盤起動
- A05 で動く feature 1 つ
- 規約 NG refusal 0 件

### 6.6 凍結審議トリガー

- Anthropic warning 1 回でも発生
- Qwen が品質要件を満たせない
- NSFW 共通基盤の構築に 3 週間以上かかる

---

## 7. Phase E: 12 並行監督業移行 (Month 5-6, 2026-09-16 〜 2026-11-15)

### 7.1 目的

12 プロジェクト並行運用を確立し、KUNIHIDE は監督業 (PR レビュー + 戦略判断) のみに専念。承認 300 回/月以下 (Phase A の 3,600 比 90% 削減) 達成。

### 7.2 投入時間: 15h/週 (Phase E 後半は 10h 目標)

### 7.3 セッション

#### NSFW 残り 5 本 (A04/A06/A07/A11/A12)

各プロジェクト 8-12 セッション × 5 = 40-60 セッション。共通基盤を流用するため、1 プロジェクトあたり 1-2 週間で着手。

| プロジェクト | 主要セッション | 所要 |
|-----------|--------------|------|
| A11 (ベンリ模倣) | DB schema + UI + 投稿自動化 | 8 セッション |
| A12 (イージーダイヤリー模倣) | 写メ日記 + SNS ハイブリッド | 10 セッション |
| A07 (ポチャデリワーク SEO) | A02 SEO 基盤流用 + 求人特化 | 6 セッション |
| A04 (デリヘル顧客管理 v-up) | 既存改修 + 新機能 | 10 セッション |
| A06 (cecare 全国展開) | UI + 多店舗管理 + 全国検索 | 12 セッション |

#### 動画・データ系 (A08/A09/A10)

| プロジェクト | 主要セッション | 所要 |
|-----------|--------------|------|
| A08 (SNS 短尺動画) | Suno + ナノバナナ + Veo3 連携、SNS 投稿自動化 | 6 セッション |
| A09 (動画マーケ 10 分ロング) | HeyGen/Synthesia 連携、台本生成 | 6 セッション |
| A10 (データ研究) | Jupyter + pgvector でデータクラスタリング | 6 セッション |

#### A03 dashboard 拡張

| Session | テーマ | 所要 |
|---------|--------|------|
| A03-saas-prep | 将来 SaaS 化への布石 | 6h |
| A03-cost-monitor | コスト集計・API 使用量集計 | 4h |
| A03-early-warning | Early Warning Sign の Directus 投入 + アラート | 4h |

### 7.4 完了条件

- 12 プロジェクトすべて active 状態
- 承認回数 1 日 10-15 回以下 (月 300 回以下)
- KUNIHIDE 投入時間 週 10-15h で運用可能

### 7.5 Day 14 Hard Gate

- 各プロジェクトで月 1 本以上の動く output
- Early Warning Sign 赤 0-1 件
- Friday public post 連続 8 週成功

### 7.6 凍結審議トリガー

- 12 プロジェクトのうち 6 本以下しか動かない (戦線縮小判定)
- 承認回数が Phase D レベルから増える
- KUNIHIDE 投入時間が週 20h を超える

---

## 8. Phase F: 安定運用 + 余剰時間で新機能 (Month 7-12, 2026-11-16 〜 2027-05-15)

### 8.1 目的

KUNIHIDE が「**開発者**」から「**経営者**」に戻る。週 8h で 12 プロジェクト並行運用を維持し、余剰時間で経営戦略・新規プロジェクト企画・クライアントワークを行う。

### 8.2 投入時間: 8h/週

### 8.3 主要活動

- Managed Agents Dreaming/Outcomes/Multiagent 検証
- `/team-onboarding` でクライアント引き継ぎ
- Skill marketplace 公開を視野
- 新規プロジェクト企画 (A13+)
- 4 原則の有効性検証 (2027-05-16 年次見直しの準備)

### 8.4 完了条件

- 12 プロジェクトすべて安定運用、月次の維持作業のみ
- KUNIHIDE が監督業 + 経営に専念
- Friday public post で「動く output: YES」が継続

### 8.5 凍結審議トリガー

- 12 プロジェクトのうち 3 本以上が同時に Early Warning 赤
- KUNIHIDE 投入時間が週 15h を超える
- 月予算が ¥50,000 超える

---

## 9. 予算規律

### 9.1 月予算上限: ¥40,000

| 項目 | 月額 (円) | 備考 |
|------|---------|------|
| Claude Code Max 20x | 30,000 | $200/月 |
| Cursor Pro | 3,000 | $20/月 |
| GitHub Copilot Pro | 1,500 | $10/月 |
| 電気代追加 | 3,000 | 事務所サーバー常時稼働 |
| Backblaze B2 (バックアップ) | 100 | 100GB クラス |
| その他予備 | 2,400 | API 一時超過、ドメイン更新等 |
| **合計** | **40,000** | |

### 9.2 自動停止ルール

- LiteLLM budget で各ルート月上限自動停止
- 月予算超過時は KUNIHIDE 司令塔判断で 翌月予算前借り or 一時停止
- API token 1 日上限超過時は **circuit breaker** で全 worktree 停止 (Phase A で実装)

### 9.3 ROI 検証

- 月次 Early Warning Sign 計測時に「投入時間 vs 動く output」を Directus collection で集計
- 四半期見直しで「投資対効果」を経営判断
- 半年で ROI 不明なプロジェクトは凍結審議

---

## 10. Early Warning Sign 月次運用

詳細は lessons-learned.md §4 参照。本ロードマップでは運用スケジュールのみ明記。

### 10.1 計測タイミング

- **毎月末日曜 22:00-23:00** (1 時間枠)
- 全 12 プロジェクト × 8 カテゴリ = 96 セル を Directus に投入

### 10.2 判定ルール

- **緑のみ**: 翌月も継続
- **黄 1-2 個**: 監視継続、翌月再評価
- **赤 1-2 個**: 警告、原因分析
- **赤 3 個以上**: 即 freeze 審議、Friday post で告白

### 10.3 結果の活用

- Friday post に「今週の Early Warning Sign」セクション追記
- 四半期見直しで赤の頻度を集計、スタック見直しの判断材料
- 半年見直しで Phase 計画の修正

---

## 11. 凍結審議プロセス (再発防止)

### 11.1 トリガー

各 Phase の「凍結審議トリガー」セクション参照。共通条件:

- 「もう少しで動く」発言 3 回/週以上
- Day 14 Hard Gate 連続 2 回失敗
- Early Warning Sign 赤 3 項目以上
- 投入時間が上限規律を 2 週連続超過

### 11.2 プロセス

1. **即時停止** (24 時間以内)
2. **原因分析** (lessons-learned.md §1 のフレームに沿って)
3. **3 つの判断オプション**:
   - **継続**: 改善計画あり + Day 14 で動く output 出せる
   - **pivot**: 方針転換、別アプローチ
   - **kill**: 中止、リソース他プロジェクトへ
4. **司令塔判断** (KUNIHIDE 専権)
5. **記録**: lessons-learned.md §2 または §3 に追記

### 11.3 復活手順

lessons-learned.md §5 「復活手順」参照。

---

## 12. 月別マイルストーン (一覧)

| 月 | 主要マイルストーン | Day 14 Hard Gate 内容 |
|---|------------------|--------------------|
| **2026-05** | Phase 0 完了 (Z2-Z5)、Phase A 着手 | 戦略文書 4 ファイル commit/push |
| **2026-06** | Phase A 完了、Phase B 着手 | A02 で WordPress 公開記事 1 本 |
| **2026-07** | Phase B 完了、Phase C 着手 | A02 月間 5+ 本、A01 P0 完了 |
| **2026-08** | Phase C 継続、Phase D 着手 | A03 dashboard 稼働、A02 17 セッション完走 |
| **2026-09** | Phase D 完了、Phase E 着手 | NSFW 共通基盤 + A05 パイロット |
| **2026-10** | Phase E 継続 (NSFW 残り 3 本) | A11 + A12 稼働、承認 600/月 |
| **2026-11** | Phase E 完了、Phase F 着手 | 12 並行運用、承認 300/月 |
| **2026-12** | Phase F: 安定運用 | 月次 Friday post 連続 8 週 |
| **2027-01** | Phase F | 新規プロジェクト企画 (A13+) |
| **2027-02** | Phase F | クライアント引き継ぎ /team-onboarding |
| **2027-03** | Phase F | Skill marketplace 公開準備 |
| **2027-04** | Phase F | 4 原則の有効性検証 |
| **2027-05** | 年次見直し | vision-and-principles.md v2 判定 |

---

## 13. 参照リソース

- vision-and-principles.md (永久固定、4 原則)
- lessons-learned.md (過去事故 + 再発防止)
- session-plan.yaml (80-100 セッション ±30%)
- 参謀リサーチ artifact: `wf-4acc611a-0950-4df3-bc11-8fa709eec1ba` (2026-05-16)
- A02 ロードマップ (A02 専用 chat で進行中)
- A03 アーキ: `/Users/kunihideyamane/AI_Team/projects/A03_mane_bikusu/docs/architecture-v2.md`
- A02-A03 疎結合契約: `/Users/kunihideyamane/AI_Team/projects/A03_mane_bikusu/docs/a02-decoupling-contract.md`

---

## 14. このファイルの更新ルール

### 14.1 四半期見直し (3 ヶ月ごと)

- Phase の進捗確認、月別マイルストーン更新
- 投入時間実績の振り返り
- 予算実績 vs 予算計画の比較
- 次四半期の Phase 内容調整

### 14.2 半年見直し (6 ヶ月ごと)

- Phase 構造の大幅修正可
- 12 プロジェクト優先順位の再判定
- AI モデル切替判定 (Sonnet → Opus 等)
- 並列数調整

### 14.3 整合性

- vision-and-principles.md §3 と本ファイル §1 は同じ 12 プロジェクト構成、矛盾させない
- session-plan.yaml の Stage 構造と本ファイル §2-7 の Phase 構造を 1:1 対応
- 衝突時は vision-and-principles.md > 本ファイル > session-plan.yaml の優先順位

---

**END OF FILE**

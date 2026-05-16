# びくす合同会社 開発ビジョン・原則 v1

**最終更新**: 2026-05-16
**次回見直し**: 2027-05-16 (年次)
**起草経緯**: 2026-04 旧 orchestrator 1ヶ月凍結後の体制 v3 確定、参謀リサーチ artifact (wf-4acc611a) 反映
**正本性**: 本ファイルは「永久固定」階層 L1 に属する。4 原則は年次見直し以外で変更しない。

---

## 0. このファイルの目的

KUNIHIDE 個人事業主 / びくす合同会社が、AI 自走開発を**持続可能に**運用するための核心原則を明文化する。

過去 1ヶ月の自作 orchestrator 凍結を**二度と繰り返さない**ための予防接種としての位置付け。「ブレずに進めたい」を技術的に保証する。

このファイルが指す内容と現実の運用に乖離が生じた場合、**まず疑うのは現実の運用**であり、本ファイルではない。

---

## 1. 4 原則 (永久固定)

これらは AI ツール・OSS・モデルが世代交代しても変えない**変えない 4 原則**である。

### 原則 1: 規律は自作、ツールは既製

**意味**: KUNIHIDE が時間を投じるべきは「規律」(=何をやらないか・誰の責任か) であり、「ツール」(=実装機械) ではない。

**自作するもの**:
- 規律 (14 キー JSON 仕様書 / 4 軸 review_points / sealed stash 不触原則 / failure_type 分類)
- CLAUDE.md (各プロジェクトの現場入口)
- ドメイン固有 Skills (`.claude/skills/*/SKILL.md`)
- Validator Sub-agent (4 軸検証など)
- Early Warning Sign チェックリスト

**自作しないもの**:
- orchestrator 本体 → n8n (workflow OSS)
- dashboard → Directus admin UI
- LLM gateway → LiteLLM
- queue manager → n8n queue
- LLM 推論 → Claude Code / Ollama
- DB → PostgreSQL
- sandbox → Docker / git worktree

**過去の違反**: 2026-04-05 月、`run_session.py` (227KB) を自作し続け、結果凍結。これを根拠とする原則。

**違反検出**: ツール側 commit 比率が月 60% 超えたら警告、80% 超えたら凍結審議。

---

### 原則 2: 2 週間 Hard Gate

**意味**: いかなるプロジェクト・セッション群も、着手から **Day 14 までに「人間が使える output」を出す**こと。出ない場合は pivot または kill 強制。

**「動く output」の定義**:
- ユーザーが触れるサイト / ページ / 機能 (UI または API)
- 公開・販売・運用に投入可能な状態
- 内部ツール改善は「動く output」に**カウントしない**

**Day 14 で動かない場合**:
- 設計を疑う、要件を疑う
- 「もう少しで動く」「あと一層」は**禁句**として認知し、即停止
- pivot (方針転換) か kill (停止) を **Day 15 までに判断**

**過去の違反**: 2026-04 〜 05-15 の 1ヶ月、Day 14 Hard Gate なしで orchestrator 開発継続、結果凍結。

**運用**: 毎セッション起票時、`day_14_check` をスケジュールに明示記録 (session-plan.yaml の `hard_gate_date` フィールド)。

---

### 原則 3: Sandbox-First 例外なし

**意味**: AI agent (Claude Code / ClaudeCode headless / Cursor / 自作スクリプト等) は、**全て sandbox 内で動かす**。本番ホスト / main branch / production DB への直接アクセスを許さない。

**Sandbox の具体定義**:
- **コード**: `git worktree` で物理分離した一時 directory (`.claude/worktrees/<name>/`)
- **環境**: Docker container または devcontainer
- **DB**: dev DB のみ accessible、production DB は credential 物理分離
- **ファイル**: `.env`、`secrets/`、production config は agent から read 不可

**例外**:
- なし。「ちょっとだけ」「テストだから」「自分だから安全」は全て却下。

**過去の違反予防**:
- 2025-07 Replit AI: vibe coding 9 日目で production DB 全削除 + 4000 件偽データ隠蔽
- 2025-07 Gemini CLI: read-after-write verification 不在で全ファイル上書き消失

**運用**: 
- 全 12 プロジェクトで `.claude/settings.json` の `permissions.deny` に production DB / `.env` / `git push --force` を強制登録
- `.claude/hooks/pre_tool_use.sh` で危険コマンド (`rm -rf` / `sudo` / `curl|sh`) を exit 2 で block
- NSFW 6 プロジェクトは別 docker network (`nsfw-isolated`) で**物理隔離**

---

### 原則 4: 1 chat = 1 project

**意味**: KUNIHIDE が AI と議論する Claude Web の 1 chat は、1 つのプロジェクト (A01-A12 のいずれか、または横断戦略) に限定する。**1 chat 内で複数プロジェクトを混在させない**。

**理由**:
- path 誤認 (A01 と A02 を取り違える)
- git add 事故 (異なる repo に commit)
- deploy 誤爆 (A02 を A01 にデプロイ)
- context 汚染 (議論ストリームが破綻、AI 判断が低下)

**運用**:
- 1 chat の冒頭で「**このチャットは A02 専用**」と明示
- 別プロジェクトの話題が出たら「**別 chat で**」と即断
- 横断戦略議論は「**全体戦略 chat**」に集約 (本 chat がそれ)

**過去の事例**: 2026-05-15 までは比較的守られていたが、明文化されていなかった。本日以降は原則として固定。

---

## 2. 体制 v3 (固定)

2026-05-15 確定の AI チーム構造。GPT 司令塔チームは**外し**、KUNIHIDE が人間司令塔となる体制。

### 2.1 役割分担

| 役割 | 担当 | 権限 |
|------|------|------|
| **司令塔** | KUNIHIDE (人間) | 最終判断 / 思想 / 優先順位 / main merge / push / deploy |
| **参謀** | Claude Web | 戦略議論 / 差分分析 / selfcheck / 提案 |
| **現場実装** | ClaudeCode | sandbox 内実装 / 4-gate 検証 / Skills 実行 |
| **施工** | Cursor | UI 修正 / 対話的微調整 |
| **マーケ・音楽** | Gemini + Suno/Udio | 作詞 / 楽曲 / SEO 補助 |

### 2.2 越権禁止

- **司令塔の領域**: 価値判定 / 優先度 / リスク受容 / 規約解釈 / 戦略方針 → KUNIHIDE 専権
- **参謀の領域**: 客観事実 / 差分分析 / 過去事例参照 / 推奨提示 → 参謀責任
- **現場の領域**: 実装 / テスト / artifact 生成 / Skills 実行 → ClaudeCode 責任
- **参謀の越権パターン**: 「これが業界標準です、採用しましょう」と価値判定するのは越権

### 2.3 approval_default 原則

KUNIHIDE の脳リソースを節約するため、「**進めてよい**」を基本とする。司令塔判定が必要なのは:

- 価値判定 (やる / やらない / 優先順位)
- 規約解釈 (NSFW 領域への参入可否等)
- 不可逆な action (main merge / push / deploy / DB migration)
- 月次 / 四半期 / 半年の見直し

**それ以外は参謀・現場の責任で進める**。1 つのアクションごとに承認を求めない。

---

## 3. 12 プロジェクト (確定)

2026-05-15 棚卸し結果。全 12 プロジェクトの位置づけ + NSFW 分離方針。

### 3.1 SFW 6 プロジェクト (Anthropic / OpenAI API 利用可)

| ID | 名称 | 概要 | 状態 |
|---|------|------|------|
| A01 | Card_task | タスク管理 SaaS (業種横断、デリヘル/ラーメン屋/不動産で同基盤) | active、task.bikusu.net 稼働中 |
| A02 | fina | SEO 自動化 (金融→不用品回収→美容へ横展開可、最高優先) | active、別 chat で進行中 |
| A03 | mane_bikusu | 並行管理 UI / ポータル (案A 確定) | active、commit 4795e1f |
| A08 | SNS 短尺動画 | AI 画像/動画生成で SNS マーケ | idle |
| A09 | 動画マーケ | 10 分ロング動画研究 (A08 と境界探索中) | idle |
| A10 | データ研究 | 蓄積データのコンテンツ化研究 (スコープ未確定) | idle |

### 3.2 NSFW 6 プロジェクト (Anthropic / OpenAI 経由禁止、自社 LLM 必須)

| ID | 名称 | 概要 | 状態 |
|---|------|------|------|
| A04 | deli_customer_management | デリヘル顧客管理 v-up | active |
| A05 | CAST_PRO | キャストPro 模倣の独自実装 | active |
| A06 | cecare | 障害者向けデリヘル全国展開 | paused |
| A07 | ポチャデリワーク | 風俗求人 SEO | idle |
| A11 | ベンリ模倣 | 風俗媒体更新ツール | idle |
| A12 | イージーダイヤリー模倣 | 写メ日記 + SNS ハイブリッド | idle |

### 3.3 NSFW 領域の特殊運用

- **物理隔離**: 別 docker network (`nsfw-isolated`) + 別 PostgreSQL instance + 別 Ollama instance
- **LLM ルート**: LiteLLM で nsfw-safe-text routeのみ allow、Anthropic / OpenAI 直接呼出は deny
- **モデル**: Qwen2.5-Coder-14B Q4 (Apache-2.0、出力制限なし、商用利用 OK)
- **Tailscale ACL**: `tag:nsfw` を Funnel 不可に
- **戦略**: 正規 LLM 挑戦 → 規約 NG なら自社 Qwen フォールバック

### 3.4 プロジェクト間の依存

- **A03** は他 11 プロジェクトの状態を**読み取り専用 API 経由**でのみ参照
- **A02 ↔ A03**: 疎結合 5 要件 (DB schema 隔離 / n8n workspace 分離 / LiteLLM ルート別建て / read-only API / Google Cloud Project 独立) — 2026-05-15 確定
- **A01-A12 横断**: 各プロジェクト独立、強い結合を避ける

---

## 4. 禁句リスト (運用上の警鐘)

これらのフレーズが KUNIHIDE 自身または AI の発言に出たら、**即停止して立ち止まる**シグナル。

| 禁句 | 出る場面 | 即時アクション |
|------|---------|-------------|
| 「もう少しで動く」 | Day 14 Hard Gate 直前 | 即 Stop、pivot 検討 |
| 「あと一層追加すれば」 | メタ開発沼の兆候 | 実装距離測定、5層以上なら凍結 |
| 「自分で作ったほうが早い」 | OSS 評価をサボった時 | 既製品 3 つ評価義務 |
| 「orchestrator を完璧にしてから」 | 本業着手の先延ばし | 「規律自作・ツール既製」原則違反 |
| 「sandbox 設定は後で」 | Sandbox-First 違反 | 即停止、設定完了まで実装禁止 |
| 「テストは動いてから書く」 | 4-gate 規律違反 | テスト先 |
| 「ちょっとだけ main で」 | Sandbox-First 違反 | 即停止 |
| 「みんなやってる」 | 業界標準を理由に判断放棄 | KUNIHIDE 思想を再確認 |
| 「業界標準に従いましょう」 | AI の越権 (価値判定) | 司令塔判定要求に変換 |

---

## 5. 過去の凍結事例 (詳細は lessons-learned.md)

### 5.1 1ヶ月 orchestrator 凍結 (2026-04 〜 2026-05-15)

**概要**: 自作 `run_session.py` (227KB) を 1ヶ月以上開発、結果 2026-05-15 に凍結。

**構造的原因**: 「規律は自作、ツールは既製」原則の違反 (規律と orchestrator 両方を自作した)。

**業界での同型事例**: AutoGPT (2024/7 ノーコード化)、BabyAGI (2024/9 archive)、LangChain (BuzzFeed/Max Woolf 放棄)、Robin Wieruch ソロ microservices 失敗。

**学び**: 認知の分離 (session-pre/judge/observation) は正しい直観だった、failure は運搬手段 (自作 orchestrator) であって設計思想ではない。

### 5.2 業界での 2025-2026 主要事故

| 事故 | 損害 | 原因 |
|------|------|------|
| 2025-07 Replit AI | production DB 全削除 + 4000 件偽データ隠蔽 | Sandbox-First 違反 |
| 2025-07 Gemini CLI | 全ファイル上書き消失 | read-after-write verification 不在 |
| 2026-03 LiteLLM 1.82.7/1.82.8 | サプライチェーン攻撃 | pin なし運用 |
| 2026-04 Axios npm | 100M downloads 経由 RAT 配布 (89 秒で C2 接続) | Approval Fatigue |

**学び**: Sandbox-First 例外なし、pin 運用、Approval Fatigue 対策の 3 つは絶対。

---

## 6. 月次 / 四半期 / 半年 / 年次 見直しサイクル

### 6.1 月次 (毎月末日曜 22:00-23:00)

- Early Warning Sign 8 カテゴリ計測 → Directus 投入
- 3 項目以上「赤」のプロジェクトは即 freeze 審議
- session-plan.yaml の status 更新

### 6.2 四半期 (3 ヶ月ごと)

- 技術スタック見直し (新 OSS 評価、契約プラン)
- roadmap-2026.md の Phase 内容更新
- AI モデル切替判定 (Sonnet → Opus 等)
- 並列数調整

### 6.3 半年 (6 ヶ月ごと)

- 戦略全面見直し (1 日)
- 12 プロジェクト優先順位の再判定
- Phase 計画の大幅修正可
- 年次予算の中間レビュー

### 6.4 年次 (1 年ごと、2027-05-16 次回)

- **4 原則の有効性検証** (KUNIHIDE 司令塔判定)
- 過去 12 ヶ月の凍結 / 事故事例追記
- vision-and-principles.md v2 への昇格判定

---

## 7. このファイルの正本性ルール

### 7.1 変更不可

- 4 原則 (§1) は年次見直し以外で変更しない
- 体制 v3 (§2) の役割分担構造は年次以外で変更しない
- 過去の凍結事例 (§5) は事実として削除しない (修正/追記のみ可)

### 7.2 変更可

- 12 プロジェクトの状態 (active / paused / idle) は月次更新可
- 禁句リスト (§4) は月次運用で追加可、削除は半年見直しで判定
- 見直しサイクル (§6) は半年で見直し可

### 7.3 衝突時の優先順位

本ファイル ↔ 他文書で衝突した場合の優先順位:

1. **本ファイル (vision-and-principles.md)** — 最高
2. docs/strategy/roadmap-2026.md
3. docs/strategy/session-plan.yaml
4. docs/strategy/lessons-learned.md
5. CLAUDE.md (各 repo root)
6. docs/master_instruction.md (v1 凍結マーク済、参考のみ)
7. docs/global_rules.md (v1 凍結マーク済、参考のみ)
8. 個別 session JSON

---

## 8. 参照リソース

- 参謀リサーチ artifact: `wf-4acc611a-0950-4df3-bc11-8fa709eec1ba` (2026-05-16 実施)
- 完了済セッション: V2-Z0-FREEZE (commit 2e7ab36)、V2-Z1-A03-ARCH (commit 9cfd281)
- A03 アーキ: `/Users/kunihideyamane/AI_Team/projects/A03_mane_bikusu/docs/architecture-v2.md`
- A02-A03 疎結合契約: `/Users/kunihideyamane/AI_Team/projects/A03_mane_bikusu/docs/a02-decoupling-contract.md`

---

**END OF FILE**

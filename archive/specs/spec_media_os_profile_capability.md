# ジャンル切替型メディアOS — 環境プロファイル・Capability 正本候補（§9–11）

本書は環境プロファイル・Capability・対応表の正本候補である。実装・API・受入は本書の `profile_id` / `capability_id` を正とする。

---

## 9. 環境プロファイル表

### 目的

環境差に応じて、利用可能な機能群・接続先・運転モードを切り替えるための基準を定義する。

### 方針

- 仕様はフルで持つ
- 実行可否は profile で切り替える
- profile は capability の集合として定義する

### profile 一覧

| profile_id | profile_name | 想定環境 | 方針 |
|---|---|---|---|
| basic | Basic | 外部連携が弱い / 仮運用 / 初期導入環境 | 最低限の手動運用で成立させる |
| standard | Standard | 一部外部連携あり / 標準運用環境 | 管理画面中心に運用を安定させる |
| full | Full | 外部連携・計測・導線が十分整う環境 | フル仕様で運転する |

### profile ごとの考え方

#### basic

- KPIは仮データまたは手動投入前提
- 外部公開先連携なし
- LINEはURLまたは固定テンプレ中心
- テンプレ複製はガイド付き中心
- 守備は警告必須、blockは環境次第

#### standard

- KPIはGA4等の一部連携可能
- LINEはテンプレメッセージ運用可能
- テンプレ複製はガイド付き + 一部自動候補
- 公開統制は標準強度

#### full

- KPIはSearch Console + GA4等を想定
- LINEは分岐シナリオまで可能
- テンプレ複製は自動差し替えを有効化可能
- 外部公開や高度導線も接続可能

### profile 運用原則

- profile は tenant / project / deployment のいずれかの単位で設定する
- Phase1では project 単位を推奨
- 将来的に tenant 単位へ拡張可能とする

---

## 10. Capability一覧表

### 目的

環境差で切り替える機能単位を明確化する。

### 命名方針

- capability は「1つの機能責務」で切る
- UI表示可否、外部接続可否、処理強度を capability で管理する
- capability は増やしすぎず、運用判断できる粒度で固定する

### capability 一覧

| capability_id | 区分 | 説明 | Phase1必須 | 備考 |
|---|---|---|---|---|
| content.article_core | core | 記事作成・編集・保存 | ○ | 全profile共通 |
| content.review_required | core | 全記事レビュー必須 | ○ | 全profile共通 |
| publish.admin_only | capability | adminのみ公開可 | △ | 環境で切替 |
| publish.admin_operator | capability | admin + operator公開可 | △ | 環境で切替 |
| template.duplicate_guided | capability | 複製 + 差し替えガイド | ○ | 初期推奨 |
| template.duplicate_auto | capability | 複製 + 自動差し替え | × | 後段拡張 |
| line.url_only | capability | URL導線のみ | ○ | 最低限導線 |
| line.message_template | capability | メッセージテンプレ付き導線 | ○ | Phase1推奨 |
| line.branching | capability | 分岐シナリオ導線 | × | 後段拡張 |
| rules.warn | core | 禁止/注意表現の警告表示 | ○ | 全profile共通推奨 |
| rules.block_publish | capability | unresolved時にpublish block | ○ | 守備上強く推奨 |
| rules.auto_fix | capability | 自動修正候補または自動修正 | × | 後段拡張 |
| kpi.mock_data | capability | 仮データでKPI表示 | ○ | 初期導入可 |
| kpi.ga4 | capability | GA4取得 | × | 接続環境依存 |
| kpi.search_console | capability | Search Console取得 | × | 接続環境依存 |
| cv.line_registration | capability | LINE登録をCVとして計測 | ○ | 環境で有効化 |
| cv.form_submission | capability | フォーム送信をCVとして計測 | ○ | 環境で有効化 |
| publish.external_wp | capability | WordPress連携公開 | × | Phase2相当 |
| publish.external_headless | capability | 独自CMS/Headless連携公開 | × | Phase2相当 |
| dashboard.kpi_basic | core | 基本KPI表示 | ○ | CTR/遷移率/CV率 |
| dashboard.kpi_extended | capability | 詳細分析表示 | × | BI前提は後段 |
| plugin.extension_slot | capability | plugin拡張枠 | ○ | 将来追加口 |

### capability 設計原則

- core は原則全profile有効
- capability は profile ごとに有効/無効
- Phase1で未実装 capability は「定義だけ保持」でもよい
- API / UI / acceptance は capability 単位で紐づける

---

## 11. Profile-Capability対応表

### 目的

どの環境プロファイルで、どのcapabilityを有効化するかを明確化する。

### 対応表

| capability_id | basic | standard | full | fallback |
|---|---|---|---|---|
| content.article_core | ON | ON | ON | なし |
| content.review_required | ON | ON | ON | なし |
| publish.admin_only | ON | OFF | OFF | 権限不足時は非表示 |
| publish.admin_operator | OFF | ON | ON | 非対応時はadmin運用へ縮退 |
| template.duplicate_guided | ON | ON | ON | 手動コピーへ縮退 |
| template.duplicate_auto | OFF | OFF | ON | guidedへ縮退 |
| line.url_only | ON | ON | ON | 手入力URL運用 |
| line.message_template | OFF | ON | ON | URLのみ表示 |
| line.branching | OFF | OFF | ON | message_templateへ縮退 |
| rules.warn | ON | ON | ON | なし |
| rules.block_publish | OFF | ON | ON | warnのみでレビュー強化 |
| rules.auto_fix | OFF | OFF | ON | 警告表示のみ |
| kpi.mock_data | ON | OFF | OFF | 手動投入または空表示 |
| kpi.ga4 | OFF | ON | ON | mockまたは未接続警告 |
| kpi.search_console | OFF | OFF | ON | GA4のみ表示 |
| cv.line_registration | ON | ON | ON | 総CVから除外可 |
| cv.form_submission | ON | ON | ON | 総CVから除外可 |
| publish.external_wp | OFF | OFF | ON | 内部公開ステータスのみ |
| publish.external_headless | OFF | OFF | ON | 内部公開ステータスのみ |
| dashboard.kpi_basic | ON | ON | ON | なし |
| dashboard.kpi_extended | OFF | OFF | ON | basic表示のみ |
| plugin.extension_slot | ON | ON | ON | スロットのみ保持 |

### fallback 原則

- capability が OFF の場合は、原則として以下のいずれかを適用する
  - 画面非表示
  - read-only表示
  - 縮退モードへ切替
  - 未接続警告表示
- fallback は APIエラーではなく、運用可能な代替挙動にする

### Phase1推奨初期値

- 初期標準プロファイルは `standard`
- 実証環境や仮導入は `basic`
- 外部連携・自動差し替え・分岐導線が整った環境のみ `full`

### 実装上の扱い

- profile は DB設定値として保持
- capability 判定は backend で一元化
- frontend は capability を受けて表示制御する
- acceptance は profile 別に分岐可能な形で記述する

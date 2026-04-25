
---

## BACKLOG-CROSS-DEPLOY-RSYNC-001(横断サマリ)
**起票日**: 2026-04-25
**起票元**: A03 session-a03-dashboard-v1-impl-001
**詳細参照**: `projects/A03_mane_bikusu/docs/BACKLOG.md` BACKLOG-A03-DEPLOY-001
**カテゴリ**: 運用 / 共通デプロイルール
**影響範囲**: A02_fina, A03_mane_bikusu, A04_deli_customer_management(mane.bikusu.net / 同サーバー配下)

### サマリ
- `rsync --exclude` で `data/` を除外する運用パターンが「ローカルbuildと本番の非対称」を生む
- 共通運用ルールとして「コード同期と data 同期を分離する」を全プロジェクト標準化すべき

### Action
- 共通 deploy 雛形(仮: `templates/deploy.sh.tmpl`)に「data同期分離」「sha256照合」を組み込む
- A02/A04 でも同サーバー運用のため事前に方針共有

---

## BACKLOG-CROSS-AC-BUILD-PREDICTION-001(横断サマリ)
**起票日**: 2026-04-25
**起票元**: A03 session-a03-dashboard-v1-impl-001
**詳細参照**: `projects/A03_mane_bikusu/docs/BACKLOG.md` BACKLOG-A03-AC-REVISION-001
**カテゴリ**: 仕様生成パイプライン / AC設計
**影響範囲**: 全プロジェクト(acceptance_yaml_generate.md を共有するため)

### サマリ
- AC生成時に「ビルド後の出力構造」を予測する仕組みが現テンプレに不在
- React + Vite 系(A03/A02/A04 想定)では `public/data/` → `dist/data/` の慣習を AC に反映すべき

### Action
- `docs/templates/acceptance_yaml_generate.md` に「ビルド後出力構造予測」セクション追加(別session起票要)
- AC を「論理パス」「物理パス」2層で記述する記法導入の検討
- 改修session起票は本BACKLOG確定後

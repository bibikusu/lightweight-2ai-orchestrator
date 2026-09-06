# プロジェクト ダッシュボード
> UIで進捗確認するための参照ドキュメント。
> 実装・ファイル変更はClaude Codeで行い、完了後にstate.jsonを更新する。
> 最終更新: 2026-05-06

---

## ステータス凡例
| status | 意味 |
|---|---|
| `active` | 進行中 |
| `paused` | 一時停止（再開予定あり・設計は完成） |
| `idle` | 未着手 |
| `done` | 完了 |

---

## プロジェクト一覧

| ID | 名前 | status | next_action |
|---|---|---|---|
| A01 | Card Task Management | paused | phases_sessions.jsonのPhase1-A（PIN認証）から実装再開 |
| A02 | fina（SEO運用OS） | active | AUTH分離バックログ解消後にパイプライン再開 |
| A03 | mane.bikusu.net | active | ID移行（A03-ID-MIGRATION-001）→ dashboard実装 |
| A04 | deli顧客管理 | active | 即姫statusAPI → 口コミ → キャスト → メルマガ の順で実装 |
| A05 | CAST PRO | active | 脱プラグイン化のロードマップ策定 |
| A06 | cecare | paused | 障がい者向け新規事業の要件定義 |
| A07 | Pochadeli Work | idle | 要件定義が必要 |
| A08 | AI Video Creation | idle | コンセプト定義が必要 |
| A09 | AI Movie Production | idle | 要件定義が必要 |
| A10 | fina_date | idle | A02との関係性を整理 |

---

## オーケストレーター自体の進捗

| 項目 | 状態 |
|---|---|
| 最新セッション | session-179-pre（VCER/RBプロモーション仕様） |
| 現フェーズ | phase-mc（Minimum Complete） |
| 直近完了 | session-177: step0_check.sh実装 / session-176: new_session.sh実装 |
| 次の実装 | session-174-pre（Decision Engine完成形）の実装着手 |

---

## 横断バックログ（要対応）

| ID | 内容 | 影響プロジェクト | 優先度 |
|---|---|---|---|
| AUTH-REQUIREMENTS-SEPARATION-001 | auth/+requirements.txtのstash退避を正式レーン化 | A02 | 高 |
| CROSS-DEPLOY-RSYNC-001 | rsync運用ルール共通化（data同期分離） | A02, A03, A04 | 中 |
| A03-ID-MIGRATION-001 | data/projects.jsonのIDを正本ID（A01〜A10）に統一 | A03 | 中 |
| CROSS-AC-BUILD-PREDICTION-001 | ACテンプレにビルド後出力構造予測を追加 | 全プロジェクト | 低 |

---

## ハイブリッド運用ルール

### UIでやること（claude.ai）
- このDASHBOARD.mdを貼り付けて進捗確認・優先度議論
- 次にやるプロジェクトの方針・設計の相談
- バックログの整理・優先度判断

### Claude Codeでやること
- 実装・修正・テスト
- 完了後に `docs/projects/{ID}/state.json` を更新
- 横断課題は `docs/BACKLOG.md` に追記

### セッション開始の型
```
「[プロジェクトID] + やること」で会話を始める
例：A04 + 即姫ステータスAPI実装
→ Claude CodeがそのプロジェクトのCLAUDE.md + state.jsonを読んで文脈補完
```

### state.json更新タイミング
- セッション完了時：`status` / `last_session` / `next_action` / `updated_at` を更新
- ブロッカー発生時：`blockers` に追記
- UIで方針変更した後：`notes` に変更内容を記録

---

## state.jsonの場所
```
docs/projects/{project_id}/state.json
```

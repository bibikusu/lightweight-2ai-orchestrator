# NEW-CREF — compact_reference_format（future_proposal）

**Status**: future_proposal（仕様未策定 / 本 wave 不採用）  
**Recorded at**: 2026-05-10  
**Recorded by**: 司令塔（GPT）→ 参謀（Claude Web）→ repo 記録  
**Scope of this document**: 提案受領記録のみ。仕様策定権は司令塔に留保。

---

## 1. 提案の背景

現在の運用において、以下のコストが顕在化している。

- chat 跨ぎ時の context 再構築コスト（毎 chat で同じ前提を再投入）
- AI 間（GPT ↔ Claude Web ↔ ClaudeCode）の context コピペ量増大
- commander の「人間 router」負荷
- session_id / phase_id / commit hash / 参照 docs の手動管理コスト

これらの根本原因は、**長大 context を毎回フルテキストで運搬していること**である。

---

## 2. 提案の正体

NEW-CREF は単なる「短縮 ID 表記ルール」ではなく、本質的には **運用上の context 圧縮方針**の設計である。実装すると以下が必要になる:

- context loader
- state sync
- agent routing

これらは現在の governance_pack_v0.1_traffic_control の scope を完全に超える。

---

## 3. 本 wave で採用しない理由

1. **scope 超過**: context loader / context engine / state sync / agent routing は現在の governance_pack_v0.1_traffic_control の scope を完全に超える。
2. **wave 規律違反**: 1 wave = 3〜4 session 規律により、Wave Now（NEW-MEMO / NEW-A2 / NEW-F+A1）と並走させるべきではない。
3. **仕様策定権**: NEW-CREF の仕様策定は司令塔（GPT）の領域であり、ClaudeCode へ仕様策定を委譲すると handoff_artifact.v2 拡張提案と同型の scope 暴走を招く。
4. **運用データ不足**: governance_pack_v0.1_traffic_control が稼働して初めて「何を圧縮すべきか」の実データが取れる。データなしに仕様を切ると空想設計になる。

---

## 4. 再評価条件（再起票ゲート）

NEW-CREF は以下が**全て**満たされた時点で、司令塔（GPT）が改めて仕様策定する:

- [ ] Wave Now（NEW-MEMO / NEW-A2 / NEW-F+A1）が main に着地
- [ ] Wave Next（NEW-B）が main に着地
- [ ] governance_pack_v0.1_traffic_control の実稼働データが3 wave 分以上蓄積
- [ ] 司令塔（GPT）が再評価を明示的に宣言

---

## 5. 本ドキュメントが定めること / 定めないこと

**定めること:**

- 提案の存在と背景の記録
- 本 wave で採用しない理由
- 再評価条件

**定めないこと:**

- compact_reference の具体的な schema
- 圧縮アルゴリズム / parser / resolver
- 実装方針
- データ構造

これらは再評価時に司令塔（GPT）が改めて起草する。

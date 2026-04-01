# セッション後作業

## STEP1 差分確認
git diff --name-only
git status --short -u

## STEP2 1秒判定
- session_id 正しい
- changed_files 正しい
- acceptance_results 構造OK
- typecheck/build OK
- risks/open_issues 非空

## STEP3 現物確認
cat artifacts/.../report.json
grep pytest requirements.txt

## STEP4 コミット
git add <必要ファイルのみ>
git commit -m "session-XX"

---

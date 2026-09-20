---
id: CHG-EVIDENCE-INTEGRITY
kind: change
scope: [DETAIL-DEVELOPMENT]
tdd:
  runner: node
  test_roots: [tests/unit/evidence-integrity.test.mjs]
---

# 検証結果の整合性

成功を宣言するJSONだけで確認記録を通せる不足を再現する。実行ログ、RedとGreen、テスト内容、変更票の一致を検査する。
改ざんできない認証基盤ではなく、欠落と古い証拠を検出するための検査である。

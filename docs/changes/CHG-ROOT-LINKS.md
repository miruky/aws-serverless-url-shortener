---
id: CHG-ROOT-LINKS
kind: change
scope: [DETAIL-DEVELOPMENT]
tdd:
  runner: node
  test_roots: [tests/unit/root-links.test.mjs]
---

# READMEもリンク検査へ含める

docs配下だけでなく、README・AGENTS・貢献手順・変更履歴・セキュリティ方針からのローカルリンク切れも拒否する。

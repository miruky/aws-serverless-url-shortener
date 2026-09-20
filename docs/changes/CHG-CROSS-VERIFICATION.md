---
id: CHG-CROSS-VERIFICATION
kind: change
scope: [DETAIL-DEVELOPMENT]
tdd:
  runner: node
  test_roots: [tests/unit/cross-verification.test.mjs]
---

# 分野をまたぐテストの変更伝播

別の設計文書が所有するテストでも、verifiesで参照する要件と、その要件の下位設計へ変更を伝播させる。
グラフに線があるだけで、入力ハッシュへ含まれていなかった不足を修正する。

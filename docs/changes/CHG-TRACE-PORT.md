---
id: CHG-TRACE-PORT
kind: change
scope: [DETAIL-DEVELOPMENT]
tdd:
  runner: node
  test_roots: [tests/unit/python-cache.test.mjs]
---

# 文書依存グラフの移植

既存のNode製グラフを再利用する。Pythonの実行後に生成されるbytecodeを未管理ソースと誤認する問題を回帰テストで修正する。
要件・設計・実装・テストの変更伝播、未管理ファイル、循環、理由のない確認を既存のハーネステストで再検証する。
移植した一般機能の初回検証と、このPython対応のRed/Greenを区別する。

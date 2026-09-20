---
id: CHG-API-BOUNDARIES
kind: change
scope: [DETAIL-API]
tdd:
  runner: pytest
  test_roots: [tests/regression/test_api_boundaries.py]
---

# URLとHTTP応答の境界条件

国際化URLのLocationをASCIIへ正規化し、旧レコードの省略フィールド、HEADの空本文、画面で表示可能な日付・バージョン数値の範囲を検証する。
作成できても転送や一覧表示で壊れる入力を残さない。

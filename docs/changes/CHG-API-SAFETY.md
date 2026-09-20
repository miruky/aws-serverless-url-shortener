---
id: CHG-API-SAFETY
kind: change
scope: [DETAIL-API]
tdd:
  runner: pytest
  test_roots: [tests/regression/test_core_safety.py]
---

# APIの安全性と入力契約

JSONの形状、URL検査、ID衝突、負のlimit、永久キャッシュ、Base64本文を修正する。
受入条件は tests/regression/test_core_safety.py。修正前の実装で同じテストの失敗を保存し、修正後の成功と比較する。
既存の匿名管理APIと301を前提としたテストは新しい製品契約へ改訂し、削除やskipで不具合を隠さない。

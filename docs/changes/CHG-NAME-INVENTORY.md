---
id: CHG-NAME-INVENTORY
kind: change
scope: [DETAIL-PLATFORM]
tdd:
  runner: pytest
  test_roots: [tests/test_deployment_prepare.py]
---

# 名前台帳の異なるPolicies型

実際の準備コマンドで、CognitoのPoliciesオブジェクトをIAMのPolicies配列として扱う失敗を確認した。
隔離した製品入力から名前台帳を作る回帰テストで、両者の違いと36個の名前の一意性を確認する。

テストは配布物の既存生成状態に依存しない。入力fixtureを自作し、配布ZIPの起動検査とは分ける。fixture変更後は初回Redの実装ハッシュ `13e6b74aa0bdcb9dd898a0f832255f1172cc54fd9c96163d513399ff0ce522bd` に一致する原文を隔離したコピーへ復元し、同じテストで失敗を取り直した。

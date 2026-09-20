---
id: CHG-MANAGEMENT-AUTH
kind: change
scope: [DETAIL-API]
tdd:
  runner: pytest
  test_roots: [tests/regression/test_management_auth.py]
---

# 匿名の管理操作を拒否する

API Gatewayの認証済みコンテキストがない管理操作を401とし、DynamoDBへ到達させない。
公開リダイレクトはこの認証ガードを使わない。実際のJWT署名検証はAPI GatewayのCognito authorizerで行う。
関数の直接invoke権限を一般利用者へ渡さないことをデプロイ契約に含める。

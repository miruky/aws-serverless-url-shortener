---
id: BASIC-API
kind: basic
depends_on: [REQ-API]
---

# 管理画面とAPIの構成

Lambdaハンドラー、ドメインモデル、DynamoDBリポジトリを分離する。入力不正と保存失敗を安定したHTTP応答へ変換する。DynamoDBの条件付き書込で作成・更新の競合を検出する。

画面は同一オリジンから配信する。Cognitoのコードフローを使い、署名検証済みのコンテキストで管理APIを呼ぶ。
データ転送に外部SaaSを使わず、クライアントで読み込んだ範囲だけを検索・集計する。

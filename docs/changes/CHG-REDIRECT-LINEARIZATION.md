---
id: CHG-REDIRECT-LINEARIZATION
kind: change
scope: [DETAIL-API]
tdd:
  runner: pytest
  test_roots: [tests/regression/test_redirect_linearization.py]
---

# 転送の判定時点を一つにする

期限前の条件付き更新で受理・計上したGETを、応答組立て時の再判定で410に変えない。
判定時点はDynamoDBの条件付き更新。HEADは計上しない読み取りなので、読み取った状態と時刻で判定する。

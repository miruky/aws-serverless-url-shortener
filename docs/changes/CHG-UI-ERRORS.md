---
id: CHG-UI-ERRORS
kind: change
scope: [DETAIL-API]
tdd:
  runner: node
  test_roots: [tests/unit/messages.test.mjs]
---

# 利用者向けのエラー表現

既存のerror.messageの直接表示を同じ挙動の関数へ抽出した時点でRedを記録する。
通信失敗や未知の内部エラーを自然な日本語にし、具体的なアプリのエラー説明は保持する。

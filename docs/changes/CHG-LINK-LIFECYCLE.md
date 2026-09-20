---
id: CHG-LINK-LIFECYCLE
kind: change
scope: [DETAIL-API]
tdd:
  runner: pytest
  test_roots: [tests/regression/test_link_lifecycle.py]
---

# 使えるリンク管理の基本機能

任意ID・タイトル・期限、HEADによるカウント抑制、ページ継続をAPIから確認する。
受入条件は tests/regression/test_link_lifecycle.py。モデルとリポジトリの準備後、ハンドラーがまだ未対応の状態をRedとして記録する。

---
id: CHG-PACKAGE-ISOLATION
kind: change
scope: [DETAIL-PLATFORM]
tdd:
  runner: pytest
  test_roots: [tests/test_package_isolation.py]
---

# 配布物を開発依存から隔離する

ZIPに含まれないMotoを、開発venvから読み込んで起動確認が通る問題を再現する。
配布物の検査にはsite-packagesを参照しないPythonを使い、依存不足を拒否する。

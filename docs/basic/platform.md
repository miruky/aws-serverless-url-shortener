---
id: BASIC-PLATFORM
kind: basic
depends_on: [REQ-PLATFORM]
---

# 配布と配置の構成

GitHub Actionsは検査と配布物生成まで。変更セットの確認と実行は運用者の操作とする。
新版のproductと配布バケットのartifactsを分け、既存のスタックへ新しい物理名を無断適用しない。
ZIPは固定の時刻・順序で作成し、実際に展開した内容で起動確認する。

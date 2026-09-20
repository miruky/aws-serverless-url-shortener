---
id: CHG-WEB-STAGE-PATHS
kind: change
scope: [DETAIL-API]
tdd:
  runner: pytest
  test_roots: [tests/regression/test_web_stage_paths.py]
---

# ステージ付きの管理画面

末尾のスラッシュがないappパスでも、CSSとJavaScriptを正しいステージのapp配下から読み込む。
資源パスは信頼されたPUBLIC_BASE_URLのパスから作り、リクエストのHostを埋め込まない。

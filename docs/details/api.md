---
id: DETAIL-API
kind: detail
depends_on:
- BASIC-API
artifacts:
- path: docs/assets/console.png
  role: configuration
- path: docs/operations/security.md
  role: configuration
- path: docs/reference/api.md
  role: configuration
- path: src/__init__.py
  role: implementation
- path: src/handlers/__init__.py
  role: implementation
- path: src/handlers/create_url.py
  role: implementation
- path: src/handlers/delete_url.py
  role: implementation
- path: src/handlers/get_url_stats.py
  role: implementation
- path: src/handlers/list_urls.py
  role: implementation
- path: src/handlers/redirect_url.py
  role: implementation
- path: src/handlers/update_url.py
  role: implementation
- path: src/handlers/web.py
  role: implementation
- path: src/models/__init__.py
  role: implementation
- path: src/models/url.py
  role: implementation
- path: src/repositories/__init__.py
  role: implementation
- path: src/repositories/url_repository.py
  role: implementation
- path: src/utils/__init__.py
  role: implementation
- path: src/utils/link_fields.py
  role: implementation
- path: src/utils/request.py
  role: implementation
- path: src/utils/response.py
  role: implementation
- path: src/utils/short_id.py
  role: implementation
- path: src/utils/validators.py
  role: implementation
- path: tests/e2e/product.spec.mjs
  role: test
  verifies:
  - REQ-API
  - REQ-DEVELOPMENT
- path: tests/regression/test_api_boundaries.py
  role: test
  verifies:
  - REQ-API
- path: tests/regression/test_core_safety.py
  role: test
  verifies:
  - REQ-API
- path: tests/regression/test_link_lifecycle.py
  role: test
  verifies:
  - REQ-API
- path: tests/regression/test_management_auth.py
  role: test
  verifies:
  - REQ-API
- path: tests/regression/test_redirect_linearization.py
  role: test
  verifies:
  - REQ-API
- path: tests/regression/test_web_stage_paths.py
  role: test
  verifies:
  - REQ-API
- path: tests/test_handlers_create_url.py
  role: test
  verifies:
  - REQ-API
- path: tests/test_handlers_delete_url.py
  role: test
  verifies:
  - REQ-API
- path: tests/test_handlers_get_url_stats.py
  role: test
  verifies:
  - REQ-API
- path: tests/test_handlers_list_urls.py
  role: test
  verifies:
  - REQ-API
- path: tests/test_handlers_redirect_url.py
  role: test
  verifies:
  - REQ-API
- path: tests/test_models_url.py
  role: test
  verifies:
  - REQ-API
- path: tests/test_product_contracts.py
  role: test
  verifies:
  - REQ-API
- path: tests/test_repositories_url_repository.py
  role: test
  verifies:
  - REQ-API
- path: tests/test_utils_response.py
  role: test
  verifies:
  - REQ-API
- path: tests/test_utils_short_id.py
  role: test
  verifies:
  - REQ-API
- path: tests/test_utils_validators.py
  role: test
  verifies:
  - REQ-API
- path: tests/unit/messages.test.mjs
  role: test
  verifies:
  - REQ-API
- path: web/app.js
  role: implementation
- path: web/auth.js
  role: implementation
- path: web/index.html
  role: implementation
- path: web/style.css
  role: implementation
---

# リンク管理と転送の詳細設計

作成はread_bodyとfieldsで型・範囲・URLを検査し、IdConflictErrorで使用済みIDを区別する。保存はattribute_not_existsを使う。
GETの転送判定とカウント更新は同じ条件付き更新にする。受理した時刻を応答時に再判定しない。HEADは読取りだけで、本文を返さない。
編集はversionを条件にし、期限解除は属性を削除する。停止済みレコードとIDは保持する。
一覧は評価件数の上限と継続cursorを持つScan。全体のソートやスナップショットを保証しない。

画面は同一オリジンの静的HTML/CSS/ES modules。DOMへ文字列を入れるときはtextContentを使う。認証はCognitoのcode+PKCE、state、nonce。
トークンはメモリのみ。汎用の内部エラーは利用者向けの日本語に変換する。HTMLの資源パスはPUBLIC_BASE_URLのパスから生成する。
[API契約](../reference/api.md)と[セキュリティ](../operations/security.md)が外部向けの契約である。

一覧はarticleごとのCSS Gridで配置し、480px以下では状態・アクセス数を右側にまとめる。
860px以下で二列を一列にし、リンク作成は既存のフォームへアンカーで移動する。フォームの任意表示はlabelから分離し、入力名を維持する。
編集は名前付きのnative dialog。動的なタイトル・転送先は引き続きtextContentで挿入し、短縮リンクの表示からだけHTTP(S)スキームを省略する。
hrefとコピー内容は完全なURLを保持する。URLが長い場合は転送先表示を省略し、title属性でも原文を確認できる。
[画面変更の受入条件と参考資料](../changes/CHG-WORKSPACE-DESIGN.md)を参照する。

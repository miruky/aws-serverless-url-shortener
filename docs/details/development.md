---
id: DETAIL-DEVELOPMENT
kind: detail
depends_on:
- BASIC-DEVELOPMENT
artifacts:
- path: .editorconfig
  role: configuration
- path: .gitattributes
  role: configuration
- path: .githooks/pre-commit
  role: configuration
- path: .githooks/pre-push
  role: configuration
- path: .github/dependabot.yml
  role: configuration
- path: .github/workflows/ci.yml
  role: configuration
- path: .gitignore
  role: configuration
- path: .node-version
  role: configuration
- path: .prettierrc.json
  role: configuration
- path: .python-version
  role: configuration
- path: AGENTS.md
  role: configuration
- path: CHANGELOG.md
  role: configuration
- path: CONTRIBUTING.md
  role: configuration
- path: LICENSE
  role: configuration
- path: Makefile
  role: configuration
- path: README.md
  role: configuration
- path: SECURITY.md
  role: configuration
- path: buildspec.yml
  role: configuration
- path: dev
  role: configuration
- path: docs/README.md
  role: configuration
- path: docs/changes/CHG-API-BOUNDARIES.md
  role: configuration
- path: docs/changes/CHG-API-SAFETY.md
  role: configuration
- path: docs/changes/CHG-CROSS-VERIFICATION.md
  role: configuration
- path: docs/changes/CHG-EVIDENCE-INTEGRITY.md
  role: configuration
- path: docs/changes/CHG-LINK-LIFECYCLE.md
  role: configuration
- path: docs/changes/CHG-MANAGEMENT-AUTH.md
  role: configuration
- path: docs/changes/CHG-NAME-INVENTORY.md
  role: configuration
- path: docs/changes/CHG-PACKAGE-ISOLATION.md
  role: configuration
- path: docs/changes/CHG-REDIRECT-LINEARIZATION.md
  role: configuration
- path: docs/changes/CHG-ROOT-LINKS.md
  role: configuration
- path: docs/changes/CHG-TRACE-PORT.md
  role: configuration
- path: docs/changes/CHG-UI-ERRORS.md
  role: configuration
- path: docs/changes/CHG-WEB-STAGE-PATHS.md
  role: configuration
- path: docs/changes/CHG-WORKSPACE-DESIGN.md
  role: configuration
- path: docs/engineering/provenance.md
  role: configuration
- path: docs/engineering/workflow.md
  role: configuration
- path: docs/operations/troubleshooting.md
  role: configuration
- path: docs/operations/verification.md
  role: configuration
- path: docs/product/improvements.md
  role: configuration
- path: package-lock.json
  role: configuration
- path: package.json
  role: configuration
- path: playwright.config.mjs
  role: implementation
- path: pyproject.toml
  role: configuration
- path: src/local_server.py
  role: implementation
- path: tests/__init__.py
  role: implementation
- path: tests/conftest.py
  role: implementation
- path: tests/helpers.py
  role: implementation
- path: tests/unit/cross-verification.test.mjs
  role: test
  verifies:
  - REQ-DEVELOPMENT
- path: tests/unit/evidence-integrity.test.mjs
  role: test
  verifies:
  - REQ-DEVELOPMENT
- path: tests/unit/harness.test.mjs
  role: test
  verifies:
  - REQ-DEVELOPMENT
- path: tests/unit/python-cache.test.mjs
  role: test
  verifies:
  - REQ-DEVELOPMENT
- path: tests/unit/root-links.test.mjs
  role: test
  verifies:
  - REQ-DEVELOPMENT
- path: tests/unit/staged.test.mjs
  role: test
  verifies:
  - REQ-DEVELOPMENT
- path: tests/unit/tdd.test.mjs
  role: test
  verifies:
  - REQ-DEVELOPMENT
- path: tools/baseline.py
  role: implementation
- path: tools/bootstrap_guard.py
  role: implementation
- path: tools/check-staged.mjs
  role: implementation
- path: tools/dev.mjs
  role: implementation
- path: tools/docs-server.mjs
  role: implementation
- path: tools/hooks.mjs
  role: implementation
- path: tools/pytest_evidence.py
  role: implementation
- path: tools/tdd.mjs
  role: implementation
- path: tools/toolchain.json
  role: configuration
- path: tools/trace/cli.mjs
  role: implementation
- path: tools/trace/model.mjs
  role: implementation
- path: tools/trace/workbench.mjs
  role: implementation
- path: trace.config.json
  role: configuration
- path: uv.lock
  role: configuration
---

# 開発基盤の詳細設計

既存のNode製グラフを再利用する。文書のid/kind/depends_on、成果物のpath/role/verifiesを検査する。
自身・上位文書・配下の成果物・関連する検証テストを入力としてSHA-256を計算し、確認記録との差を示す。別の設計が所有する検証テストも含める。
Pythonの__pycache__は生成物として除外する。通常のソースファイルは除外せず、未管理なら拒否する。

TDDはNodeのTAPとpytestの実行レポートを読み、起動失敗、skip、0件を成功にしない。ログ、テスト、対象scope、変更票の整合性を確認する。
元のGitコミットを隔離して実行でき、作業中のソースを巻き戻さない。修正履歴を隠すために失敗出力やテストを削除しない。
pre-commitはステージ済みのスナップショット、pre-push/CIは統合検査を行う。公開前にGitHub側でもqualityを必須チェックにする。

ローカルデモはMoto、ダミー資格情報、一時トークン、Host/Origin検査を使う。データはメモリ内だけ。
Node依存とPython依存は別のロックで固定し、フロントとツールのJavaScriptをPrettier、PythonをRuff/mypyで検査する。
[変更手順](../engineering/workflow.md)を参照する。

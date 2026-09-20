---
id: DETAIL-PLATFORM
kind: detail
depends_on:
- BASIC-PLATFORM
artifacts:
- path: docs/operations/deployment.md
  role: configuration
- path: docs/operations/migration.md
  role: configuration
- path: infrastructure/artifacts.yaml
  role: configuration
- path: infrastructure/pipeline.yaml
  role: configuration
- path: infrastructure/product.yaml
  role: configuration
- path: infrastructure/rules/LICENSE-aws-guard-rules
  role: configuration
- path: infrastructure/rules/artifacts.guard
  role: configuration
- path: infrastructure/rules/dynamodb_pitr_enabled.guard
  role: configuration
- path: infrastructure/rules/product.guard
  role: configuration
- path: infrastructure/template.yaml
  role: configuration
- path: tests/test_deployment_prepare.py
  role: test
  verifies:
  - REQ-PLATFORM
- path: tests/test_infrastructure.py
  role: test
  verifies:
  - REQ-PLATFORM
- path: tests/test_package_isolation.py
  role: test
  verifies:
  - REQ-PLATFORM
- path: tools/package.py
  role: implementation
- path: tools/prepare_deployment.py
  role: implementation
- path: tools/vendor/aws_resource_names.py
  role: implementation
---

# 配布とAWS配置の詳細設計

product.yamlは新規v2環境、artifacts.yamlは非公開・暗号化・バージョン付きの配布バケット。旧template/pipelineは参照資料として保持する。
管理メソッドはCognito authorizerとクライアントaudience検査を必須にし、公開GET/HEADと画面だけを例外にする。
作成・管理・転送・画面のIAMロールを分け、テーブル操作とログ保存先を絞る。招待制、TOTP、15分のIDトークンを定義する。
テーブル・ユーザープール・ログ・配布バケットはRetainする。アラームは状態検出のみで、通知先の接続は別途必要。

ロック済み本番依存をLinux ARM64向けに収集し、順序とZIP内時刻を固定する。展開先をPython -I -Sで読み、開発用依存の混入を検出する。
API形状のハッシュでDeploymentの論理IDを変える。配布物と入力のハッシュをmanifestへ保存し、prepareは古いZIPやソースを拒否する。
名前の生成は既存のaws-resource-name-v1を再利用し、未作成の計画として台帳へ保持する。名前を更新するために既存資源を置換しない。
[配置手順](../operations/deployment.md)と[移行手順](../operations/migration.md)を参照する。

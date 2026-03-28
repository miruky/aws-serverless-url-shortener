# AWS Serverless URL Shortener

[![CI](https://github.com/miruky/aws-serverless-url-shortener/actions/workflows/ci.yml/badge.svg)](https://github.com/miruky/aws-serverless-url-shortener/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Test](https://img.shields.io/badge/Test-pytest-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Ruff](https://img.shields.io/badge/Linter-Ruff-D7FF64?logo=ruff&logoColor=black)](https://docs.astral.sh/ruff/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AWS Lambda + API Gateway + DynamoDB で構築した、本番環境対応のサーバーレス URL 短縮サービスです。**

## 概要

5 つの Lambda 関数が REST API を提供し、DynamoDB をデータストアとして短縮 URL の作成・リダイレクト・統計取得・一覧表示・論理削除を行います。Clean Architecture の原則に沿ってレイヤーを分離し、92 件の pytest テストで品質を担保しています。

### なぜ作ったのか

AWS サーバーレスアーキテクチャの設計力を示すポートフォリオとして作成しました。Lambda / API Gateway / DynamoDB の実践的な組み合わせに加え、CloudFormation による IaC、GitHub Actions + CodePipeline による CI/CD パイプラインまで一貫して構築しています。

## アーキテクチャ

```text
クライアント
  │
  ▼
API Gateway (REST)
  ├── POST   /urls          → CreateUrl Lambda
  ├── GET    /urls          → ListUrls Lambda
  ├── GET    /urls/{id}     → GetUrlStats Lambda
  ├── DELETE /urls/{id}     → DeleteUrl Lambda
  └── GET    /{id}          → RedirectUrl Lambda (301)
                                    │
                                    ▼
                              DynamoDB (urls)
```

## 技術スタック

| カテゴリ | 技術 |
|:--|:--|
| 言語 | Python 3.12 |
| コンピュート | AWS Lambda |
| API | Amazon API Gateway (REST) |
| データベース | Amazon DynamoDB (オンデマンド) |
| IaC | AWS CloudFormation |
| CI | GitHub Actions |
| CD | AWS CodePipeline + CodeBuild |
| テスト | pytest + moto |
| リンター | Ruff |

## API リファレンス

| メソッド | パス | 説明 |
|:--|:--|:--|
| POST | `/urls` | 短縮 URL を作成 |
| GET | `/{short_id}` | 元の URL へ 301 リダイレクト |
| GET | `/urls/{short_id}` | クリック統計を取得 |
| GET | `/urls?limit=N` | 有効な URL の一覧を取得 |
| DELETE | `/urls/{short_id}` | URL を論理削除 |

**リクエスト例 (POST /urls)**

```json
{ "url": "https://example.com/very/long/path" }
```

**レスポンス例 (201)**

```json
{
  "short_id": "aB3kZ9x",
  "original_url": "https://example.com/very/long/path",
  "created_at": 1711612800,
  "click_count": 0,
  "is_active": true
}
```

## プロジェクト構成

```
.
├── .github/workflows/ci.yml       # GitHub Actions CI パイプライン
├── infrastructure/
│   ├── template.yaml               # コアインフラ (API GW, Lambda, DynamoDB)
│   └── pipeline.yaml               # CodePipeline + CodeBuild
├── src/
│   ├── handlers/                    # Lambda 関数ハンドラー (5 関数)
│   ├── models/
│   │   └── url.py                   # ドメインモデル (frozen データクラス)
│   ├── repositories/
│   │   └── url_repository.py        # DynamoDB データアクセス層
│   └── utils/
│       ├── response.py              # API Gateway レスポンスビルダー
│       ├── validators.py            # 入力バリデーション
│       └── short_id.py              # 短縮 ID 生成 (SHA-256 ベース)
├── tests/                           # pytest テストスイート (92 テスト)
├── buildspec.yml                    # CodeBuild ビルド仕様
├── pyproject.toml                   # プロジェクトメタデータ・ツール設定
└── Makefile                         # 開発用ショートカット
```

## はじめ方

### 前提条件

- Python 3.12 以上
- AWS CLI (デプロイ時)

### セットアップ

```bash
git clone https://github.com/miruky/aws-serverless-url-shortener.git
cd aws-serverless-url-shortener
python -m venv .venv && source .venv/bin/activate
make install
```

### テストの実行

```bash
make test
```

### Lint の実行

```bash
make lint
```

### デプロイ

```bash
# CI/CD パイプラインのデプロイ
aws cloudformation deploy \
  --template-file infrastructure/pipeline.yaml \
  --stack-name url-shortener-pipeline \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      CodeStarConnectionArn=arn:aws:codestar-connections:... \
      Environment=dev
```

パイプラインは `main` ブランチへのプッシュ時に自動で Build → Deploy を実行します。

## 設計方針

- **frozen データクラス** — `UrlItem` を不変にし、意図しない変更を防止
- **リポジトリパターン** — ビジネスロジックと DynamoDB SDK 呼び出しを分離
- **依存性注入** — `UrlRepository` へモックを注入し、moto ベースのテストを容易化
- **論理削除** — 監査証跡を保持しつつ、一覧からは除外
- **SHA-256 + タイムスタンプ** — 外部状態なしで衝突耐性の高い ID を生成

## ライセンス

[MIT](https://opensource.org/licenses/MIT)

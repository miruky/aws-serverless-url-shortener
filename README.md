# aws-serverless-url-shortener

AWS Lambda、API Gateway、DynamoDB上に構築された本番環境対応のサーバーレスURL短縮サービス。

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
| CI | GitHub Actions (リント + テスト) |
| CD | AWS CodePipeline + CodeBuild + CodeDeploy |
| テスト | pytest + moto (AWSモック) |
| リンター | ruff |

## プロジェクト構成

```
.
├── .github/workflows/ci.yml       # GitHub Actions CIパイプライン
├── infrastructure/
│   ├── template.yaml               # コアインフラ (API GW, Lambda, DynamoDB)
│   └── pipeline.yaml               # CodePipeline + CodeBuild + CodeDeploy
├── src/
│   ├── handlers/                    # Lambda関数ハンドラー
│   │   ├── create_url.py
│   │   ├── redirect_url.py
│   │   ├── get_url_stats.py
│   │   ├── delete_url.py
│   │   └── list_urls.py
│   ├── models/
│   │   └── url.py                   # ドメインモデル (frozenデータクラス)
│   ├── repositories/
│   │   └── url_repository.py        # DynamoDBデータアクセス層
│   └── utils/
│       ├── response.py              # API Gatewayレスポンスビルダー
│       ├── validators.py            # 入力バリデーション
│       └── short_id.py              # 短縮ID生成 (SHA-256ベース)
├── tests/                           # 包括的なpytestテストスイート
├── buildspec.yml                    # CodeBuildビルド仕様
├── pyproject.toml                   # プロジェクトメタデータ・ツール設定
└── Makefile                         # 開発用ショートカット
```

## APIリファレンス

### POST /urls

短縮URLを作成する。

```json
// リクエスト
{ "url": "https://example.com/very/long/path" }

// レスポンス (201)
{
  "short_id": "aB3kZ9x",
  "original_url": "https://example.com/very/long/path",
  "created_at": 1711612800,
  "click_count": 0,
  "is_active": true
}
```

### GET /{short_id}

元のURLへリダイレクトする（301）。

### GET /urls/{short_id}

クリック統計情報を取得する。

### GET /urls?limit=20

有効なURLの一覧を取得する。

### DELETE /urls/{short_id}

URLを論理削除する（`is_active` を `false` に設定）。

## ローカル開発

```bash
# 依存関係のインストール
make install

# テスト実行
make test

# リンター実行
make lint
```

## デプロイ

### 1. CI/CDパイプラインのデプロイ

```bash
aws cloudformation deploy \
  --template-file infrastructure/pipeline.yaml \
  --stack-name url-shortener-pipeline \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      CodeStarConnectionArn=arn:aws:codestar-connections:... \
      Environment=dev
```

### 2. パイプラインの自動実行フロー

1. **Source** — `main` ブランチへのプッシュ時にGitHubからコードを取得
2. **Build** — CodeBuildでリント・テストを実行し、Lambda zipをパッケージング
3. **Deploy** — Lambda関数を含むCloudFormationスタックを作成・更新

## 設計方針

- **frozenデータクラス** (`UrlItem`) — 不変性により意図しない変更を防止
- **リポジトリパターン** — ビジネスロジックとDynamoDB SDKの呼び出しを分離
- **依存性注入** (`UrlRepository`) — モンキーパッチなしでmotoベースのテストが可能
- **論理削除** — 監査証跡を保持。`is_active=false` のアイテムは一覧から除外
- **SHA-256 + タイムスタンプ** によるID生成 — 外部状態なしで衝突耐性を確保

## ライセンス

MIT

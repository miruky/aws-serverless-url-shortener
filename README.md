# AWS Serverless URL Shortener

AWSにセルフホストするURL短縮・リンク管理サービスです。短縮URLの作成から、転送先の編集、有効期限の設定、公開の停止・再開までを管理画面で操作できます。

管理画面は招待制のログインに対応しています。共有した短縮URLへのアクセスにログインは不要です。

![リンク管理画面](docs/assets/console.png)

## 主な機能

- **短縮URLの作成** — ランダムなIDの自動生成、または英数字1〜20文字の任意IDを指定
- **リンクの編集** — タイトル、転送先URL、有効期限を変更
- **公開状態の管理** — 短縮URLを保持したまま公開を停止・再開
- **一覧と検索** — タイトル・URL・IDによる検索、公開状態による絞り込み、リンクのコピー
- **アクセス数の表示** — リダイレクトを処理した回数をリンクごとに表示
- **管理者認証** — Amazon Cognitoによる招待制ログインとTOTPによる多要素認証

一人またはチームで共有する管理領域として利用できます。検索と集計は画面に読み込んだリンクが対象です。アクセス数にはボットや再試行によるアクセスも含まれます。

## 構成

| レイヤー | 技術 |
| --- | --- |
| 管理画面 | HTML / CSS / JavaScript |
| API・リダイレクト | Amazon API Gateway REST API / AWS Lambda / Python 3.12 |
| データ保存 | Amazon DynamoDB |
| 認証 | Amazon Cognito |
| インフラ定義 | AWS CloudFormation |
| ローカル環境 | Moto / Python |

管理画面とAPIは同じオリジンで配信します。リンク作成・編集などの管理APIに認証を適用し、公開URLへのアクセスは302リダイレクトで転送します。

## セットアップ

### ローカル環境

必要なツールはNode.js 24.19.0、Python 3.12.13、uv 0.11.20、Gitです。

```sh
git clone https://github.com/miruky/aws-serverless-url-shortener.git
cd aws-serverless-url-shortener
./dev setup
./dev serve
```

[管理画面](http://127.0.0.1:4310/app/)を開き、リンク先URLを入力して短縮リンクを作成します。

ローカル環境ではMotoを使用します。AWSアカウントは不要で、データはプロセス終了時に破棄されます。

### AWS環境

CloudFormationの定義は `infrastructure/product.yaml` と `infrastructure/artifacts.yaml` にあります。
配布用ZIPとデプロイパラメータを次のコマンドで生成します。

```sh
./dev check
./dev prepare --region ap-northeast-1
```

AWSへの配置と管理者アカウントの設定は[デプロイ手順](docs/operations/deployment.md)を参照してください。
旧版から更新する場合は[移行手順](docs/operations/migration.md)を参照してください。

## API

管理APIでは、CognitoのIDトークンを `Authorization: Bearer <ID_TOKEN>` に指定します。

| メソッド | パス | 操作 | 認証 |
| --- | --- | --- | --- |
| POST | `/urls` | リンクの作成 | 必須 |
| GET | `/urls` | 一覧の取得 | 必須 |
| GET | `/urls/{short_id}` | 詳細・アクセス数の取得 | 必須 |
| PATCH | `/urls/{short_id}` | 編集・停止・再開 | 必須 |
| DELETE | `/urls/{short_id}` | 公開停止 | 必須 |
| GET / HEAD | `/{short_id}` | 転送 | 不要 |

`POST /urls` のリクエスト例:

```json
{
  "url": "https://example.com/article",
  "title": "記事",
  "custom_alias": "article"
}
```

作成成功時は201を返します。編集時は取得したリンクの `version` を指定します。
入力項目、ページング、レスポンス形式は[APIリファレンス](docs/reference/api.md)を参照してください。

## 開発

`./dev setup` は依存関係とリポジトリ内のGitフックを設定します。ブラウザテストにはChromiumをインストールします。

```sh
npx playwright install chromium
```

| コマンド | 用途 |
| --- | --- |
| `./dev serve` | ローカルサーバーを起動 |
| `./dev test` | Pythonテストを実行 |
| `npm run test:e2e` | ブラウザテストを実行 |
| `./dev check` | コード・テスト・文書・インフラ定義を検査し、配布ZIPを生成 |
| `./dev docs` | 要件・設計・実装・テストの依存グラフを表示 |

開発手順は[開発ガイド](docs/engineering/workflow.md)、変更の提出方法は[CONTRIBUTING](CONTRIBUTING.md)を参照してください。
API・運用・設計の文書は[ドキュメント一覧](docs/README.md)にまとめています。脆弱性の報告方法は[SECURITY](SECURITY.md)を参照してください。

## ライセンス

[MIT](LICENSE)。外部ソフトウェアの出典とライセンスは[こちら](docs/engineering/provenance.md)を参照してください。

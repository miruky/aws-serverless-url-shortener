# デプロイとリリース

商用AWSリージョン向けの構成です。GovCloud・中国リージョンは対象に含めません。
この手順は実AWSで未実行です。ローカルの構文・規則・配布ZIP検査と、AWSアカウントでの受入確認を区別します。
通常のCIはAWSへ接続せず、配布物を生成するところまでです。

## ローカルで準備する

```sh
./dev check
./dev prepare --region ap-northeast-1
```

`dist/lambda-package.zip`、`dist/product.json`、`dist/manifest.json` が配布物です。
ZIPにはロック済みの本番依存、ハンドラー、画面だけを入れ、Moto・ローカルサーバー・テストを除外します。
ZIPを展開した場所からハンドラーと画面を読み込めるか検査します。
API定義の内容からDeploymentの論理IDを決め、メソッドを変えたのに古いStage設定が残るのを防ぎます。

`prepare` は物理名を一度生成し、`.harness/deployment/` に名前・パラメータ・台帳を保存します。
既存計画の上書きは拒否します。リソースの作成・削除や認証情報の取得は行いません。
名前は暗号学的乱数から生成し、用途は台帳のラベルで区別します。名前へ日時・サービス・環境名を埋め込みません。
台帳の「作成していない」は準備時の状態であり、AWS全体の不存在を調査した証拠ではありません。

## 新規環境に配置する

ここからはAWS CLIの認証と、選択したアカウント・リージョンでの権限が必要です。AWS利用料金が発生し得ます。
既存スタックへ適用する前には[移行手順](migration.md)を確認してください。新しい物理名を既存データの置換に使わないでください。
以下の読み取りには `jq` を使用します。

```sh
DEPLOY_REGION=ap-northeast-1
ARTIFACT_STACK=$(jq -r .ArtifactsStackName .harness/deployment/names.json)
ARTIFACT_CHANGE=$(jq -r .ArtifactsChangeSetName .harness/deployment/names.json)
PRODUCT_STACK=$(jq -r .ProductStackName .harness/deployment/names.json)
PRODUCT_CHANGE=$(jq -r .ProductChangeSetName .harness/deployment/names.json)
ARTIFACT_BUCKET=$(jq -r .ArtifactBucketName .harness/deployment/names.json)
PACKAGE_SHA=$(jq -r .sha256 dist/manifest.json)
```

まず、暗号化・公開遮断・バージョン管理・TLS必須の配布バケットを作る変更セットを確認します。

```sh
aws cloudformation create-change-set \
  --region "$DEPLOY_REGION" \
  --stack-name "$ARTIFACT_STACK" --change-set-name "$ARTIFACT_CHANGE" \
  --change-set-type CREATE \
  --template-body file://infrastructure/artifacts.yaml \
  --parameters file://.harness/deployment/artifacts-parameters.json

aws cloudformation wait change-set-create-complete \
  --region "$DEPLOY_REGION" \
  --stack-name "$ARTIFACT_STACK" --change-set-name "$ARTIFACT_CHANGE"

aws cloudformation describe-change-set \
  --region "$DEPLOY_REGION" \
  --stack-name "$ARTIFACT_STACK" --change-set-name "$ARTIFACT_CHANGE"
```

内容とアカウントを確認した後に実行します。

```sh
aws cloudformation execute-change-set \
  --region "$DEPLOY_REGION" \
  --stack-name "$ARTIFACT_STACK" --change-set-name "$ARTIFACT_CHANGE"
aws cloudformation wait stack-create-complete \
  --region "$DEPLOY_REGION" --stack-name "$ARTIFACT_STACK"

aws s3 cp dist/lambda-package.zip \
  "s3://$ARTIFACT_BUCKET/packages/$PACKAGE_SHA.zip" --region "$DEPLOY_REGION"

aws cloudformation create-change-set \
  --region "$DEPLOY_REGION" \
  --stack-name "$PRODUCT_STACK" --change-set-name "$PRODUCT_CHANGE" \
  --change-set-type CREATE --capabilities CAPABILITY_NAMED_IAM \
  --template-body file://dist/product.json \
  --parameters file://.harness/deployment/parameters.json

aws cloudformation wait change-set-create-complete \
  --region "$DEPLOY_REGION" \
  --stack-name "$PRODUCT_STACK" --change-set-name "$PRODUCT_CHANGE"
aws cloudformation describe-change-set \
  --region "$DEPLOY_REGION" \
  --stack-name "$PRODUCT_STACK" --change-set-name "$PRODUCT_CHANGE"
```

IAM・Cognito・テーブル・ログの内容を確認してから、新版の変更セットを実行します。

```sh
aws cloudformation execute-change-set \
  --region "$DEPLOY_REGION" \
  --stack-name "$PRODUCT_STACK" --change-set-name "$PRODUCT_CHANGE"
aws cloudformation wait stack-create-complete \
  --region "$DEPLOY_REGION" --stack-name "$PRODUCT_STACK"
aws cloudformation describe-stacks \
  --region "$DEPLOY_REGION" --stack-name "$PRODUCT_STACK" \
  --query 'Stacks[0].Outputs'
```

出力のUserPoolIdで、Cognitoの管理者アカウントを作成します。ユーザー名は台帳のAdministratorNameを使用します。
メールアドレスや招待の送信先は運用者が指定してください。共有の初期パスワードをリポジトリへ保存しないでください。
`ManagementUrl` を開き、初回パスワード変更とTOTPを設定して、管理操作を受入確認します。

Cognitoの古典的なHosted UIをLITEプランで使用します。Managed Login v2へ変更する場合は、対応プランとアプリクライアントごとのbrandingを合わせて設計してください。

## 公開前にAWS上で確かめること

- 匿名の作成・一覧・編集・停止が拒否される
- 招待した管理者のログイン、MFA、期限切れ、ログアウト
- 作成、転送、HEAD、編集、停止、再開、期限切れ
- 別クライアント向けトークンが管理APIで拒否される
- 各Lambdaのログ出力と保存期間、公開URLやトークンがログに残らないこと
- 障害時の5xxアラーム。通知先はこのテンプレートでは接続していない
- 料金・クォータ・監査設定。APIのスロットリングは支出のハード上限ではない

## 更新・復旧・削除

更新時は同じ物理名と同じテーブルを保ち、検査済みの新しいZIPを別の内容ハッシュのキーへ保存します。
`LambdaS3Key` だけを新しいキーへ変更し、設定変更も含めたUPDATE変更セットを別の生成済み名で準備してください。
古いZIPとmanifest、適用パラメータを保管します。コードの巻き戻しと、データの復元は別の作業です。

テーブル、ログ、ユーザープール、配布バケットはRetainされます。スタック削除だけではデータと料金がなくなりません。
削除時は利用中の公開リンク、アカウント、バックアップを確認し、残った資源の扱いを明示してから作業します。
バックアップ復元、DNS切替、緊急時の管理API遮断は実AWSでの演習が必要です。この版で演習済みとは扱いません。

## 参照

[CognitoのPKCE](https://docs.aws.amazon.com/cognito/latest/developerguide/using-pkce-in-authorization-code.html)、
[API GatewayのCognito認証](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html)、
[DynamoDBの条件付き操作](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html)。

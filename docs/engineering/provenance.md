# 再利用した基盤とライセンス

## 文書依存グラフ

所有者の別の個人開発プロジェクトで使用している `tools/trace/model.mjs`、`cli.mjs`、`workbench.mjs`、ハーネステストを移植しました。
要件・設計・実装・テストのグラフと理由付き確認を再利用し、Pythonキャッシュの扱い、READMEのリンク検査、実行証拠の整合性、ステージ済み内容の検査を追加しています。
ゲーム固有のコードや仕様は含めません。

AWSの物理名生成器は所有者の既存 `aws-resource-name-v1` を `tools/vendor/aws_resource_names.py` へ同一内容で取り込みました。
このファイルは既存規約との一致を維持するため、一般のフォーマッターの対象外です。生成名、用途、未作成の状態は準備台帳で確認します。

## AWS Guard規則

`infrastructure/rules/dynamodb_pitr_enabled.guard` は [AWS Guard Rules Registry](https://github.com/aws-cloudformation/aws-guard-rules-registry) の
コミット `7f7340c26ae5d5e8874651dbffeb12e0e9f505b6` から取得したPITR規則です。
ライセンスは [Apache License 2.0](../../infrastructure/rules/LICENSE-aws-guard-rules)。他の規則はこの製品の認証・保持・ログ・配布バケットの契約を検査するために作成しました。
ルールで検証する項目以外の安全性や、特定の認証制度への適合を保証するものではありません。

Guard 3.2.1は公式リリースのSHA-256を確認します。固定値は `tools/toolchain.json` に保存します。
PythonとNodeの依存はそれぞれ `uv.lock` と `package-lock.json` に固定しています。SDK等のライセンス文書は配布時も各パッケージに含めます。

## 実行証拠

`evidence/tdd/` は、このローカル作業で実行したテストの出力と対象ハッシュです。
最初のRedを保存した後にテストの整形・検査補助を変更した場合は、同じテストを元のGitコミットへ隔離実行して証拠を取り直します。
ハッシュは実行記録の整合性を確認するもので、改ざん防止署名や独立監査ではありません。

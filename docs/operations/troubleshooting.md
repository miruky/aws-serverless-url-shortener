# 開発時のトラブル

| 状況 | 確認すること |
| --- | --- |
| setupでuv/Nodeが見つからない | READMEの前提バージョンを用意する。依存ロックを削除して回避しない |
| ブラウザ実行ファイルがない | `npx playwright install chromium`。Linux CIは `--with-deps` も使う |
| 開発ポートが使用中 | `./dev serve --port 4315`。文書は `DOCS_PORT=4325 ./dev docs` |
| STALE_REVIEW | `./dev trace impact` で変わった入力を読み、文書更新・テスト・理由付き確認を行う |
| UNMANAGED_FILE | 担当する詳細設計のartifactsへ追加する。要件を実際に検証するテストだけにverifiesを付ける |
| Greenが古い、Redとテストが違う | ファイルのハッシュを手修正せず、同じテストでRed/Greenを取り直す |
| pre-commitだけ失敗する | 必要な文書とtrace.lockもステージされているか確認する |
| Cognitoのredirect_mismatch | CallbackURLsと画面のURLを、末尾の `/` まで一致させる |
| 管理APIが401 | IDトークンの期限、対象クライアント、API Gatewayのauthorizerを確認する |
| 編集が409 | 他の操作でversionが変わった可能性がある。一覧を更新して再編集する |
| 期限切れリンクが一覧にある | 期限切れは削除ではない。過去のIDを再利用しないため保持している |
| prepareが古い配布物を拒否する | `./dev check` で現在の内容を再検査・再生成する |
| prepareが既存計画を拒否する | 既存名を再利用する。新規環境と既存環境の更新を混同しない |

実AWSでの問題は[デプロイ手順](deployment.md)と[移行手順](migration.md)を確認してください。
ログやIssueへURLの秘密、トークン、メールアドレスを貼らないでください。

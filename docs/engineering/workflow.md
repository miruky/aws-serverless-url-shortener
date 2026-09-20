# 変更の進め方

## 準備

```sh
./dev setup
npx playwright install chromium
./dev doctor
./dev serve
```

PythonとNodeの依存はロック済みです。`setup` はロックの不整合を拒否し、プロジェクトのGitフックを設定します。
Nodeは24.19.0、Pythonは3.12.13を基準とします。Guardは3.2.1。対応するCLIがなければ、公式配布物のSHA-256を検証してプロジェクト内へ導入します。
再生成できる `.venv`、`node_modules`、`.harness`、`dist` はGitへ含めません。

## 動作を変える

1. `./dev trace impact` で影響する文書を確認する。
2. `docs/changes/CHG-ID.md` に問題、対象ノード、受入条件を記載する。
3. 要件・基本設計・詳細設計を更新し、失敗する回帰テストを追加する。
4. `./dev tdd red --change CHG-ID` で実際の失敗を保存する。
5. 実装を修正し、同じテストで `./dev tdd green --change CHG-ID` を実行する。
6. 文書と差分を読み合わせ、各ノードを理由付きで確認する。
7. `./dev check` で全体を検査する。

変更票の例:

```yaml
id: CHG-EXAMPLE
kind: change
scope: [DETAIL-API]
tdd:
  runner: pytest
  test_roots: [tests/regression/test_core_safety.py]
```

このメタデータをMarkdown冒頭の `---` で囲み、本文へ実際の問題と受入条件を書きます。
Nodeの検査では `runner: node` と `.test.mjs` を指定します。skip・0件・起動失敗を合格やRedに数えません。

```sh
./dev trace ack DETAIL-API --change CHG-ID \
  --reason '実際に照合した関数・入力・期待する挙動と、文書への反映内容を具体的に記載する。'
```

依存する要件・基本設計も、それぞれ確認します。コピーした定型文を確認作業の代わりにしないでください。
文書だけの変更に人工的なRedは不要です。コードやテストを変えた場合は、変更後の内容に一致するGreenが必要です。

## 修正前の版へテストを当てる

```sh
./dev tdd red --change CHG-ID --baseline COMMIT_SHA
```

`COMMIT_SHA` は実在する40文字のGitコミットです。現在のテストを隔離した修正前ソースへコピーして実行し、作業ツリーを巻き戻しません。
結果は `evidence/tdd/` に保存し、取り直す前の結果はhistoryへ残します。
テストの整形や共通fixtureの変更もテスト内容の変更です。新しいテスト内容でRedを取り直してください。

## 自動で拒否するもの

- 要件・設計の参照切れ、重複ID、循環、未管理の実装・設定
- 入力が変わったままの確認記録
- 別の設計が所有する検証テストを含む、要件との対応漏れ
- 実行ログが欠落・変更されたTDD記録、テスト内容の不一致、古い対象ハッシュ
- READMEを含むローカルの文書リンク切れ

pre-commitはGitのインデックスを別の場所へ展開して検査します。未ステージの文書確認で、古いステージ済みの文書を通すことはできません。
pre-pushとCIは `./dev check` を使います。Gitのないソースアーカイブでもファイル・振る舞いの検査は実行し、Git固有の差分検査とフック導入だけを対象外とします。

GitHubへ反映した後は `quality` を必須チェックに設定してください。現時点でリモートのブランチルールを変更したという意味ではありません。
フックは `--no-verify` 等で迂回できるため、唯一の防御にはしません。

## 正本と限界

Markdownが正本です。`./dev docs` はCanvasと表で同じ関係を示します。`./dev trace graph` で閲覧用HTMLとJSONも書き出せます。
SHA-256は変更を検出しますが、文章の意味の正しさやテストの十分性を証明しません。実行者自身による確認を独立監査と呼ばないでください。

[開発基盤の要件](../requirements/development.md) / [再利用した基盤](provenance.md)

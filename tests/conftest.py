"""共通のpytestフィクスチャ。"""

from __future__ import annotations

import os
from collections.abc import Generator
from typing import Any

import boto3
import pytest
from moto import mock_aws


@pytest.fixture(autouse=True)
def _aws_credentials() -> None:
    """各テスト実行前にmoto用のダミーAWS認証情報を設定する。"""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "ap-northeast-1"


@pytest.fixture()
def dynamodb_resource() -> Generator[Any, None, None]:
    """事前にURLsテーブルを作成したmotoベースのDynamoDBリソースを提供する。

    ``test-urls`` テーブルを作成し、``URLS_TABLE_NAME`` 環境変数を設定した上で、
    リポジトリテストで使用するDynamoDBサービスリソースをyieldする。
    """
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")
        dynamodb.create_table(
            TableName="test-urls",
            KeySchema=[{"AttributeName": "short_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "short_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        os.environ["URLS_TABLE_NAME"] = "test-urls"
        yield dynamodb

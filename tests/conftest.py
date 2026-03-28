"""Shared pytest fixtures."""

from __future__ import annotations

import os
from typing import Any, Generator

import boto3
import pytest
from moto import mock_aws


@pytest.fixture(autouse=True)
def _aws_credentials() -> None:
    """Inject fake AWS credentials for moto before every test."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "ap-northeast-1"


@pytest.fixture()
def dynamodb_resource() -> Generator[Any, None, None]:
    """Provide a moto-backed DynamoDB resource with a pre-created URLs table.

    The fixture creates the ``test-urls`` table, sets the
    ``URLS_TABLE_NAME`` environment variable, and yields the DynamoDB
    service resource for use in repository tests.
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

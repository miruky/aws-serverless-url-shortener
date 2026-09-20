"""ダミーAWS資格情報とMotoだけで動く、端末内の開発サーバー。"""

from __future__ import annotations

import argparse
import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

import boto3
from moto import mock_aws

from src.handlers import (
    create_url,
    delete_url,
    get_url_stats,
    list_urls,
    redirect_url,
    update_url,
    web,
)


class LocalServer(ThreadingHTTPServer):
    token: str


class RequestHandler(BaseHTTPRequestHandler):
    server: LocalServer

    def log_message(self, format: str, *args: Any) -> None:
        """URLや認証情報を開発ログに残さない。"""

    def respond(self, response: dict[str, Any]) -> None:
        self.send_response(response["statusCode"])
        payload = str(response.get("body", "")).encode()
        for key, value in response.get("headers", {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def route(self) -> None:
        port = self.server.server_port
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if self.headers.get("Host") not in hosts or (
            self.headers.get("Origin")
            and self.headers["Origin"] not in {f"http://{h}" for h in hosts}
        ):
            self.respond({"statusCode": 403, "body": "Forbidden"})
            return
        parsed = urlsplit(self.path)
        path = unquote(parsed.path)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 16384:
                raise ValueError
        except ValueError:
            self.respond({"statusCode": 413, "body": "Request too large"})
            return
        if self.headers.get("Transfer-Encoding"):
            self.respond({"statusCode": 400, "body": "Unsupported transfer encoding"})
            return
        try:
            body = self.rfile.read(length).decode("utf-8")
        except UnicodeError:
            self.respond({"statusCode": 400, "body": "Invalid UTF-8"})
            return
        if path == "/" or path == "/app":
            self.respond({"statusCode": 302, "headers": {"Location": "/app/"}, "body": ""})
            return
        if path == "/health" and self.command in {"GET", "HEAD"}:
            self.respond({"statusCode": 200, "body": "ok"})
            return
        if path.startswith("/app/") and self.command in {"GET", "HEAD"}:
            response = web.handler({"pathParameters": {"proxy": path[5:]}}, None)
            if path == "/app/config":
                response["body"] = json.dumps({"mode": "local", "token": self.server.token})
            self.respond(response)
            return
        event: dict[str, Any] = {
            "body": body,
            "httpMethod": self.command,
            "queryStringParameters": {
                key: values[-1] for key, values in parse_qs(parsed.query).items()
            },
            "requestContext": {},
        }
        if secrets.compare_digest(
            self.headers.get("Authorization", ""), f"Bearer {self.server.token}"
        ):
            event["requestContext"] = {"authorizer": {"claims": {"sub": "local-demo"}}}
        operation = None
        if path == "/urls":
            operation = {"POST": create_url.handler, "GET": list_urls.handler}.get(self.command)
        elif path.startswith("/urls/") and path.count("/") == 2:
            event["pathParameters"] = {"short_id": path.split("/")[-1]}
            operation = {
                "GET": get_url_stats.handler,
                "DELETE": delete_url.handler,
                "PATCH": update_url.handler,
            }.get(self.command)
        elif path.count("/") == 1 and self.command in {"GET", "HEAD"}:
            event["pathParameters"] = {"short_id": path[1:]}
            operation = redirect_url.handler
        self.respond(
            operation(event, None) if operation else {"statusCode": 404, "body": "Not found"}
        )

    do_GET = route  # noqa: N815 -- BaseHTTPRequestHandler protocol
    do_HEAD = route  # noqa: N815 -- BaseHTTPRequestHandler protocol
    do_POST = route  # noqa: N815 -- BaseHTTPRequestHandler protocol
    do_PATCH = route  # noqa: N815 -- BaseHTTPRequestHandler protocol
    do_DELETE = route  # noqa: N815 -- BaseHTTPRequestHandler protocol
    do_OPTIONS = route  # noqa: N815 -- BaseHTTPRequestHandler protocol


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4310)
    args = parser.parse_args()
    for key in list(os.environ):
        if key.startswith("AWS_"):
            del os.environ[key]
    os.environ.update(
        {
            "AWS_ACCESS_KEY_ID": "testing",
            "AWS_SECRET_ACCESS_KEY": "testing",
            "AWS_DEFAULT_REGION": "us-east-1",
            "AWS_EC2_METADATA_DISABLED": "true",
            "URLS_TABLE_NAME": "local-links",
        }
    )
    with mock_aws():
        boto3.resource("dynamodb").create_table(
            TableName="local-links",
            KeySchema=[{"AttributeName": "short_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "short_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        server = LocalServer(("127.0.0.1", args.port), RequestHandler)
        server.token = secrets.token_urlsafe(32)
        os.environ["PUBLIC_BASE_URL"] = f"http://127.0.0.1:{server.server_port}"
        print(
            f"Local demo: http://127.0.0.1:{server.server_port}/app/ "
            "(temporary data; no AWS connection)",
            flush=True,
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


if __name__ == "__main__":
    main()

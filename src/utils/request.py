"""管理操作の認証境界と本文の読み取り。"""

from __future__ import annotations

import base64
import binascii
import json
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from src.utils.response import error_response

Handler = Callable[[dict[str, Any], Any], dict[str, Any]]
logger = logging.getLogger(__name__)
MAX_BODY_BYTES = 8192


def read_body(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("body") or "{}"
    if not isinstance(raw, str) or len(raw) > MAX_BODY_BYTES * 2:
        raise ValueError("リクエスト本文が大きすぎるか、形式が不正です。")
    try:
        data = (
            base64.b64decode(raw, validate=True) if event.get("isBase64Encoded") else raw.encode()
        )
        if len(data) > MAX_BODY_BYTES:
            raise ValueError("リクエスト本文は8KB以内にしてください。")
        body = json.loads(data.decode("utf-8"))
    except (binascii.Error, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("リクエスト本文のJSONが不正です。") from exc
    if not isinstance(body, dict):
        raise ValueError("リクエスト本文はJSONオブジェクトにしてください。")
    return body


def api_handler(*, management: bool) -> Callable[[Handler], Handler]:
    """API Gatewayが署名検証したclaimsを信頼する。JWTの検証を省略する機能ではない。"""

    def decorate(function: Handler) -> Handler:
        @wraps(function)
        def wrapped(event: dict[str, Any], context: Any) -> dict[str, Any]:
            claims = ((event.get("requestContext") or {}).get("authorizer") or {}).get("claims")
            if management and (
                not isinstance(claims, dict)
                or not isinstance(claims.get("sub"), str)
                or not claims["sub"]
            ):
                return error_response("ログインしてください。", 401)
            try:
                response = function(event, context)
            except ValueError as exc:
                response = error_response(str(exc), 400)
            except (BotoCoreError, ClientError):
                logger.warning("storage_unavailable")
                response = error_response(
                    "保存先に接続できません。少し待って再試行してください。", 503
                )
                response["headers"]["Retry-After"] = "3"
            if event.get("httpMethod") == "HEAD":
                response["body"] = ""
            return response

        return wrapped

    return decorate

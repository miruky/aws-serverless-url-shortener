"""同一オリジンの管理画面と公開設定のみを配信する。"""

from __future__ import annotations

import json
import os
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

WEB_ROOT = Path(__file__).resolve().parents[2] / "web"
FILES = {
    "": ("index.html", "text/html"),
    "index.html": ("index.html", "text/html"),
    "app.js": ("app.js", "text/javascript"),
    "auth.js": ("auth.js", "text/javascript"),
    "style.css": ("style.css", "text/css"),
}


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    path = (event.get("pathParameters") or {}).get("proxy", "")
    domain = os.environ.get("AUTH_DOMAIN", "")
    headers = {
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "X-Frame-Options": "DENY",
        "Cross-Origin-Resource-Policy": "same-origin",
        "Strict-Transport-Security": "max-age=31536000",
        "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; "
        "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; "
        "form-action 'self'; img-src 'self' data:; connect-src 'self'"
        + (f" {domain}" if domain else ""),
    }
    if path == "config":
        headers["Content-Type"] = "application/json; charset=utf-8"
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps(
                {
                    "mode": "cognito",
                    "domain": domain,
                    "client_id": os.environ.get("AUTH_CLIENT_ID", ""),
                }
            ),
        }
    if path not in FILES:
        return {"statusCode": 404, "headers": headers, "body": "Not found"}
    name, content_type = FILES[path]
    headers["Content-Type"] = content_type + "; charset=utf-8"
    body = (WEB_ROOT / name).read_text()
    if name == "index.html":
        asset_path = urlsplit(os.environ.get("PUBLIC_BASE_URL", "")).path.rstrip("/") + "/app"
        body = body.replace("{{ASSET_PATH}}", escape(asset_path, quote=True))
    return {"statusCode": 200, "headers": headers, "body": body}

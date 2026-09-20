"""ステージ付きURLで、末尾のスラッシュに依存せず画面の資源を参照する。"""

from src.handlers.web import handler


def test_management_assets_use_the_configured_stage_path(monkeypatch):
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://example.com/preview")
    response = handler({"path": "/app", "pathParameters": None}, None)
    assert response["statusCode"] == 200
    assert 'href="/preview/app/style.css"' in response["body"]
    assert 'src="/preview/app/app.js"' in response["body"]
    assert 'href="/preview/app/"' in response["body"]

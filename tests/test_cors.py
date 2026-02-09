from fastapi.testclient import TestClient

from notion_synth.main import create_app


def test_cors_disabled_by_default() -> None:
    app = create_app(":memory:")
    client = TestClient(app)
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") is None


def test_cors_enabled_exposes_paging_headers(monkeypatch) -> None:
    origin = "http://localhost:5173"
    monkeypatch.setenv("NOTION_SYNTH_CORS_ORIGINS", origin)

    app = create_app(":memory:")
    client = TestClient(app)

    response = client.get(
        "/pages?limit=1&offset=0&include_pagination=true",
        headers={"Origin": origin},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin

    exposed = (response.headers.get("access-control-expose-headers") or "").lower()
    # Browser clients need these exposed to read paging metadata.
    assert "x-total-count" in exposed
    assert "x-limit" in exposed
    assert "x-offset" in exposed
    assert "x-has-more" in exposed
    assert "x-next-offset" in exposed
    assert "link" in exposed

from fastapi.testclient import TestClient

from notion_synth.main import create_app


def _client() -> TestClient:
    app = create_app("file:testdb?mode=memory&cache=shared")
    return TestClient(app)


def test_health() -> None:
    client = _client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_seeded_pages() -> None:
    client = _client()
    response = client.get("/pages")
    assert response.status_code == 200
    pages = response.json()
    assert len(pages) >= 1
    assert pages[0]["id"]


def test_create_page() -> None:
    client = _client()
    payload = {
        "workspace_id": "ws_demo",
        "title": "Notes",
        "content": {"blocks": ["Line 1", "Line 2"]},
        "parent_type": "workspace",
        "parent_id": "ws_demo",
    }
    response = client.post("/pages", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Notes"
    assert body["content"]["blocks"][0] == "Line 1"

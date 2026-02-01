from fastapi.testclient import TestClient

from notion_synth.main import create_app


def _client() -> TestClient:
    app = create_app(":memory:")
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


def test_homepage_html() -> None:
    client = _client()
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Notion Workspace Synth" in response.text
    assert "/docs" in response.text


def test_stats() -> None:
    client = _client()
    response = client.get("/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["db_path"] == ":memory:"
    assert body["workspaces"] == 1
    assert body["users"] == 3
    assert body["pages"] == 2
    assert body["databases"] == 1
    assert body["database_rows"] == 2
    assert body["comments"] == 2


def test_list_pages_filters_and_total_header() -> None:
    client = _client()

    response = client.get("/pages?title_contains=Welcome&include_total=true")
    assert response.status_code == 200
    assert response.headers.get("x-total-count") == "1"
    pages = response.json()
    assert len(pages) == 1
    assert pages[0]["id"] == "page_home"

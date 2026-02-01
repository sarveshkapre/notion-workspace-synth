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


def test_create_workspace_and_user() -> None:
    client = _client()

    created_ws = client.post("/workspaces", json={"name": "Acme"})
    assert created_ws.status_code == 201
    ws = created_ws.json()
    assert ws["id"].startswith("ws_")
    assert ws["name"] == "Acme"

    created_user = client.post(
        "/users",
        json={"workspace_id": ws["id"], "name": "Taylor", "email": "taylor@example.com"},
    )
    assert created_user.status_code == 201
    user = created_user.json()
    assert user["id"].startswith("user_")
    assert user["workspace_id"] == ws["id"]
    assert user["email"] == "taylor@example.com"

    fetched = client.get(f"/users/{user['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == user["id"]


def test_create_user_rejects_invalid_workspace() -> None:
    client = _client()
    created_user = client.post(
        "/users",
        json={"workspace_id": "ws_does_not_exist", "name": "Taylor", "email": "t@example.com"},
    )
    assert created_user.status_code == 400


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


def test_fixtures_export_import_roundtrip() -> None:
    client_a = TestClient(create_app(":memory:"))
    exported = client_a.get("/fixtures/export")
    assert exported.status_code == 200
    fixture = exported.json()
    assert fixture["format_version"] == 1
    assert len(fixture["pages"]) >= 1

    client_b = TestClient(create_app(":memory:"))
    extra = client_b.post(
        "/pages",
        json={
            "workspace_id": "ws_demo",
            "title": "Extra Page",
            "content": {"blocks": ["Extra"]},
            "parent_type": "workspace",
            "parent_id": "ws_demo",
        },
    )
    assert extra.status_code == 201

    imported = client_b.post("/fixtures/import?mode=replace", json=fixture)
    assert imported.status_code == 200
    body = imported.json()
    assert body["status"] == "ok"
    assert body["inserted"]["workspaces"] == 1

    stats = client_b.get("/stats").json()
    assert stats["workspaces"] == body["inserted"]["workspaces"]
    assert stats["pages"] == body["inserted"]["pages"]
    assert stats["databases"] == body["inserted"]["databases"]

    # Merge should not delete existing objects.
    client_c = TestClient(create_app(":memory:"))
    extra_c = client_c.post(
        "/pages",
        json={
            "workspace_id": "ws_demo",
            "title": "Extra Page",
            "content": {"blocks": ["Extra"]},
            "parent_type": "workspace",
            "parent_id": "ws_demo",
        },
    )
    assert extra_c.status_code == 201

    merged = client_c.post("/fixtures/import?mode=merge", json=fixture)
    assert merged.status_code == 200
    merged_stats = client_c.get("/stats").json()
    assert merged_stats["pages"] == body["inserted"]["pages"] + 1
    extra_pages = client_c.get("/pages?title_contains=Extra%20Page").json()
    assert len(extra_pages) == 1

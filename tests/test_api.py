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


def test_delete_workspace_requires_cascade_and_cascades() -> None:
    client = _client()

    created_ws = client.post("/workspaces", json={"name": "Acme"})
    assert created_ws.status_code == 201
    ws_id = created_ws.json()["id"]

    created_user = client.post(
        "/users",
        json={"workspace_id": ws_id, "name": "Taylor", "email": "taylor@example.com"},
    )
    assert created_user.status_code == 201
    user_id = created_user.json()["id"]

    created_page = client.post(
        "/pages",
        json={
            "workspace_id": ws_id,
            "title": "Notes",
            "content": {"blocks": ["Line 1"]},
            "parent_type": "workspace",
            "parent_id": ws_id,
        },
    )
    assert created_page.status_code == 201
    page_id = created_page.json()["id"]

    created_db = client.post(
        "/databases",
        json={
            "workspace_id": ws_id,
            "name": "Tickets",
            "schema": {"properties": {"Title": {"type": "title"}, "Status": {"type": "select"}}},
        },
    )
    assert created_db.status_code == 201
    db_id = created_db.json()["id"]

    created_row = client.post(
        f"/databases/{db_id}/rows",
        json={"properties": {"Title": "Investigate", "Status": "Open"}},
    )
    assert created_row.status_code == 201

    created_comment = client.post(
        "/comments",
        json={"page_id": page_id, "author_id": user_id, "body": "Ship it."},
    )
    assert created_comment.status_code == 201

    refused = client.delete(f"/workspaces/{ws_id}")
    assert refused.status_code == 409
    detail = refused.json()["detail"]
    assert detail["workspace_id"] == ws_id
    assert detail["counts"]["users"] == 1
    assert detail["counts"]["pages"] == 1
    assert detail["counts"]["databases"] == 1
    assert detail["counts"]["database_rows"] == 1
    assert detail["counts"]["comments"] == 1

    preview = client.delete(f"/workspaces/{ws_id}?dry_run=true")
    assert preview.status_code == 200
    body = preview.json()
    assert body["workspace_id"] == ws_id
    assert body["requires_force"] is False
    assert body["requires_cascade"] is True
    assert body["can_delete"] is False
    assert body["counts"]["users"] == 1
    assert client.get(f"/workspaces/{ws_id}").status_code == 200

    deleted = client.delete(f"/workspaces/{ws_id}?cascade=true")
    assert deleted.status_code == 204
    assert client.get(f"/workspaces/{ws_id}").status_code == 404
    assert client.get(f"/users?workspace_id={ws_id}").json() == []
    assert client.get(f"/pages?workspace_id={ws_id}").json() == []
    assert client.get(f"/databases?workspace_id={ws_id}").json() == []
    assert client.get(f"/comments?author_id={user_id}").json() == []


def test_delete_demo_workspace_requires_force() -> None:
    client = _client()

    preview = client.delete("/workspaces/ws_demo?dry_run=true")
    assert preview.status_code == 200
    body = preview.json()
    assert body["workspace_id"] == "ws_demo"
    assert body["requires_force"] is True
    assert body["requires_cascade"] is True
    assert body["can_delete"] is False

    preview_ok = client.delete("/workspaces/ws_demo?dry_run=true&cascade=true&force=true")
    assert preview_ok.status_code == 200
    assert preview_ok.json()["can_delete"] is True

    refused = client.delete("/workspaces/ws_demo?cascade=true")
    assert refused.status_code == 400

    deleted = client.delete("/workspaces/ws_demo?cascade=true&force=true")
    assert deleted.status_code == 204
    assert client.get("/workspaces/ws_demo").status_code == 404
    assert client.get("/stats").json()["workspaces"] == 0


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


def test_list_pages_pagination_headers() -> None:
    client = _client()

    response = client.get("/pages?limit=1&offset=0&include_pagination=true")
    assert response.status_code == 200
    assert response.headers.get("x-limit") == "1"
    assert response.headers.get("x-offset") == "0"
    assert response.headers.get("x-has-more") == "true"
    assert response.headers.get("x-next-offset") == "1"
    assert "rel=\"next\"" in response.headers.get("link", "")
    assert "offset=1" in response.headers.get("link", "")
    assert len(response.json()) == 1

    last_page = client.get("/pages?limit=1&offset=1&include_pagination=true")
    assert last_page.status_code == 200
    assert last_page.headers.get("x-has-more") == "false"
    assert last_page.headers.get("x-next-offset") is None
    assert last_page.headers.get("link") is None
    assert len(last_page.json()) == 1


def test_search_pages() -> None:
    client = _client()
    response = client.get("/search/pages?q=Welcome")
    assert response.status_code == 200
    pages = response.json()
    assert [page["id"] for page in pages] == ["page_home"]

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


def test_delete_page_also_deletes_comments() -> None:
    client = _client()
    seeded_comments = client.get("/comments?page_id=page_home").json()
    assert len(seeded_comments) == 1

    deleted = client.delete("/pages/page_home")
    assert deleted.status_code == 204
    assert client.get("/pages/page_home").status_code == 404
    assert client.get("/comments?page_id=page_home").json() == []


def test_delete_user_also_deletes_authored_comments() -> None:
    client = _client()

    assert len(client.get("/comments?author_id=user_alex").json()) == 1
    deleted = client.delete("/users/user_alex")
    assert deleted.status_code == 204

    assert client.get("/users/user_alex").status_code == 404
    assert client.get("/comments?author_id=user_alex").json() == []
    assert len(client.get("/comments").json()) == 1


def test_comment_get_and_delete() -> None:
    client = _client()
    created = client.post(
        "/comments",
        json={"page_id": "page_home", "author_id": "user_bianca", "body": "Ship it."},
    )
    assert created.status_code == 201
    comment_id = created.json()["id"]

    fetched = client.get(f"/comments/{comment_id}")
    assert fetched.status_code == 200
    assert fetched.json()["body"] == "Ship it."

    deleted = client.delete(f"/comments/{comment_id}")
    assert deleted.status_code == 204
    assert client.get(f"/comments/{comment_id}").status_code == 404


def test_database_update_delete_and_rows_crud() -> None:
    client = _client()

    created_db = client.post(
        "/databases",
        json={
            "workspace_id": "ws_demo",
            "name": "Tickets",
            "schema": {"properties": {"Title": {"type": "title"}}},
        },
    )
    assert created_db.status_code == 201
    db_id = created_db.json()["id"]

    updated_db = client.patch(f"/databases/{db_id}", json={"name": "Tickets v2"})
    assert updated_db.status_code == 200
    assert updated_db.json()["name"] == "Tickets v2"

    created_row = client.post(
        f"/databases/{db_id}/rows",
        json={"properties": {"Title": "Hello"}},
    )
    assert created_row.status_code == 201
    row_id = created_row.json()["id"]

    fetched_row = client.get(f"/databases/{db_id}/rows/{row_id}")
    assert fetched_row.status_code == 200
    assert fetched_row.json()["properties"]["Title"] == "Hello"

    updated_row = client.patch(
        f"/databases/{db_id}/rows/{row_id}",
        json={"properties": {"Title": "Hello v2"}},
    )
    assert updated_row.status_code == 200
    assert updated_row.json()["properties"]["Title"] == "Hello v2"

    deleted_row = client.delete(f"/databases/{db_id}/rows/{row_id}")
    assert deleted_row.status_code == 204
    assert client.get(f"/databases/{db_id}/rows/{row_id}").status_code == 404

    deleted_db = client.delete(f"/databases/{db_id}")
    assert deleted_db.status_code == 204
    assert client.get(f"/databases/{db_id}").status_code == 404


def test_database_rows_filtering_and_total_header() -> None:
    client = _client()
    response = client.get(
        "/databases/db_tasks/rows?property_name=Task&property_value_contains=Prototype&include_total=true"
    )
    assert response.status_code == 200
    assert response.headers.get("x-total-count") == "1"

    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["id"] == "row_1"

    status_rows = client.get(
        "/databases/db_tasks/rows?property_name=Status&property_value_contains=Done"
    )
    assert status_rows.status_code == 200
    assert len(status_rows.json()) == 1
    assert status_rows.json()[0]["id"] == "row_2"

    status_exact = client.get(
        "/databases/db_tasks/rows?property_name=Status&property_value_equals=Done&include_total=true"
    )
    assert status_exact.status_code == 200
    assert status_exact.headers.get("x-total-count") == "1"
    assert [row["id"] for row in status_exact.json()] == ["row_2"]

    status_equals = client.get("/databases/db_tasks/rows?property_equals=Status:Done")
    assert status_equals.status_code == 200
    assert [row["id"] for row in status_equals.json()] == ["row_2"]

    multi = client.get(
        "/databases/db_tasks/rows?property_equals=Status:Done&property_equals=Task:Seed%20demo%20data"
    )
    assert multi.status_code == 200
    assert [row["id"] for row in multi.json()] == ["row_2"]

    rejected = client.get("/databases/db_tasks/rows?property_equals=badformat")
    assert rejected.status_code == 400


def test_create_database_rejects_invalid_workspace() -> None:
    client = _client()
    created_db = client.post(
        "/databases",
        json={
            "workspace_id": "ws_does_not_exist",
            "name": "X",
            "schema": {"properties": {"Title": {"type": "title"}}},
        },
    )
    assert created_db.status_code == 400


def test_create_database_row_rejects_invalid_database() -> None:
    client = _client()
    created_row = client.post(
        "/databases/db_does_not_exist/rows",
        json={"properties": {"Title": "X"}},
    )
    assert created_row.status_code == 400

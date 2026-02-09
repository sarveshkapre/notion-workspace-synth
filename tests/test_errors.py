from __future__ import annotations

from fastapi.testclient import TestClient

from notion_synth.main import create_app


def _client() -> TestClient:
    app = create_app(":memory:")
    return TestClient(app)


def test_request_id_header_on_success() -> None:
    client = _client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Request-Id")


def test_default_error_shape_unchanged() -> None:
    client = _client()
    response = client.get("/workspaces/ws_does_not_exist")
    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_structured_error_shape_opt_in() -> None:
    client = _client()
    response = client.get(
        "/workspaces/ws_does_not_exist",
        headers={"Accept": "application/vnd.notion-synth.error+json"},
    )
    assert response.status_code == 404
    payload = response.json()
    assert "error" in payload
    assert payload["error"]["code"] == "not_found"
    assert payload["error"]["message"] == "Workspace not found"
    assert payload["error"]["request_id"] == response.headers.get("X-Request-Id")


def test_structured_error_preserves_object_details() -> None:
    client = _client()
    created_ws = client.post("/workspaces", json={"name": "Acme"})
    assert created_ws.status_code == 201
    ws_id = created_ws.json()["id"]

    created_user = client.post(
        "/users",
        json={"workspace_id": ws_id, "name": "Taylor", "email": "taylor@example.com"},
    )
    assert created_user.status_code == 201

    refused = client.delete(
        f"/workspaces/{ws_id}",
        headers={"Accept": "application/vnd.notion-synth.error+json"},
    )
    assert refused.status_code == 409
    payload = refused.json()
    assert payload["error"]["code"] == "conflict"
    assert isinstance(payload["error"]["details"], dict)
    assert payload["error"]["details"]["workspace_id"] == ws_id


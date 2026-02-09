from __future__ import annotations

from fastapi.testclient import TestClient

from notion_synth.main import create_app


def _client() -> TestClient:
    app = create_app(":memory:")
    return TestClient(app)


def test_list_packs() -> None:
    client = _client()
    response = client.get("/packs")
    assert response.status_code == 200
    packs = response.json()
    assert isinstance(packs, list)
    assert any(p["name"] == "engineering_small" for p in packs)
    assert any(p["name"] == "engineering" for p in packs)
    assert any(p["name"] == "engineering_large" for p in packs)


def test_admin_apply_pack_requires_admin_enabled(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_SYNTH_ADMIN", raising=False)
    client = _client()
    response = client.post("/admin/apply-pack?name=engineering_small&confirm=true")
    assert response.status_code == 404


def test_admin_apply_pack_preview_and_apply(monkeypatch) -> None:
    monkeypatch.setenv("NOTION_SYNTH_ADMIN", "1")
    client = _client()

    preview = client.post("/admin/apply-pack?name=engineering_small&dry_run=true")
    assert preview.status_code == 200
    payload = preview.json()
    assert payload["status"] == "preview"
    assert payload["pack"]["name"] == "engineering_small"
    assert payload["before"] == payload["after"]
    assert payload["expected_inserted"]["workspaces"] == 1
    assert payload["expected_inserted"]["users"] == payload["pack"]["counts"]["users"]

    refused = client.post("/admin/apply-pack?name=engineering_small")
    assert refused.status_code == 400

    applied = client.post("/admin/apply-pack?name=engineering_small&confirm=true")
    assert applied.status_code == 200
    result = applied.json()
    assert result["status"] == "ok"
    assert result["pack"]["name"] == "engineering_small"
    assert result["after"]["workspaces"] == 1
    assert result["after"]["users"] == result["pack"]["counts"]["users"]

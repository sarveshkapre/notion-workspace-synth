import json
import time

import httpx

from notion_synth.cli import main
from notion_synth.providers.entra.graph import GraphClient
from notion_synth.providers.notion.client import NotionClient


def test_notion_client_retries_on_429(monkeypatch) -> None:
    calls: list[tuple[str, str, dict[str, str] | None, object | None]] = []
    slept: list[float] = []

    def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    def fake_request(
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json: object | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        _ = timeout
        calls.append((method, url, headers, json))
        req = httpx.Request(method, url)
        if len(calls) == 1:
            return httpx.Response(
                429,
                headers={"retry-after": "0"},
                json={"error": "rate limited"},
                request=req,
            )
        return httpx.Response(200, json={"ok": True}, request=req)

    monkeypatch.setattr(time, "sleep", fake_sleep)
    monkeypatch.setattr(httpx, "request", fake_request)

    client = NotionClient(token="tok", max_retries=2, timeout=1)
    payload = client.request("GET", "/pages/page_123")
    assert payload["ok"] is True
    assert len(calls) == 2
    assert slept == [0.0]
    assert calls[0][2] is not None
    assert calls[0][2]["Authorization"] == "Bearer tok"
    assert calls[0][2]["Notion-Version"]


def test_graph_client_returns_empty_dict_on_204(monkeypatch) -> None:
    token_calls: list[str] = []
    req_calls: list[tuple[str, str, dict[str, str] | None]] = []

    def fake_post(url: str, *, data: dict[str, str], timeout: float) -> httpx.Response:
        _ = timeout
        token_calls.append(url)
        req = httpx.Request("POST", url)
        return httpx.Response(200, json={"access_token": "graph_token"}, request=req)

    def fake_request(
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json: object | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        _ = (json, timeout)
        req_calls.append((method, url, headers))
        req = httpx.Request(method, url)
        return httpx.Response(204, request=req)

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(httpx, "request", fake_request)

    client = GraphClient(tenant_id="t", client_id="c", client_secret="s", max_retries=0, timeout=1)
    assert client.request("DELETE", "/users/user_123") == {}
    assert token_calls
    assert req_calls
    assert req_calls[0][2] is not None
    assert req_calls[0][2]["Authorization"] == "Bearer graph_token"


def test_cli_generate_smoke(capsys) -> None:
    rc = main(
        [
            "generate",
            "--company",
            "Acme Robotics",
            "--seed",
            "2026",
            "--users",
            "8",
            "--teams",
            "2",
            "--projects",
            "2",
            "--incidents",
            "1",
            "--candidates",
            "2",
            "--output",
            "-",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out.strip()
    data = json.loads(out)
    assert data["format_version"] == 1
    assert data["workspaces"]


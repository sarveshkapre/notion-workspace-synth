#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import suppress
import urllib.error
import urllib.request


def main() -> int:
    port = _pick_free_port()
    base_url = f"http://127.0.0.1:{port}"

    tmp_db = tempfile.NamedTemporaryFile(prefix="notion_synth.", suffix=".db", delete=False)
    tmp_db.close()

    env = dict(os.environ)
    env["NOTION_SYNTH_DB"] = tmp_db.name
    env["NOTION_SYNTH_ADMIN"] = "1"

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "notion_synth.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        env=env,
        # Inherit stdout/stderr so failures are visible when running locally.
    )

    try:
        _wait_for_health(f"{base_url}/health", timeout_s=20)

        packs = _json_request("GET", f"{base_url}/packs")
        assert any(p.get("name") == "engineering_small" for p in packs)

        preview = _json_request("POST", f"{base_url}/admin/apply-pack?name=engineering_small&dry_run=true")
        assert preview.get("status") == "preview"

        applied = _json_request("POST", f"{base_url}/admin/apply-pack?name=engineering_small&confirm=true")
        assert applied.get("status") == "ok"

        workspaces = _json_request("GET", f"{base_url}/workspaces")
        ws_id = workspaces[0]["id"]

        created_page = _json_request(
            "POST",
            f"{base_url}/pages",
            {
                "workspace_id": ws_id,
                "title": "Smoke Page",
                "content": {"type": "doc", "blocks": ["hello"]},
                "attachments": [
                    {"name": "smoke-plan.txt", "mime_type": "text/plain", "size_bytes": 321}
                ],
                "parent_type": "workspace",
                "parent_id": ws_id,
            },
        )
        page_id = str(created_page["id"])

        search = _json_request("GET", f"{base_url}/search/pages?q=Smoke")
        assert any("Smoke" in p.get("title", "") for p in search)

        users = _json_request("GET", f"{base_url}/users?workspace_id={ws_id}")
        assert users
        author_id = str(users[0]["id"])

        comment = _json_request(
            "POST",
            f"{base_url}/comments",
            {
                "page_id": page_id,
                "author_id": author_id,
                "body": "Smoke comment note",
                "attachments": [
                    {"name": "smoke-comment.md", "mime_type": "text/markdown", "size_bytes": 144}
                ],
            },
        )
        assert str(comment.get("id", "")).startswith("comment_")

        comment_search = _json_request("GET", f"{base_url}/search/comments?q=Smoke")
        assert any("Smoke" in c.get("body", "") for c in comment_search)

        row_search = _json_request("GET", f"{base_url}/search/rows?q=Project&property_name=Name")
        assert row_search
        return 0
    except Exception:
        raise
    finally:
        _terminate(proc)
        with suppress(OSError):
            os.unlink(tmp_db.name)


def _pick_free_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])
    finally:
        sock.close()


def _wait_for_health(url: str, *, timeout_s: int) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            _json_request("GET", url)
            return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError(f"Server did not become healthy within {timeout_s}s")


def _json_request(method: str, url: str, payload: object | None = None) -> object:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["content-type"] = "application/json"
    req = urllib.request.Request(url, method=method, data=data, headers=headers)  # noqa: S310
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> {exc.code}: {body}") from exc


def _terminate(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    with suppress(ProcessLookupError):
        proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=3)
        return
    except subprocess.TimeoutExpired:
        with suppress(ProcessLookupError):
            proc.kill()
        with suppress(ProcessLookupError):
            proc.wait(timeout=3)


if __name__ == "__main__":
    raise SystemExit(main())

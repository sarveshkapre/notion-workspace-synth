from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx


DEFAULT_NOTION_VERSION = "2022-06-28"


@dataclass
class NotionClient:
    token: str
    base_url: str = "https://api.notion.com/v1"
    version: str = DEFAULT_NOTION_VERSION
    timeout: float = 30.0
    max_retries: int = 5

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.version,
            "Content-Type": "application/json",
        }

    def request(self, method: str, path: str, *, json: Any | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        retries = 0
        while True:
            response = httpx.request(
                method,
                url,
                headers=self._headers(),
                json=json,
                timeout=self.timeout,
            )
            if response.status_code in {429, 500, 502, 503, 504} and retries < self.max_retries:
                wait = _retry_delay(response, retries)
                time.sleep(wait)
                retries += 1
                continue
            response.raise_for_status()
            return response.json()

    def list_users(self) -> list[dict[str, Any]]:
        users: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            payload = {"page_size": 100}
            if cursor:
                payload["start_cursor"] = cursor
            data = self.request("POST", "/users/list", json=payload)
            users.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return users

    def create_page(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/pages", json=payload)

    def update_page(self, page_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("PATCH", f"/pages/{page_id}", json=payload)

    def create_database(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/databases", json=payload)

    def update_database(self, database_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("PATCH", f"/databases/{database_id}", json=payload)

    def create_comment(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/comments", json=payload)

    def archive_page(self, page_id: str) -> dict[str, Any]:
        return self.request("PATCH", f"/pages/{page_id}", json={"archived": True})

    def get_page(self, page_id: str) -> dict[str, Any]:
        return self.request("GET", f"/pages/{page_id}")


def _retry_delay(response: httpx.Response, retries: int) -> float:
    retry_after = response.headers.get("retry-after")
    if retry_after:
        try:
            return float(retry_after)
        except ValueError:
            pass
    return min(2 ** retries, 20)

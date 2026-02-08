from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, cast

import httpx


@dataclass
class GraphClient:
    tenant_id: str
    client_id: str
    client_secret: str
    base_url: str = "https://graph.microsoft.com/v1.0"
    timeout: float = 30.0
    max_retries: int = 5

    def _token(self) -> str:
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        response = httpx.post(
            token_url,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "https://graph.microsoft.com/.default",
                "grant_type": "client_credentials",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return cast(str, response.json()["access_token"])

    def request(self, method: str, path: str, *, json: Any | None = None) -> dict[str, Any]:
        token = self._token()
        url = f"{self.base_url}{path}"
        retries = 0
        while True:
            response = httpx.request(
                method,
                url,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=json,
                timeout=self.timeout,
            )
            if response.status_code in {429, 500, 502, 503, 504} and retries < self.max_retries:
                time.sleep(min(2 ** retries, 20))
                retries += 1
                continue
            response.raise_for_status()
            if response.status_code == 204:
                return {}
            return cast(dict[str, Any], response.json())

    def find_user_by_upn(self, upn: str) -> dict[str, Any] | None:
        encoded = upn.replace("'", "''")
        response = self.request("GET", f"/users?$filter=userPrincipalName eq '{encoded}'")
        values = response.get("value", [])
        return values[0] if values else None

    def create_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/users", json=payload)

    def find_group_by_name(self, name: str) -> dict[str, Any] | None:
        encoded = name.replace("'", "''")
        response = self.request("GET", f"/groups?$filter=displayName eq '{encoded}'")
        values = response.get("value", [])
        return values[0] if values else None

    def create_group(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/groups", json=payload)

    def add_member(self, group_id: str, user_id: str) -> None:
        self.request(
            "POST",
            f"/groups/{group_id}/members/$ref",
            json={"@odata.id": f"{self.base_url}/directoryObjects/{user_id}"},
        )

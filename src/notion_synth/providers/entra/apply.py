from __future__ import annotations

import secrets
from dataclasses import dataclass

import httpx

from notion_synth.blueprint_models import IdentityUser
from notion_synth.providers.entra.graph import GraphClient
from notion_synth.state import StateStore, upsert_identity


@dataclass
class EntraApplyResult:
    created_users: int = 0
    existing_users: int = 0
    created_groups: int = 0
    existing_groups: int = 0
    memberships_added: int = 0


def apply_entra(
    *,
    client: GraphClient,
    roster: list[IdentityUser],
    groups: dict[str, list[IdentityUser]],
    store: StateStore,
    mode: str = "create",
    dry_run: bool = False,
) -> EntraApplyResult:
    if mode not in {"create", "sync"}:
        raise ValueError("mode must be 'create' or 'sync'")
    result = EntraApplyResult()

    group_ids: dict[str, str] = {}
    for group_name, _members in groups.items():
        existing = client.find_group_by_name(group_name)
        if existing:
            group_ids[group_name] = existing["id"]
            result.existing_groups += 1
            continue
        if mode == "sync":
            continue
        if dry_run:
            result.created_groups += 1
            continue
        created = client.create_group(
            {
                "displayName": group_name,
                "mailEnabled": False,
                "mailNickname": group_name.replace(" ", "").lower()[:40],
                "securityEnabled": True,
            }
        )
        group_ids[group_name] = created["id"]
        result.created_groups += 1

    for user in roster:
        if not user.upn:
            raise ValueError("Roster entries must include upn for Entra provisioning.")
        existing = client.find_user_by_upn(user.upn)
        if existing:
            upsert_identity(store, user.synth_user_id, entra_object_id=existing["id"], email=user.email)
            result.existing_users += 1
            continue
        if mode == "sync":
            continue
        if dry_run:
            result.created_users += 1
            continue
        password = _random_password()
        created = client.create_user(
            {
                "accountEnabled": True,
                "displayName": user.display_name,
                "mailNickname": user.upn.split("@")[0],
                "userPrincipalName": user.upn,
                "givenName": user.given_name,
                "surname": user.surname,
                "jobTitle": user.job_title,
                "department": user.department,
                "officeLocation": user.office_location,
                "passwordProfile": {"forceChangePasswordNextSignIn": True, "password": password},
            }
        )
        upsert_identity(store, user.synth_user_id, entra_object_id=created["id"], email=user.email)
        result.created_users += 1

    # Memberships
    for group_name, members in groups.items():
        group_id = group_ids.get(group_name)
        if not group_id:
            continue
        for member in members:
            identity = store.query_one(
                "SELECT entra_object_id FROM identity_map WHERE synth_user_id = ?", [member.synth_user_id]
            )
            if not identity or not identity["entra_object_id"]:
                continue
            if dry_run:
                result.memberships_added += 1
                continue
            try:
                client.add_member(group_id, identity["entra_object_id"])
                result.memberships_added += 1
            except httpx.HTTPStatusError as exc:
                if exc.response is not None and exc.response.status_code in {400, 409}:
                    continue
                raise

    return result


def _random_password() -> str:
    return f"Aa{secrets.token_urlsafe(12)}1!"

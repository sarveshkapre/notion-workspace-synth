from __future__ import annotations

from dataclasses import dataclass

from notion_synth.blueprint_models import IdentityUser
from notion_synth.providers.entra.graph import GraphClient
from notion_synth.providers.notion.client import NotionClient
from notion_synth.state import StateStore, upsert_identity


@dataclass
class ProvisioningReport:
    total: int
    matched: int
    missing_in_entra: list[str]
    missing_in_notion: list[str]
    missing_groups: list[str]


def verify_provisioning(
    *,
    graph: GraphClient,
    notion: NotionClient,
    roster: list[IdentityUser],
    company: str,
    store: StateStore,
) -> ProvisioningReport:
    missing_in_entra: list[str] = []
    missing_in_notion: list[str] = []
    missing_groups: list[str] = []

    # Entra users
    for user in roster:
        if not user.upn:
            continue
        if not graph.find_user_by_upn(user.upn):
            missing_in_entra.append(user.upn)

    # Entra groups
    groups = sorted({f"SYNTH-{company}-{user.team}" for user in roster if user.team})
    for group in groups:
        if not graph.find_group_by_name(group):
            missing_groups.append(group)

    # Notion users
    notion_users = notion.list_users()
    email_map: dict[str, str] = {}
    for notion_user in notion_users:
        person = notion_user.get("person") or {}
        email = person.get("email")
        if email:
            notion_user_id = notion_user.get("id")
            if notion_user_id:
                email_map[email.lower()] = notion_user_id

    matched = 0
    for user in roster:
        email = user.email.lower() if user.email else ""
        if email and email in email_map:
            upsert_identity(store, user.synth_user_id, notion_user_id=email_map[email], email=email)
            matched += 1
        elif email:
            missing_in_notion.append(email)

    return ProvisioningReport(
        total=len(roster),
        matched=matched,
        missing_in_entra=missing_in_entra,
        missing_in_notion=missing_in_notion,
        missing_groups=missing_groups,
    )

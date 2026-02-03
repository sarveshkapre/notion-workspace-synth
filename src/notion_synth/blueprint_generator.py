from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from notion_synth.blueprint_models import (
    ActivityEvent,
    Blueprint,
    CommentSpec,
    DatabaseSpec,
    GroupMembership,
    IdentityGroup,
    IdentitySpec,
    IdentityUser,
    NotionPlan,
    PageSpec,
    RootSpec,
    RowPropertySpec,
    RowSpec,
    BlockSpec,
)
from notion_synth.util import stable_uuid, utc_now


@dataclass(frozen=True)
class BlueprintConfig:
    company: str
    seed: int
    org_profile: str
    scale: str


SCALE_PRESETS = {
    "small": {
        "pages_per_team": 12,
        "kb_pages": 15,
        "onboarding_pages": 10,
        "meeting_notes": 18,
        "tasks": 120,
        "projects": 20,
        "incidents": 18,
    }
}


def generate_blueprint(
    config: BlueprintConfig,
    roster: list[IdentityUser],
) -> Blueprint:
    rng = random.Random(config.seed)
    preset = SCALE_PRESETS.get(config.scale, SCALE_PRESETS["small"])
    teams = sorted({user.team for user in roster if user.team})
    if not teams:
        teams = ["Platform", "Product Engineering", "SRE", "Security", "Data"]

    groups = [
        IdentityGroup(
            synth_group_id=f"group_{stable_uuid(f'{config.company}:{team}')}",
            name=f"{config.company} · {team}",
            description=f"{team} team group",
        )
        for team in teams
    ]
    memberships = []
    for user in roster:
        matching = next((g for g in groups if g.name.endswith(user.team)), None)
        if matching:
            memberships.append(
                GroupMembership(group_synth_id=matching.synth_group_id, user_synth_id=user.synth_user_id)
            )

    identity = IdentitySpec(users=roster, groups=groups, memberships=memberships)

    roots = [
        RootSpec(
            synth_id=f"page_{stable_uuid(f'{config.company}:root:{team}')}",
            title=f"{team} Team",
        )
        for team in teams
    ]

    handbook = PageSpec(
        synth_id=f"page_{stable_uuid(f'{config.company}:handbook')}",
        parent_synth_id="root",
        parent_type="root",
        title="📚 Company Handbook",
        blocks=_paragraph_blocks(
            [
                f"{config.company} builds reliable software with high empathy for customers.",
                "Operating principles:",
                "- Customer empathy first",
                "- Secure by default",
                "- Measure and iterate",
                "Key rituals: weekly planning, monthly retros, quarterly roadmap reviews.",
            ]
        ),
    )

    overview = PageSpec(
        synth_id=f"page_{stable_uuid(f'{config.company}:engineering-overview')}",
        parent_synth_id="root",
        parent_type="root",
        title="Engineering Overview",
        blocks=_paragraph_blocks(
            [
                f"Engineering spans {len(teams)} teams with shared platform standards.",
                "Current focus areas:",
                "- Platform observability",
                "- Reliability automation",
                "- Developer enablement",
                "Team list: " + ", ".join(teams),
            ]
        ),
    )

    pages: list[PageSpec] = [handbook, overview]
    for team in teams:
        parent_id = next(r.synth_id for r in roots if r.title.startswith(team))
        for index in range(preset["pages_per_team"]):
            title = f"{team} Working Doc {index + 1}"
            pages.append(
                PageSpec(
                    synth_id=f"page_{stable_uuid(f'{config.company}:{team}:doc:{index}')}",
                    parent_synth_id=parent_id,
                    parent_type="page",
                    title=title,
                    blocks=_paragraph_blocks(
                        [
                            f"Mission: {team} delivers quarterly milestones with high availability.",
                            "Current priorities:",
                            "- Reliability OKRs",
                            "- Automation backlog",
                            "- Cross-team alignment",
                            "Related: [[synth:page:page_"
                            + stable_uuid(f'{config.company}:engineering-overview')
                            + "]]",
                        ]
                    ),
                )
            )

    for index in range(preset["kb_pages"]):
        pages.append(
            PageSpec(
                synth_id=f"page_{stable_uuid(f'{config.company}:kb:{index}')}",
                parent_synth_id="root",
                parent_type="root",
                title=f"KB: {rng.choice(_KB_TOPICS)}",
                blocks=_paragraph_blocks(
                    [
                        rng.choice(_KB_SNIPPETS),
                        "Owner: [[synth:user:"
                        + rng.choice(roster).synth_user_id
                        + "]]"
                        if roster
                        else "Owner: TBD",
                    ]
                ),
            )
        )

    for index in range(preset["onboarding_pages"]):
        pages.append(
            PageSpec(
                synth_id=f"page_{stable_uuid(f'{config.company}:onboarding:{index}')}",
                parent_synth_id="root",
                parent_type="root",
                title=f"Onboarding Week {index + 1}",
                blocks=_paragraph_blocks(
                    [
                        "Week goals:",
                        "- Workspace tour",
                        "- Access provisioning",
                        "- Pairing sessions",
                    ]
                ),
            )
        )

    for index in range(preset["meeting_notes"]):
        team = teams[index % len(teams)]
        pages.append(
            PageSpec(
                synth_id=f"page_{stable_uuid(f'{config.company}:{team}:meeting:{index}')}",
                parent_synth_id="root",
                parent_type="root",
                title=f"{team} Sync {index + 1}",
                blocks=_paragraph_blocks(
                    [
                        "Agenda:",
                        "- Metrics review",
                        "- Risks and blockers",
                        "- Next steps",
                        "Action owner: [[synth:user:"
                        + rng.choice(roster).synth_user_id
                        + "]]"
                        if roster
                        else "Action owner: TBD",
                    ]
                ),
            )
        )

    databases = [
        DatabaseSpec(
            synth_id=f"db_{stable_uuid(f'{config.company}:projects')}",
            parent_synth_id="root",
            parent_type="root",
            title="Projects",
            properties={
                "Name": {"title": {}},
                "Owner": {"people": {}},
                "Team": {"select": {"options": [{"name": team} for team in teams]}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Planned"},
                            {"name": "In Progress"},
                            {"name": "On Hold"},
                            {"name": "Done"},
                        ]
                    }
                },
                "Target": {"date": {}},
            },
        ),
        DatabaseSpec(
            synth_id=f"db_{stable_uuid(f'{config.company}:tasks')}",
            parent_synth_id="root",
            parent_type="root",
            title="Tasks",
            properties={
                "Task": {"title": {}},
                "Owner": {"people": {}},
                "Team": {"select": {"options": [{"name": team} for team in teams]}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Todo"},
                            {"name": "In Progress"},
                            {"name": "Blocked"},
                            {"name": "Done"},
                        ]
                    }
                },
                "Due": {"date": {}},
                "Priority": {
                    "select": {"options": [{"name": "P0"}, {"name": "P1"}, {"name": "P2"}]}
                },
            },
        ),
        DatabaseSpec(
            synth_id=f"db_{stable_uuid(f'{config.company}:incidents')}",
            parent_synth_id="root",
            parent_type="root",
            title="Incidents",
            properties={
                "Title": {"title": {}},
                "Severity": {"select": {"options": [{"name": "SEV1"}, {"name": "SEV2"}, {"name": "SEV3"}]}},
                "Status": {
                    "select": {
                        "options": [{"name": "Resolved"}, {"name": "Monitoring"}, {"name": "Postmortem"}]
                    }
                },
                "Owner": {"people": {}},
                "Detected": {"date": {}},
                "Resolved": {"date": {}},
            },
        ),
        DatabaseSpec(
            synth_id=f"db_{stable_uuid(f'{config.company}:meetings')}",
            parent_synth_id="root",
            parent_type="root",
            title="Meetings",
            properties={
                "Title": {"title": {}},
                "Team": {"select": {"options": [{"name": team} for team in teams]}},
                "Host": {"people": {}},
                "Date": {"date": {}},
                "Notes": {"rich_text": {}},
            },
        ),
        DatabaseSpec(
            synth_id=f"db_{stable_uuid(f'{config.company}:kb')}",
            parent_synth_id="root",
            parent_type="root",
            title="Knowledge Base",
            properties={
                "Title": {"title": {}},
                "Category": {"select": {"options": [{"name": "Runbook"}, {"name": "How-to"}, {"name": "Spec"}]}},
                "Owner": {"people": {}},
                "Last Reviewed": {"date": {}},
                "Link": {"url": {}},
            },
        ),
        DatabaseSpec(
            synth_id=f"db_{stable_uuid(f'{config.company}:onboarding')}",
            parent_synth_id="root",
            parent_type="root",
            title="Onboarding",
            properties={
                "Title": {"title": {}},
                "Owner": {"people": {}},
                "Week": {"number": {"format": "number"}},
                "Complete": {"checkbox": {}},
            },
        ),
    ]

    rows = _build_rows(config, roster, teams, preset, rng)
    comments = _build_comments(config, pages, roster, rng)
    activity_stream = _build_activity_stream(config, pages, rows, rng)

    notion_plan = NotionPlan(roots=roots, databases=databases, pages=pages, rows=rows, comments=comments)

    return Blueprint(
        generated_at=utc_now(),
        seed=config.seed,
        company=config.company,
        org_profile=config.org_profile,
        identity=identity,
        notion_plan=notion_plan,
        activity_stream=activity_stream,
    )


def _paragraph_blocks(lines: list[str]) -> list[BlockSpec]:
    blocks: list[BlockSpec] = []
    for line in lines:
        if line.startswith("- "):
            blocks.append(BlockSpec(type="bulleted_list_item", text=line[2:]))
        else:
            blocks.append(BlockSpec(type="paragraph", text=line))
    return blocks


def _build_rows(
    config: BlueprintConfig,
    roster: list[IdentityUser],
    teams: list[str],
    preset: dict[str, int],
    rng: random.Random,
) -> list[RowSpec]:
    rows: list[RowSpec] = []
    base_date = datetime(2026, 1, 10, tzinfo=UTC)

    projects_db_id = f"db_{stable_uuid(f'{config.company}:projects')}"
    for index in range(preset["projects"]):
        owner = rng.choice(roster).synth_user_id if roster else ""
        team = teams[index % len(teams)]
        rows.append(
            RowSpec(
                synth_id=f"row_{stable_uuid(f'{config.company}:project:{index}')}",
                database_synth_id=projects_db_id,
                properties=[
                    RowPropertySpec(name="Name", type="title", value=f"Project {index + 1}: {rng.choice(_PROJECT_NAMES)}"),
                    RowPropertySpec(name="Owner", type="people", value=[owner] if owner else []),
                    RowPropertySpec(name="Team", type="select", value=team),
                    RowPropertySpec(name="Status", type="select", value=rng.choice(["Planned", "In Progress", "On Hold", "Done"])),
                    RowPropertySpec(name="Target", type="date", value=(base_date + timedelta(days=index * 7)).date().isoformat()),
                ],
            )
        )

    tasks_db_id = f"db_{stable_uuid(f'{config.company}:tasks')}"
    for index in range(preset["tasks"]):
        owner = rng.choice(roster).synth_user_id if roster else ""
        team = teams[index % len(teams)]
        rows.append(
            RowSpec(
                synth_id=f"row_{stable_uuid(f'{config.company}:task:{index}')}",
                database_synth_id=tasks_db_id,
                properties=[
                    RowPropertySpec(name="Task", type="title", value=f"{rng.choice(_TASK_VERBS)} {rng.choice(_TASK_OBJECTS)}"),
                    RowPropertySpec(name="Owner", type="people", value=[owner] if owner else []),
                    RowPropertySpec(name="Team", type="select", value=team),
                    RowPropertySpec(name="Status", type="select", value=rng.choice(["Todo", "In Progress", "Blocked", "Done"])),
                    RowPropertySpec(name="Due", type="date", value=(base_date + timedelta(days=index % 30)).date().isoformat()),
                    RowPropertySpec(name="Priority", type="select", value=rng.choice(["P0", "P1", "P2"])),
                ],
            )
        )

    incidents_db_id = f"db_{stable_uuid(f'{config.company}:incidents')}"
    for index in range(preset["incidents"]):
        owner = rng.choice(roster).synth_user_id if roster else ""
        rows.append(
            RowSpec(
                synth_id=f"row_{stable_uuid(f'{config.company}:incident:{index}')}",
                database_synth_id=incidents_db_id,
                properties=[
                    RowPropertySpec(name="Title", type="title", value=f"INC-{1000 + index} {rng.choice(_INCIDENT_SUMMARIES)}"),
                    RowPropertySpec(name="Severity", type="select", value=rng.choice(["SEV1", "SEV2", "SEV3"])),
                    RowPropertySpec(name="Status", type="select", value=rng.choice(["Resolved", "Monitoring", "Postmortem"])),
                    RowPropertySpec(name="Owner", type="people", value=[owner] if owner else []),
                    RowPropertySpec(
                        name="Detected",
                        type="date",
                        value=(base_date + timedelta(days=index)).date().isoformat(),
                    ),
                    RowPropertySpec(
                        name="Resolved",
                        type="date",
                        value=(base_date + timedelta(days=index + 2)).date().isoformat(),
                    ),
                ],
            )
        )
    return rows


def _build_comments(
    config: BlueprintConfig,
    pages: list[PageSpec],
    roster: list[IdentityUser],
    rng: random.Random,
) -> list[CommentSpec]:
    comments: list[CommentSpec] = []
    if not roster:
        return comments
    for index, page in enumerate(pages[: min(len(pages), 40)]):
        if index % 2 == 0:
            comments.append(
                CommentSpec(
                    synth_id=f"comment_{stable_uuid(f'{config.company}:comment:{index}')}",
                    page_synth_id=page.synth_id,
                    body=f"Please align this with Q{(index % 4) + 1} OKRs. Owner [[synth:user:{rng.choice(roster).synth_user_id}]]",
                )
            )
    return comments


def _build_activity_stream(
    config: BlueprintConfig,
    pages: list[PageSpec],
    rows: list[RowSpec],
    rng: random.Random,
) -> list[ActivityEvent]:
    events: list[ActivityEvent] = []
    base = datetime(2026, 1, 20, 9, 0, tzinfo=UTC)
    for index, page in enumerate(pages[:20]):
        events.append(
            ActivityEvent(
                event_id=f"evt_{stable_uuid(f'{config.company}:page_edit:{index}')}",
                kind="page_edit",
                target_synth_id=page.synth_id,
                scheduled_at=(base + timedelta(minutes=index * 30)).isoformat(),
                payload={"append": f"Follow-up note {index + 1}."},
            )
        )
    for index, row in enumerate(rows[:20]):
        events.append(
            ActivityEvent(
                event_id=f"evt_{stable_uuid(f'{config.company}:row_update:{index}')}",
                kind="row_update",
                target_synth_id=row.synth_id,
                scheduled_at=(base + timedelta(minutes=index * 35)).isoformat(),
                payload={"Status": rng.choice(["In Progress", "Done", "Blocked"])},
            )
        )
    return events


_PROJECT_NAMES = [
    "Atlas",
    "Orbit",
    "Signal",
    "Voyager",
    "Nimbus",
    "Catalyst",
    "Summit",
    "Aurora",
    "Lighthouse",
    "Pulse",
]

_TASK_VERBS = [
    "Refactor",
    "Implement",
    "Audit",
    "Document",
    "Optimize",
    "Harden",
    "Deploy",
    "Automate",
]

_TASK_OBJECTS = [
    "observability pipeline",
    "incident workflow",
    "onboarding checklist",
    "auth service",
    "runbook coverage",
    "release pipeline",
    "security controls",
]

_INCIDENT_SUMMARIES = [
    "API latency regression",
    "Queue backlog spike",
    "Search index drift",
    "Billing webhook delay",
    "Auth token expiration bug",
    "Cache invalidation issue",
]

_KB_TOPICS = [
    "Service ownership map",
    "Incident response checklist",
    "Security review playbook",
    "Data retention policy",
    "Release readiness guide",
]

_KB_SNIPPETS = [
    "This document outlines the operational steps required before a production release.",
    "Use this runbook to triage elevated latency across critical services.",
    "This guide captures escalation paths and contact points by team.",
]

from __future__ import annotations

import random
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from notion_synth.models import Comment, Database, DatabaseRow, Fixture, Page, User, Workspace


@dataclass(frozen=True)
class SyntheticProfile:
    name: str
    description: str
    default_users: int
    default_teams: int
    default_projects: int
    default_incidents: int
    default_candidates: int


PROFILES: dict[str, SyntheticProfile] = {
    "engineering": SyntheticProfile(
        name="engineering",
        description="Full-stack engineering org with product, platform, and SRE workflows.",
        default_users=85,
        default_teams=7,
        default_projects=14,
        default_incidents=10,
        default_candidates=12,
    )
}


@dataclass(frozen=True)
class SyntheticWorkspaceConfig:
    company_name: str
    industry: str = "SaaS"
    profile: str = "engineering"
    seed: int = 42
    user_count: int | None = None
    team_count: int | None = None
    project_count: int | None = None
    incident_count: int | None = None
    candidate_count: int | None = None

    def resolved(self) -> SyntheticWorkspaceConfig:
        profile = PROFILES.get(self.profile)
        if profile is None:
            raise ValueError(f"Unknown profile '{self.profile}'")
        return SyntheticWorkspaceConfig(
            company_name=self.company_name,
            industry=self.industry,
            profile=self.profile,
            seed=self.seed,
            user_count=self.user_count or profile.default_users,
            team_count=self.team_count or profile.default_teams,
            project_count=self.project_count or profile.default_projects,
            incident_count=self.incident_count or profile.default_incidents,
            candidate_count=self.candidate_count or profile.default_candidates,
        )


def generate_fixture(config: SyntheticWorkspaceConfig) -> Fixture:
    resolved = config.resolved()
    # Deterministic synthetic fixture generation by seed.
    rng = random.Random(resolved.seed)  # nosec B311
    base_time = _base_time(resolved.seed)

    workspace_id = _slug_id("ws", resolved.company_name)
    workspace = Workspace(id=workspace_id, name=resolved.company_name, created_at=_ts(base_time, 0))

    teams = _pick_teams(resolved.team_count or 0)
    users = _build_users(workspace_id, resolved.user_count or 0, teams, rng, base_time)
    pages = _build_pages(
        workspace_id,
        resolved.company_name,
        resolved.industry,
        teams,
        users,
        rng,
        base_time,
    )
    databases, rows = _build_databases(
        workspace_id,
        users,
        teams,
        resolved.project_count or 0,
        resolved.incident_count or 0,
        resolved.candidate_count or 0,
        rng,
        base_time,
    )
    comments = _build_comments(pages, users, rng, base_time)

    return Fixture(
        exported_at=_ts(base_time, 1),
        workspaces=[workspace],
        users=users,
        pages=pages,
        databases=databases,
        database_rows=rows,
        comments=comments,
    )


def _base_time(seed: int) -> datetime:
    base = datetime(2026, 1, 15, 9, 30, tzinfo=UTC)
    return base + timedelta(days=seed % 20, hours=(seed % 5))


def _ts(base: datetime, offset: int) -> str:
    return (base + timedelta(minutes=offset * 17)).isoformat()


def _slug_id(prefix: str, name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return f"{prefix}_{slug[:18] or 'workspace'}"


def _pick_teams(team_count: int) -> list[str]:
    default = [
        "Platform",
        "Product Engineering",
        "Growth",
        "Data",
        "Security",
        "Infrastructure",
        "SRE",
        "Developer Experience",
        "Mobile",
        "QA",
    ]
    return default[: max(1, team_count)]


def _build_users(
    workspace_id: str,
    user_count: int,
    teams: list[str],
    rng: random.Random,
    base_time: datetime,
) -> list[User]:
    first_names = [
        "Alex",
        "Bianca",
        "Cheng",
        "Daria",
        "Evan",
        "Fatima",
        "George",
        "Hannah",
        "Isaac",
        "Jules",
        "Kai",
        "Lina",
        "Maya",
        "Noah",
        "Omar",
        "Priya",
        "Quinn",
        "Ravi",
        "Sasha",
        "Tara",
        "Uma",
        "Victor",
        "Wen",
        "Yara",
        "Zane",
    ]
    last_names = [
        "Rivers",
        "Holt",
        "Zhao",
        "Martinez",
        "Singh",
        "Kim",
        "Patel",
        "Nguyen",
        "Chen",
        "Khan",
        "Garcia",
        "Adams",
        "Bennett",
        "Stone",
        "Li",
        "Brown",
        "Miller",
        "Davis",
        "Sato",
        "Costa",
    ]
    roles = [
        "Engineering Manager",
        "Senior Software Engineer",
        "Staff Software Engineer",
        "Product Manager",
        "Tech Lead",
        "Platform Engineer",
        "SRE",
        "Security Engineer",
        "Data Engineer",
        "QA Engineer",
        "Designer",
    ]

    users: list[User] = []
    for index in range(user_count):
        first = rng.choice(first_names)
        last = rng.choice(last_names)
        team = teams[index % len(teams)]
        role = rng.choice(roles)
        name = f"{first} {last}"
        email = f"{first}.{last}.{index}@{_email_domain(workspace_id)}".lower()
        created_at = _ts(base_time, 10 + index)
        user = User(
            id=_rand_id("user", rng),
            workspace_id=workspace_id,
            name=f"{name} · {role} ({team})",
            email=email,
            created_at=created_at,
        )
        users.append(user)
    return users


def _build_pages(
    workspace_id: str,
    company_name: str,
    industry: str,
    teams: list[str],
    users: list[User],
    rng: random.Random,
    base_time: datetime,
) -> list[Page]:
    pages: list[Page] = []
    page_defs = [
        ("Company Handbook", _handbook_blocks(company_name, industry)),
        ("Engineering Overview", _engineering_overview_blocks(company_name, teams)),
        ("Onboarding Checklist", _onboarding_blocks(company_name)),
        ("Incident Response", _incident_blocks()),
        ("Architecture Map", _architecture_blocks()),
        ("Product Roadmap", _roadmap_blocks()),
        ("Security & Compliance", _security_blocks()),
    ]
    for index, (title, blocks) in enumerate(page_defs):
        pages.append(
            Page(
                id=_rand_id("page", rng),
                workspace_id=workspace_id,
                title=title,
                content={"type": "doc", "blocks": blocks},
                parent_type="workspace",
                parent_id=workspace_id,
                created_at=_ts(base_time, 200 + index),
                updated_at=_ts(base_time, 200 + index + 3),
            )
        )

    for index, team in enumerate(teams):
        pages.append(
            Page(
                id=_rand_id("page", rng),
                workspace_id=workspace_id,
                title=f"{team} Team Space",
                content={
                    "type": "doc",
                    "blocks": [
                        f"Mission: {team} delivers quarterly milestones with high availability.",
                        "Current priorities:",
                        "- Reliability OKRs",
                        "- Automation backlog",
                        "- Cross-team alignment",
                    ],
                    "owner": rng.choice(users).name if users else "TBD",
                },
                parent_type="workspace",
                parent_id=workspace_id,
                created_at=_ts(base_time, 240 + index),
                updated_at=_ts(base_time, 240 + index + 1),
            )
        )
    return pages


def _build_databases(
    workspace_id: str,
    users: list[User],
    teams: list[str],
    project_count: int,
    incident_count: int,
    candidate_count: int,
    rng: random.Random,
    base_time: datetime,
) -> tuple[list[Database], list[DatabaseRow]]:
    databases: list[Database] = []
    rows: list[DatabaseRow] = []

    projects_db_id = _rand_id("db", rng)
    databases.append(
        Database(
            id=projects_db_id,
            workspace_id=workspace_id,
            name="Program & Project Portfolio",
            schema={
                "properties": {
                    "Name": {"type": "title"},
                    "Owner": {"type": "person"},
                    "Team": {"type": "select"},
                    "Status": {"type": "select"},
                    "Target": {"type": "date"},
                }
            },
            created_at=_ts(base_time, 310),
            updated_at=_ts(base_time, 311),
        )
    )
    for index in range(project_count):
        rows.append(
            DatabaseRow(
                id=_rand_id("row", rng),
                database_id=projects_db_id,
                properties={
                    "Name": f"Project {index + 1}: {rng.choice(_PROJECT_NAMES)}",
                    "Owner": rng.choice(users).name if users else "TBD",
                    "Team": teams[index % len(teams)],
                    "Status": rng.choice(["Planned", "In Progress", "On Hold", "Done"]),
                    "Target": _ts(base_time, 400 + index * 2)[:10],
                },
                created_at=_ts(base_time, 330 + index),
                updated_at=_ts(base_time, 330 + index + 1),
            )
        )

    incidents_db_id = _rand_id("db", rng)
    databases.append(
        Database(
            id=incidents_db_id,
            workspace_id=workspace_id,
            name="Incident Log",
            schema={
                "properties": {
                    "Title": {"type": "title"},
                    "Severity": {"type": "select"},
                    "Status": {"type": "select"},
                    "Owner": {"type": "person"},
                    "Detected": {"type": "date"},
                    "Resolved": {"type": "date"},
                }
            },
            created_at=_ts(base_time, 360),
            updated_at=_ts(base_time, 361),
        )
    )
    for index in range(incident_count):
        detected = _ts(base_time, 500 + index * 3)
        resolved = _ts(base_time, 500 + index * 3 + 4)
        rows.append(
            DatabaseRow(
                id=_rand_id("row", rng),
                database_id=incidents_db_id,
                properties={
                    "Title": f"INC-{1000 + index} {rng.choice(_INCIDENT_SUMMARIES)}",
                    "Severity": rng.choice(["SEV1", "SEV2", "SEV3"]),
                    "Status": rng.choice(["Resolved", "Monitoring", "Postmortem"]),
                    "Owner": rng.choice(users).name if users else "TBD",
                    "Detected": detected[:10],
                    "Resolved": resolved[:10],
                },
                created_at=_ts(base_time, 370 + index),
                updated_at=_ts(base_time, 370 + index + 2),
            )
        )

    hiring_db_id = _rand_id("db", rng)
    databases.append(
        Database(
            id=hiring_db_id,
            workspace_id=workspace_id,
            name="Hiring Pipeline",
            schema={
                "properties": {
                    "Candidate": {"type": "title"},
                    "Role": {"type": "select"},
                    "Stage": {"type": "select"},
                    "Source": {"type": "select"},
                    "Recruiter": {"type": "person"},
                }
            },
            created_at=_ts(base_time, 390),
            updated_at=_ts(base_time, 391),
        )
    )
    for index in range(candidate_count):
        rows.append(
            DatabaseRow(
                id=_rand_id("row", rng),
                database_id=hiring_db_id,
                properties={
                    "Candidate": f"{rng.choice(_CANDIDATE_NAMES)}",
                    "Role": rng.choice(_ROLES),
                    "Stage": rng.choice(["Screen", "Onsite", "Offer", "Hired"]),
                    "Source": rng.choice(["Inbound", "Referral", "Sourcing", "Agency"]),
                    "Recruiter": rng.choice(users).name if users else "TBD",
                },
                created_at=_ts(base_time, 420 + index),
                updated_at=_ts(base_time, 420 + index + 1),
            )
        )

    return databases, rows


def _build_comments(
    pages: Iterable[Page],
    users: list[User],
    rng: random.Random,
    base_time: datetime,
) -> list[Comment]:
    comments: list[Comment] = []
    if not users:
        return comments
    notes = [
        "Please align this with Q3 OKRs.",
        "Action item: update runbook links.",
        "We should add metrics ownership for this section.",
        "Confirmed with Legal: proceed.",
        "Draft reviewed, ready for sign-off.",
    ]
    for index, page in enumerate(pages):
        if index % 2 == 0:
            comments.append(
                Comment(
                    id=_rand_id("comment", rng),
                    page_id=page.id,
                    author_id=rng.choice(users).id,
                    body=rng.choice(notes),
                    created_at=_ts(base_time, 600 + index),
                )
            )
    return comments


def _rand_id(prefix: str, rng: random.Random) -> str:
    return f"{prefix}_{rng.getrandbits(40):010x}"


def _email_domain(workspace_id: str) -> str:
    return workspace_id.replace("ws_", "") or "example.com"


def _handbook_blocks(company_name: str, industry: str) -> list[str]:
    return [
        f"{company_name} is a {industry} company focused on product velocity and reliability.",
        "Operating principles:",
        "- Customer empathy first",
        "- Secure by default",
        "- Measure and iterate",
        "Key rituals: weekly planning, monthly retros, quarterly roadmap reviews.",
    ]


def _engineering_overview_blocks(company_name: str, teams: list[str]) -> list[str]:
    return [
        f"{company_name} Engineering spans {len(teams)} teams with shared platform standards.",
        "Current focus areas:",
        "- Platform observability",
        "- Reliability automation",
        "- Developer enablement",
        "Team list: " + ", ".join(teams),
    ]


def _onboarding_blocks(company_name: str) -> list[str]:
    return [
        f"Welcome to {company_name}!",
        "Week 1 checklist:",
        "- Workspace tour",
        "- Access provisioning",
        "- Pairing sessions",
        "Week 2 checklist:",
        "- First PR",
        "- Incident shadowing",
    ]


def _incident_blocks() -> list[str]:
    return [
        "Incident response process:",
        "1. Declare SEV and assign incident commander.",
        "2. Open Slack channel and status page update.",
        "3. Stabilize, mitigate, document.",
        "4. Postmortem within 48 hours.",
    ]


def _architecture_blocks() -> list[str]:
    return [
        "System overview:",
        "- Edge: CDN + WAF",
        "- Core: API mesh + background workers",
        "- Data: OLTP + analytics warehouse",
        "Critical dependencies: identity provider, payment processor, logging pipeline.",
    ]


def _roadmap_blocks() -> list[str]:
    return [
        "Roadmap themes:",
        "- Faster onboarding",
        "- AI-assisted workflows",
        "- Cost efficiency",
        "Major bets: workflow automation, shared component library, unified analytics.",
    ]


def _security_blocks() -> list[str]:
    return [
        "Security posture:",
        "- SOC2 readiness",
        "- Annual pen test",
        "- Secrets rotation every 90 days",
        "Policy owners: Security Engineering + Compliance.",
    ]


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

_INCIDENT_SUMMARIES = [
    "API latency regression",
    "Queue backlog spike",
    "Search index drift",
    "Billing webhook delay",
    "Auth token expiration bug",
    "Cache invalidation issue",
]

_CANDIDATE_NAMES = [
    "Taylor James",
    "Morgan Lee",
    "Jordan Patel",
    "Casey Nguyen",
    "Harper Ross",
    "Riley Morgan",
    "Avery Chen",
    "Reese Kim",
    "Skyler Diaz",
    "Parker Shah",
]

_ROLES = [
    "Senior Backend Engineer",
    "Frontend Engineer",
    "Product Designer",
    "Data Engineer",
    "Site Reliability Engineer",
    "Security Engineer",
]

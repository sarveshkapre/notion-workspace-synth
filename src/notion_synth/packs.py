from __future__ import annotations

from dataclasses import dataclass

from notion_synth.generator import SyntheticWorkspaceConfig


@dataclass(frozen=True)
class FixturePack:
    """
    Named dataset preset intended for demos and quick local resets.

    Packs are deterministic by (name + seed + company), and are meant to be applied via
    the admin endpoint (or a CLI wrapper) without having to manually delete the SQLite file.
    """

    name: str
    description: str
    profile: str
    industry: str
    default_company: str
    default_seed: int
    users: int
    teams: int
    projects: int
    incidents: int
    candidates: int

    def to_config(self, *, company: str | None = None, seed: int | None = None) -> SyntheticWorkspaceConfig:
        return SyntheticWorkspaceConfig(
            company_name=company or self.default_company,
            industry=self.industry,
            profile=self.profile,
            seed=seed if seed is not None else self.default_seed,
            user_count=self.users,
            team_count=self.teams,
            project_count=self.projects,
            incident_count=self.incidents,
            candidate_count=self.candidates,
        )


PACKS: list[FixturePack] = [
    FixturePack(
        name="engineering_small",
        description="Smaller engineering org: quick demos and tests.",
        profile="engineering",
        industry="Cloud Infrastructure",
        default_company="Acme Robotics",
        default_seed=2026,
        users=30,
        teams=4,
        projects=6,
        incidents=4,
        candidates=5,
    ),
    FixturePack(
        name="engineering",
        description="Default engineering org: realistic baseline dataset.",
        profile="engineering",
        industry="Cloud Infrastructure",
        default_company="Acme Robotics",
        default_seed=2026,
        users=85,
        teams=7,
        projects=14,
        incidents=10,
        candidates=12,
    ),
    FixturePack(
        name="engineering_large",
        description="Large engineering org: stress test paging and search.",
        profile="engineering",
        industry="Cloud Infrastructure",
        default_company="Acme Robotics",
        default_seed=2026,
        users=220,
        teams=10,
        projects=30,
        incidents=20,
        candidates=30,
    ),
]


def list_packs() -> list[FixturePack]:
    return list(PACKS)


def get_pack(name: str) -> FixturePack | None:
    for pack in PACKS:
        if pack.name == name:
            return pack
    return None


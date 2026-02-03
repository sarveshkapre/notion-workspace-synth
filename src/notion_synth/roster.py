from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path

from notion_synth.blueprint_models import IdentityUser
from notion_synth.util import stable_uuid


ROSTER_FIELDS = [
    "synth_user_id",
    "display_name",
    "given_name",
    "surname",
    "upn",
    "email",
    "department",
    "job_title",
    "office_location",
    "manager_synth_user_id",
    "team",
]


@dataclass(frozen=True)
class RosterConfig:
    seed: int
    users: int


def generate_roster(config: RosterConfig, output_path: str) -> None:
    rng = random.Random(config.seed)
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
    teams = ["Platform", "Product Engineering", "SRE", "Security", "Data"]
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
    departments = ["Engineering", "Product", "Security", "Data"]
    locations = ["San Francisco", "New York", "London", "Bangalore", "Remote"]

    rows: list[dict[str, str]] = []
    for idx in range(config.users):
        first = rng.choice(first_names)
        last = rng.choice(last_names)
        team = teams[idx % len(teams)]
        role = rng.choice(roles)
        dept = rng.choice(departments)
        loc = rng.choice(locations)
        display_name = f"{first} {last}"
        synth_user_id = f"user_{stable_uuid(f'{display_name}:{idx}')}"
        rows.append(
            {
                "synth_user_id": synth_user_id,
                "display_name": display_name,
                "given_name": first,
                "surname": last,
                "upn": "",
                "email": "",
                "department": dept,
                "job_title": role,
                "office_location": loc,
                "manager_synth_user_id": "",
                "team": team,
            }
        )

    path = Path(output_path)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROSTER_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def load_roster(path: str) -> list[IdentityUser]:
    resolved: list[IdentityUser] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [field for field in ROSTER_FIELDS if field not in reader.fieldnames]
        if missing:
            raise ValueError(f"Roster missing fields: {', '.join(missing)}")
        for row in reader:
            if not row.get("synth_user_id") or not row.get("display_name"):
                raise ValueError("Roster rows must include synth_user_id and display_name.")
            resolved.append(
                IdentityUser(
                    synth_user_id=row["synth_user_id"].strip(),
                    display_name=row["display_name"].strip(),
                    given_name=row.get("given_name", "").strip(),
                    surname=row.get("surname", "").strip(),
                    upn=row.get("upn", "").strip(),
                    email=row.get("email", "").strip(),
                    department=row.get("department", "").strip(),
                    job_title=row.get("job_title", "").strip(),
                    office_location=row.get("office_location", "").strip(),
                    manager_synth_user_id=row.get("manager_synth_user_id", "").strip() or None,
                    team=row.get("team", "").strip(),
                )
            )
    return resolved

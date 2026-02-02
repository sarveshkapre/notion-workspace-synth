from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from notion_synth.db import connect
from notion_synth.fixtures import export_fixture, import_fixture
from notion_synth.generator import PROFILES, SyntheticWorkspaceConfig, generate_fixture
from notion_synth.models import Fixture


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="notion-synth",
        description="Generate and manage synthetic Notion-like workspaces.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate a synthetic workspace fixture JSON.",
    )
    _add_generation_args(generate_parser)
    generate_parser.add_argument(
        "--output",
        "-o",
        default="-",
        help="Write fixture JSON to a file path (default: stdout).",
    )

    seed_parser = subparsers.add_parser(
        "seed",
        help="Generate and load a synthetic workspace into a local DB.",
    )
    _add_generation_args(seed_parser)
    seed_parser.add_argument(
        "--db",
        default=None,
        help="SQLite path or URI (defaults to NOTION_SYNTH_DB).",
    )
    seed_parser.add_argument(
        "--mode",
        choices=["replace", "merge"],
        default="replace",
        help="Import mode: replace wipes existing data, merge upserts.",
    )

    export_parser = subparsers.add_parser(
        "export",
        help="Export the current DB into a fixture JSON.",
    )
    export_parser.add_argument(
        "--db",
        default=None,
        help="SQLite path or URI (defaults to NOTION_SYNTH_DB).",
    )
    export_parser.add_argument(
        "--output",
        "-o",
        default="-",
        help="Write fixture JSON to a file path (default: stdout).",
    )

    import_parser = subparsers.add_parser(
        "import",
        help="Import a fixture JSON into the local DB.",
    )
    import_parser.add_argument("fixture", help="Path to a fixture JSON file.")
    import_parser.add_argument(
        "--db",
        default=None,
        help="SQLite path or URI (defaults to NOTION_SYNTH_DB).",
    )
    import_parser.add_argument(
        "--mode",
        choices=["replace", "merge"],
        default="replace",
        help="Import mode: replace wipes existing data, merge upserts.",
    )

    args = parser.parse_args(argv)

    if args.command == "generate":
        fixture = generate_fixture(_config_from_args(args))
        _write_fixture(args.output, fixture)
        return 0

    if args.command == "seed":
        fixture = generate_fixture(_config_from_args(args))
        db = connect(args.db)
        result = import_fixture(db, fixture, mode=args.mode)
        print(json.dumps(result.model_dump(), indent=2))
        return 0

    if args.command == "export":
        db = connect(args.db)
        fixture = export_fixture(db)
        _write_fixture(args.output, fixture)
        return 0

    if args.command == "import":
        fixture = _load_fixture(args.fixture)
        db = connect(args.db)
        result = import_fixture(db, fixture, mode=args.mode)
        print(json.dumps(result.model_dump(), indent=2))
        return 0

    parser.error("Unknown command")
    return 2


def _add_generation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--company", required=True, help="Company name.")
    parser.add_argument("--industry", default="SaaS", help="Industry label.")
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES.keys()),
        default="engineering",
        help="Synthetic data profile.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Deterministic seed.")
    parser.add_argument("--users", type=int, default=None, help="Number of users.")
    parser.add_argument("--teams", type=int, default=None, help="Number of teams.")
    parser.add_argument("--projects", type=int, default=None, help="Number of projects.")
    parser.add_argument("--incidents", type=int, default=None, help="Number of incidents.")
    parser.add_argument("--candidates", type=int, default=None, help="Number of candidates.")


def _config_from_args(args: argparse.Namespace) -> SyntheticWorkspaceConfig:
    return SyntheticWorkspaceConfig(
        company_name=args.company,
        industry=args.industry,
        profile=args.profile,
        seed=args.seed,
        user_count=args.users,
        team_count=args.teams,
        project_count=args.projects,
        incident_count=args.incidents,
        candidate_count=args.candidates,
    )


def _write_fixture(output_path: str, fixture: Fixture) -> None:
    payload = json.dumps(fixture.model_dump(by_alias=True), indent=2)
    if output_path == "-":
        print(payload)
        return
    path = Path(output_path)
    path.write_text(payload)


def _load_fixture(path: str) -> Fixture:
    raw = Path(path).read_text()
    return Fixture.model_validate_json(raw)


if __name__ == "__main__":
    raise SystemExit(main())

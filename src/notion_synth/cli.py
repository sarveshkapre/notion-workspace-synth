from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from notion_synth.audit import AuditLog
from notion_synth.blueprint_generator import BlueprintConfig, generate_blueprint
from notion_synth.blueprint_models import Blueprint
from notion_synth.db import Database, connect
from notion_synth.fixtures import export_fixture, import_fixture
from notion_synth.generator import PROFILES, SyntheticWorkspaceConfig, generate_fixture
from notion_synth.llm.enrich import enrich_blueprint
from notion_synth.models import Fixture
from notion_synth.packs import FixturePack, get_pack, list_packs
from notion_synth.providers.entra.apply import apply_entra
from notion_synth.providers.entra.graph import GraphClient
from notion_synth.providers.entra.verify import verify_provisioning
from notion_synth.providers.notion.apply import (
    apply_blueprint,
    destroy_blueprint,
    run_activity,
    verify_users,
)
from notion_synth.providers.notion.client import NotionClient
from notion_synth.roster import RosterConfig, generate_roster, load_roster
from notion_synth.state import connect_state, record_run_finish, record_run_start
from notion_synth.util import stable_hash, utc_now


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

    profiles_parser = subparsers.add_parser("profiles", help="Synthetic data profile utilities.")
    profiles_sub = profiles_parser.add_subparsers(dest="profiles_command", required=True)
    profiles_list = profiles_sub.add_parser("list", help="List available profiles.")
    profiles_list.add_argument(
        "--output",
        "-o",
        default="-",
        help="Write JSON to a file path (default: stdout).",
    )

    packs_parser = subparsers.add_parser("packs", help="Fixture pack presets for local demos/tests.")
    packs_sub = packs_parser.add_subparsers(dest="packs_command", required=True)
    packs_list = packs_sub.add_parser("list", help="List available packs.")
    packs_list.add_argument(
        "--output",
        "-o",
        default="-",
        help="Write JSON to a file path (default: stdout).",
    )
    packs_apply = packs_sub.add_parser(
        "apply",
        help="Apply a pack to a local DB (replace). Use --dry-run to preview, or --confirm to apply.",
    )
    packs_apply.add_argument("--name", required=True, help="Pack name (see `packs list`).")
    packs_apply.add_argument(
        "--db",
        default=None,
        help="SQLite path or URI (defaults to NOTION_SYNTH_DB).",
    )
    packs_apply.add_argument("--company", default=None, help="Optional override for the pack company name.")
    packs_apply.add_argument("--seed", type=int, default=None, help="Optional deterministic seed override.")
    packs_apply.add_argument("--dry-run", action="store_true", help="Preview without mutating the DB.")
    packs_apply.add_argument("--confirm", action="store_true", help="Required to apply when not --dry-run.")

    roster_parser = subparsers.add_parser("roster", help="Roster utilities.")
    roster_sub = roster_parser.add_subparsers(dest="roster_command", required=True)
    roster_generate = roster_sub.add_parser("generate", help="Generate a roster CSV template.")
    roster_generate.add_argument("--seed", type=int, default=42)
    roster_generate.add_argument("--users", type=int, default=50)
    roster_generate.add_argument("--output", "-o", required=True)

    entra_parser = subparsers.add_parser("entra", help="Entra provisioning.")
    entra_sub = entra_parser.add_subparsers(dest="entra_command", required=True)
    entra_apply = entra_sub.add_parser("apply", help="Create or sync Entra users/groups.")
    entra_apply.add_argument("--roster", required=True)
    entra_apply.add_argument("--mode", choices=["create", "sync"], default="create")
    entra_apply.add_argument("--dry-run", action="store_true")
    entra_apply.add_argument("--tenant-id", required=True)
    entra_apply.add_argument("--client-id", required=True)
    entra_apply.add_argument("--client-secret", required=True)
    entra_apply.add_argument("--company", required=True)
    entra_apply.add_argument("--report", default="entra_apply_report.json")
    entra_apply.add_argument("--state", default=None)

    entra_verify = entra_sub.add_parser("verify-provisioning", help="Verify Entra -> Notion SCIM.")
    entra_verify.add_argument("--roster", required=True)
    entra_verify.add_argument("--tenant-id", required=True)
    entra_verify.add_argument("--client-id", required=True)
    entra_verify.add_argument("--client-secret", required=True)
    entra_verify.add_argument("--token", required=True)
    entra_verify.add_argument("--company", required=True)
    entra_verify.add_argument("--report", default="entra_verify_report.json")
    entra_verify.add_argument("--state", default=None)
    entra_verify.add_argument("--require-all", action="store_true")
    entra_verify.add_argument("--wait-minutes", type=int, default=0)
    entra_verify.add_argument("--interval-seconds", type=int, default=60)

    blueprint_parser = subparsers.add_parser("blueprint", help="Blueprint utilities.")
    blueprint_sub = blueprint_parser.add_subparsers(dest="blueprint_command", required=True)
    blueprint_generate = blueprint_sub.add_parser("generate", help="Generate a blueprint JSON.")
    blueprint_generate.add_argument("--company", required=True)
    blueprint_generate.add_argument("--seed", type=int, default=42)
    blueprint_generate.add_argument("--roster", required=True)
    blueprint_generate.add_argument("--output", "-o", required=True)
    blueprint_generate.add_argument("--profile", default="engineering")
    blueprint_generate.add_argument("--scale", default="small")

    notion_parser = subparsers.add_parser("notion", help="Notion apply/verify.")
    notion_sub = notion_parser.add_subparsers(dest="notion_command", required=True)
    notion_verify = notion_sub.add_parser("verify-users", help="Verify users exist in Notion.")
    notion_verify.add_argument("--roster", required=True)
    notion_verify.add_argument("--state", default=None)
    notion_verify.add_argument("--token", required=True)
    notion_verify.add_argument("--report", default="notion_verify_report.json")
    notion_verify.add_argument("--require-all", action="store_true")

    notion_validate = notion_sub.add_parser("validate-root", help="Validate root page access.")
    notion_validate.add_argument("--root-page-id", required=True)
    notion_validate.add_argument("--token", required=True)
    notion_validate.add_argument("--report", default="notion_root_report.json")

    notion_apply = notion_sub.add_parser("apply", help="Apply a blueprint to Notion.")
    notion_apply.add_argument("blueprint")
    notion_apply.add_argument("--root-page-id", required=True)
    notion_apply.add_argument("--token", required=True)
    notion_apply.add_argument("--state", default=None)
    notion_apply.add_argument("--audit-dir", default="audit")
    notion_apply.add_argument("--mode", choices=["apply", "plan"], default="apply")
    notion_apply.add_argument("--redact-emails", action="store_true")

    notion_destroy = notion_sub.add_parser("destroy", help="Archive created pages.")
    notion_destroy.add_argument("--token", required=True)
    notion_destroy.add_argument("--state", default=None)
    notion_destroy.add_argument("--audit-dir", default="audit")
    notion_destroy.add_argument("--redact-emails", action="store_true")

    notion_activity = notion_sub.add_parser("activity", help="Run synthetic activity.")
    notion_activity.add_argument("blueprint")
    notion_activity.add_argument("--token", required=True)
    notion_activity.add_argument("--state", default=None)
    notion_activity.add_argument("--audit-dir", default="audit")
    notion_activity.add_argument("--tick-minutes", type=int, default=15)
    notion_activity.add_argument("--jitter", type=float, default=0.3)
    notion_activity.add_argument("--iterations", type=int, default=1)
    notion_activity.add_argument("--redact-emails", action="store_true")

    llm_parser = subparsers.add_parser("llm", help="LLM enrichment.")
    llm_sub = llm_parser.add_subparsers(dest="llm_command", required=True)
    llm_enrich = llm_sub.add_parser("enrich", help="Enrich a blueprint using OpenAI.")
    llm_enrich.add_argument("blueprint")
    llm_enrich.add_argument("--output", "-o", required=True)
    llm_enrich.add_argument("--cache-dir", default=".cache/llm")
    llm_enrich.add_argument("--model", default="gpt-5.2")
    llm_enrich.add_argument("--base-url", default=None)
    llm_enrich.add_argument("--api-key", default=None)

    args = parser.parse_args(argv)

    if args.command == "generate":
        fixture = generate_fixture(_config_from_args(args))
        _write_fixture(args.output, fixture)
        return 0

    elif args.command == "seed":
        fixture = generate_fixture(_config_from_args(args))
        db = connect(args.db)
        fixture_result = import_fixture(db, fixture, mode=args.mode)
        print(json.dumps(fixture_result.model_dump(), indent=2))
        return 0

    elif args.command == "export":
        db = connect(args.db)
        fixture = export_fixture(db)
        _write_fixture(args.output, fixture)
        return 0

    elif args.command == "import":
        fixture = _load_fixture(args.fixture)
        db = connect(args.db)
        fixture_result = import_fixture(db, fixture, mode=args.mode)
        print(json.dumps(fixture_result.model_dump(), indent=2))
        return 0

    elif args.command == "profiles" and args.profiles_command == "list":
        profiles_payload: list[dict[str, object]] = [
            {
                "name": p.name,
                "description": p.description,
                "defaults": {
                    "users": p.default_users,
                    "teams": p.default_teams,
                    "projects": p.default_projects,
                    "incidents": p.default_incidents,
                    "candidates": p.default_candidates,
                },
            }
            for p in sorted(PROFILES.values(), key=lambda pr: pr.name)
        ]
        _write_payload(args.output, profiles_payload)
        return 0

    elif args.command == "packs" and args.packs_command == "list":
        packs_payload: list[dict[str, object]] = [_pack_info(pack) for pack in list_packs()]
        _write_payload(args.output, packs_payload)
        return 0

    elif args.command == "packs" and args.packs_command == "apply":
        pack = get_pack(args.name)
        if pack is None:
            print("Unknown pack (see `notion-synth packs list`).", file=sys.stderr)
            return 2

        db = connect(args.db)
        before = _db_stats(db)

        config = pack.to_config(company=args.company, seed=args.seed)
        fixture = generate_fixture(config)
        expected_inserted = {
            "workspaces": len(fixture.workspaces),
            "users": len(fixture.users),
            "pages": len(fixture.pages),
            "databases": len(fixture.databases),
            "database_rows": len(fixture.database_rows),
            "comments": len(fixture.comments),
        }
        pack_info = _pack_info(pack)

        if args.dry_run:
            _write_payload(
                "-",
                {
                    "status": "preview",
                    "pack": pack_info,
                    "before": before,
                    "after": before,
                    "expected_inserted": expected_inserted,
                },
            )
            return 0

        if not args.confirm:
            print("Refusing to apply pack without --confirm (or use --dry-run).", file=sys.stderr)
            return 2

        fixture_result = import_fixture(db, fixture, mode="replace")
        after = _db_stats(db)
        _write_payload(
            "-",
            {
                "status": "ok",
                "pack": pack_info,
                "before": before,
                "after": after,
                "inserted": fixture_result.inserted,
            },
        )
        return 0

    elif args.command == "roster" and args.roster_command == "generate":
        generate_roster(RosterConfig(seed=args.seed, users=args.users), args.output)
        print(f"Wrote roster template to {args.output}")
        return 0

    elif args.command == "entra" and args.entra_command == "apply":
        roster = load_roster(args.roster)
        groups: dict[str, list] = {}
        for user in roster:
            groups.setdefault(f"SYNTH-{args.company}-{user.team}", []).append(user)
        graph_client = GraphClient(
            tenant_id=args.tenant_id,
            client_id=args.client_id,
            client_secret=args.client_secret,
        )
        store = connect_state(args.state)
        run_id = stable_hash({"command": "entra-apply", "timestamp": utc_now()})
        record_run_start(store, run_id, "entra-apply", _hash_roster(args.roster))
        try:
            apply_result = apply_entra(
                client=graph_client,
                roster=roster,
                groups=groups,
                store=store,
                mode=args.mode,
                dry_run=args.dry_run,
            )
            _write_json(Path(args.report), apply_result.__dict__)
            record_run_finish(store, run_id, "ok")
            print(json.dumps(apply_result.__dict__, indent=2))
            return 0
        except Exception:
            record_run_finish(store, run_id, "error")
            raise

    elif args.command == "entra" and args.entra_command == "verify-provisioning":
        roster = load_roster(args.roster)
        graph = GraphClient(
            tenant_id=args.tenant_id,
            client_id=args.client_id,
            client_secret=args.client_secret,
        )
        notion = NotionClient(token=args.token)
        store = connect_state(args.state)
        run_id = stable_hash({"command": "entra-verify", "timestamp": utc_now()})
        record_run_start(store, run_id, "entra-verify", _hash_roster(args.roster))
        deadline = time.time() + (args.wait_minutes * 60)
        provisioning_report = None
        try:
            while True:
                provisioning_report = verify_provisioning(
                    graph=graph,
                    notion=notion,
                    roster=roster,
                    company=args.company,
                    store=store,
                )
                if (
                    not provisioning_report.missing_in_notion
                    and not provisioning_report.missing_in_entra
                    and not provisioning_report.missing_groups
                ):
                    break
                if time.time() >= deadline:
                    break
                time.sleep(max(5, args.interval_seconds))
            verify_payload = {
                "matched": provisioning_report.matched if provisioning_report else 0,
                "total": provisioning_report.total if provisioning_report else 0,
                "missing_in_entra": provisioning_report.missing_in_entra if provisioning_report else [],
                "missing_in_notion": provisioning_report.missing_in_notion if provisioning_report else [],
                "missing_groups": provisioning_report.missing_groups if provisioning_report else [],
            }
            _write_json(Path(args.report), verify_payload)
            record_run_finish(store, run_id, "ok")
            print(json.dumps(verify_payload, indent=2))
            if args.require_all and (
                verify_payload["missing_in_entra"]
                or verify_payload["missing_in_notion"]
                or verify_payload["missing_groups"]
            ):
                return 2
            return 0
        except Exception:
            record_run_finish(store, run_id, "error")
            raise

    elif args.command == "blueprint" and args.blueprint_command == "generate":
        roster = load_roster(args.roster)
        blueprint = generate_blueprint(
            BlueprintConfig(
                company=args.company,
                seed=args.seed,
                org_profile=args.profile,
                scale=args.scale,
            ),
            roster=roster,
        )
        _write_blueprint(args.output, blueprint)
        return 0

    elif args.command == "notion" and args.notion_command == "verify-users":
        roster = load_roster(args.roster)
        store = connect_state(args.state)
        notion_client = NotionClient(token=args.token)
        verify_result = verify_users(notion_client, store, [user.model_dump() for user in roster])
        verify_report = {
            "matched": verify_result.matched,
            "total": verify_result.total,
            "missing": verify_result.missing,
        }
        _write_json(Path(args.report), verify_report)
        print(json.dumps(verify_report, indent=2))
        if args.require_all and verify_result.missing:
            return 2
        return 0

    elif args.command == "notion" and args.notion_command == "validate-root":
        notion_client = NotionClient(token=args.token)
        try:
            page = notion_client.get_page(args.root_page_id)
            root_report = {"ok": True, "page_id": page.get("id")}
        except Exception as exc:
            root_report = {"ok": False, "error": str(exc)}
        _write_json(Path(args.report), root_report)
        print(json.dumps(root_report, indent=2))
        return 0 if root_report["ok"] else 2

    elif args.command == "notion" and args.notion_command == "apply":
        blueprint = _load_blueprint(args.blueprint)
        store = connect_state(args.state)
        run_id = stable_hash({"command": "notion-apply", "timestamp": utc_now()})
        record_run_start(store, run_id, "notion-apply", stable_hash(blueprint.model_dump()))
        audit = AuditLog.open(args.audit_dir, run_id, redact_emails=args.redact_emails)
        notion_client = NotionClient(token=args.token)
        try:
            notion_apply_result = apply_blueprint(
                blueprint,
                root_page_id=args.root_page_id,
                store=store,
                client=notion_client,
                audit=audit,
                mode=args.mode,
            )
            record_run_finish(store, run_id, "ok")
            print(json.dumps(notion_apply_result.__dict__, indent=2))
            return 0
        except Exception:
            record_run_finish(store, run_id, "error")
            raise

    elif args.command == "notion" and args.notion_command == "destroy":
        store = connect_state(args.state)
        run_id = stable_hash({"command": "notion-destroy", "timestamp": utc_now()})
        record_run_start(store, run_id, "notion-destroy", "n/a")
        audit = AuditLog.open(args.audit_dir, run_id, redact_emails=args.redact_emails)
        notion_client = NotionClient(token=args.token)
        try:
            archived = destroy_blueprint(store, notion_client, audit)
            record_run_finish(store, run_id, "ok")
            print(json.dumps({"archived": archived}, indent=2))
            return 0
        except Exception:
            record_run_finish(store, run_id, "error")
            raise

    elif args.command == "notion" and args.notion_command == "activity":
        blueprint = _load_blueprint(args.blueprint)
        store = connect_state(args.state)
        run_id = stable_hash({"command": "notion-activity", "timestamp": utc_now()})
        record_run_start(store, run_id, "notion-activity", stable_hash(blueprint.model_dump()))
        audit = AuditLog.open(args.audit_dir, run_id, redact_emails=args.redact_emails)
        notion_client = NotionClient(token=args.token)
        try:
            executed = run_activity(
                blueprint,
                store=store,
                client=notion_client,
                audit=audit,
                tick_minutes=args.tick_minutes,
                jitter=args.jitter,
                iterations=args.iterations,
            )
            record_run_finish(store, run_id, "ok")
            print(json.dumps({"executed": executed}, indent=2))
            return 0
        except Exception:
            record_run_finish(store, run_id, "error")
            raise

    elif args.command == "llm" and args.llm_command == "enrich":
        blueprint = _load_blueprint(args.blueprint)
        enriched = enrich_blueprint(
            blueprint,
            model=args.model,
            cache_dir=args.cache_dir,
            api_key=args.api_key,
            base_url=args.base_url,
        )
        _write_blueprint(args.output, enriched)
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
    _write_payload(output_path, fixture.model_dump(by_alias=True))


def _load_fixture(path: str) -> Fixture:
    raw = Path(path).read_text()
    return Fixture.model_validate_json(raw)


def _write_blueprint(output_path: str, blueprint: Blueprint) -> None:
    _write_payload(output_path, blueprint.model_dump())


def _load_blueprint(path: str) -> Blueprint:
    raw = Path(path).read_text()
    return Blueprint.model_validate_json(raw)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2))


def _hash_roster(path: str) -> str:
    return stable_hash(Path(path).read_text())


def _write_payload(output_path: str, payload: object) -> None:
    rendered = json.dumps(payload, indent=2)
    if output_path == "-":
        print(rendered)
        return
    Path(output_path).write_text(rendered)


def _pack_info(pack: FixturePack) -> dict[str, object]:
    return {
        "name": pack.name,
        "description": pack.description,
        "profile": pack.profile,
        "industry": pack.industry,
        "default_company": pack.default_company,
        "default_seed": pack.default_seed,
        "counts": {
            "users": pack.users,
            "teams": pack.teams,
            "projects": pack.projects,
            "incidents": pack.incidents,
            "candidates": pack.candidates,
        },
    }


def _db_stats(db: Database) -> dict[str, object]:
    workspaces = db.query_one("SELECT COUNT(*) AS count FROM workspaces")
    users = db.query_one("SELECT COUNT(*) AS count FROM users")
    pages = db.query_one("SELECT COUNT(*) AS count FROM pages")
    databases = db.query_one("SELECT COUNT(*) AS count FROM databases")
    database_rows = db.query_one("SELECT COUNT(*) AS count FROM database_rows")
    comments = db.query_one("SELECT COUNT(*) AS count FROM comments")

    return {
        "db_path": db.path,
        "workspaces": int(workspaces["count"]) if workspaces else 0,
        "users": int(users["count"]) if users else 0,
        "pages": int(pages["count"]) if pages else 0,
        "databases": int(databases["count"]) if databases else 0,
        "database_rows": int(database_rows["count"]) if database_rows else 0,
        "comments": int(comments["count"]) if comments else 0,
    }


if __name__ == "__main__":
    raise SystemExit(main())

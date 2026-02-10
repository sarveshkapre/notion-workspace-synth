import json

from notion_synth.cli import main


def test_cli_profiles_list(capsys) -> None:
    rc = main(["profiles", "list", "--output", "-"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    assert any(p["name"] == "engineering" for p in payload)


def test_cli_packs_list(capsys) -> None:
    rc = main(["packs", "list", "--output", "-"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    assert any(p["name"] == "engineering_small" for p in payload)


def test_cli_packs_apply_preview_and_apply(tmp_path, capsys) -> None:
    db_path = tmp_path / "test.db"

    preview_rc = main(
        [
            "packs",
            "apply",
            "--name",
            "engineering_small",
            "--db",
            str(db_path),
            "--dry-run",
        ]
    )
    assert preview_rc == 0
    preview = json.loads(capsys.readouterr().out.strip())
    assert preview["status"] == "preview"
    assert preview["pack"]["name"] == "engineering_small"
    assert preview["before"] == preview["after"]
    assert preview["expected_inserted"]["workspaces"] == 1

    apply_rc = main(
        [
            "packs",
            "apply",
            "--name",
            "engineering_small",
            "--db",
            str(db_path),
            "--confirm",
        ]
    )
    assert apply_rc == 0
    applied = json.loads(capsys.readouterr().out.strip())
    assert applied["status"] == "ok"
    assert applied["pack"]["name"] == "engineering_small"
    assert applied["after"]["workspaces"] == 1
    assert applied["after"]["users"] == applied["pack"]["counts"]["users"]


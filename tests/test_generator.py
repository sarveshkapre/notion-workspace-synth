from notion_synth.db import connect
from notion_synth.fixtures import import_fixture
from notion_synth.generator import SyntheticWorkspaceConfig, generate_fixture


def test_generate_fixture_is_deterministic() -> None:
    fixture_a = generate_fixture(
        SyntheticWorkspaceConfig(company_name="Acme", seed=123, user_count=5)
    )
    fixture_b = generate_fixture(
        SyntheticWorkspaceConfig(company_name="Acme", seed=123, user_count=5)
    )
    assert fixture_a.workspaces[0].id == fixture_b.workspaces[0].id
    assert fixture_a.users[0].email == fixture_b.users[0].email
    assert fixture_a.pages[0].title == fixture_b.pages[0].title


def test_import_generated_fixture_replaces_seed_data() -> None:
    fixture = generate_fixture(
        SyntheticWorkspaceConfig(company_name="Acme", seed=7, user_count=8)
    )
    db = connect(":memory:")
    result = import_fixture(db, fixture, mode="replace")
    assert result.inserted["workspaces"] == 1
    assert result.inserted["users"] == 8
    stats = db.query_one("SELECT COUNT(*) AS count FROM users")
    assert stats is not None
    assert stats["count"] == 8

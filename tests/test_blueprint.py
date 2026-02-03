from notion_synth.blueprint_generator import BlueprintConfig, generate_blueprint
from notion_synth.blueprint_models import IdentityUser


def _roster() -> list[IdentityUser]:
    return [
        IdentityUser(
            synth_user_id="user_1",
            display_name="Alex Rivers",
            given_name="Alex",
            surname="Rivers",
            upn="alex@example.com",
            email="alex@example.com",
            department="Engineering",
            job_title="Engineer",
            office_location="Remote",
            manager_synth_user_id=None,
            team="Platform",
        ),
        IdentityUser(
            synth_user_id="user_2",
            display_name="Bianca Holt",
            given_name="Bianca",
            surname="Holt",
            upn="bianca@example.com",
            email="bianca@example.com",
            department="Engineering",
            job_title="Engineer",
            office_location="Remote",
            manager_synth_user_id=None,
            team="SRE",
        ),
    ]


def test_blueprint_is_deterministic() -> None:
    roster = _roster()
    blueprint_a = generate_blueprint(
        BlueprintConfig(company="Acme", seed=7, org_profile="engineering", scale="small"),
        roster=roster,
    )
    blueprint_b = generate_blueprint(
        BlueprintConfig(company="Acme", seed=7, org_profile="engineering", scale="small"),
        roster=roster,
    )
    assert blueprint_a.company == blueprint_b.company
    assert blueprint_a.notion_plan.pages[0].title == blueprint_b.notion_plan.pages[0].title
    assert blueprint_a.notion_plan.rows[0].properties[0].value == blueprint_b.notion_plan.rows[0].properties[0].value

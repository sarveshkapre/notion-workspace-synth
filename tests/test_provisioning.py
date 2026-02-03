from dataclasses import dataclass

from notion_synth.blueprint_models import IdentityUser
from notion_synth.providers.entra.verify import verify_provisioning
from notion_synth.state import connect_state


@dataclass
class FakeGraph:
    users: set[str]
    groups: set[str]

    def find_user_by_upn(self, upn: str):
        return {"id": upn} if upn in self.users else None

    def find_group_by_name(self, name: str):
        return {"id": name} if name in self.groups else None


@dataclass
class FakeNotion:
    emails: set[str]

    def list_users(self):
        return [{"person": {"email": email}, "id": email} for email in self.emails]


def test_verify_provisioning_reports_missing() -> None:
    roster = [
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
    graph = FakeGraph(users={"alex@example.com"}, groups={"SYNTH-Acme-Platform"})
    notion = FakeNotion(emails={"alex@example.com"})
    store = connect_state(":memory:")

    report = verify_provisioning(
        graph=graph,
        notion=notion,
        roster=roster,
        company="Acme",
        store=store,
    )

    assert report.missing_in_entra == ["bianca@example.com"]
    assert report.missing_in_notion == ["bianca@example.com"]
    assert report.missing_groups == ["SYNTH-Acme-SRE"]

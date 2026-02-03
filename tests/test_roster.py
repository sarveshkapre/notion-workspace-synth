from notion_synth.roster import RosterConfig, generate_roster, load_roster


def test_roster_is_deterministic(tmp_path) -> None:
    path_a = tmp_path / "roster_a.csv"
    path_b = tmp_path / "roster_b.csv"

    generate_roster(RosterConfig(seed=123, users=5), str(path_a))
    generate_roster(RosterConfig(seed=123, users=5), str(path_b))

    roster_a = load_roster(str(path_a))
    roster_b = load_roster(str(path_b))

    assert roster_a[0].synth_user_id == roster_b[0].synth_user_id
    assert roster_a[0].display_name == roster_b[0].display_name

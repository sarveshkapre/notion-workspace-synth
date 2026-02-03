from notion_synth.providers.notion.apply import _rich_text_with_placeholders
from notion_synth.state import connect_state, upsert_identity, upsert_object


def test_placeholder_resolution() -> None:
    store = connect_state(":memory:")
    upsert_object(
        store,
        "page_abc",
        kind="page",
        provider="notion",
        remote_id="remote-page",
        parent_synth_id=None,
        spec_hash="hash",
    )
    upsert_identity(store, "user_abc", notion_user_id="remote-user")

    rich_text, unresolved = _rich_text_with_placeholders(
        "See [[synth:page:page_abc]] and ping [[synth:user:user_abc]].",
        store,
    )
    assert not unresolved
    assert any(item.get("type") == "mention" for item in rich_text)

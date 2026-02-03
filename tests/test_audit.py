from notion_synth.audit import redact_payload


def test_redact_payload_redacts_emails() -> None:
    payload = {
        "email": "alex@example.com",
        "nested": ["keep", "bianca@example.org"],
        "obj": {"value": "contact me at user@domain.com"},
    }
    redacted = redact_payload(payload)
    assert redacted["email"] == "[redacted-email]"
    assert redacted["nested"][1] == "[redacted-email]"
    assert "domain.com" not in redacted["obj"]["value"]

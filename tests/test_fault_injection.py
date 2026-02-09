from fastapi.testclient import TestClient

from notion_synth import fault_injection
from notion_synth.main import create_app


def test_fault_injection_ignored_when_disabled(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_SYNTH_FAULT_INJECTION", raising=False)
    client = TestClient(create_app(":memory:"))
    response = client.get("/health?fail_rate=1&delay_ms=10")
    assert response.status_code == 200


def test_fault_injection_enabled_can_fail_and_delay(monkeypatch) -> None:
    monkeypatch.setenv("NOTION_SYNTH_FAULT_INJECTION", "1")

    slept: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr(fault_injection.anyio, "sleep", fake_sleep)

    client = TestClient(create_app(":memory:"))

    delayed = client.get("/health?delay_ms=5")
    assert delayed.status_code == 200
    assert delayed.headers.get("x-notion-synth-delay-ms") == "5"
    assert slept == [0.005]

    failed = client.get("/health?fail_rate=1&fail_status=503")
    assert failed.status_code == 503
    assert failed.headers.get("x-notion-synth-fault-injected") == "true"

    invalid = client.get("/health?fail_rate=2")
    assert invalid.status_code == 400


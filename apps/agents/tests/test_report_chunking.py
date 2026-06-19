"""Tests : publication du rapport complet en messages Band (découpage)."""

from apps.agents.band_client import BandClient
from apps.api.band_messages import format_messages_for_ui


def _client_capturing(calls: list[dict]) -> BandClient:
    client = BandClient(api_key="test", agent_id="agent")

    def fake_request(method, path, *, json=None, params=None):
        calls.append({"method": method, "path": path, "json": json})
        return {"ok": True}

    client._request = fake_request  # type: ignore[assignment]
    return client


def test_short_report_single_message(settings):
    settings.BAND_MAX_EVENT_CHARS = 6000
    calls: list[dict] = []
    client = _client_capturing(calls)
    client.post_agent_report("room", agent_name="ScannerAgent", content="Court rapport.")

    assert len(calls) == 1
    assert calls[0]["path"] == "/chats/room/messages"
    content = calls[0]["json"]["message"]["content"]
    assert content.startswith("**ScannerAgent — rapport**")
    assert "(1/" not in content  # pas de compteur si un seul morceau


def test_long_report_is_chunked_not_truncated(settings):
    settings.BAND_MAX_EVENT_CHARS = 1000
    calls: list[dict] = []
    client = _client_capturing(calls)
    body = "Z" * 3500  # > limite → plusieurs morceaux (Z absent des en-têtes)
    client.post_agent_report("room", agent_name="ScannerAgent", content=body)

    assert len(calls) >= 3  # découpé, pas tronqué
    # Chaque morceau est posté comme message avec compteur
    for call in calls:
        assert call["path"] == "/chats/room/messages"
        assert "rapport (" in call["json"]["message"]["content"]
    # Le contenu total reconstruit couvre tout le corps (rien perdu)
    total_body = sum(c["json"]["message"]["content"].count("Z") for c in calls)
    assert total_body == 3500


def test_chunked_report_header_classified_as_report():
    messages = [
        {
            "id": "1",
            "content": "**ScannerAgent — rapport (2/3)**\n\nSuite du rapport...",
            "sender_name": "ScannerAgent",
        }
    ]
    formatted = format_messages_for_ui(messages)
    assert formatted[0]["kind"] == "report"
    assert formatted[0]["author"] == "ScannerAgent"
    assert "rapport (2/3)" not in formatted[0]["content"]

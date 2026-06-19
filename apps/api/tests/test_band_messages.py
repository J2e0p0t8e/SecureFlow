"""Tests de classification des messages Band Room."""

from apps.api.band_messages import format_messages_for_ui


def test_disagreement_message_is_classified():
    raw = [
        {
            "id": "m1",
            "content": "**DÉSACCORD DÉTECTÉ**\n\n- ThreatAgent: 8/10\n- RiskAgent: 3/10\n\nÉcart ≥ 3 points",
            "sender_name": "DecisionAgent",
        }
    ]
    out = format_messages_for_ui(raw)
    assert len(out) == 1
    assert out[0]["kind"] == "disagreement"


def test_regular_message_not_disagreement():
    raw = [{"id": "m2", "content": "**ScannerAgent — discussion**\n\nJe m'y mets.", "sender_name": "ScannerAgent"}]
    out = format_messages_for_ui(raw)
    assert out[0]["kind"] != "disagreement"

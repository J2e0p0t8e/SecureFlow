"""Tests du cross-check SAST ↔ décision (recrutement & escalade)."""

from apps.agents.base import AgentResult
from apps.core.pipeline_context import set_static_signal
from apps.orchestrator.audit_to_fix import (
    _should_recruit_compliance,
    _should_recruit_risk,
)


def _threat(content: str = "Analyse menace neutre.") -> AgentResult:
    return AgentResult(agent_name="ThreatAgent", room_id="room", content=content)


def test_compliance_recruited_on_bandit_high():
    set_static_signal({"high": 2, "medium": 0, "total": 4, "risk_floor": 7.0})
    recruit, reason = _should_recruit_compliance(_threat())
    assert recruit is True
    assert "HIGH" in reason or "Bandit" in reason


def test_compliance_not_recruited_without_signal():
    set_static_signal({"high": 0, "medium": 0, "total": 0, "risk_floor": 0.0})
    recruit, _ = _should_recruit_compliance(_threat())
    assert recruit is False


def test_risk_recruited_on_high_static_floor():
    set_static_signal({"high": 0, "medium": 1, "total": 8, "risk_floor": 6.0})
    recruit, reason = _should_recruit_risk(_threat(), "code neutre")
    assert recruit is True


def test_risk_not_recruited_on_low_signal():
    set_static_signal({"high": 0, "medium": 0, "total": 2, "risk_floor": 0.0})
    recruit, _ = _should_recruit_risk(_threat(), "code neutre")
    assert recruit is False

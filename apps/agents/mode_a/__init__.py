"""Agents du Mode A — Security Audit."""

from apps.agents.mode_a.compliance import ComplianceAgent
from apps.agents.mode_a.decision import DecisionAgent
from apps.agents.mode_a.risk import RiskAgent
from apps.agents.mode_a.scanner import ScannerAgent
from apps.agents.mode_a.threat import ThreatAgent

MODE_A_AGENT_CLASSES = [
    ScannerAgent,
    ThreatAgent,
    ComplianceAgent,
    RiskAgent,
    DecisionAgent,
]

__all__ = [
    "ComplianceAgent",
    "DecisionAgent",
    "MODE_A_AGENT_CLASSES",
    "RiskAgent",
    "ScannerAgent",
    "ThreatAgent",
]

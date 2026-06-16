# Mode C — Analyse et rapport PDF (5 agents)
# Réutilise Scanner, Threat, Compliance du Mode A (Personne 1)
# Ajoute Metrics et Report (Personne 4)

from apps.agents.mode_a.scanner import ScannerAgent
from apps.agents.mode_a.threat import ThreatAgent
from apps.agents.mode_a.compliance import ComplianceAgent
from apps.agents.mode_c.metrics import MetricsAgent
from apps.agents.mode_c.report import ReportAgent

# Pipeline complet Mode C
MODE_C_AGENT_CLASSES = [
    ScannerAgent,      # Mode A - Personne 1
    ThreatAgent,       # Mode A - Personne 1
    ComplianceAgent,   # Mode A - Personne 1
    MetricsAgent,      # Mode C - Personne 4
    ReportAgent,       # Mode C - Personne 4
]

__all__ = [
    "ScannerAgent",
    "ThreatAgent",
    "ComplianceAgent",
    "MetricsAgent",
    "ReportAgent",
    "MODE_C_AGENT_CLASSES",
]

# Made with Bob

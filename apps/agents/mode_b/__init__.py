# Mode B — Pipeline complet de développement (6 agents)
# Personne 3 : FeasibilityAgent, ArchitectAgent, DesignAgent
# Personne 4 : DevAgent, SecurityAgent, QAAgent

from apps.agents.mode_b.architect import ArchitectAgent
from apps.agents.mode_b.design import DesignAgent
from apps.agents.mode_b.dev import DevAgent
from apps.agents.mode_b.feasibility import FeasibilityAgent
from apps.agents.mode_b.qa import QAAgent
from apps.agents.mode_b.security import SecurityAgent

MODE_B_AGENT_CLASSES = [
    FeasibilityAgent,
    ArchitectAgent,
    DesignAgent,
    DevAgent,
    SecurityAgent,
    QAAgent,
]

MODE_B_CONCEPTION_CLASSES = [
    FeasibilityAgent,
    ArchitectAgent,
    DesignAgent,
]

__all__ = [
    "ArchitectAgent",
    "DesignAgent",
    "DevAgent",
    "FeasibilityAgent",
    "QAAgent",
    "SecurityAgent",
    "MODE_B_AGENT_CLASSES",
    "MODE_B_CONCEPTION_CLASSES",
]

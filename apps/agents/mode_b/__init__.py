from apps.agents.mode_b.architect import ArchitectAgent
from apps.agents.mode_b.design import DesignAgent
from apps.agents.mode_b.feasibility import FeasibilityAgent

MODE_B_CONCEPTION_CLASSES = [
    FeasibilityAgent,
    ArchitectAgent,
    DesignAgent,
]

__all__ = ["ArchitectAgent", "DesignAgent", "FeasibilityAgent", "MODE_B_CONCEPTION_CLASSES"]# Personne 3 — FeasibilityAgent, ArchitectAgent, DesignAgent

# apps/agents/mode_b/workflows.py
# Définition des workflows du Mode B

# ═══════════════════════════════════════════════════
# IMPORTS DE TES AGENTS (Personne 3)
# ═══════════════════════════════════════════════════
from apps.agents.mode_b.feasibility import FeasibilityAgent
from apps.agents.mode_b.architect import ArchitectAgent
from apps.agents.mode_b.design import DesignAgent

# ═══════════════════════════════════════════════════
# IMPORTS DES AGENTS DE LA PERSONNE 4
# ═══════════════════════════════════════════════════
try:
    from apps.agents.mode_b.dev import DevAgent  # noqa: F401
    from apps.agents.mode_b.security import SecurityAgent  # noqa: F401
    from apps.agents.mode_b.qa import QAAgent  # noqa: F401
except ImportError:
    class DevAgent: 
        name = "DevAgent (En attente de la Personne 4)"
    class SecurityAgent: 
        name = "SecurityAgent (En attente de la Personne 4)"
    class QAAgent: 
        name = "QAAgent (En attente de la Personne 4)"

# ═══════════════════════════════════════════════════
# WORKFLOWS
# ═══════════════════════════════════════════════════
MODE_B_CONCEPTION_CLASSES = [
    FeasibilityAgent,
    ArchitectAgent,
    DesignAgent,
]

MODE_B_FULL_WORKFLOW = [
    FeasibilityAgent,   # Personne 3
    ArchitectAgent,     # Personne 3
    DesignAgent,        # Personne 3
    DevAgent,           # Personne 4
    SecurityAgent,      # Personne 4
    QAAgent,            # Personne 4
]

__all__ = [
    "FeasibilityAgent",
    "ArchitectAgent",
    "DesignAgent",
    "DevAgent",
    "SecurityAgent",
    "QAAgent",
    "MODE_B_CONCEPTION_CLASSES",
    "MODE_B_FULL_WORKFLOW",
]
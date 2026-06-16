# Mode B — Pipeline complet de développement (6 agents)
# Personne 3 : FeasibilityAgent, ArchitectAgent, DesignAgent
# Personne 4 : DevAgent, SecurityAgent, QAAgent

# Import des agents de la Personne 4
from apps.agents.mode_b.dev import DevAgent
from apps.agents.mode_b.security import SecurityAgent
from apps.agents.mode_b.qa import QAAgent

# Les agents de la Personne 3 seront ajoutés ici quand ils seront créés :
# from apps.agents.mode_b.feasibility import FeasibilityAgent
# from apps.agents.mode_b.architect import ArchitectAgent
# from apps.agents.mode_b.design import DesignAgent

# Pipeline complet Mode B (à compléter avec les agents de Personne 3)
MODE_B_AGENT_CLASSES = [
    # FeasibilityAgent,  # Personne 3
    # ArchitectAgent,    # Personne 3
    # DesignAgent,       # Personne 3
    DevAgent,
    SecurityAgent,
    QAAgent,
]

__all__ = [
    "DevAgent",
    "SecurityAgent",
    "QAAgent",
    "MODE_B_AGENT_CLASSES",
]

# Made with Bob

"""
Registre des 13 agents Band AI — un Remote Agent Band par agent SecureFlow.

Chaque agent a ses propres variables .env :
    BAND_{SLUG}_AGENT_ID
    BAND_{SLUG}_API_KEY
    BAND_{SLUG}_HANDLE   (optionnel — récupéré via /agent/me si absent)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from django.conf import settings


@dataclass(frozen=True)
class BandAgentCredentials:
    """Identifiants Band pour un agent SecureFlow."""

    secureflow_name: str
    slug: str
    agent_id: str
    api_key: str
    handle: str = ""


# 13 agents uniques (Scanner/Threat/Compliance partagés entre Mode A et C)
BAND_AGENT_SLUGS: dict[str, str] = {
    "ScannerAgent": "SCANNER",
    "ThreatAgent": "THREAT",
    "ComplianceAgent": "COMPLIANCE",
    "RiskAgent": "RISK",
    "DecisionAgent": "DECISION",
    "FeasibilityAgent": "FEASIBILITY",
    "ArchitectAgent": "ARCHITECT",
    "DesignAgent": "DESIGN",
    "DevAgent": "DEV",
    "SecurityAgent": "SECURITY",
    "QAAgent": "QA",
    "MetricsAgent": "METRICS",
    "ReportAgent": "REPORT",
}

ALL_BAND_AGENT_NAMES: list[str] = list(BAND_AGENT_SLUGS.keys())


def _env_key(slug: str, suffix: str) -> str:
    return f"BAND_{slug}_{suffix}"


def load_credentials(secureflow_name: str) -> BandAgentCredentials:
    """Charge les identifiants Band d'un agent depuis .env."""
    slug = BAND_AGENT_SLUGS.get(secureflow_name)
    if not slug:
        raise KeyError(f"Agent Band inconnu : {secureflow_name!r}")

    agent_id = os.getenv(_env_key(slug, "AGENT_ID"), "").strip()
    api_key = os.getenv(_env_key(slug, "API_KEY"), "").strip()
    handle = os.getenv(_env_key(slug, "HANDLE"), "").strip()

    return BandAgentCredentials(
        secureflow_name=secureflow_name,
        slug=slug,
        agent_id=agent_id,
        api_key=api_key,
        handle=handle,
    )


def get_band_client_for(secureflow_name: str):
    """Retourne un BandClient configuré pour l'agent nommé."""
    from apps.agents.band_client import BandClient

    creds = load_credentials(secureflow_name)
    return BandClient(
        api_key=creds.api_key,
        agent_id=creds.agent_id,
        base_url=settings.BAND_BASE_URL,
    )


@lru_cache(maxsize=32)
def resolve_handle(secureflow_name: str) -> str:
    """
    Retourne le @handle Band d'un agent (pour les mentions).
    Utilise BAND_*_HANDLE si défini, sinon interroge GET /agent/me.
    """
    creds = load_credentials(secureflow_name)
    if creds.handle:
        return creds.handle.lstrip("@")

    client = get_band_client_for(secureflow_name)
    profile = client.get_me()
    agent = profile.get("agent") or client._unwrap(profile)
    handle = (
        agent.get("handle")
        or agent.get("username")
        or agent.get("name")
        or secureflow_name
    )
    return str(handle).lstrip("@")


def validate_agent_credentials(secureflow_name: str) -> list[str]:
    """Erreurs de config pour un agent donné."""
    errors: list[str] = []
    slug = BAND_AGENT_SLUGS.get(secureflow_name)
    if not slug:
        return [f"Agent inconnu : {secureflow_name}"]

    creds = load_credentials(secureflow_name)
    if not creds.agent_id:
        errors.append(f"BAND_{slug}_AGENT_ID manquant ({secureflow_name})")
    if not creds.api_key:
        errors.append(f"BAND_{slug}_API_KEY manquant ({secureflow_name})")
    return errors


def validate_all_band_agents() -> list[str]:
    """Vérifie les 13 agents Band."""
    errors: list[str] = []
    for name in ALL_BAND_AGENT_NAMES:
        errors.extend(validate_agent_credentials(name))
    return errors

"""Vérification de la configuration avant exécution des agents."""

from __future__ import annotations

from django.conf import settings

from apps.agents.band_registry import validate_agent_credentials


def validate_runtime_config(required_band_agents: list[str] | None = None) -> list[str]:
    """
    Retourne la liste des erreurs de configuration bloquantes.

    Args:
        required_band_agents: Noms SecureFlow des agents Band requis.
                              Si None, vérifie les 13 agents.
    """
    errors: list[str] = []

    if required_band_agents:
        for agent_name in required_band_agents:
            errors.extend(validate_agent_credentials(agent_name))
    else:
        from apps.agents.band_registry import validate_all_band_agents

        errors.extend(validate_all_band_agents())

    provider = settings.LLM_PROVIDER
    if provider == "groq" and not settings.GROQ_API_KEY:
        errors.append("GROQ_API_KEY manquante (LLM_PROVIDER=groq)")
    elif provider == "aimlapi" and not settings.AIMLAPI_API_KEY:
        errors.append("AIMLAPI_API_KEY manquante (LLM_PROVIDER=aimlapi)")
    elif provider not in ("groq", "aimlapi"):
        errors.append(f"LLM_PROVIDER invalide : {provider!r}")

    return errors


def check_runtime_config(required_band_agents: list[str] | None = None) -> None:
    """Lève RuntimeError si la configuration est incomplète."""
    errors = validate_runtime_config(required_band_agents)
    if errors:
        raise RuntimeError(
            "Configuration incomplète pour SecureFlow :\n- " + "\n- ".join(errors)
        )

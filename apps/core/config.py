"""Vérification de la configuration avant exécution des agents."""

from __future__ import annotations

from django.conf import settings

from apps.agents.band_registry import validate_agent_credentials


def get_ingestion_max_files(mode: str | None = None) -> int:
    """Limite de fichiers ingérés pour Audit-to-Fix (dépôt complet)."""
    return getattr(
        settings,
        "INGESTION_MAX_FILES_A",
        getattr(settings, "INGESTION_MAX_FILES_C", 50),
    )


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
    openrouter_key = getattr(settings, "OPENROUTER_API_KEY", "")
    google_key = getattr(settings, "GOOGLE_API_KEY", "")

    if provider == "featherless" and not getattr(settings, "FEATHERLESS_API_KEY", ""):
        errors.append(
            "FEATHERLESS_API_KEY manquante (LLM_PROVIDER=featherless). "
            "Récupérez votre clé sur https://featherless.ai"
        )
    elif provider in ("openrouter", "open-router") and not openrouter_key:
        errors.append(
            "OPENROUTER_API_KEY manquante (LLM_PROVIDER=openrouter). "
            "Créez une clé sur https://openrouter.ai/keys"
        )
    elif provider in ("google", "gemini") and not google_key:
        errors.append(
            "GOOGLE_API_KEY manquante (LLM_PROVIDER=google). "
            "Créez une clé sur https://aistudio.google.com/apikey"
        )
    elif provider == "groq":
        groq_keys = getattr(settings, "GROQ_API_KEYS", None) or (
            [settings.GROQ_API_KEY] if getattr(settings, "GROQ_API_KEY", "") else []
        )
        if not groq_keys:
            errors.append("GROQ_API_KEY manquante (LLM_PROVIDER=groq, legacy)")
    elif provider == "aimlapi":
        if not getattr(settings, "LLM_USE_AIMLAPI", False):
            errors.append(
                "AI/ML API désactivée. Utilisez LLM_PROVIDER=openrouter dans .env"
            )
        elif not settings.AIMLAPI_API_KEY:
            errors.append("AIMLAPI_API_KEY manquante (LLM_PROVIDER=aimlapi)")
    elif provider not in (
        "featherless",
        "groq",
        "google",
        "gemini",
        "aimlapi",
        "openrouter",
        "open-router",
    ):
        errors.append(f"LLM_PROVIDER invalide : {provider!r}")

    return errors


def check_runtime_config(required_band_agents: list[str] | None = None) -> None:
    """Lève RuntimeError si la configuration est incomplète."""
    errors = validate_runtime_config(required_band_agents)
    if errors:
        raise RuntimeError(
            "Configuration incomplète pour SecureFlow :\n- " + "\n- ".join(errors)
        )

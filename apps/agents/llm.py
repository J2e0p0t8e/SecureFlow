"""
Client LLM unifié pour SecureFlow AI.

Priorité hackathon :
- aimlapi (crédits lablab) si LLM_PROVIDER=aimlapi
- groq (gratuit) sinon
"""

from __future__ import annotations

import logging
from typing import Protocol

from django.conf import settings

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    """Interface minimale attendue par BaseAgent."""

    def complete(self, *, system: str, user: str) -> str: ...


class GroqLLMClient:
    """Appels via l'API Groq (OpenAI-compatible)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL

        if not self.api_key:
            raise LLMConfigurationError("GROQ_API_KEY manquante dans .env")

    def complete(self, *, system: str, user: str) -> str:
        try:
            from groq import Groq
        except ImportError as exc:
            raise LLMConfigurationError(
                "Package 'groq' non installé. Lance : pip install groq"
            ) from exc

        client = Groq(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return (response.choices[0].message.content or "").strip()


class AimlApiLLMClient:
    """Appels via AI/ML API (compatible OpenAI)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.AIMLAPI_API_KEY
        self.base_url = base_url or settings.AIMLAPI_BASE_URL
        self.model = model or settings.AIMLAPI_MODEL

        if not self.api_key:
            raise LLMConfigurationError("AIMLAPI_API_KEY manquante dans .env")

    def complete(self, *, system: str, user: str) -> str:
        import requests

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
            },
            timeout=120,
        )
        if not response.ok:
            raise LLMError(f"AI/ML API error {response.status_code}: {response.text}")

        data = response.json()
        return (data["choices"][0]["message"]["content"] or "").strip()


def get_llm_client(provider: str | None = None) -> LLMClient:
    """Fabrique le client LLM selon LLM_PROVIDER."""
    selected = (provider or settings.LLM_PROVIDER).lower()

    if selected == "aimlapi":
        return AimlApiLLMClient()
    if selected == "groq":
        return GroqLLMClient()

    raise LLMConfigurationError(
        f"LLM_PROVIDER inconnu : {selected!r}. Valeurs : groq, aimlapi"
    )


class LLMError(Exception):
    """Erreur lors d'un appel LLM."""


class LLMConfigurationError(LLMError):
    """Configuration LLM invalide ou incomplète."""

"""Client LLM unifié pour SecureFlow AI.

Provider par défaut : OpenRouter (Llama 3.3 70B free).
Repli automatique : provider interne puis Google Gemini si quota.
Agents dédiés : MetricsAgent → AI/ML API ; DevAgent → Featherless.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Protocol

from django.conf import settings

logger = logging.getLogger(__name__)

_RETRY_AFTER_RE = re.compile(r"try again in (?P<duration>[^.]+)", re.IGNORECASE)


class LLMClient(Protocol):
    """Interface minimale attendue par BaseAgent."""

    def complete(self, *, system: str, user: str) -> str: ...


def _aimlapi_enabled() -> bool:
    return bool(getattr(settings, "LLM_USE_AIMLAPI", False))


def _openrouter_model_chain() -> list[str]:
    chain = getattr(settings, "OPENROUTER_MODEL_CHAIN", None)
    if chain:
        return list(chain)
    primary = getattr(settings, "OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    return [primary]


def _groq_model_chain() -> list[str]:
    chain = getattr(settings, "GROQ_MODEL_CHAIN", None)
    if chain:
        return list(chain)
    primary = getattr(settings, "GROQ_MODEL", "llama-3.1-8b-instant")
    return [primary]


def _groq_api_keys() -> list[str]:
    keys = getattr(settings, "GROQ_API_KEYS", None)
    if keys:
        return [k for k in keys if k]
    primary = getattr(settings, "GROQ_API_KEY", "")
    return [primary] if primary else []


class GroqModelChainClient:
    """Chaîne clés Groq × modèles Groq — bascule si quota ou modèle indisponible."""

    def __init__(
        self,
        models: list[str] | None = None,
        api_key: str | None = None,
        api_keys: list[str] | None = None,
    ) -> None:
        if api_keys is not None:
            self.api_keys = [k for k in api_keys if k]
        elif api_key:
            self.api_keys = [api_key]
        else:
            self.api_keys = _groq_api_keys()

        self.api_key = self.api_keys[0] if self.api_keys else ""
        self.models = models or _groq_model_chain()
        self._groq = None

        if not self.api_keys:
            raise LLMConfigurationError(
                "GROQ_API_KEY manquante dans .env (ou GROQ_API_KEY_2 pour une 2e clé)."
            )
        if not self.models:
            raise LLMConfigurationError(
                "Aucun modèle Groq configuré (GROQ_MODEL / GROQ_MODEL_FALLBACKS)."
            )

    def _reset_client(self, api_key: str) -> None:
        self.api_key = api_key
        self._groq = None

    def _groq_timeout(self) -> float:
        return float(getattr(settings, "GROQ_TIMEOUT", 180))

    def _groq_max_tokens(self) -> int:
        return int(getattr(settings, "GROQ_MAX_TOKENS", 2048))

    def _client(self):
        if self._groq is None:
            try:
                from groq import Groq
            except ImportError as exc:
                raise LLMConfigurationError(
                    "Package 'groq' non installé. Lance : pip install groq"
                ) from exc
            self._groq = Groq(api_key=self.api_key, timeout=self._groq_timeout())
        return self._groq

    def complete(self, *, system: str, user: str) -> str:
        last_error: LLMRateLimitError | None = None

        for key_index, api_key in enumerate(self.api_keys):
            self._reset_client(api_key)
            try:
                return self._complete_with_models(system=system, user=user, key_index=key_index)
            except LLMRateLimitError as exc:
                last_error = exc
                if key_index < len(self.api_keys) - 1:
                    logger.warning(
                        "Quota clé Groq #%s — bascule vers la clé suivante…",
                        key_index + 1,
                    )
                    try:
                        from apps.core.pipeline_context import add_warning

                        add_warning(
                            f"Clé Groq #{key_index + 2} utilisée "
                            f"(quota atteint sur la clé #{key_index + 1})."
                        )
                    except Exception:
                        pass
                continue

        keys_count = len(self.api_keys)
        models_list = ", ".join(self.models)
        hint = str(last_error) if last_error else ""
        raise LLMRateLimitError(
            f"Quota Groq atteint ({keys_count} clé(s), modèles : {models_list}). "
            f"{hint} Attendez la réinitialisation ou réduisez INGESTION_MAX_FILES."
        )

    def _complete_with_models(
        self, *, system: str, user: str, key_index: int
    ) -> str:
        last_error: LLMRateLimitError | None = None
        primary = self.models[0]

        for index, model in enumerate(self.models):
            try:
                content = self._complete_with_model(
                    model, system=system, user=user
                )
                if index > 0:
                    logger.info(
                        "Groq clé #%s — repli modèle %s (après limite sur %s)",
                        key_index + 1,
                        model,
                        primary,
                    )
                    try:
                        from apps.core.pipeline_context import add_warning

                        add_warning(
                            f"Modèle Groq « {model} » utilisé "
                            f"(quota atteint sur « {primary} »)."
                        )
                    except Exception:
                        pass
                return content
            except LLMRateLimitError as exc:
                last_error = exc
                if index < len(self.models) - 1:
                    logger.warning(
                        "Rate limit Groq clé #%s / %s — modèle suivant…",
                        key_index + 1,
                        model,
                    )
                continue

        if last_error:
            raise last_error
        raise LLMRateLimitError("Quota Groq atteint sur tous les modèles de la clé active.")

    def _complete_with_model(self, model: str, *, system: str, user: str) -> str:
        last_exc: Exception | None = None
        for attempt in range(2):
            try:
                response = self._client().chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=0.2,
                    max_tokens=self._groq_max_tokens(),
                    timeout=self._groq_timeout(),
                )
                return (response.choices[0].message.content or "").strip()
            except Exception as exc:
                last_exc = exc
                if attempt == 0 and _is_llm_timeout(exc):
                    logger.warning(
                        "Groq/%s timeout (tentative %s/2) — nouvel essai…",
                        model,
                        attempt + 1,
                    )
                    time.sleep(1.5)
                    continue
                if _is_llm_retryable(exc):
                    raise _map_provider_error(exc, provider=f"Groq/{model}") from exc
                raise LLMError(f"Groq/{model} : {exc}") from exc
        if last_exc:
            if _is_llm_retryable(last_exc):
                raise _map_provider_error(last_exc, provider=f"Groq/{model}") from last_exc
            raise LLMError(f"Groq/{model} : {last_exc}") from last_exc
        raise LLMError(f"Groq/{model} : échec après reprise")


class GroqLLMClient(GroqModelChainClient):
    """Alias — un seul modèle (chaîne d'un élément)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        single = model or settings.GROQ_MODEL
        keys = [api_key] if api_key else None
        super().__init__(models=[single], api_keys=keys)


class OpenRouterModelChainClient:
    """OpenRouter — API OpenAI-compatible (Llama 3.3 70B free, etc.)."""

    def __init__(
        self,
        models: list[str] | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = (api_key or getattr(settings, "OPENROUTER_API_KEY", "")).strip()
        self.models = models or _openrouter_model_chain()
        if base_url:
            self.base_url = base_url.rstrip("/")
        elif settings.configured:
            self.base_url = getattr(
                settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ).rstrip("/")
        else:
            self.base_url = "https://openrouter.ai/api/v1"

        if not self.api_key:
            raise LLMConfigurationError(
                "OPENROUTER_API_KEY manquante dans .env — https://openrouter.ai/keys"
            )
        if not self.models:
            raise LLMConfigurationError(
                "Aucun modèle OpenRouter (OPENROUTER_MODEL / OPENROUTER_MODEL_FALLBACKS)."
            )

    def _timeout(self) -> float:
        return float(getattr(settings, "OPENROUTER_TIMEOUT", 180))

    def _max_tokens(self) -> int:
        return int(getattr(settings, "OPENROUTER_MAX_TOKENS", 2048))

    def complete(self, *, system: str, user: str) -> str:
        last_error: LLMRateLimitError | None = None
        primary = self.models[0]

        for index, model in enumerate(self.models):
            try:
                content = self._complete_with_model(model, system=system, user=user)
                if index > 0:
                    logger.info(
                        "OpenRouter — repli modèle %s (après limite sur %s)",
                        model,
                        primary,
                    )
                    try:
                        from apps.core.pipeline_context import add_warning

                        add_warning(
                            f"Modèle OpenRouter « {model} » utilisé "
                            f"(quota ou indisponibilité sur « {primary} »)."
                        )
                    except Exception:
                        pass
                return content
            except LLMRateLimitError as exc:
                last_error = exc
                if index < len(self.models) - 1:
                    logger.warning("OpenRouter / %s — modèle suivant…", model)
                continue
            except LLMError as exc:
                if _is_llm_retryable(exc):
                    last_error = LLMRateLimitError(str(exc))
                    if index < len(self.models) - 1:
                        logger.warning("OpenRouter / %s — modèle suivant…", model)
                    continue
                raise

        if last_error:
            raise last_error
        raise LLMRateLimitError("OpenRouter : tous les modèles de la chaîne ont échoué.")

    def _complete_with_model(self, model: str, *, system: str, user: str) -> str:
        import requests

        last_exc: Exception | None = None
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": getattr(settings, "OPENROUTER_HTTP_REFERER", "http://localhost:8000"),
            "X-Title": getattr(settings, "OPENROUTER_APP_TITLE", "SecureFlow AI"),
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "max_tokens": self._max_tokens(),
        }

        for attempt in range(2):
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self._timeout(),
                )
                if response.status_code == 429:
                    raise LLMRateLimitError(f"Quota OpenRouter/{model} atteint.")
                if not response.ok:
                    raise LLMError(
                        f"OpenRouter/{model} error {response.status_code}: {response.text[:500]}"
                    )
                data = response.json()
                return (data["choices"][0]["message"]["content"] or "").strip()
            except Exception as exc:
                last_exc = exc
                if isinstance(exc, LLMRateLimitError):
                    raise
                if attempt == 0 and _is_llm_timeout(exc):
                    logger.warning(
                        "OpenRouter/%s timeout (tentative %s/2)…",
                        model,
                        attempt + 1,
                    )
                    time.sleep(1.5)
                    continue
                if _is_llm_retryable(exc):
                    raise _map_provider_error(exc, provider=f"OpenRouter/{model}") from exc
                raise LLMError(f"OpenRouter/{model} : {exc}") from exc

        if last_exc:
            if _is_llm_retryable(last_exc):
                raise _map_provider_error(last_exc, provider=f"OpenRouter/{model}") from last_exc
            raise LLMError(f"OpenRouter/{model} : {last_exc}") from last_exc
        raise LLMError(f"OpenRouter/{model} : échec après reprise")


class GoogleGeminiClient:
    """Google AI Studio (Gemini) — modèle gratuit avec clé AI Studio."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or getattr(settings, "GOOGLE_API_KEY", "")
        self.model = model or getattr(settings, "GOOGLE_MODEL", "gemini-2.0-flash")

        if not self.api_key:
            raise LLMConfigurationError(
                "GOOGLE_API_KEY manquante. Créez une clé sur https://aistudio.google.com/apikey"
            )

    def complete(self, *, system: str, user: str) -> str:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise LLMConfigurationError(
                "Package 'google-generativeai' non installé. Lance : pip install google-generativeai"
            ) from exc

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model, system_instruction=system)

        try:
            response = model.generate_content(
                user,
                generation_config={"temperature": 0.2},
            )
        except Exception as exc:
            raise _map_google_error(exc) from exc

        text = getattr(response, "text", None) or ""
        if not text.strip():
            raise LLMError("Gemini : réponse vide")
        return text.strip()


class AimlApiLLMClient:
    """Appels via AI/ML API — global si LLM_USE_AIMLAPI=true, ou forcé par agent."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        *,
        require_global_flag: bool = True,
    ) -> None:
        if require_global_flag and not _aimlapi_enabled():
            raise LLMConfigurationError(
                "AI/ML API désactivée. Utilisez LLM_PROVIDER=openrouter dans .env."
            )
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
        if response.status_code == 429:
            raise LLMRateLimitError(
                "Quota AI/ML API atteint. Réessayez plus tard ou utilisez Groq."
            )
        if not response.ok:
            raise LLMError(f"AI/ML API error {response.status_code}: {response.text}")

        data = response.json()
        return (data["choices"][0]["message"]["content"] or "").strip()


class FeatherlessLLMClient:
    """Featherless.ai — modèles open-source (OpenAI-compatible). DevAgent / remédiation."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or getattr(settings, "FEATHERLESS_API_KEY", "")
        self.base_url = (base_url or getattr(settings, "FEATHERLESS_BASE_URL", "")).rstrip("/")
        self.model = model or getattr(settings, "FEATHERLESS_MODEL", "meta-llama/Llama-3.1-8B-Instruct")

        if not self.api_key:
            raise LLMConfigurationError(
                "FEATHERLESS_API_KEY manquante. Obtenez une clé sur https://featherless.ai"
            )

    def _timeout(self) -> float:
        return float(getattr(settings, "FEATHERLESS_TIMEOUT", 300))

    def _max_retries(self) -> int:
        return max(1, int(getattr(settings, "FEATHERLESS_MAX_RETRIES", 2)))

    def complete(self, *, system: str, user: str) -> str:
        import requests

        attempts = self._max_retries()
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
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
                    timeout=self._timeout(),
                )
            except requests.exceptions.RequestException as exc:
                last_error = exc
                if attempt < attempts - 1 and _is_llm_timeout(exc):
                    logger.warning(
                        "Featherless/%s timeout (tentative %s/%s) — nouvel essai…",
                        self.model,
                        attempt + 1,
                        attempts,
                    )
                    time.sleep(2 * (attempt + 1))
                    continue
                raise LLMError(f"Featherless: {exc}") from exc

            if response.status_code == 429:
                raise LLMRateLimitError("Quota Featherless atteint.")
            if not response.ok:
                raise LLMError(f"Featherless error {response.status_code}: {response.text[:500]}")

            data = response.json()
            return (data["choices"][0]["message"]["content"] or "").strip()

        raise LLMError(f"Featherless: {last_error}")


class ChainedFallbackLLMClient:
    """Essaie plusieurs providers dans l'ordre (quota / timeout)."""

    _SILENT_PROVIDERS = {"groq"}

    def __init__(self, providers: list[str]) -> None:
        self.provider_names: list[str] = []
        self._clients: list[tuple[str, LLMClient]] = []
        for name in providers:
            normalized = _normalize_provider(name)
            if normalized in self.provider_names:
                continue
            if not _has_credentials(normalized):
                continue
            self.provider_names.append(normalized)
            self._clients.append((normalized, _build_client(normalized)))

        if not self._clients:
            raise LLMConfigurationError("Aucun provider LLM configuré.")

    def complete(self, *, system: str, user: str) -> str:
        last_exc: Exception | None = None
        for index, (name, client) in enumerate(self._clients):
            try:
                result = client.complete(system=system, user=user)
                if index > 0:
                    _notify_provider_fallback(self._clients[0][0], name)
                return result
            except LLMConfigurationError as exc:
                last_exc = exc
                logger.warning("Provider %s non configuré (%s)", name, exc)
            except LLMRateLimitError as exc:
                last_exc = exc
                logger.warning("Quota %s — provider suivant…", name)
            except LLMError as exc:
                last_exc = exc
                if index < len(self._clients) - 1 and _is_llm_retryable(exc):
                    logger.warning("%s indisponible (%s) — provider suivant…", name, exc)
                    continue
                raise

        if last_exc:
            raise last_exc
        raise LLMError("Tous les providers LLM ont échoué.")


class FallbackLLMClient(ChainedFallbackLLMClient):
    """Compat — chaîne à deux providers."""

    def __init__(self, primary: str, fallback: str | None = None) -> None:
        chain = [_normalize_provider(primary)]
        if fallback:
            chain.append(_normalize_provider(fallback))
        super().__init__(chain)


def _normalize_provider(name: str) -> str:
    selected = (name or "").strip().lower()
    if selected in ("gemini",):
        return "google"
    if selected in ("open-router",):
        return "openrouter"
    return selected


def _notify_provider_fallback(from_name: str, to_name: str) -> None:
    if to_name in ChainedFallbackLLMClient._SILENT_PROVIDERS:
        logger.info("Repli LLM silencieux : %s → %s", from_name, to_name)
        return
    try:
        from apps.core.pipeline_context import add_warning

        labels = {
            "google": "Google Gemini",
            "openrouter": "OpenRouter",
        }
        label = labels.get(to_name, to_name)
        add_warning(
            f"Provider LLM « {label} » utilisé (quota atteint sur {from_name})."
        )
    except Exception:
        pass


def _build_provider_chain(primary: str) -> list[str]:
    """Provider principal + repli explicite (LLM_FALLBACK_PROVIDER) uniquement."""
    primary = _normalize_provider(primary)
    chain = [primary]

    explicit = _normalize_provider(getattr(settings, "LLM_FALLBACK_PROVIDER", ""))
    if explicit and explicit != primary and _has_credentials(explicit):
        chain.append(explicit)

    return chain


def _build_client(provider: str) -> LLMClient:
    if provider == "featherless":
        return FeatherlessLLMClient()
    if provider == "aimlapi":
        return AimlApiLLMClient()
    if provider in ("openrouter", "open-router"):
        return OpenRouterModelChainClient()
    if provider == "groq":
        return GroqModelChainClient()
    if provider in ("google", "gemini"):
        return GoogleGeminiClient()
    raise LLMConfigurationError(
        f"LLM_PROVIDER inconnu : {provider!r}. "
        "Valeurs : featherless, openrouter, google, aimlapi, groq (legacy)"
    )


def _is_llm_timeout(exc: Exception) -> bool:
    message = str(exc).lower()
    return "timeout" in message or "timed out" in message


_is_groq_timeout = _is_llm_timeout  # compat tests / imports


def _is_llm_retryable(exc: Exception) -> bool:
    message = str(exc).lower()
    if _is_llm_timeout(exc):
        return True
    if isinstance(exc, LLMRateLimitError):
        return True
    if "429" in str(exc) or "rate limit" in message or "rate_limit" in message:
        return True
    if "quota" in message or "atteint" in message:
        return True
    if "decommissioned" in message:
        return True
    if "model" in message and ("not found" in message or "does not exist" in message):
        return True
    if "tokens per day" in message or "tpd" in message:
        return True
    return False


_is_groq_retryable = _is_llm_retryable  # compat


def _map_google_error(exc: Exception) -> Exception:
    message = str(exc).lower()
    if (
        "429" in str(exc)
        or "resource exhausted" in message
        or "quota" in message
        or "rate limit" in message
    ):
        return LLMRateLimitError(f"Quota Google Gemini atteint : {exc}")
    return LLMError(f"Google Gemini : {exc}")


def _map_provider_error(exc: Exception, *, provider: str) -> Exception:
    message = str(exc)
    if _is_llm_timeout(exc):
        return LLMRateLimitError(
            f"{provider} : délai dépassé — bascule modèle ou provider suivant."
        )
    if _is_llm_retryable(exc):
        retry = _RETRY_AFTER_RE.search(message)
        hint = f" Réessayez dans {retry.group('duration')}." if retry else ""
        return LLMRateLimitError(f"Quota {provider} atteint.{hint}")
    return LLMError(f"{provider} : {message}")


def get_llm_client(provider: str | None = None) -> LLMClient:
    """Fabrique le client LLM — OpenRouter par défaut, chaîne de repli automatique."""
    selected = (provider or settings.LLM_PROVIDER).lower()

    if selected == "aimlapi" and not _aimlapi_enabled():
        selected = "openrouter"
    selected = _normalize_provider(selected)

    chain = _build_provider_chain(selected)
    if len(chain) > 1:
        return ChainedFallbackLLMClient(chain)

    return _build_client(selected)


def get_llm_client_for_agent(agent_name: str) -> LLMClient:
    """
    Routage LLM par agent (partenaires hackathon).
    - MetricsAgent → AI/ML API si AIMLAPI_API_KEY + LLM_METRICS_USE_AIMLAPI
    - DevAgent → Featherless si FEATHERLESS_API_KEY + LLM_DEV_USE_FEATHERLESS
    Sinon provider global avec repli habituel.
    """
    if agent_name == "MetricsAgent" and getattr(settings, "LLM_METRICS_USE_AIMLAPI", True):
        if getattr(settings, "AIMLAPI_API_KEY", ""):
            try:
                return AimlApiLLMClient(require_global_flag=False)
            except LLMConfigurationError:
                pass

    if agent_name == "DevAgent" and getattr(settings, "LLM_DEV_USE_FEATHERLESS", True):
        if getattr(settings, "FEATHERLESS_API_KEY", ""):
            try:
                return FeatherlessLLMClient()
            except LLMConfigurationError:
                pass

    return get_llm_client()


def _has_credentials(provider: str) -> bool:
    if provider == "featherless":
        return bool(getattr(settings, "FEATHERLESS_API_KEY", ""))
    if provider in ("openrouter", "open-router"):
        return bool(getattr(settings, "OPENROUTER_API_KEY", ""))
    if provider == "groq":
        return bool(_groq_api_keys())
    if provider in ("google", "gemini"):
        return bool(getattr(settings, "GOOGLE_API_KEY", ""))
    if provider == "aimlapi":
        return _aimlapi_enabled() and bool(settings.AIMLAPI_API_KEY)
    return False


class LLMError(Exception):
    """Erreur lors d'un appel LLM."""


class LLMConfigurationError(LLMError):
    """Configuration LLM invalide ou incomplète."""


class LLMRateLimitError(LLMError):
    """Quota ou rate limit du fournisseur LLM."""

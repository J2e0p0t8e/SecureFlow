"""
Configuration Django — SecureFlow AI.

Les clés sensibles viennent de .env (voir .env.example).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("1", "true", "yes")
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "apps.core",
    "apps.agents",
    "apps.orchestrator",
    "apps.ingestion",
    "apps.api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# CORS configuration (pour déploiement si frontend séparé)
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "False").lower() in ("1", "true", "yes")

ROOT_URLCONF = "secureflow.urls"
WSGI_APPLICATION = "secureflow.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Durcissement sécurité (actif uniquement hors DEBUG / production) ---
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() in ("1", "true", "yes")
    # Render/Heroku terminent TLS via proxy → on lit l'en-tête de forwarding
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# --- SecureFlow / intégrations externes ---

BAND_BASE_URL = os.getenv("BAND_BASE_URL", "https://app.band.ai").rstrip("/")
BAND_WEB_APP_URL = os.getenv("BAND_WEB_APP_URL", BAND_BASE_URL).rstrip("/")
BAND_ROOM_URL_TEMPLATE = os.getenv("BAND_ROOM_URL_TEMPLATE", "{base}/chat/{room_id}")
# UUID du compte Band humain (propriétaire des agents) — requis pour répondre APPROUVE/REJETE dans la Room
BAND_OWNER_USER_ID = os.getenv("BAND_OWNER_USER_ID", "").strip()

# Les 13 agents Band utilisent BAND_{SLUG}_AGENT_ID / BAND_{SLUG}_API_KEY
# Voir apps/agents/band_registry.py et docs/SETUP_BAND_13_AGENTS.md

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_API_KEY_2 = os.getenv("GROQ_API_KEY_2", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()


def _build_groq_api_keys() -> list[str]:
    keys: list[str] = []
    for part in [GROQ_API_KEY, GROQ_API_KEY_2, os.getenv("GROQ_API_KEYS", "")]:
        if not part:
            continue
        if "," in part:
            for item in part.split(","):
                k = item.strip()
                if k and k not in keys:
                    keys.append(k)
        elif part not in keys:
            keys.append(part)
    return keys


GROQ_API_KEYS = _build_groq_api_keys()

# Chaîne de repli Groq (429 / quota) — modèles essayés dans l'ordre
_default_groq_fallbacks = "llama-3.3-70b-versatile,gemma2-9b-it,mixtral-8x7b-32768"
_groq_fallbacks_raw = os.getenv("GROQ_MODEL_FALLBACKS", _default_groq_fallbacks)


def _build_groq_model_chain() -> list[str]:
    models: list[str] = []
    for part in [GROQ_MODEL, *_groq_fallbacks_raw.split(",")]:
        name = part.strip()
        if name and name not in models:
            models.append(name)
    return models


GROQ_MODEL_CHAIN = _build_groq_model_chain()
GROQ_TIMEOUT = float(os.getenv("GROQ_TIMEOUT", "180"))
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "2048"))

# OpenRouter — Llama 3.3 70B (free) par défaut : https://openrouter.ai/keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"
).strip()
OPENROUTER_HTTP_REFERER = os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost:8000").strip()
OPENROUTER_APP_TITLE = os.getenv("OPENROUTER_APP_TITLE", "SecureFlow AI").strip()
_openrouter_fallbacks_raw = os.getenv("OPENROUTER_MODEL_FALLBACKS", "")


def _build_openrouter_model_chain() -> list[str]:
    models: list[str] = []
    for part in [OPENROUTER_MODEL, *_openrouter_fallbacks_raw.split(",")]:
        name = part.strip()
        if name and name not in models:
            models.append(name)
    return models


OPENROUTER_MODEL_CHAIN = _build_openrouter_model_chain()
OPENROUTER_TIMEOUT = float(os.getenv("OPENROUTER_TIMEOUT", "180"))
OPENROUTER_MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "2048"))

# Google AI Studio / Gemini (repli optionnel)
GOOGLE_API_KEY = (
    os.getenv("GOOGLE_API_KEY", "").strip()
    or os.getenv("GEMINI_API_KEY", "").strip()
)
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash").strip()

AIMLAPI_API_KEY = os.getenv("AIMLAPI_API_KEY", "")
AIMLAPI_BASE_URL = os.getenv("AIMLAPI_BASE_URL", "https://api.aimlapi.com/v1").rstrip("/")
AIMLAPI_MODEL = os.getenv("AIMLAPI_MODEL", "anthropic/claude-3.5-sonnet")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter").lower()
# Repli si quota épuisé (vide = auto : openrouter↔google selon clés disponibles)
LLM_FALLBACK_PROVIDER = os.getenv("LLM_FALLBACK_PROVIDER", "").strip().lower()
LLM_USE_AIMLAPI = os.getenv("LLM_USE_AIMLAPI", "false").lower() in ("1", "true", "yes")

# Partenaires hackathon — routage LLM par agent (optionnel)
FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY", "").strip()
FEATHERLESS_BASE_URL = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1").rstrip("/")
FEATHERLESS_MODEL = os.getenv("FEATHERLESS_MODEL", "meta-llama/Llama-3.1-8B-Instruct").strip()
FEATHERLESS_TIMEOUT = float(os.getenv("FEATHERLESS_TIMEOUT", "300"))
FEATHERLESS_MAX_RETRIES = int(os.getenv("FEATHERLESS_MAX_RETRIES", "2"))
# MetricsAgent → AI/ML API si clé présente ; DevAgent → Featherless si clé présente
LLM_METRICS_USE_AIMLAPI = os.getenv("LLM_METRICS_USE_AIMLAPI", "true").lower() in ("1", "true", "yes")
LLM_DEV_USE_FEATHERLESS = os.getenv("LLM_DEV_USE_FEATHERLESS", "true").lower() in ("1", "true", "yes")

# Limites tokens / ingestion
INGESTION_MAX_FILES = int(os.getenv("INGESTION_MAX_FILES", "80"))
INGESTION_MAX_FILES_A = int(os.getenv("INGESTION_MAX_FILES_A", "80"))
INGESTION_MAX_FILES_C = int(os.getenv("INGESTION_MAX_FILES_C", "100"))
INGESTION_MAX_FILE_CHARS = int(os.getenv("INGESTION_MAX_FILE_CHARS", "8000"))
INGESTION_MAX_TOTAL_CHARS = int(os.getenv("INGESTION_MAX_TOTAL_CHARS", "120000"))
LLM_MAX_PROMPT_CHARS = int(os.getenv("LLM_MAX_PROMPT_CHARS", "35000"))
LLM_INITIAL_CONTENT_CHARS = int(os.getenv("LLM_INITIAL_CONTENT_CHARS", "45000"))
LLM_AGENT_RESULT_CHARS = int(os.getenv("LLM_AGENT_RESULT_CHARS", "8000"))

# Clé API optionnelle pour protéger POST /api/analyze/ (vide = désactivé)
SECUREFLOW_API_KEY = os.getenv("SECUREFLOW_API_KEY", "")

# Dossiers ignorés lors de l'ingestion ZIP / GitHub (Personne 2)
INGESTION_IGNORE_DIRS = {
    ".git",
    ".svn",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "venv",
    ".venv",
    "dist",
    "build",
    "vendor",
    ".idea",
    ".vscode",
}

# Taille max upload ZIP (20 Mo)
INGESTION_MAX_UPLOAD_BYTES = 20 * 1024 * 1024

# Token GitHub optionnel (évite les rate-limits sur l'API publique)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REQUEST_TIMEOUT = float(os.getenv("GITHUB_REQUEST_TIMEOUT", "60"))
GITHUB_FETCH_WORKERS = int(os.getenv("GITHUB_FETCH_WORKERS", "12"))
# Cache d'ingestion GitHub en mémoire (secondes) — 0 = désactivé
GITHUB_CACHE_TTL = float(os.getenv("GITHUB_CACHE_TTL", "300"))

# Taille max d'un message/event publié dans la Band Room
BAND_MAX_EVENT_CHARS = int(os.getenv("BAND_MAX_EVENT_CHARS", "6000"))

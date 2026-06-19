"""
Module d'ingestion GitHub pour SecureFlow AI.
Récupère le contenu d'un repo GitHub public via l'API GitHub.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from urllib.parse import urlparse

import requests
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from apps.ingestion.bundle import truncate_file_body
from apps.ingestion.selectors import build_file_manifest, is_binary_path, select_paths
from apps.ingestion.types import IngestionResult

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
RAW_BASE = "https://raw.githubusercontent.com"

# Cache d'ingestion en mémoire (TTL) — évite de re-cloner le même dépôt.
_cache_lock = threading.Lock()
_ingestion_cache: dict[tuple, tuple[float, IngestionResult]] = {}


def _cache_ttl() -> float:
    return float(getattr(settings, "GITHUB_CACHE_TTL", 300))


def _cache_get(key: tuple) -> IngestionResult | None:
    ttl = _cache_ttl()
    if ttl <= 0:
        return None
    with _cache_lock:
        entry = _ingestion_cache.get(key)
        if not entry:
            return None
        stored_at, result = entry
        if time.time() - stored_at > ttl:
            _ingestion_cache.pop(key, None)
            return None
        return result


def _cache_set(key: tuple, result: IngestionResult) -> None:
    if _cache_ttl() <= 0:
        return
    with _cache_lock:
        _ingestion_cache[key] = (time.time(), result)
        # Garde-fou mémoire : conserve les 32 entrées les plus récentes.
        if len(_ingestion_cache) > 32:
            oldest = sorted(_ingestion_cache.items(), key=lambda kv: kv[1][0])
            for stale_key, _ in oldest[:-32]:
                _ingestion_cache.pop(stale_key, None)


def clear_ingestion_cache() -> None:
    with _cache_lock:
        _ingestion_cache.clear()


def _request_timeout() -> float:
    return float(getattr(settings, "GITHUB_REQUEST_TIMEOUT", 60))


def _fetch_workers() -> int:
    return max(1, int(getattr(settings, "GITHUB_FETCH_WORKERS", 12)))


def _github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "SecureFlow-AI",
    }
    token = getattr(settings, "GITHUB_TOKEN", "") or ""
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _github_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(_github_headers())
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    adapter = HTTPAdapter(max_retries=retry, pool_maxsize=_fetch_workers() + 4)
    session.mount("https://", adapter)
    return session


def parse_github_url(url: str) -> tuple[str, str, str | None]:
    """
    Parse une URL GitHub et retourne (owner, repo, branch_or_none).

    Exemples:
        https://github.com/user/repo -> (user, repo, None)
        https://github.com/user/repo.git -> (user, repo, None)
        https://github.com/user/repo/tree/dev -> (user, repo, dev)
    """
    parsed = urlparse(url.strip())
    path_parts = [p for p in parsed.path.split("/") if p]

    if len(path_parts) < 2:
        raise ValueError(f"URL GitHub invalide : {url}")

    owner = path_parts[0]
    repo = path_parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]

    branch: str | None = None
    if len(path_parts) >= 4 and path_parts[2] == "tree":
        branch = path_parts[3]

    return owner, repo, branch


def _github_error_message(response: requests.Response) -> str:
    if response.status_code == 403:
        return (
            "Accès GitHub refusé (rate limit ou dépôt privé). "
            "Ajoutez GITHUB_TOKEN dans .env ou réessayez plus tard."
        )
    if response.status_code == 404:
        return "Dépôt ou branche GitHub introuvable — vérifiez l'URL."
    return f"Erreur GitHub HTTP {response.status_code}"


def _resolve_default_branch(session: requests.Session, owner: str, repo: str) -> str:
    repo_url = f"{GITHUB_API}/repos/{owner}/{repo}"
    response = session.get(repo_url, timeout=_request_timeout())
    if response.status_code in (403, 404):
        raise ValueError(_github_error_message(response))
    response.raise_for_status()
    data = response.json()
    return data.get("default_branch") or "main"


def _fetch_raw_file(
    session: requests.Session,
    owner: str,
    repo: str,
    branch: str,
    path: str,
) -> tuple[str, str | None, str | None]:
    raw_url = f"{RAW_BASE}/{owner}/{repo}/{branch}/{path}"
    try:
        content_response = session.get(raw_url, timeout=_request_timeout())
        if content_response.status_code >= 400:
            return path, None, _github_error_message(content_response)
        content = content_response.content.decode("utf-8")
        return path, truncate_file_body(content, path), None
    except UnicodeDecodeError:
        return path, None, "fichier binaire ignoré"
    except requests.RequestException as exc:
        return path, None, str(exc)


def fetch_github_project(
    url: str,
    max_files: int = 50,
    branch: Optional[str] = None,
) -> IngestionResult:
    """Récupère le contenu d'un repo GitHub public."""
    owner, repo, detected_branch = parse_github_url(url)
    session = _github_session()
    branch = branch or detected_branch or _resolve_default_branch(session, owner, repo)
    source_label = f"github:{owner}/{repo}@{branch}"

    cache_key = (owner.lower(), repo.lower(), branch, int(max_files))
    cached = _cache_get(cache_key)
    if cached is not None:
        logger.info("GitHub ingestion %s/%s@%s — servi depuis le cache", owner, repo, branch)
        return cached

    tree_url = f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{branch}"
    response = session.get(
        tree_url,
        params={"recursive": "1"},
        timeout=_request_timeout(),
    )

    if response.status_code == 404 and branch == "main":
        return fetch_github_project(url, max_files, branch="master")

    if response.status_code in (403, 404):
        raise ValueError(_github_error_message(response))
    response.raise_for_status()

    tree_data = response.json()
    if "tree" not in tree_data:
        raise ValueError(f"Réponse API GitHub invalide pour {owner}/{repo}")

    files: list[str] = []
    for item in tree_data["tree"]:
        if item.get("type") != "blob":
            continue

        path = item["path"]
        path_parts = path.split("/")
        if any(part in settings.INGESTION_IGNORE_DIRS for part in path_parts):
            continue
        if is_binary_path(path):
            continue

        files.append(path)

    total_files = len(files)
    selected, truncated = select_paths(files, max_files)
    manifest = build_file_manifest(files, selected)

    project_content = f"# Projet GitHub : {owner}/{repo} (branche: {branch})\n"
    project_content += f"# Fichiers analysés : {len(selected)}/{total_files}\n\n"
    project_content += manifest
    project_content += "\n\n"

    workers = min(_fetch_workers(), max(1, len(selected)))
    loaded = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(_fetch_raw_file, session, owner, repo, branch, path)
            for path in selected
        ]
        for future in as_completed(futures):
            path, content, error = future.result()
            if content:
                loaded += 1
                project_content += (
                    f"\n{'=' * 80}\nFichier : {path}\n{'=' * 80}\n{content}\n\n"
                )
            elif error:
                project_content += f"\n[Erreur lors de la récupération de {path} : {error}]\n\n"

    if loaded == 0:
        raise ValueError(
            f"Aucun fichier texte récupérable dans {owner}/{repo}. "
            "Vérifiez l'URL, la branche, ou définissez GITHUB_TOKEN dans .env."
        )

    logger.info(
        "GitHub ingestion %s/%s@%s — %s/%s fichiers chargés",
        owner,
        repo,
        branch,
        loaded,
        total_files,
    )

    result = IngestionResult(
        content=project_content,
        files_analyzed=loaded,
        files_total=total_files,
        truncated=truncated,
        source_label=source_label,
        file_manifest=manifest,
    )
    _cache_set(cache_key, result)
    return result


def is_valid_github_url(url: str) -> bool:
    """Vérifie si une URL est une URL GitHub valide."""
    pattern = r"^https?://(?:www\.)?github\.com/[\w\-.]+/[\w\-.]+(?:/.*)?$"
    return bool(re.match(pattern, url.strip()))

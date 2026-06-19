"""Tests du cache d'ingestion GitHub (TTL en mémoire)."""

import apps.ingestion.github as gh
from apps.ingestion.github import clear_ingestion_cache
from apps.ingestion.types import IngestionResult


def _fake_result(label: str = "github:o/r@main") -> IngestionResult:
    return IngestionResult(
        content="# contenu",
        files_analyzed=1,
        files_total=1,
        truncated=False,
        source_label=label,
        file_manifest="manifest",
    )


def test_cache_set_get_roundtrip(settings):
    settings.GITHUB_CACHE_TTL = 300
    clear_ingestion_cache()
    key = ("o", "r", "main", 50)
    assert gh._cache_get(key) is None
    result = _fake_result()
    gh._cache_set(key, result)
    cached = gh._cache_get(key)
    assert cached is result


def test_cache_disabled_when_ttl_zero(settings):
    settings.GITHUB_CACHE_TTL = 0
    clear_ingestion_cache()
    key = ("o", "r", "main", 50)
    gh._cache_set(key, _fake_result())
    assert gh._cache_get(key) is None


def test_cache_expires(settings, monkeypatch):
    settings.GITHUB_CACHE_TTL = 10
    clear_ingestion_cache()
    key = ("o", "r", "main", 50)

    times = {"now": 1000.0}
    monkeypatch.setattr(gh.time, "time", lambda: times["now"])

    gh._cache_set(key, _fake_result())
    assert gh._cache_get(key) is not None

    times["now"] = 1000.0 + 11  # dépasse le TTL
    assert gh._cache_get(key) is None

"""Préparation du contenu projet pour les agents (scan A→Z)."""

from __future__ import annotations

from django.conf import settings

from apps.core.text_limits import truncate_text
from apps.ingestion.sast import run_bandit_scan
from apps.ingestion.static_analysis import format_static_scan_report, scan_project_content


def _max_file_chars() -> int:
    return int(getattr(settings, "INGESTION_MAX_FILE_CHARS", 8000))


def _max_total_chars() -> int:
    return int(getattr(settings, "INGESTION_MAX_TOTAL_CHARS", 120000))


def _scanner_char_limit() -> int:
    return int(getattr(settings, "LLM_INITIAL_CONTENT_CHARS", 45000))


def truncate_file_body(body: str, path: str) -> str:
    limit = _max_file_chars()
    cleaned = (body or "").strip()
    if len(cleaned) <= limit:
        return cleaned
    return (
        f"{cleaned[:limit]}\n\n"
        f"[… fichier tronqué — {path}, {len(cleaned):,} caractères au total]"
    )


def cap_project_content(content: str) -> str:
    """Limite la taille totale du bundle ingéré."""
    limit = _max_total_chars()
    cleaned = (content or "").strip()
    if len(cleaned) <= limit:
        return cleaned
    return (
        f"{cleaned[:limit]}\n\n"
        f"[… projet tronqué — {len(cleaned):,} caractères au total, "
        f"augmentez INGESTION_MAX_TOTAL_CHARS si besoin]"
    )


def _static_risk_floor(*, high: int, medium: int, total: int) -> float:
    """Plancher de risque /10 déduit des signaux statiques objectifs."""
    floor = 0.0
    if total >= 5:
        floor = 5.0
    if total >= 10:
        floor = 6.0
    if medium >= 1:
        floor = max(floor, 6.0)
    if high >= 1:
        floor = max(floor, 7.0)
    if high >= 3:
        floor = max(floor, 8.0)
    if high >= 5:
        floor = max(floor, 9.0)
    return floor


def _record_static_signal(regex_findings, bandit_findings) -> None:
    """Calcule et stocke le résumé d'analyse statique pour le cross-check."""
    high = sum(1 for f in bandit_findings if " HIGH " in f.category)
    medium = sum(1 for f in bandit_findings if " MEDIUM " in f.category)
    total = len(regex_findings) + len(bandit_findings)
    signal = {
        "regex": len(regex_findings),
        "bandit": len(bandit_findings),
        "high": high,
        "medium": medium,
        "total": total,
        "risk_floor": _static_risk_floor(high=high, medium=medium, total=total),
    }
    try:
        from apps.core.pipeline_context import set_static_signal

        set_static_signal(signal)
    except Exception:  # le cross-check ne doit jamais bloquer le scan
        pass


def prepare_project_for_scan(
    content: str,
    ingestion_meta: dict | None = None,
    *,
    locale: str = "fr",
) -> str:
    """
    Enrichit le projet avec le pré-scan statique pour ScannerAgent.
    """
    meta = ingestion_meta or {}
    header_lines = ["# Bundle scan SecureFlow", ""]

    if meta.get("truncated"):
        if locale == "en":
            header_lines.append(
                f"Partial ingestion: {meta.get('files_analyzed', '?')}/"
                f"{meta.get('files_total', '?')} files loaded — review manifest below."
            )
        else:
            header_lines.append(
                f"Ingestion partielle : {meta.get('files_analyzed', '?')}/"
                f"{meta.get('files_total', '?')} fichiers chargés — voir inventaire ci-dessous."
            )
        header_lines.append("")

    if meta.get("file_manifest"):
        header_lines.append(meta["file_manifest"])
        header_lines.append("")

    findings = scan_project_content(content)
    header_lines.append(format_static_scan_report(findings, locale=locale))
    header_lines.append("")

    try:
        bandit_findings = run_bandit_scan(content)
    except Exception:  # SAST ne doit jamais bloquer le scan
        bandit_findings = []

    _record_static_signal(findings, bandit_findings)
    if bandit_findings:
        sast_title = "SAST BANDIT" if locale == "en" else "SAST BANDIT (analyse statique réelle)"
        header_lines.append(sast_title)
        header_lines.append(
            f"{'Automated issues' if locale == 'en' else 'Problèmes détectés'} : "
            f"{len(bandit_findings)}"
        )
        for item in bandit_findings:
            header_lines.append(
                f"• [{item.category}] {item.path}:{item.line} — {item.snippet}"
            )
        header_lines.append("")
    header_lines.append("=" * 80)
    header_lines.append("CONTENU SOURCE" if locale != "en" else "SOURCE CONTENT")
    header_lines.append("=" * 80)
    header_lines.append("")

    bundle = "\n".join(header_lines) + content.strip()
    bundle = cap_project_content(bundle)
    return truncate_text(bundle, max_chars=_scanner_char_limit(), label="projet")

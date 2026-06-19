"""Locale / langue d'exécution (fr | en)."""

from __future__ import annotations

SUPPORTED_LOCALES = frozenset({"fr", "en"})


def normalize_locale(value: str | None) -> str:
    if not value:
        return "fr"
    code = str(value).lower().strip().replace("_", "-")[:2]
    return code if code in SUPPORTED_LOCALES else "fr"


def api_message(key: str, locale: str = "fr", **kwargs) -> str:
    """Messages d'erreur API localisés."""
    return _localized_message(_API_MESSAGES, key, locale, **kwargs)


def pdf_message(key: str, locale: str = "fr", **kwargs) -> str:
    """Libellés PDF Mode C localisés."""
    return _localized_message(_PDF_MESSAGES, key, locale, **kwargs)


def pdf_report_name(audit_id: str, locale: str = "fr") -> str:
    """Nom affiché du rapport PDF (ex. SecureFlow Analysis SF-REPORT-…)."""
    return pdf_message("report_name", locale, audit_id=audit_id)


def pdf_decision_label(decision: str | None, locale: str = "fr") -> str:
    """Libellé de décision localisé pour le PDF."""
    if not decision:
        return "N/A"
    lang = normalize_locale(locale)
    mapping = _DECISION_LABELS.get(decision.upper(), {})
    return mapping.get(lang) or mapping.get("fr") or decision.upper()


def _localized_message(
    catalog: dict[str, dict[str, str]],
    key: str,
    locale: str,
    **kwargs,
) -> str:
    lang = normalize_locale(locale)
    messages = catalog.get(key, {})
    template = messages.get(lang) or messages.get("fr") or key
    return template.format(**kwargs) if kwargs else template


_DECISION_LABELS: dict[str, dict[str, str]] = {
    "CRITIQUE": {"fr": "CRITIQUE", "en": "CRITICAL"},
    "CORRIGER": {"fr": "CORRIGER", "en": "REMEDIATE"},
    "SURVEILLER": {"fr": "SURVEILLER", "en": "MONITOR"},
    "PROPRE": {"fr": "PROPRE", "en": "CLEAR"},
}


_PDF_MESSAGES: dict[str, dict[str, str]] = {
    "subtitle": {
        "fr": "Rapport d'audit de sécurité — Mode C",
        "en": "Security Audit Report — Mode C",
    },
    "security_score": {
        "fr": "Score sécurité",
        "en": "Security score",
    },
    "score_not_calculated": {
        "fr": "Score non calculé",
        "en": "Score not calculated",
    },
    "field_report": {
        "fr": "Rapport",
        "en": "Report",
    },
    "report_name": {
        "fr": "SecureFlow Analyse {audit_id}",
        "en": "SecureFlow Analysis {audit_id}",
    },
    "field_id": {
        "fr": "Identifiant",
        "en": "ID",
    },
    "field_date": {
        "fr": "Date",
        "en": "Date",
    },
    "field_decision": {
        "fr": "Décision",
        "en": "Decision",
    },
    "final_decision": {
        "fr": "Décision finale",
        "en": "Final decision",
    },
    "professional_report": {
        "fr": "RAPPORT PROFESSIONNEL",
        "en": "PROFESSIONAL REPORT",
    },
    "metrics_appendix": {
        "fr": "ANNEXE — MÉTRIQUES DE SÉCURITÉ",
        "en": "APPENDIX — SECURITY METRICS",
    },
    "footer_confidential": {
        "fr": "Document confidentiel · SecureFlow AI · {audit_id}",
        "en": "Confidential document · SecureFlow AI · {audit_id}",
    },
}


_API_MESSAGES: dict[str, dict[str, str]] = {
    "invalid_mode": {
        "fr": "mode doit être 'A', 'B' ou 'C'",
        "en": "mode must be 'A', 'B', or 'C'",
    },
    "input_type_required": {
        "fr": "input_type requis",
        "en": "input_type is required",
    },
    "mode_c_text_forbidden": {
        "fr": (
            "Mode C (Rapport PDF) : fournissez un dépôt GitHub ou une archive ZIP. "
            "L'audit formel nécessite un projet complet, pas un simple extrait de code."
        ),
        "en": (
            "Mode C (PDF Report): provide a GitHub repository or ZIP archive. "
            "Formal audit requires a full project, not a short code snippet."
        ),
    },
    "mode_b_no_github_zip": {
        "fr": (
            "Mode B (Dev Pipeline) : décrivez le projet à créer de zéro "
            "dans le champ texte. GitHub et ZIP sont réservés aux modes Audit (A) et Rapport (C)."
        ),
        "en": (
            "Mode B (Dev Pipeline): describe the project to build from scratch in the text field. "
            "GitHub and ZIP are reserved for Audit (A) and Report (C) modes."
        ),
    },
    "pdf_mode_a_only": {
        "fr": (
            "Le PDF est réservé au Mode C (Rapport PDF). "
            "Mode A : consultez le verdict et la checklist dans la Band Room."
        ),
        "en": (
            "PDF is available for Mode C only. "
            "Mode A: see the verdict and checklist in the Band Room."
        ),
    },
    "ingestion_partial": {
        "fr": (
            "Ingestion partielle : {files_analyzed}/{files_total} fichiers "
            "inclus dans l'analyse. Les autres fichiers n'ont pas été lus par les agents."
        ),
        "en": (
            "Partial ingestion: {files_analyzed}/{files_total} files "
            "included in the analysis. Other files were not read by agents."
        ),
    },
    "band_seed_partial": {
        "fr": (
            "Band Room : aperçu du projet partiellement publié "
            "(seed limité ou indisponible)."
        ),
        "en": (
            "Band Room: project preview partially published "
            "(limited or unavailable seed)."
        ),
    },
    "analysis_failed": {
        "fr": "L'analyse n'a pas pu être terminée. Veuillez réessayer dans quelques instants.",
        "en": "The analysis could not be completed. Please try again in a few moments.",
    },
    "human_review_not_pending": {
        "fr": "Aucune validation humaine en attente pour cette session.",
        "en": "No human validation pending for this session.",
    },
    "human_review_invalid_action": {
        "fr": "Action invalide — utilisez « proceed » ou « abort ».",
        "en": "Invalid action — use « proceed » or « abort ».",
    },
    "human_review_accepted": {
        "fr": "Décision enregistrée dans la Band Room — reprise du pipeline.",
        "en": "Decision recorded in the Band Room — resuming pipeline.",
    },
}

"""Extraction normalisée des données de rapport (partagée PDF / HTML)."""

from __future__ import annotations

from typing import Any

from apps.core.locale import normalize_locale

_DECISION_MEANING = {
    "CRITIQUE": {
        "fr": "vulnérabilités critiques — corrections obligatoires avant mise en production",
        "en": "critical vulnerabilities — fixes required before production",
    },
    "CORRIGER": {
        "fr": "corrections nécessaires avant déploiement",
        "en": "fixes needed before deployment",
    },
    "SURVEILLER": {
        "fr": "pas de blocage, points à surveiller",
        "en": "no blockers, items to monitor",
    },
    "PROPRE": {
        "fr": "aucun problème bloquant détecté",
        "en": "no blocking issues found",
    },
}


def _decision_meaning(decision: str, locale: str) -> str:
    entry = _DECISION_MEANING.get((decision or "").upper())
    if not entry:
        return ""
    return entry["en"] if locale == "en" else entry["fr"]


def _score_qualifier(score: Any, locale: str) -> str:
    try:
        value = float(score)
    except (TypeError, ValueError):
        return ""
    if locale == "en":
        if value >= 80:
            return "strong"
        if value >= 60:
            return "moderate"
        if value >= 40:
            return "weak"
        return "critical"
    if value >= 80:
        return "bon"
    if value >= 60:
        return "moyen"
    if value >= 40:
        return "faible"
    return "critique"


def extract_report_context(session: Any) -> dict[str, Any]:
    """Construit un contexte rapport homogène à partir d'une AnalysisSession."""
    result_data = session.result_json or {}
    mode = result_data.get("mode") or session.mode
    branch = result_data.get("branch")
    ingestion = result_data.get("ingestion", {}) or {}
    locale = normalize_locale(result_data.get("locale") or ingestion.get("locale"))

    audit_id = (
        result_data.get("audit_id")
        or session.audit_id
        or f"SF-REPORT-{(session.room_id or '')[:8].upper()}"
    )
    final_report = (
        result_data.get("final_report")
        or session.final_report
        or "Rapport non disponible"
    )
    decision = result_data.get("decision") or session.decision or "N/A"
    agents = result_data.get("agents", []) or []
    security_score = result_data.get("security_score")
    disagreement = result_data.get("disagreement")

    report_agent = next((a for a in agents if a.get("name") == "ReportAgent"), None)
    metrics_agent = next((a for a in agents if a.get("name") == "MetricsAgent"), None)
    report_body = (report_agent or {}).get("content") or final_report
    metrics_body = (metrics_agent or {}).get("content") or ""

    return {
        "audit_id": audit_id,
        "room_id": session.room_id or "",
        "date": session.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "mode": mode,
        "mode_display": session.get_mode_display(),
        "input_type_display": session.get_input_type_display(),
        "decision": decision,
        "project_label": session.project_label or "",
        "duration_seconds": session.duration_seconds,
        "security_score": security_score,
        "branch": branch,
        "locale": locale,
        "agents": agents,
        "final_report": final_report,
        "report_body": report_body,
        "metrics_body": metrics_body,
        "disagreement": disagreement,
    }


def format_disagreement(disagreement: dict[str, Any] | None, locale: str) -> dict[str, Any] | None:
    """Normalise un désaccord pour l'affichage PDF/HTML. Renvoie None si absent."""
    if not disagreement:
        return None
    scores = disagreement.get("scores") or {}
    if not scores:
        return None
    en = locale == "en"
    spread = disagreement.get("spread")
    rows = [(str(agent), f"{score}/10") for agent, score in scores.items()]
    return {
        "title": "Disagreement detected" if en else "Désaccord détecté",
        "rows": rows,
        "spread_label": "Spread" if en else "Écart",
        "spread": f"{spread} pts" if spread is not None else "",
        "note": (
            "The triage agents diverged; DecisionAgent ruled and the final verdict reflects it."
            if en
            else "Les agents de triage ont divergé ; DecisionAgent a tranché et le verdict final en tient compte."
        ),
    }


def build_executive_summary(ctx: dict[str, Any]) -> dict[str, Any]:
    """Construit un résumé exécutif clair et textuel (FR/EN) à partir du contexte.

    Renvoie un dict structuré que le PDF et le HTML formatent à leur façon.
    """
    locale = ctx.get("locale", "fr")
    en = locale == "en"
    decision = (ctx.get("decision") or "N/A").upper()
    score = ctx.get("security_score")
    branch = ctx.get("branch")
    agents = ctx.get("agents", []) or []
    is_remediation = branch == "remediation" or decision in ("CRITIQUE", "CORRIGER")

    meaning = _decision_meaning(decision, locale)
    verdict = f"{decision}" + (f" — {meaning}" if meaning else "")

    if score not in (None, ""):
        qualifier = _score_qualifier(score, locale)
        score_line = f"{score}/100" + (f" ({qualifier})" if qualifier else "")
    else:
        score_line = "N/A"

    if is_remediation:
        takeaways = (
            [
                "Vulnerabilities requiring remediation were identified.",
                "A fix (ZIP patch) was generated and reviewed by the pipeline.",
                "The HTML/PDF report details every finding and its correction.",
            ]
            if en
            else [
                "Des vulnérabilités nécessitant une remédiation ont été identifiées.",
                "Un correctif (patch ZIP) a été généré et vérifié par le pipeline.",
                "Le rapport HTML/PDF détaille chaque faille et sa correction.",
            ]
        )
        recommendation = (
            "Apply the provided patch, then run a new audit to confirm the fixes."
            if en
            else "Appliquez le correctif fourni, puis relancez un audit pour confirmer."
        )
    else:
        takeaways = (
            [
                "No blocking vulnerability was detected — project deemed acceptable.",
                "A formal report and a security score were produced.",
                "Flagged items should be monitored over time.",
            ]
            if en
            else [
                "Aucune vulnérabilité bloquante détectée — projet jugé acceptable.",
                "Un rapport formel et un score de sécurité ont été produits.",
                "Les points signalés sont à surveiller dans le temps.",
            ]
        )
        recommendation = (
            "Monitor the flagged items and schedule regular security audits."
            if en
            else "Surveillez les points signalés et planifiez des audits réguliers."
        )

    disagreement = ctx.get("disagreement")
    if disagreement and (disagreement.get("scores")):
        spread = disagreement.get("spread")
        takeaways.append(
            (f"Agents disagreed (spread {spread} pts) — DecisionAgent ruled." if en
             else f"Désaccord entre agents (écart {spread} pts) — DecisionAgent a tranché.")
        )

    return {
        "title": "Executive summary" if en else "Résumé exécutif",
        "verdict_label": "Verdict" if en else "Verdict",
        "verdict": verdict,
        "score_label": "Security score" if en else "Score de sécurité",
        "score": score_line,
        "agents_label": "Agents involved" if en else "Agents mobilisés",
        "agents": len(agents),
        "project_label": "Project" if en else "Projet",
        "project": ctx.get("project_label") or "—",
        "takeaways_label": "Key points" if en else "À retenir",
        "takeaways": takeaways,
        "recommendation_label": "Recommendation" if en else "Recommandation",
        "recommendation": recommendation,
    }

"""Validation et extraction structurée des sorties agents."""

from __future__ import annotations

import json
import random
import re
from datetime import datetime
from typing import Any

METADATA_BLOCK_RE = re.compile(
    r"===\s*METADATA\s+JSON\s*===\s*(\{.*?\})\s*===\s*END\s+METADATA\s*===",
    re.DOTALL | re.IGNORECASE,
)

AUDIT_ID_PATTERN = re.compile(r"SF-AUDIT-\d{8}-\d{4}", re.IGNORECASE)
REPORT_ID_PATTERN = re.compile(r"SF-(?:REPORT|DEV)-\d{8}-\d{4}", re.IGNORECASE)

REQUIRED_PREFIX_BY_AGENT: dict[str, str] = {
    "ScannerAgent": "SCAN TERMINÉ :",
    "ThreatAgent": "MENACES IDENTIFIÉES :",
    "ComplianceAgent": "CONFORMITÉ OWASP/CWE :",
    "RiskAgent": "RISQUE GLOBAL :",
    "DecisionAgent": "DÉCISION FINALE :",
    "FeasibilityAgent": "ANALYSE DE FAISABILITÉ :",
    "ArchitectAgent": "ARCHITECTURE TECHNIQUE :",
    "DesignAgent": "GUIDE DESIGN :",
    "DevAgent": "CODE GÉNÉRÉ :",
    "SecurityAgent": "AUDIT DU CODE GÉNÉRÉ :",
    "QAAgent": "RAPPORT DE VALIDATION :",
    "MetricsAgent": "MÉTRIQUES DE SÉCURITÉ :",
    "ReportAgent": "RAPPORT FINAL :",
}

REQUIRED_PREFIX_BY_AGENT_EN: dict[str, str] = {
    "ScannerAgent": "SCAN COMPLETE:",
    "ThreatAgent": "THREATS IDENTIFIED:",
    "ComplianceAgent": "OWASP/CWE COMPLIANCE:",
    "RiskAgent": "GLOBAL RISK:",
    "DecisionAgent": "FINAL DECISION:",
    "FeasibilityAgent": "FEASIBILITY ANALYSIS:",
    "ArchitectAgent": "TECHNICAL ARCHITECTURE:",
    "DesignAgent": "DESIGN GUIDE:",
    "DevAgent": "CODE GENERATED:",
    "SecurityAgent": "GENERATED CODE AUDIT:",
    "QAAgent": "VALIDATION REPORT:",
    "MetricsAgent": "SECURITY METRICS:",
    "ReportAgent": "FINAL REPORT:",
}


def get_required_prefix(agent_name: str, locale: str = "fr") -> str | None:
    from apps.core.locale import normalize_locale

    lang = normalize_locale(locale)
    if lang == "en":
        return REQUIRED_PREFIX_BY_AGENT_EN.get(agent_name)
    return REQUIRED_PREFIX_BY_AGENT.get(agent_name)


def generate_id(prefix: str = "SF-AUDIT") -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"


def validate_prefix(content: str, required_prefix: str) -> bool:
    if not content or not required_prefix:
        return True
    normalized = content.lstrip()
    prefix = required_prefix.strip()
    if normalized.startswith(prefix):
        return True
    first_line = normalized.split("\n", 1)[0].strip()
    return prefix.lower() in first_line.lower()


_DISCUSSION_REPORT_RE = re.compile(
    r"^DISCUSSION\s*:\s*\n(?P<discussion>.+?)\n\s*(?:RAPPORT|REPORT)\s*:\s*\n(?P<report>.+)$",
    re.DOTALL | re.IGNORECASE,
)


def split_discussion_and_report(content: str) -> tuple[str, str]:
    """
    Sépare le fil de discussion (ton humain) du rapport technique structuré.
    Retourne (discussion, rapport). Si pas de marqueurs, rapport = contenu entier.
    """
    text = (content or "").strip()
    if not text:
        return "", ""
    match = _DISCUSSION_REPORT_RE.match(text)
    if match:
        return match.group("discussion").strip(), match.group("report").strip()
    return "", text


def extract_metadata_json(text: str) -> dict[str, Any]:
    if not text:
        return {}
    match = METADATA_BLOCK_RE.search(text)
    if not match:
        return {}
    try:
        data = json.loads(match.group(1))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def extract_audit_id(text: str, metadata: dict[str, Any] | None = None) -> str | None:
    meta = metadata or extract_metadata_json(text)
    for key in ("audit_id", "report_id"):
        value = meta.get(key)
        if value and isinstance(value, str):
            return value.upper()
    match = AUDIT_ID_PATTERN.search(text or "")
    if match:
        return match.group(0).upper()
    match = REPORT_ID_PATTERN.search(text or "")
    return match.group(0).upper() if match else None


def extract_decision(text: str, metadata: dict[str, Any] | None = None) -> str | None:
    meta = metadata or extract_metadata_json(text)
    raw = meta.get("decision")
    if isinstance(raw, str):
        normalized = _normalize_security_decision(raw)
        if normalized:
            return normalized

    if not text:
        return None

    patterns = (
        (r"🔴\s*CRITIQUE|\bCRITIQUE\b", "CRITIQUE"),
        (r"🟠\s*CORRIGER|\bCORRIGER\b", "CORRIGER"),
        (r"🟡\s*SURVEILLER|\bSURVEILLER\b", "SURVEILLER"),
        (r"🟢\s*PROPRE|\bPROPRE\b", "PROPRE"),
    )
    for pattern, label in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return label
    return None


def extract_risk_score(text: str, metadata: dict[str, Any] | None = None) -> float | None:
    meta = metadata or extract_metadata_json(text)
    for key in ("risk_score", "score", "global_risk"):
        raw = meta.get(key)
        if isinstance(raw, (int, float)):
            return float(raw)
        if isinstance(raw, str):
            match = re.search(r"(\d+(?:\.\d+)?)", raw)
            if match:
                return float(match.group(1))
    if not text:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", text)
    if match:
        return float(match.group(1))
    return None


def needs_remediation(decision: str | None) -> bool:
    if not decision:
        return False
    return decision.upper() in ("CRITIQUE", "CORRIGER")


def extract_qa_decision(text: str, metadata: dict[str, Any] | None = None) -> str | None:
    meta = metadata or extract_metadata_json(text)
    raw = meta.get("decision") or meta.get("validation")
    if isinstance(raw, str):
        normalized = _normalize_qa_decision(raw)
        if normalized:
            return normalized

    if not text:
        return None

    for label in ("REJETÉ", "REJETE", "AVEC RÉSERVES", "AVEC RESERVES", "VALIDÉ", "VALIDE"):
        if re.search(rf"\b{label}\b", text, re.IGNORECASE):
            if label.startswith("REJ"):
                return "REJETÉ"
            if "RÉSER" in label or "RESER" in label:
                return "AVEC RÉSERVES"
            return "VALIDÉ"

    validation_match = re.search(
        r"validation\s*:\s*(oui|partiellement|non)",
        text,
        re.IGNORECASE,
    )
    if validation_match:
        return _normalize_qa_decision(validation_match.group(1))

    return None


def _normalize_security_decision(value: str) -> str | None:
    upper = value.upper().strip()
    for label in ("CRITIQUE", "CORRIGER", "SURVEILLER", "PROPRE"):
        if label in upper:
            return label
    return None


def _normalize_qa_decision(value: str) -> str | None:
    lower = value.lower().strip()
    mapping = {
        "oui": "VALIDÉ",
        "yes": "VALIDÉ",
        "validé": "VALIDÉ",
        "valide": "VALIDÉ",
        "validé.": "VALIDÉ",
        "partiellement": "AVEC RÉSERVES",
        "partial": "AVEC RÉSERVES",
        "avec réserves": "AVEC RÉSERVES",
        "avec reservess": "AVEC RÉSERVES",
        "avec reserves": "AVEC RÉSERVES",
        "non": "REJETÉ",
        "no": "REJETÉ",
        "rejeté": "REJETÉ",
        "rejete": "REJETÉ",
    }
    if lower in mapping:
        return mapping[lower]
    upper = value.upper()
    for label in ("VALIDÉ", "VALIDE", "REJETÉ", "REJETE", "AVEC RÉSERVES", "AVEC RESERVES"):
        if label in upper:
            if "REJ" in label:
                return "REJETÉ"
            if "RÉSER" in label or "RESER" in label:
                return "AVEC RÉSERVES"
            return "VALIDÉ"
    return None

"""Tests du résumé exécutif et de la génération PDF."""

from apps.api.pdf_generator import generate_audit_pdf, generate_mode_c_pdf
from apps.api.report_data import build_executive_summary, format_disagreement


def _ctx(**overrides):
    base = {
        "audit_id": "SF-AUDIT-1234",
        "decision": "CRITIQUE",
        "security_score": 30,
        "branch": "remediation",
        "locale": "fr",
        "agents": [{"name": "ScannerAgent", "content": "x"}, {"name": "ThreatAgent", "content": "y"}],
        "project_label": "vulnerable",
    }
    base.update(overrides)
    return base


def test_summary_remediation_fr():
    summary = build_executive_summary(_ctx())
    assert summary["title"] == "Résumé exécutif"
    assert summary["verdict"].startswith("CRITIQUE")
    assert "30/100" in summary["score"]
    assert summary["agents"] == 2
    assert any("patch" in t.lower() or "correctif" in t.lower() for t in summary["takeaways"])
    assert "audit" in summary["recommendation"].lower()


def test_summary_reporting_en():
    summary = build_executive_summary(
        _ctx(decision="PROPRE", branch="reporting", security_score=88, locale="en")
    )
    assert summary["title"] == "Executive summary"
    assert "88/100" in summary["score"]
    assert any("no blocking" in t.lower() for t in summary["takeaways"])


def test_summary_without_score():
    summary = build_executive_summary(_ctx(security_score=None))
    assert summary["score"] == "N/A"


def test_generate_audit_pdf_with_summary():
    summary = build_executive_summary(_ctx())
    pdf = generate_audit_pdf(
        "Rapport d'audit",
        report_text="## Section\nContenu",
        audit_id="SF-AUDIT-1234",
        decision="CRITIQUE",
        decision_label="CRITIQUE",
        security_score=30,
        summary=summary,
        meta_rows=[("Date", "2026-06-19")],
        locale="fr",
    )
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1000


def test_format_disagreement():
    dis = format_disagreement({"scores": {"ThreatAgent": 8, "RiskAgent": 3}, "spread": 5}, "fr")
    assert dis is not None
    assert dis["title"] == "Désaccord détecté"
    assert ("ThreatAgent", "8/10") in dis["rows"]
    assert dis["spread"] == "5 pts"


def test_format_disagreement_none():
    assert format_disagreement(None, "fr") is None
    assert format_disagreement({"scores": {}}, "fr") is None


def test_summary_mentions_disagreement():
    ctx = _ctx(disagreement={"scores": {"ThreatAgent": 8, "RiskAgent": 3}, "spread": 5})
    summary = build_executive_summary(ctx)
    assert any("ésaccord" in t for t in summary["takeaways"])


def test_audit_pdf_with_disagreement():
    dis = format_disagreement({"scores": {"ThreatAgent": 8, "RiskAgent": 3}, "spread": 5}, "fr")
    pdf = generate_audit_pdf(
        "Rapport",
        report_text="## S\nx",
        audit_id="SF-1",
        decision="CRITIQUE",
        summary=build_executive_summary(_ctx()),
        disagreement=dis,
        locale="fr",
    )
    assert pdf[:4] == b"%PDF"


def test_generate_mode_c_pdf_with_summary():
    summary = build_executive_summary(_ctx(decision="PROPRE", branch="reporting", security_score=80))
    pdf = generate_mode_c_pdf(
        audit_id="SF-AUDIT-1234",
        decision="PROPRE",
        security_score=80,
        report_text="## Rapport\nOK",
        metrics_text="## Metrics\n10",
        session_date="2026-06-19 03:00:00",
        locale="fr",
        summary=summary,
    )
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1000

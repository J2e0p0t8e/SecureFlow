"""Tests pour le rapport HTML autonome."""

from apps.api.html_report import render_report_html


def _ctx(**overrides):
    base = {
        "audit_id": "SF-REPORT-ABCD1234",
        "room_id": "room-xyz",
        "date": "2026-06-19 03:00:00",
        "mode": "A",
        "mode_display": "Audit-to-Fix",
        "input_type_display": "GitHub",
        "decision": "CRITIQUE",
        "project_label": "vulnerable",
        "duration_seconds": 42,
        "security_score": 35,
        "branch": "remediation",
        "locale": "fr",
        "agents": [
            {"name": "ScannerAgent", "content": "## Findings\n* MD5 faible\n* shell=True"},
        ],
        "final_report": "**Verdict** : remédiation requise.",
        "report_body": "",
        "metrics_body": "",
    }
    base.update(overrides)
    return base


def test_render_report_html_structure():
    doc = render_report_html(_ctx())
    assert doc.startswith("<!DOCTYPE html>")
    assert "SF-REPORT-ABCD1234" in doc
    assert "ScannerAgent" in doc
    assert "CRITIQUE" in doc
    assert "35" in doc
    assert "<style>" in doc  # CSS inline → fichier autonome


def test_render_report_html_escapes_content():
    doc = render_report_html(
        _ctx(agents=[{"name": "X", "content": "<script>alert(1)</script>"}])
    )
    assert "<script>alert(1)</script>" not in doc
    assert "&lt;script&gt;" in doc


def test_render_report_html_decision_badges():
    ok_doc = render_report_html(_ctx(decision="PROPRE", security_score=92))
    assert "badge ok" in ok_doc
    crit_doc = render_report_html(_ctx(decision="CRITIQUE", security_score=20))
    assert "badge crit" in crit_doc


def test_render_report_html_without_score():
    doc = render_report_html(_ctx(security_score=None))
    assert "/100" not in doc


def test_render_report_html_includes_summary():
    doc = render_report_html(_ctx())
    assert "Résumé exécutif" in doc
    assert "À retenir" in doc
    assert "Recommandation" in doc
    # le résumé apparaît deux fois (en tête + fin)
    assert doc.count('class="summary"') == 2


def test_render_report_html_includes_disagreement():
    doc = render_report_html(
        _ctx(disagreement={"scores": {"ThreatAgent": 8, "RiskAgent": 3}, "spread": 5})
    )
    assert "Désaccord détecté" in doc
    assert 'class="disagree"' in doc
    assert "ThreatAgent" in doc


def test_render_report_html_without_disagreement():
    doc = render_report_html(_ctx())
    assert 'class="disagree"' not in doc

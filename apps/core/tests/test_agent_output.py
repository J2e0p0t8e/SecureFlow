"""Tests extraction métadonnées agents."""

from apps.core.agent_output import (
    extract_audit_id,
    extract_decision,
    extract_metadata_json,
    extract_qa_decision,
    split_discussion_and_report,
    validate_prefix,
)


def test_validate_prefix():
    assert validate_prefix("SCAN TERMINÉ :\n• item", "SCAN TERMINÉ :")
    assert validate_prefix("  MENACES IDENTIFIÉES :\nok", "MENACES IDENTIFIÉES :")
    assert not validate_prefix("Erreur de format", "SCAN TERMINÉ :")


def test_extract_metadata_json():
    text = """
RAPPORT DE VALIDATION :
Validation : oui

=== METADATA JSON ===
{"validation": "oui", "decision": "VALIDÉ", "report_id": "SF-DEV-20260617-1234"}
=== END METADATA ===
"""
    meta = extract_metadata_json(text)
    assert meta["decision"] == "VALIDÉ"
    assert extract_qa_decision(text, meta) == "VALIDÉ"
    assert extract_audit_id(text, meta) == "SF-DEV-20260617-1234"


def test_extract_decision_with_emoji():
    text = "DÉCISION FINALE :\n🔴 CRITIQUE — ne pas déployer."
    assert extract_decision(text) == "CRITIQUE"


def test_extract_qa_from_validation_line():
    text = "RAPPORT DE VALIDATION :\nValidation : partiellement\nScore : 6/10"
    assert extract_qa_decision(text) == "AVEC RÉSERVES"


def test_split_discussion_and_report():
    raw = (
        "DISCUSSION :\n"
        "Salut @Threat, le repo sent le SQLi partout.\n\n"
        "RAPPORT :\n"
        "SCAN TERMINÉ :\n"
        "• routes non filtrées"
    )
    discussion, report = split_discussion_and_report(raw)
    assert "SQLi" in discussion
    assert report.startswith("SCAN TERMINÉ :")

    discussion_en, report_en = split_discussion_and_report(
        "DISCUSSION:\nHey team.\n\nREPORT:\nSCAN COMPLETE:\n• item"
    )
    assert "Hey team" in discussion_en
    assert report_en.startswith("SCAN COMPLETE:")

    empty_disc, full = split_discussion_and_report("SCAN TERMINÉ :\n• seul bloc")
    assert empty_disc == ""
    assert full.startswith("SCAN TERMINÉ :")

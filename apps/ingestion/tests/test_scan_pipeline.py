"""Tests ingestion — sélection, analyse statique, bundle scan."""

from apps.core.pipeline_context import get_static_signal, set_static_signal
from apps.ingestion.bundle import (
    _static_risk_floor,
    prepare_project_for_scan,
    truncate_file_body,
)
from apps.ingestion.selectors import build_file_manifest, priority_score, select_paths
from apps.ingestion.static_analysis import scan_project_content


def test_priority_score_prefers_security_paths():
    assert priority_score("app/auth/login.py") > priority_score("docs/readme.txt")
    assert priority_score("requirements.txt") > priority_score("misc/foo.txt")


def test_select_paths_truncates():
    paths = [f"src/file_{i}.py" for i in range(10)]
    selected, truncated = select_paths(paths, max_files=3)
    assert len(selected) == 3
    assert truncated is True


def test_static_scan_finds_hardcoded_secret():
    content = (
        "================\nFichier : app/settings.py\n================\n"
        'API_KEY = "sk_live_abc123secret"\n'
    )
    findings = scan_project_content(content)
    assert findings
    assert any("settings.py" in f.path for f in findings)


def test_prepare_project_for_scan_includes_manifest_and_static():
    content = (
        "INVENTAIRE\n\n================\nFichier : routes.py\n================\n"
        "cursor.execute(f\"SELECT * FROM users WHERE id={user_id}\")\n"
    )
    bundle = prepare_project_for_scan(
        content,
        {
            "truncated": True,
            "files_analyzed": 1,
            "files_total": 5,
            "file_manifest": "INVENTAIRE DU DÉPÔT\nFichiers texte repérés : 5",
        },
        locale="fr",
    )
    assert "PRÉ-SCAN STATIQUE" in bundle
    assert "Ingestion partielle" in bundle
    assert "routes.py" in bundle


def test_truncate_file_body():
    long_body = "x" * 9000
    truncated = truncate_file_body(long_body, "big.py")
    assert len(truncate_file_body("short", "a.py")) == 5
    assert "big.py" in truncated


def test_static_risk_floor_escalates_with_high():
    assert _static_risk_floor(high=0, medium=0, total=0) == 0.0
    assert _static_risk_floor(high=0, medium=0, total=5) == 5.0
    assert _static_risk_floor(high=1, medium=0, total=1) == 7.0
    assert _static_risk_floor(high=3, medium=0, total=3) == 8.0
    assert _static_risk_floor(high=5, medium=0, total=5) == 9.0


def test_prepare_project_for_scan_records_static_signal():
    set_static_signal(None)
    content = (
        "================\nFichier : app/settings.py\n================\n"
        'API_KEY = "sk_live_abc123secret"\n'
    )
    prepare_project_for_scan(content, {}, locale="fr")
    signal = get_static_signal()
    assert signal is not None
    assert signal["total"] >= 1
    assert "risk_floor" in signal

"""Tests pour l'extraction ZIP Mode B."""

import io
import zipfile

from apps.api.project_bundle import (
    build_mode_b_zip,
    build_readme_content,
    build_syntax_report,
    parse_dev_agent_files,
    validate_python_files,
)


def test_parse_dev_file_blocks():
    content = """CODE GÉNÉRÉ :

=== FILE: backend/main.py ===
from fastapi import FastAPI
app = FastAPI()
=== END FILE ===

=== FILE: requirements.txt ===
fastapi==0.110.0
=== END FILE ===
"""
    files = parse_dev_agent_files(content)
    assert "backend/main.py" in files
    assert "FastAPI" in files["backend/main.py"]
    assert files["requirements.txt"].startswith("fastapi")


def test_build_mode_b_zip():
    result = {
        "agents": [
            {
                "name": "ArchitectAgent",
                "content": "ARCHITECTURE TECHNIQUE :\n=== PROJECT TREE ===\napp/\n  main.py\n=== END PROJECT TREE ===",
            },
            {
                "name": "DevAgent",
                "content": "=== FILE: app/main.py ===\nprint('hi')\n=== END FILE ===",
            },
        ]
    }
    data = build_mode_b_zip(result, project_label="demo")
    assert data is not None
    assert len(data) > 100


def test_readme_includes_launch_instructions():
    readme = build_readme_content(
        label="Todo App",
        tree="app/\n  main.py",
        architect="ARCHITECTURE TECHNIQUE :\nStack : Django + React",
        feasibility="",
        dev_readme=(
            "DESCRIPTION :\nApp de todos\n\n"
            "INSTALLATION :\n  pip install -r requirements.txt\n\n"
            "LANCEMENT :\n  python manage.py runserver\n\n"
            "ACCÈS :\n  http://localhost:8000"
        ),
        dev_raw="",
        qa="",
        project_files={"manage.py": "..."},
    )
    assert "COMMENT LANCER LE PROJET" in readme
    assert "python manage.py runserver" in readme
    assert "http://localhost:8000" in readme


def test_validate_python_files_detects_syntax_error():
    files = {
        "good.py": "def ok():\n    return 1\n",
        "bad.py": "def broken(:\n    return\n",
        "notes.txt": "def not_python(:",
    }
    errors = validate_python_files(files)
    paths = [path for path, _ in errors]
    assert "bad.py" in paths
    assert "good.py" not in paths
    assert "notes.txt" not in paths


def test_build_syntax_report_clean():
    report = build_syntax_report({"a.py": "x = 1\n"})
    assert "Fichiers invalides : 0" in report
    assert "compilent sans erreur" in report


def test_zip_includes_syntax_check():
    result = {
        "agents": [
            {
                "name": "DevAgent",
                "content": "=== FILE: app/main.py ===\nprint('hi')\n=== END FILE ===",
            },
        ]
    }
    data = build_mode_b_zip(result, project_label="demo")
    assert data is not None
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
    assert "docs/SYNTAX_CHECK.md" in names

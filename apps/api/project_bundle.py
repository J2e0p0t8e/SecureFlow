"""Construction d'une archive ZIP à partir des livrables Mode B."""

from __future__ import annotations

import io
import re
import zipfile
from typing import Any

from apps.ingestion.zip_loader import _is_safe_zip_path

_FILE_BLOCK_RE = re.compile(
    r"===\s*FILE:\s*(.+?)\s*===\s*\n(.*?)(?=\n===\s*(?:FILE:|END\s+FILE)|\Z)",
    re.DOTALL | re.IGNORECASE,
)
_FILE_LINE_RE = re.compile(
    r"(?:^|\n)(?:Fichier|File)\s*:\s*([^\n]+)\s*\n(?:={3,}|-{3,})?\s*\n(.*?)(?=\n(?:Fichier|File)\s*:|\Z)",
    re.DOTALL | re.IGNORECASE,
)
_FENCE_RE = re.compile(
    r"```[^\n]*\n(?:#\s*(?:file|path)\s*:\s*)?([^\n]+)\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)
_TREE_RE = re.compile(
    r"===\s*PROJECT TREE\s*===\s*\n(.*?)(?:===\s*END PROJECT TREE\s*===|\Z)",
    re.DOTALL | re.IGNORECASE,
)
_SECTION_RE = re.compile(
    r"(?:^|\n)([A-ZÉÈÊÀÔÎÙÇ][A-ZÉÈÊÀÔÎÙÇ0-9 \-/]{2,})\s*:?\s*\n",
    re.MULTILINE,
)


def _normalize_path(path: str) -> str:
    cleaned = path.strip().strip("`\"'").replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


def _add_file(files: dict[str, str], path: str, content: str) -> None:
    path = _normalize_path(path)
    content = content.strip()
    if not path or not content:
        return
    if not _is_safe_zip_path(path):
        return
    files[path] = content


def parse_dev_agent_files(content: str) -> dict[str, str]:
    """Extrait les fichiers du rapport DevAgent."""
    files: dict[str, str] = {}

    for match in _FILE_BLOCK_RE.finditer(content):
        _add_file(files, match.group(1), match.group(2))

    for match in _FILE_LINE_RE.finditer(content):
        _add_file(files, match.group(1), match.group(2))

    for match in _FENCE_RE.finditer(content):
        path_hint = match.group(1).strip()
        body = match.group(2)
        if "/" in path_hint or "." in path_hint:
            _add_file(files, path_hint, body)

    return files


def extract_project_tree(architect_content: str) -> str:
    """Extrait l'arborescence déclarée par ArchitectAgent."""
    match = _TREE_RE.search(architect_content)
    if match:
        return match.group(1).strip()

    structure_match = re.search(
        r"(?:^|\n)Structure\s*:?\s*\n(.*?)(?=\n(?:Données|API|Dépendances|\Z))",
        architect_content,
        re.DOTALL | re.IGNORECASE,
    )
    if structure_match:
        return structure_match.group(1).strip()

    return ""


def _extract_architect_section(architect: str, section: str) -> str:
    pattern = re.compile(
        rf"(?:^|\n){re.escape(section)}\s*:?\s*\n(.*?)(?=\n[A-Za-zÉÈÊÀÔÎÙ][^\n]{{0,40}}:|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(architect)
    return match.group(1).strip() if match else ""


def _extract_run_sections(text: str) -> str:
    """Extrait les sections liées au lancement depuis un README ou rapport."""
    if not text:
        return ""

    keywords = (
        "LANCEMENT",
        "INSTALLATION",
        "PRÉREQUIS",
        "PREREQUIS",
        "DÉMARRAGE",
        "DEMARRAGE",
        "COMMENT LANCER",
        "ACCÈS",
        "ACCES",
        "VARIABLES D'ENVIRONNEMENT",
    )
    parts: list[str] = []
    for match in _SECTION_RE.finditer(text):
        title = match.group(1).strip().upper()
        if not any(key in title for key in keywords):
            continue
        start = match.end()
        next_match = _SECTION_RE.search(text, start)
        end = next_match.start() if next_match else len(text)
        body = text[start:end].strip()
        if body:
            parts.append(f"{match.group(1).strip()} :\n{body}")

    return "\n\n".join(parts).strip()


def _guess_run_commands(architect: str, project_files: dict[str, str]) -> str:
    """Instructions de secours déduites de la stack et des fichiers présents."""
    stack = architect.lower()
    paths = " ".join(project_files.keys()).lower()
    lines = [
        "PRÉREQUIS :",
        "Installez les outils correspondant à la stack du projet (voir docs/ARCHITECTURE.md).",
        "",
    ]

    if "docker" in stack or "docker-compose" in paths:
        lines.extend(
            [
                "LANCEMENT AVEC DOCKER :",
                "  docker compose build",
                "  docker compose up",
                "",
                "ACCÈS : http://localhost (voir docker-compose.yml pour le port)",
                "",
            ]
        )

    if "django" in stack or "manage.py" in paths:
        lines.extend(
            [
                "LANCEMENT BACKEND DJANGO :",
                "  python -m venv .venv",
                "  pip install -r requirements.txt",
                "  cp .env.example .env   # puis éditez les variables",
                "  python manage.py migrate",
                "  python manage.py runserver",
                "",
                "ACCÈS : http://localhost:8000",
                "",
            ]
        )

    if any(x in stack for x in ("react", "vue", "next", "vite")) or "package.json" in paths:
        lines.extend(
            [
                "LANCEMENT FRONTEND :",
                "  npm install",
                "  npm run dev",
                "",
                "ACCÈS : http://localhost:5173 (ou le port indiqué dans le terminal)",
                "",
            ]
        )

    if "fastapi" in stack or "uvicorn" in stack:
        lines.extend(
            [
                "LANCEMENT API FASTAPI :",
                "  pip install -r requirements.txt",
                "  uvicorn main:app --reload",
                "",
                "ACCÈS : http://localhost:8000/docs",
                "",
            ]
        )

    if "flask" in stack:
        lines.extend(
            [
                "LANCEMENT FLASK :",
                "  pip install -r requirements.txt",
                "  flask --app app run --debug",
                "",
                "ACCÈS : http://localhost:5000",
                "",
            ]
        )

    if len(lines) <= 3:
        lines.extend(
            [
                "LANCEMENT :",
                "Consultez docs/ARCHITECTURE.md et les fichiers requirements.txt / package.json.",
            ]
        )

    return "\n".join(lines).strip()


def build_readme_content(
    *,
    label: str,
    tree: str,
    architect: str,
    feasibility: str,
    dev_readme: str | None,
    dev_raw: str,
    qa: str,
    project_files: dict[str, str],
) -> str:
    """Assemble le README racine avec instructions de lancement."""
    description = (
        _extract_architect_section(feasibility, "Périmètre")
        or _extract_architect_section(feasibility, "Faisabilité")
        or _extract_architect_section(architect, "Stack")
        or f"Projet {label} généré par SecureFlow AI (Mode B)."
    )
    stack = _extract_architect_section(architect, "Stack") or "Voir docs/ARCHITECTURE.md"

    run_from_readme = _extract_run_sections(dev_readme or "")
    if not run_from_readme:
        run_from_readme = _extract_run_sections(dev_raw)
    if not run_from_readme:
        run_from_readme = _guess_run_commands(architect, project_files)

    lines = [
        label.upper(),
        "=" * len(label),
        "",
        "DESCRIPTION :",
        description,
        "",
        "STACK TECHNIQUE :",
        stack,
        "",
    ]

    if tree:
        lines.extend(["STRUCTURE DU PROJET :", tree, ""])

    lines.extend(
        [
            "COMMENT LANCER LE PROJET :",
            run_from_readme,
            "",
        ]
    )

    if dev_readme and dev_readme.strip() and not run_from_readme:
        lines.extend(["GUIDE DÉVELOPPEUR (DevAgent) :", dev_readme.strip(), ""])

    if qa:
        livraison = _extract_architect_section(qa, "Livraison") or _extract_run_sections(qa)
        if livraison:
            lines.extend(["NOTES DE LIVRAISON (QA) :", livraison, ""])

    lines.extend(
        [
            "DOCUMENTATION COMPLÈMENTAIRE :",
            "  docs/ARCHITECTURE.md — architecture détaillée",
            "  docs/DESIGN.md — guide design",
            "  docs/SECURITY_AUDIT.md — audit sécurité",
            "  docs/QA_REPORT.md — validation qualité",
            "",
            "Généré par SecureFlow AI — Mode B (Dev Pipeline).",
        ]
    )

    return "\n".join(lines).strip() + "\n"


def validate_python_files(project_files: dict[str, str]) -> list[tuple[str, str]]:
    """Compile chaque fichier .py généré pour détecter les erreurs de syntaxe.

    Renvoie une liste (chemin, message d'erreur) pour les fichiers invalides.
    """
    errors: list[tuple[str, str]] = []
    for path, content in sorted(project_files.items()):
        if not path.lower().endswith(".py"):
            continue
        try:
            compile(content, path, "exec")
        except SyntaxError as exc:
            location = f"ligne {exc.lineno}" if exc.lineno else "position inconnue"
            errors.append((path, f"{exc.msg} ({location})"))
        except ValueError as exc:
            errors.append((path, f"Contenu non compilable : {exc}"))
    return errors


def build_syntax_report(project_files: dict[str, str]) -> str:
    """Rapport Markdown de validation syntaxique du code généré."""
    py_files = [p for p in project_files if p.lower().endswith(".py")]
    errors = validate_python_files(project_files)
    lines = [
        "# Validation syntaxique du code généré",
        "",
        f"Fichiers Python vérifiés : {len(py_files)}",
        f"Fichiers invalides : {len(errors)}",
        "",
    ]
    if not py_files:
        lines.append("Aucun fichier Python à valider (stack non-Python ou code non extrait).")
    elif not errors:
        lines.append("Tous les fichiers Python générés compilent sans erreur de syntaxe.")
    else:
        lines.append("Fichiers à corriger avant exécution :")
        lines.append("")
        for path, message in errors:
            lines.append(f"- `{path}` — {message}")
    lines.append("")
    lines.append("Vérification automatique via `compile()` (SecureFlow).")
    return "\n".join(lines) + "\n"


def _agent_content(agents: list[dict[str, Any]], name: str) -> str:
    for agent in agents:
        if agent.get("name") == name:
            return agent.get("content") or ""
    return ""


def _pop_readme(project_files: dict[str, str]) -> str | None:
    for key in list(project_files.keys()):
        if key.lower().replace("\\", "/").endswith("readme.md"):
            return project_files.pop(key)
    return None


def build_mode_b_zip(
    result_data: dict[str, Any],
    *,
    project_label: str = "projet",
) -> bytes | None:
    """Assemble README + STRUCTURE + code DevAgent en archive ZIP."""
    agents = result_data.get("agents") or []
    architect = _agent_content(agents, "ArchitectAgent")
    design = _agent_content(agents, "DesignAgent")
    dev = _agent_content(agents, "DevAgent")
    security = _agent_content(agents, "SecurityAgent")
    qa = _agent_content(agents, "QAAgent")
    feasibility = _agent_content(agents, "FeasibilityAgent")

    project_files = parse_dev_agent_files(dev)
    if not project_files and not architect:
        return None

    dev_readme = _pop_readme(project_files)

    buffer = io.BytesIO()
    label = (project_label or "projet").strip() or "projet"
    tree = extract_project_tree(architect)

    readme_content = build_readme_content(
        label=label,
        tree=tree,
        architect=architect,
        feasibility=feasibility,
        dev_readme=dev_readme,
        dev_raw=dev,
        qa=qa,
        project_files=project_files,
    )

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README.md", readme_content)

        if tree:
            archive.writestr(
                "STRUCTURE.md",
                f"STRUCTURE DU PROJET — {label}\n\n{tree}\n",
            )

        if architect:
            archive.writestr("docs/ARCHITECTURE.md", architect.strip() + "\n")
        if feasibility:
            archive.writestr("docs/FEASIBILITY.md", feasibility.strip() + "\n")
        if design:
            archive.writestr("docs/DESIGN.md", design.strip() + "\n")
        if security:
            archive.writestr("docs/SECURITY_AUDIT.md", security.strip() + "\n")
        if qa:
            archive.writestr("docs/QA_REPORT.md", qa.strip() + "\n")

        for path, file_content in sorted(project_files.items()):
            archive.writestr(path, file_content)

        if any(p.lower().endswith(".py") for p in project_files):
            archive.writestr(
                "docs/SYNTAX_CHECK.md",
                build_syntax_report(project_files),
            )

        if not project_files:
            archive.writestr(
                "docs/DEV_OUTPUT.md",
                (dev or "Aucun fichier extrait du DevAgent.") + "\n",
            )

    return buffer.getvalue()


def project_file_count(result_data: dict[str, Any]) -> int:
    dev = _agent_content(result_data.get("agents") or [], "DevAgent")
    return len(parse_dev_agent_files(dev))

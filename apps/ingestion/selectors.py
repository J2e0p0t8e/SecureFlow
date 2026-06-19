"""Sélection intelligente des fichiers à ingérer pour un scan sécurité complet."""

from __future__ import annotations

from pathlib import PurePosixPath

BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".zip",
    ".exe",
    ".dll",
    ".so",
    ".woff",
    ".woff2",
    ".pyc",
    ".class",
    ".o",
    ".ico",
    ".mp4",
    ".mp3",
    ".wasm",
}

PRIORITY_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".vue",
    ".go",
    ".rb",
    ".java",
    ".kt",
    ".cs",
    ".php",
    ".sql",
    ".env",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".md",
    ".txt",
    ".sh",
    ".bash",
    ".html",
    ".htm",
    ".xml",
}

PRIORITY_NAMES = {
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "Pipfile",
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "composer.json",
    "Gemfile",
    "go.mod",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Makefile",
    "README.md",
    ".env",
    ".env.example",
    ".env.local",
    "settings.py",
    "config.py",
    "appsettings.json",
    "web.config",
}

SECURITY_PATH_HINTS = (
    "auth",
    "login",
    "password",
    "secret",
    "token",
    "payment",
    "checkout",
    "admin",
    "api",
    "route",
    "controller",
    "middleware",
    "upload",
    "sql",
    "db",
    "database",
    "migrate",
    "security",
    "crypto",
    "session",
    "oauth",
    "webhook",
)


def is_binary_path(path: str) -> bool:
    name = PurePosixPath(path.replace("\\", "/")).name
    if "." not in name:
        return False
    ext = "." + name.rsplit(".", 1)[-1].lower()
    return ext in BINARY_EXTENSIONS


def priority_score(path: str) -> int:
    normalized = path.replace("\\", "/")
    name = PurePosixPath(normalized).name
    lower = normalized.lower()
    ext = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""

    score = 0
    if name in PRIORITY_NAMES:
        score += 120
    if ext in PRIORITY_EXTENSIONS:
        score += 60
    if any(hint in lower for hint in SECURITY_PATH_HINTS):
        score += 40
    if "test" not in lower and "spec" not in lower:
        score += 15
    depth = len(PurePosixPath(normalized).parts)
    if depth <= 2:
        score += 25
    elif depth <= 4:
        score += 10
    return score


def select_paths(paths: list[str], max_files: int) -> tuple[list[str], bool]:
    """Retourne les chemins sélectionnés et si la liste a été tronquée."""
    unique = sorted(set(paths), key=lambda p: p.replace("\\", "/"))
    ordered = sorted(unique, key=priority_score, reverse=True)
    selected = ordered[:max_files]
    return selected, len(unique) > len(selected)


def build_file_manifest(all_paths: list[str], selected_paths: list[str]) -> str:
    """Inventaire textuel — tous les fichiers visibles, même non chargés."""
    selected = set(selected_paths)
    lines = [
        "INVENTAIRE DU DÉPÔT",
        f"Fichiers texte repérés : {len(all_paths)}",
        f"Fichiers chargés pour analyse : {len(selected_paths)}",
        "",
    ]
    if len(all_paths) > len(selected_paths):
        skipped = [p for p in sorted(all_paths) if p not in selected]
        lines.append("Fichiers non chargés (priorité moindre) :")
        for path in skipped[:120]:
            lines.append(f"  - {path}")
        if len(skipped) > 120:
            lines.append(f"  … et {len(skipped) - 120} autres")
        lines.append("")
    lines.append("Fichiers chargés :")
    for path in selected_paths:
        lines.append(f"  + {path}")
    return "\n".join(lines)

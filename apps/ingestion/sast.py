"""Analyse statique réelle (Bandit) sur le contenu ingéré.

Reconstruit les fichiers Python à partir du bundle texte, lance Bandit en
sous-processus et renvoie des findings normalisés. Tout échec (Bandit absent,
timeout, etc.) est silencieux : on retombe alors sur le pré-scan regex.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile

from apps.ingestion.selectors import is_binary_path
from apps.ingestion.static_analysis import FILE_HEADER_RE, StaticFinding

logger = logging.getLogger(__name__)

_BANDIT_TIMEOUT = 90
_MAX_FILES = 60


def _reconstruct_python_files(content: str) -> dict[str, str]:
    files: dict[str, str] = {}
    for block in FILE_HEADER_RE.finditer(content or ""):
        path = block.group("path").strip()
        if not path.endswith(".py") or is_binary_path(path):
            continue
        body = block.group("body")
        # Coupe le marqueur de troncature éventuel ajouté à l'ingestion
        body = body.split("\n[… fichier tronqué", 1)[0]
        files[path] = body
        if len(files) >= _MAX_FILES:
            break
    return files


def _safe_rel_path(path: str) -> str | None:
    normalized = path.replace("\\", "/").lstrip("/")
    if ".." in normalized.split("/"):
        return None
    return normalized


def bandit_available() -> bool:
    try:
        import bandit  # noqa: F401

        return True
    except Exception:
        return False


def run_bandit_scan(content: str, *, max_findings: int = 40) -> list[StaticFinding]:
    """Lance Bandit sur les fichiers Python du bundle. Renvoie [] si indisponible."""
    if not bandit_available():
        return []

    py_files = _reconstruct_python_files(content)
    if not py_files:
        return []

    findings: list[StaticFinding] = []
    with tempfile.TemporaryDirectory(prefix="sf_sast_") as tmp:
        written = 0
        for path, body in py_files.items():
            rel = _safe_rel_path(path)
            if not rel:
                continue
            dest = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(dest) or tmp, exist_ok=True)
            try:
                with open(dest, "w", encoding="utf-8") as handle:
                    handle.write(body)
                written += 1
            except OSError:
                continue

        if not written:
            return []

        try:
            proc = subprocess.run(
                [sys.executable, "-m", "bandit", "-r", tmp, "-f", "json", "-q"],
                capture_output=True,
                text=True,
                timeout=_BANDIT_TIMEOUT,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            logger.warning("Bandit indisponible / timeout : %s", exc)
            return []

        raw = proc.stdout.strip()
        if not raw:
            return []
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Bandit : sortie JSON illisible")
            return []

        for item in data.get("results", []):
            filename = (item.get("filename") or "").replace("\\", "/")
            rel = filename[len(tmp.replace("\\", "/")):].lstrip("/") if filename else "?"
            severity = (item.get("issue_severity") or "LOW").upper()
            test_id = item.get("test_id") or ""
            text = (item.get("issue_text") or "").strip()
            if len(text) > 140:
                text = text[:137] + "…"
            findings.append(
                StaticFinding(
                    path=rel or "?",
                    line=int(item.get("line_number") or 0),
                    category=f"Bandit {severity} [{test_id}]",
                    snippet=text,
                )
            )
            if len(findings) >= max_findings:
                break

    return findings

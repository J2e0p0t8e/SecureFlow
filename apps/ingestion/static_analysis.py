"""Analyse statique légère (regex) avant passage aux agents LLM."""

from __future__ import annotations

import re
from dataclasses import dataclass

FILE_HEADER_RE = re.compile(
    r"^={10,}\s*\nFichier\s*:\s*(?P<path>.+?)\s*\n={10,}\s*\n(?P<body>.*?)(?=\n={10,}\s*\nFichier\s*:|\Z)",
    re.MULTILINE | re.DOTALL,
)

@dataclass
class StaticFinding:
    path: str
    line: int
    category: str
    snippet: str


PATTERN_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("Secret / credential hardcodé", re.compile(r"(?i)(api[_-]?key|secret|password|token|private[_-]?key)\s*=\s*['\"][^'\"]{4,}['\"]")),
    ("Clé Stripe / AWS / GitHub", re.compile(r"(?i)(sk_live_|sk_test_|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{20,}|gsk_[a-zA-Z0-9]+)")),
    ("SQL concaténé / f-string dangereux", re.compile(r"(?i)(execute\s*\(|cursor\.execute|\.raw\s*\(|f['\"].*(select|insert|update|delete).*\{)")),
    ("eval / exec", re.compile(r"\b(eval|exec)\s*\(")),
    ("pickle / désérialisation", re.compile(r"(?i)\b(pickle\.loads|yaml\.load\s*\(|marshal\.loads)\b")),
    ("subprocess shell=True", re.compile(r"(?i)subprocess\.(run|Popen|call)\([^)]*shell\s*=\s*True")),
    ("CORS permissif", re.compile(r"(?i)(Access-Control-Allow-Origin\s*[:=]\s*['\"]?\*|CORS\(.*origins\s*=\s*['\"]?\*)")),
    ("Debug mode activé", re.compile(r"(?i)(DEBUG\s*=\s*True|app\.run\s*\([^)]*debug\s*=\s*True)")),
    ("XSS reflet (innerHTML / dangerouslySetInnerHTML)", re.compile(r"(?i)(innerHTML\s*=|dangerouslySetInnerHTML)")),
]


def _line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def scan_file(path: str, body: str, *, max_findings: int = 3) -> list[StaticFinding]:
    findings: list[StaticFinding] = []
    for category, pattern in PATTERN_RULES:
        for match in pattern.finditer(body):
            line = _line_number(body, match.start())
            snippet = match.group(0).strip()
            if len(snippet) > 120:
                snippet = snippet[:117] + "…"
            findings.append(StaticFinding(path=path, line=line, category=category, snippet=snippet))
            if len(findings) >= max_findings:
                return findings
    return findings


def scan_project_content(content: str, *, max_findings: int = 40) -> list[StaticFinding]:
    findings: list[StaticFinding] = []
    for block in FILE_HEADER_RE.finditer(content or ""):
        path = block.group("path").strip()
        body = block.group("body")
        for item in scan_file(path, body, max_findings=5):
            findings.append(item)
            if len(findings) >= max_findings:
                return findings
    return findings


def format_static_scan_report(findings: list[StaticFinding], *, locale: str = "fr") -> str:
    if not findings:
        if locale == "en":
            return "STATIC PRE-SCAN: no obvious pattern matched (LLM review still required)."
        return "PRÉ-SCAN STATIQUE : aucun pattern évident détecté (revue LLM requise)."

    title = "STATIC PRE-SCAN (regex)" if locale == "en" else "PRÉ-SCAN STATIQUE (regex)"
    lines = [title, f"Signaux automatiques : {len(findings)}", ""]
    for item in findings:
        lines.append(f"• [{item.category}] {item.path}:{item.line} — {item.snippet}")
    return "\n".join(lines)

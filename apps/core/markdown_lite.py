"""Conversion markdown légère → HTML sûr (titres, gras, italique, puces)."""

from __future__ import annotations

import html
import re

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+?)\*(?!\*)")
_HEADER_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_BARE_HEADER_RE = re.compile(r"^#{1,6}\s*$")
_BULLET_RE = re.compile(r"^[\*\-\+]\s+")


def _apply_inline_styles(text: str, bold_tag: str = "strong") -> str:
    text = _BOLD_RE.sub(rf"<{bold_tag}>\1</{bold_tag}>", text)
    text = _ITALIC_RE.sub(r"<em>\1</em>", text)
    return text


def _inline_html(text: str) -> str:
    return _apply_inline_styles(text, bold_tag="strong")


def _inline_reportlab(text: str) -> str:
    # ReportLab interprète le texte comme du mini-HTML : on échappe d'abord
    # les caractères spéciaux (<, >, &) du contenu brut, puis on ajoute le
    # balisage gras/italique nous-mêmes. Sinon un fragment de code comme
    # "<int:order_id>" est vu comme une balise ouverte non fermée → crash.
    text = html.escape(text, quote=False)
    text = _BOLD_RE.sub(r"<b>\1</b>", text)
    return _ITALIC_RE.sub(r"<i>\1</i>", text)


def is_skippable_markdown_line(line: str) -> bool:
    return bool(_BARE_HEADER_RE.match(line.strip()))


def is_markdown_heading(line: str) -> bool:
    return bool(_HEADER_RE.match(line.strip()))


def heading_text(line: str) -> str:
    match = _HEADER_RE.match(line.strip())
    return match.group(2).strip() if match else line


def markdown_to_html(text: str) -> str:
    """Échappe le HTML puis convertit le markdown léger pour le frontend."""
    if not text:
        return ""

    lines: list[str] = []
    for line in html.escape(text).split("\n"):
        stripped = line.strip()
        if _BARE_HEADER_RE.match(stripped):
            continue
        header = _HEADER_RE.match(stripped)
        if header:
            level = min(len(header.group(1)), 4)
            title = _inline_html(header.group(2).strip())
            lines.append(f'<div class="md-heading md-h{level}">{title}</div>')
            continue
        if _BULLET_RE.match(stripped):
            body = _BULLET_RE.sub("", stripped, count=1)
            lines.append(f'<div class="md-bullet">• {_inline_html(body)}</div>')
            continue
        lines.append(_inline_html(line) if line else "")

    return "\n".join(lines)


def markdown_to_reportlab(line: str) -> str:
    """Convertit une ligne (titres, gras, italique) pour ReportLab."""
    stripped = line.strip()
    if _BARE_HEADER_RE.match(stripped):
        return ""
    header = _HEADER_RE.match(stripped)
    if header:
        return f"<b>{_inline_reportlab(header.group(2).strip())}</b>"
    if _BULLET_RE.match(stripped):
        body = _BULLET_RE.sub("", stripped, count=1)
        return f"• {_inline_reportlab(body)}"
    return _inline_reportlab(line)

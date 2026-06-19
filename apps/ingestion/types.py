"""Types partagés pour l'ingestion GitHub / ZIP."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IngestionResult:
    """Résultat d'ingestion avec métadonnées de couverture."""

    content: str
    files_analyzed: int = 0
    files_total: int = 0
    truncated: bool = False
    source_label: str = ""
    file_manifest: str = ""

    def to_dict(self, locale: str = "fr") -> dict:
        return {
            "files_analyzed": self.files_analyzed,
            "files_total": self.files_total,
            "truncated": self.truncated,
            "source_label": self.source_label,
            "file_manifest": self.file_manifest,
        }

"""Commande Django pour tester le Mode A depuis le terminal."""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.core.config import validate_runtime_config
from apps.orchestrator.services import run_security_audit


def _console_safe(text: str) -> str:
    """Evite les crashs d'encodage Windows (emojis, accents)."""
    return text.encode("cp1252", errors="replace").decode("cp1252")


class Command(BaseCommand):
    help = "Lance un audit sécurité Mode A (5 agents) sur un fichier ou un texte."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Chemin vers un fichier contenant le code du projet à auditer.",
        )
        parser.add_argument(
            "--text",
            type=str,
            help="Contenu texte direct (alternative à --file).",
        )
        parser.add_argument(
            "--label",
            type=str,
            default="Projet",
            help="Libellé affiché dans la Band Room.",
        )

    def handle(self, *args, **options):
        from apps.orchestrator.mode_a import MODE_A_BAND_AGENTS

        config_errors = validate_runtime_config(required_band_agents=MODE_A_BAND_AGENTS)
        if config_errors:
            raise CommandError(
                "Configuration incomplète :\n- " + "\n- ".join(config_errors)
            )

        content = self._load_content(options)
        self.stdout.write("Lancement Mode A (5 agents)... Patience.\n")

        result = run_security_audit(content, project_label=options["label"])

        self.stdout.write(self.style.SUCCESS(f"Room Band : {result.room_id}"))
        self.stdout.write(f"Décision   : {result.decision or 'non détectée'}")
        self.stdout.write(f"Audit ID   : {result.audit_id or 'non détecté'}\n")

        for step in result.results:
            preview = _console_safe(step.content[:100].replace("\n", " "))
            self.stdout.write(f"  [OK] {step.agent_name} - {preview}...")

        self.stdout.write("\n--- Rapport final ---\n")
        self.stdout.write(_console_safe(result.final_report))

    def _load_content(self, options) -> str:
        file_path = options.get("file")
        text = options.get("text")

        if file_path and text:
            raise CommandError("Utilise --file OU --text, pas les deux.")

        if file_path:
            path = Path(file_path)
            if not path.is_file():
                raise CommandError(f"Fichier introuvable : {path}")
            return path.read_text(encoding="utf-8")

        if text:
            return text

        raise CommandError("Indique --file <chemin> ou --text \"contenu du projet\".")

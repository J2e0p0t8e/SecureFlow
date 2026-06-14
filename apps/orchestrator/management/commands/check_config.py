"""Vérifie les 13 agents Band + connexion Groq."""

from django.core.management.base import BaseCommand

from apps.agents.band_registry import ALL_BAND_AGENT_NAMES, get_band_client_for
from apps.core.config import validate_runtime_config


class Command(BaseCommand):
    help = "Vérifie le .env (13 agents Band + LLM) et teste GET /agent/me pour chacun."

    def add_arguments(self, parser):
        parser.add_argument(
            "--mode-a-only",
            action="store_true",
            help="Ne vérifie que les 5 agents du Mode A.",
        )

    def handle(self, *args, **options):
        if options["mode_a_only"]:
            from apps.orchestrator.mode_a import MODE_A_BAND_AGENTS

            agents = MODE_A_BAND_AGENTS
            label = "Mode A (5 agents)"
        else:
            agents = ALL_BAND_AGENT_NAMES
            label = "13 agents"

        errors = validate_runtime_config(required_band_agents=agents)
        if errors:
            self.stdout.write(self.style.ERROR(f"Configuration incomplete ({label}) :"))
            for err in errors:
                self.stdout.write(f"  - {err}")
            self.stdout.write("\nVoir docs/SETUP_BAND_13_AGENTS.md")
            return

        self.stdout.write(self.style.SUCCESS(f"Variables .env : OK ({label})"))

        ok = 0
        for agent_name in agents:
            try:
                client = get_band_client_for(agent_name)
                profile = client.get_me()
                band_agent = profile.get("agent") or profile
                display = band_agent.get("name") or agent_name
                self.stdout.write(self.style.SUCCESS(f"  [OK] {agent_name} -> {display}"))
                ok += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"  [FAIL] {agent_name} -> {exc}"))

        self.stdout.write(f"\n{ok}/{len(agents)} agents Band connectes.")

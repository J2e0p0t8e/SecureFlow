"""SecurityAgent — Mode B, étape 5."""

from apps.agents.base import AgentResult, BaseAgent
from apps.agents.prompts import SECURITY_PROMPT


class SecurityAgent(BaseAgent):
    name = "SecurityAgent"
    role_description = SECURITY_PROMPT.strip()

    def run(
        self,
        room_id: str,
        extra_input: str | None = None,
        next_agent: BaseAgent | None = None,
    ) -> AgentResult:
        return super().run(room_id, extra_input=extra_input, next_agent=next_agent)

# Made with Bob

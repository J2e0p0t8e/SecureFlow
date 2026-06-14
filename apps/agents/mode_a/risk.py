"""RiskAgent — Mode A, étape 4."""

from apps.agents.base import AgentResult, BaseAgent
from apps.agents.prompts import RISK_PROMPT


class RiskAgent(BaseAgent):
    name = "RiskAgent"
    role_description = RISK_PROMPT.strip()

    def run(
        self,
        room_id: str,
        extra_input: str | None = None,
        next_agent: BaseAgent | None = None,
    ) -> AgentResult:
        return super().run(room_id, extra_input=extra_input, next_agent=next_agent)

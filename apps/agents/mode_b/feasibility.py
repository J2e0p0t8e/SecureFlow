"""FeasibilityAgent — Mode B, étape 1."""

from apps.agents.base import AgentResult, BaseAgent
from apps.agents.prompts import FEASIBILITY_PROMPT


class FeasibilityAgent(BaseAgent):
    name = "FeasibilityAgent"
    role_description = FEASIBILITY_PROMPT.strip()

    def run(
        self,
        room_id: str,
        extra_input: str | None = None,
        next_agent: BaseAgent | None = None,
        prior_agent: BaseAgent | None = None,
        **kwargs,
    ) -> AgentResult:
        return super().run(
            room_id,
            extra_input=extra_input,
            next_agent=next_agent,
            prior_agent=prior_agent,
            **kwargs,
        )
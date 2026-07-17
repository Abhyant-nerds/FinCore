"""Decision explanation skill."""

from ..models import Decision


class DecisionExplanationSkill:
    def explain(self, decision: Decision) -> str:
        reasons = ", ".join(decision.reason_codes) if decision.reason_codes else "no blocking reason codes"
        return (
            f"Official disposition is {decision.disposition.value}, calculated by policy version "
            f"{decision.calculated_by_policy_version}. Reason codes: {reasons}."
        )


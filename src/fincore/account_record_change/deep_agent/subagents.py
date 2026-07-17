"""Specialist subagent wrappers."""

from ..skills import DecisionExplanationSkill, EvidenceAnalysisSkill, RequestUnderstandingSkill


class AccountRecordChangeSubagents:
    def __init__(self) -> None:
        self.request_understanding = RequestUnderstandingSkill()
        self.evidence_analysis = EvidenceAnalysisSkill()
        self.decision_explanation = DecisionExplanationSkill()


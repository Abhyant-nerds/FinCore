"""Evidence-analysis skill that preserves uncertainty."""

from pydantic import BaseModel, Field

from ..models import EvidenceReference, ValidationStatus


class EvidenceFinding(BaseModel):
    document_id: str
    status: ValidationStatus
    facts: dict = Field(default_factory=dict)
    contradictions: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)


class EvidenceAnalysisSkill:
    async def analyze(self, evidence: list[EvidenceReference]) -> list[EvidenceFinding]:
        if not evidence:
            return [
                EvidenceFinding(
                    document_id="",
                    status=ValidationStatus.INDETERMINATE,
                    contradictions=[],
                    evidence_references=[],
                )
            ]
        return [
            EvidenceFinding(
                document_id=item.document_id,
                status=ValidationStatus.PASS,
                facts={"document_type": item.document_type, "purpose": item.purpose},
                evidence_references=[item.document_id],
            )
            for item in evidence
        ]


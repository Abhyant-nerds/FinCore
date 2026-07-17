"""Human review task creation."""

from ..models import Decision, ReviewTask, ReviewTaskReference
from ..repositories.protocols import ReviewRepository


class ReviewService:
    def __init__(self, repository: ReviewRepository | None = None) -> None:
        self._repository = repository

    async def create_task(self, request_id: str, decision: Decision) -> ReviewTask:
        first_result = decision.validation_results[0] if decision.validation_results else None
        first_field = first_result.field_paths[0] if first_result and first_result.field_paths else None
        task = ReviewTask(
            request_id=request_id,
            field_path=first_field,
            failed_or_uncertain_rule=first_result.rule_id if first_result else None,
            evidence_references=first_result.evidence_references if first_result else [],
            agent_summary="Human review is required by the official policy decision.",
        )
        if self._repository:
            task = await self._repository.create_review_task(task)
        decision.review_tasks.append(ReviewTaskReference(review_task_id=task.review_task_id))
        return task


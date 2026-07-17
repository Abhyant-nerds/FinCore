"""Deep Agent-first coordinator for Account Record Change."""

from ..config import AccountProfileLoader, DEFAULT_POLICY_VERSION, RuleLoader
from ..graph import CheckpointSaver, HumanReviewInterrupt, InMemoryCheckpointSaver, MissingInformationInterrupt
from ..models import (
    AccountRecordChangeOutput,
    ChangeRequest,
    ChangeWorkflowState,
    Disposition,
    Provenance,
    RequestStatus,
)
from ..policy import PolicyEngine, RuleResolver
from ..repositories.protocols import IdempotencyRepository, RecordRepository
from ..services import CommandService, EventService, ProposedRecordService, ReviewService, ValidationService
from ..skills import DecisionExplanationSkill, EvidenceAnalysisSkill, RequestUnderstandingSkill
from ..validators import ValidationContext, default_validator_registry


class AccountRecordChangeDeepAgent:
    """Coordinates the domain flow while deterministic services retain authority."""

    def __init__(
        self,
        *,
        record_repository: RecordRepository,
        idempotency_repository: IdempotencyRepository | None = None,
        checkpoint_saver: CheckpointSaver | None = None,
        profile_loader: AccountProfileLoader | None = None,
        rule_loader: RuleLoader | None = None,
        policy_engine: PolicyEngine | None = None,
        validation_service: ValidationService | None = None,
        proposed_record_service: ProposedRecordService | None = None,
        review_service: ReviewService | None = None,
        command_service: CommandService | None = None,
        event_service: EventService | None = None,
    ) -> None:
        self.record_repository = record_repository
        self.idempotency_repository = idempotency_repository
        self.checkpoint_saver = checkpoint_saver or InMemoryCheckpointSaver()
        self.profile_loader = profile_loader or AccountProfileLoader()
        self.rule_loader = rule_loader or RuleLoader()
        self.policy_engine = policy_engine or PolicyEngine(DEFAULT_POLICY_VERSION)
        self.validation_service = validation_service or ValidationService(default_validator_registry())
        self.proposed_record_service = proposed_record_service or ProposedRecordService()
        self.review_service = review_service or ReviewService()
        self.command_service = command_service or CommandService()
        self.event_service = event_service or EventService()
        self.request_understanding = RequestUnderstandingSkill()
        self.evidence_analysis = EvidenceAnalysisSkill()
        self.decision_explanation = DecisionExplanationSkill()

    async def run(self, request: ChangeRequest, *, execute: bool = False) -> "DeepAgentRunResult":
        from .runtime import DeepAgentRunResult

        state = ChangeWorkflowState(request=request, status=RequestStatus.RECEIVED)
        thread_id = request.request_id
        await self.checkpoint_saver.save(thread_id, state)

        summary = self.request_understanding.summarize(request)
        if summary.missing_request_data:
            state.status = RequestStatus.INFORMATION_REQUIRED
            state.pending_information = []
            await self.checkpoint_saver.save(thread_id, state)
            return DeepAgentRunResult(
                state=state,
                interrupt=MissingInformationInterrupt(
                    request_id=request.request_id,
                    payload={"missing_request_data": summary.missing_request_data},
                ),
            )

        if self.idempotency_repository:
            source = request.source_channel or request.requested_by.channel or "UNKNOWN"
            key = f"{request.tenant_id}:{source}:{request.idempotency_key}"
            await self.idempotency_repository.register(key, request.request_id)

        state.status = RequestStatus.CONTEXT_LOADING
        if request.record_id:
            state.existing_record = await self.record_repository.load_snapshot(request.tenant_id, request.record_id)
        state.proposed_record = self.proposed_record_service.build(request, state.existing_record)
        profile = self.profile_loader.get(request.account_type)
        state.status = RequestStatus.CONTEXT_LOADED
        await self.checkpoint_saver.save(thread_id, state)

        rules = RuleResolver(self.rule_loader.list_rules()).resolve(request)
        state.applicable_rules = rules
        state.validation_plan = [rule.validator_name for rule in rules]
        state.status = RequestStatus.POLICY_RESOLVED

        await self.evidence_analysis.analyze(request.evidence)
        context = ValidationContext(
            request=request,
            existing_record=state.existing_record,
            proposed_record=state.proposed_record,
            profile=profile,
        )
        state.status = RequestStatus.VALIDATION_IN_PROGRESS
        state.validation_results = await self.validation_service.run(rules, context)
        state.decision = self.policy_engine.decide(request, rules, state.validation_results)
        explanation = self.decision_explanation.explain(state.decision)

        provenance = Provenance(
            rule_ids=[rule.rule_id for rule in rules],
            evidence_references=[item.document_id for item in request.evidence],
            policy_version=state.decision.calculated_by_policy_version,
        )
        await self.event_service.audit(request.request_id, "ValidationCompleted", {"disposition": state.decision.disposition.value}, provenance)

        if state.decision.disposition == Disposition.REQUEST_INFORMATION:
            state.status = RequestStatus.INFORMATION_REQUIRED
            state.pending_information = state.decision.missing_information
            await self.checkpoint_saver.save(thread_id, state)
            return DeepAgentRunResult(
                state=state,
                interrupt=MissingInformationInterrupt(
                    request_id=request.request_id,
                    payload={"missing_information": [item.model_dump(mode="json") for item in state.pending_information]},
                ),
                explanation=explanation,
            )

        if state.decision.disposition == Disposition.HUMAN_REVIEW:
            task = await self.review_service.create_task(request.request_id, state.decision)
            state.review_task_id = task.review_task_id
            state.status = RequestStatus.REVIEW_REQUIRED
            await self.checkpoint_saver.save(thread_id, state)
            return DeepAgentRunResult(
                state=state,
                interrupt=HumanReviewInterrupt(
                    request_id=request.request_id,
                    payload={"review_task": task.model_dump(mode="json")},
                ),
                explanation=explanation,
            )

        if state.decision.disposition == Disposition.REJECT:
            state.status = RequestStatus.REJECTED
            output = self._output(state)
            await self.checkpoint_saver.save(thread_id, state)
            return DeepAgentRunResult(state=state, output=output, explanation=explanation)

        state.status = RequestStatus.EXECUTION_PENDING
        state.command = self.command_service.prepare(request, state.decision, profile, state.existing_record)
        if execute:
            state.status = RequestStatus.EXECUTING
            state.execution_result = await self.command_service.execute_approved_command(
                state.command,
                state.existing_record,
                authorized=True,
            )
            state.status = RequestStatus.COMPLETED
            await self.event_service.publish(request.request_id, "ChangeExecutionCompleted", state.execution_result.model_dump(mode="json"))
        else:
            state.status = RequestStatus.VALIDATED

        output = self._output(state)
        await self.checkpoint_saver.save(thread_id, state)
        return DeepAgentRunResult(state=state, output=output, explanation=explanation)

    async def resume_after_review(self, request_id: str, approval_reference: str, *, execute: bool = False) -> "DeepAgentRunResult":
        from .runtime import DeepAgentRunResult

        state = await self.checkpoint_saver.load(request_id)
        if not state or not state.decision:
            raise ValueError("No paused review state found")
        profile = self.profile_loader.get(state.request.account_type)
        state.approval_reference = approval_reference
        state.status = RequestStatus.EXECUTION_PENDING
        state.command = self.command_service.prepare(
            state.request,
            state.decision,
            profile,
            state.existing_record,
            approval_reference=approval_reference,
        )
        if execute:
            state.status = RequestStatus.EXECUTING
            state.execution_result = await self.command_service.execute_approved_command(
                state.command,
                state.existing_record,
                authorized=True,
            )
            state.status = RequestStatus.COMPLETED
        else:
            state.status = RequestStatus.VALIDATED
        await self.checkpoint_saver.save(request_id, state)
        return DeepAgentRunResult(state=state, output=self._output(state))

    def _output(self, state: ChangeWorkflowState) -> AccountRecordChangeOutput:
        disposition = state.decision.disposition if state.decision else Disposition.REQUEST_INFORMATION
        return AccountRecordChangeOutput(
            request_id=state.request.request_id,
            status=state.status,
            disposition=disposition,
            policy_version=state.decision.calculated_by_policy_version if state.decision else None,
            field_results=[
                {
                    "field_path": field_decision.field_path,
                    "decision": field_decision.decision,
                    "validation_execution_ids": field_decision.validation_execution_ids,
                }
                for field_decision in (state.decision.field_decisions if state.decision else [])
            ],
            review_task={"review_task_id": state.review_task_id} if state.review_task_id else None,
            execution_result=state.execution_result.model_dump(mode="json") if state.execution_result else None,
        )


def create_account_record_change_agent(**kwargs) -> AccountRecordChangeDeepAgent:
    return AccountRecordChangeDeepAgent(**kwargs)


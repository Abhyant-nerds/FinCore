"""Runtime result types for the Deep Agent coordinator."""

from pydantic import BaseModel

from ..graph import WorkflowInterrupt
from ..models import AccountRecordChangeOutput, ChangeWorkflowState


class DeepAgentRunResult(BaseModel):
    state: ChangeWorkflowState
    output: AccountRecordChangeOutput | None = None
    interrupt: WorkflowInterrupt | None = None
    explanation: str | None = None


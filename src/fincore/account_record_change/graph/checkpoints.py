"""Small checkpoint abstraction matching LangGraph durability requirements."""

from typing import Protocol

from ..models import ChangeWorkflowState


class CheckpointSaver(Protocol):
    async def save(self, thread_id: str, state: ChangeWorkflowState) -> None: ...

    async def load(self, thread_id: str) -> ChangeWorkflowState | None: ...


class InMemoryCheckpointSaver:
    def __init__(self) -> None:
        self._states: dict[str, ChangeWorkflowState] = {}

    async def save(self, thread_id: str, state: ChangeWorkflowState) -> None:
        self._states[thread_id] = state.model_copy(deep=True)

    async def load(self, thread_id: str) -> ChangeWorkflowState | None:
        state = self._states.get(thread_id)
        return state.model_copy(deep=True) if state else None


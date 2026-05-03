from abc import ABC, abstractmethod
from typing import Any


class StateStorage(ABC):
    @abstractmethod
    async def save(
        self,
        workflow_name: str,
        step_index: int,
        context: Any,  # noqa: ANN401
    ) -> None:
        ...

    async def load(
        self,
        workflow_name: str,
    ) -> tuple[int, Any] | None:
        ...

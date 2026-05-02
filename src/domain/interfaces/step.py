from abc import ABC, abstractmethod
from typing import Generic, TypeVar

C = TypeVar('C')

class Step(ABC, Generic[C]):
    @abstractmethod
    async def execute(self, context: C) -> C:
        """Execute the step and return a new context (immutable)."""
        pass

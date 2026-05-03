import asyncio
from typing import Generic, TypeVar

from src.common.retry import RetryPolicy
from src.domain.interfaces.state_storage import StateStorage
from src.domain.interfaces.step import Step

C = TypeVar('C')


class WorkflowEngine(Generic[C]):
    def __init__(
        self,
        steps: list[Step[C]],
        step_timeout_seconds: float | None = None,
        retry_policy: RetryPolicy | None = None,
        state_storage: StateStorage | None = None,
    ) -> None:
        self._steps = steps
        self._step_timeout = step_timeout_seconds
        self._retry_policy = retry_policy or RetryPolicy()
        self._state_storage = state_storage

    async def _handle_error_if_retriable(
        self,
        attempt: int,
        exception: Exception,
    ) -> None:
        if not self._retry_policy.is_retriable(exception) or attempt == self._retry_policy.max_retries - 1:
            raise

        await self._retry_policy.wait(attempt=attempt)  # type: ignore

    async def _run_step_with_retry(
        self,
        step: Step[C],
        context: C,
    ) -> C:
        last_exception: Exception | None = None
        for attempt in range(self._retry_policy.max_retries):
            try:
                if self._step_timeout is not None:
                    return await asyncio.wait_for(
                        fut=step.execute(context=context),
                        timeout=self._step_timeout,
                    )
                return await step.execute(context=context)

            except asyncio.TimeoutError as e:
                last_exception = e
                await self._handle_error_if_retriable(attempt=attempt, exception=e)

            except Exception as e:
                last_exception = e
                await self._handle_error_if_retriable(
                    attempt=attempt,
                    exception=e,
                )

        raise last_exception  # type: ignore

    async def run(self, initial_context: C, workflow_name: str | None = None) -> C:
        if workflow_name and self._state_storage:
            state = await self._state_storage.load(workflow_name=workflow_name)

            if state:
                start_index, context = state
            else:
                context = initial_context
                start_index = 0

        else:
            context = initial_context
            start_index = 0

        for i, step in enumerate(self._steps[start_index:], start=start_index):
            try:
                context = await self._run_step_with_retry(
                    step=step,
                    context=context,
                )

                if self._state_storage and workflow_name:
                    await self._state_storage.save(
                        workflow_name=workflow_name,
                        step_index=i + 1,
                        context=context,
                    )

            except Exception as e:
                raise RuntimeError(f'Step {i} failed after retries: {e}') from e

        return context

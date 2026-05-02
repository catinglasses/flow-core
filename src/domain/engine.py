import asyncio
from typing import Generic, TypeVar

from src.common.retry import RetryPolicy
from src.domain.interfaces.step import Step

C = TypeVar('C')

class WorkflowEngine(Generic[C]):
    def __init__(
        self,
        steps: list[Step[C]],
        retry_policy: RetryPolicy | None = None,
        step_timeout_seconds: float | None = None,
    ) -> None:
        self._steps = steps
        self._retry_policy = retry_policy or RetryPolicy()
        self._step_timeout = step_timeout_seconds

    async def _run_step_with_retry(
        self,
        step: Step[C],
        context: C,
    ) -> C:
        last_exception = None
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
                if (
                    not self._retry_policy.is_retriable(e) or
                    attempt == self._retry_policy.max_retries - 1
                ):
                    raise

            except Exception as e:
                last_exception = e
                if (
                    not self._retry_policy.is_retriable(exception=e) or
                    attempt == self._retry_policy.max_retries - 1
                ):
                    raise

                await self._retry_policy.wait(attempt=attempt)

        raise last_exception  # type: ignore

    async def run(self, initial_context: C) -> C:
        context = initial_context

        for i, step in enumerate(self._steps):
            try:
                context = await self._run_step_with_retry(
                    step=step,
                    context=context,
                )
            except Exception as e:
                raise RuntimeError(f'Step {i} failed after retries: {e}') from e

        return context

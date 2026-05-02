from asyncio import TimeoutError, sleep
from typing import Type


class RetryPolicy:
    def __init__(
        self,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        retryable_exceptions: tuple[Type[Exception], ...] | None = None,
    ) -> None:
        self.max_retries = max_retries
        self.delay = delay
        self.backoff = backoff
        self.retryable_exceptions = retryable_exceptions or (
            Exception,
            TimeoutError,
        )

    def is_retriable(self, exception: Exception) -> bool:
        return isinstance(exception, self.retryable_exceptions)

    async def wait(self, attempt: int) -> None:
        wait_time = self.delay * (self.backoff ** attempt)
        await sleep(wait_time)

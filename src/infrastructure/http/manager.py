from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiohttp


class HTTPClientManager:
    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        if self._session is None:
            self._session = aiohttp.ClientSession()

    async def stop(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    def get_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError('HTTPClientManager not started')
        return self._session

    @asynccontextmanager
    async def managed_session(self) -> AsyncGenerator[aiohttp.ClientSession]:
        await self.start()

        try:
            yield self.get_session()
        finally:
            await self.stop()

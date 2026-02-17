from json import dumps as json_dumps
from types import TracebackType
from typing import Type

from aiohttp import ClientSession


class BaseHTTPClient:
    def __init__(self) -> None:
        self._session: ClientSession | None = None
        self._json_serialize = json_dumps

    @property
    def session(self) -> ClientSession:
        if self._session is None:
            raise RuntimeError('session not started yet, use `async with` first.')
        return self._session

    async def __aenter__(self) -> 'BaseHTTPClient':
        self._session = ClientSession(json_serialize=self._json_serialize)
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None

import asyncio

import aiohttp
from pydantic import BaseModel

from examples.ip_api_client import IpApiClient
from src.domain.engine import WorkflowEngine
from src.domain.interfaces.step import Step


class IpContext(BaseModel):
    ip: str
    info: dict = {}  # type: ignore


class EnrichIpStep(Step[IpContext]):
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._client = IpApiClient()  # this is stateless!

    async def execute(self, context: IpContext) -> IpContext:
        info = await self._client.get_ip_info(ip=context.ip, session=self._session)
        return IpContext(ip=context.ip, info=info)


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        step = EnrichIpStep(session=session)
        engine = WorkflowEngine([step])
        result = await engine.run(IpContext(ip='8.8.8.8'))
        print(result)


if __name__ == '__main__':
    asyncio.run(main())

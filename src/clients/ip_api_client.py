from enum import Enum
from typing import Any

from src.clients.base_http_client import BaseHTTPClient
from src.common.constants import IP_API_HOST


class IpApiLanguage(Enum):
    ENGLISH = 'en'
    RUSSIAN = 'ru'
    GERMAN = 'de'
    SPANISH = 'spanish'
    PORTUGUESE = 'pt-BR'
    FRENCH = 'fr'
    JAPANESE = 'ja'
    CHINESE = 'zh-CN'

class IpApiClient(BaseHTTPClient):
    BASE_URL = f'http://{IP_API_HOST}/json'

    async def get_ip_info(
        self,
        ip: str,
        language: IpApiLanguage = IpApiLanguage.ENGLISH,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        async with self.session.get(
            url=f'{self.BASE_URL}/{ip}',
            params={
                'lang': language.value,
                **({'fields': ','.join(fields)} if fields else {}),
            },
        ) as response:
            response.raise_for_status()
            return await response.json()


if __name__ == '__main__':
    client = IpApiClient()
    import asyncio

    async def test() -> None:
        async with client:
            result = await client.get_ip_info('8.8.8.8')

        print(result)

    asyncio.run(test())

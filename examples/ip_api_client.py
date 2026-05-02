from enum import Enum
from typing import Any

import aiohttp

from src.infrastructure.http.base_client import BaseHTTPClient

IP_API_HOST = 'ip-api.com'


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
    def __init__(
        self,
    ) -> None:
        super().__init__(base_url=f'http://{IP_API_HOST}/json')

    async def get_ip_info(
        self,
        ip: str,
        session: aiohttp.ClientSession,
        language: IpApiLanguage = IpApiLanguage.ENGLISH,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        return await self.get(
            session=session,
            path=ip,
            params={
                'lang': language.value,
                **({'fields': ','.join(fields)} if fields else {}),
            },
        )

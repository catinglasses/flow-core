from enum import Enum

from src.clients.base_http_client import BaseHTTPClient


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
    BASE_URL = 'http://ip-api.com/json'

    async def get_ip_info(
        self,
        ip: str,
        language: IpApiLanguage = IpApiLanguage.ENGLISH,
        fields: list[str] | None = None,
    ):
        async with self.session.get(
            url=f'{self.BASE_URL}/{ip}',
            params={
                'lang': language.value,
                **({'fields': ','.join(fields)} if fields else {}),
            },
        ) as response:
            response.raise_for_status()
            return await response.json()

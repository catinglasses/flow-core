from __future__ import annotations

import asyncio
import json
from typing import IO, Any, AsyncIterable, Callable, Mapping

import aiohttp

JSONSerializer = Callable[[Any], str]
JSONDeserializer = Callable[[str], Any]

JSONDataType = str | int | float | bool | list['JSONDataType'] | dict[str, 'JSONDataType'] | None
RequestDataType = Mapping[str, Any] | aiohttp.FormData | bytes | str | IO[Any] | AsyncIterable[bytes] | None
Headers = dict[str, str]
Params = dict[str, Any]

class BaseHTTPClient:
    """
    Base class for stateless HTTP clients.

    All HTTP methods require an active aiohttp.ClientSession to be passed as an argument.
    This class handles authentication header construction, response deserialization,
    and automatic retries with exponential backoff.

    Subclasses should implement domain-specific methods that call the public HTTP methods
    (get, post, etc.) provided here.

    Example:
        class MyAPIClient(BaseHTTPClient):
            async def get_data(self, session: aiohttp.ClientSession, params: str) -> dict:
                return await self.get(session=session, path='/endpoint', params=params)
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 10,
        default_headers: Headers | None = None,
        api_token: str | None = None,
        token_header: str = 'Authorization',
        token_type: str = 'Bearer',
        json_serialize: JSONSerializer = json.dumps,
        json_deserialize: JSONDeserializer = json.loads,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
    ) -> None:
        """
        Initialize the base HTTP client.

        Args:
            base_url: The base URL for all requests (e.g., "https://api.example.com/v1").
            timeout: Default timeout in seconds for requests (used when creating the session).
            default_headers: Headers to include in every request.
            api_token: Optional token for authentication.
            token_header: Header name for the token (default: "Authorization").
            token_type: Token type prefix (e.g., "Bearer", "Token"). If empty, the token is sent as is.
            json_serialize: Function to serialize JSON data (default: json.dumps).
            json_deserialize: Function to deserialize JSON responses (default: json.loads).
            max_retries: Maximum number of retry attempts on transient errors.
            retry_delay: Initial delay in seconds before the first retry.
            retry_backoff: Multiplier for the delay after each retry.
        """

        self._base_url = base_url.rstrip('/')
        self._timeout = timeout
        self._default_headers = default_headers or {}
        self._api_token = api_token
        self._token_header = token_header
        self._token_type = token_type
        self._json_serialize = json_serialize
        self._json_deserialize = json_deserialize
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._retry_backoff = retry_backoff

    def _get_auth_headers(self) -> Headers:
        if not self._api_token:
            return {}

        if self._token_type:
            return {self._token_header: f'{self._token_type} {self._api_token}'}

        return {self._token_header: self._api_token}

    async def _request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        path: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> aiohttp.ClientResponse:
        """
        Low-level request without retries.

        Args:
            session: Active aiohttp client session.
            method: HTTP method (GET, POST, etc.).
            path: URL path to append to base_url.
            **kwargs: Additional arguments passed to session.request (e.g., params, data, json, headers).

        Returns:
            aiohttp.ClientResponse: The raw response object.
        """

        url = f'{self._base_url}/{path.lstrip("/")}'
        headers: dict[str, Any] = {
            **self._default_headers,
            **self._get_auth_headers(),
            **kwargs.pop('headers', {}),
        }

        return await session.request(
            method=method,
            url=url,
            headers=headers,
            **kwargs,
        )

    async def _request_with_retry(
        self,
        session: aiohttp.ClientSession,
        method: str,
        path: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> aiohttp.ClientResponse:
        """
        Execute a request with automatic retries on certain exceptions.

        Retries occur on aiohttp.ClientError and asyncio.TimeoutError.
        The delay increases exponentially after each failed attempt.

        Args:
            session: Active aiohttp client session.
            method: HTTP method.
            path: URL path.
            **kwargs: Additional arguments for the request.

        Returns:
            aiohttp.ClientResponse: The response after a successful attempt.

        Raises:
            The last exception encountered if all retries fail.
        """

        last_exception = None
        delay = self._retry_delay

        for attempt in range(self._max_retries):
            try:
                return await self._request(
                    session=session,
                    method=method,
                    path=path,
                    **kwargs,
                )
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                if attempt == self._max_retries - 1:
                    raise
                await asyncio.sleep(delay=delay)
                delay *= self._retry_backoff
            except Exception:
                raise

        raise last_exception or RuntimeError('Unexpected retry exit')

    async def _handle_response(
        self,
        response: aiohttp.ClientResponse,
    ) -> Any:  # noqa: ANN401
        """
        Deserialize the response based on its content type.

        - For JSON responses (Content-Type: application/json), uses the configured deserializer.
        - For plain text responses (text/*), returns the text.
        - For everything else, returns raw bytes.

        Args:
            response: The HTTP response object.

        Returns:
            Parsed response data (dict, list, str, bytes, etc.).
        """

        content_type = response.headers.get('Content-Type', '')

        if 'application/json' in content_type:
            text = await response.text()
            return self._json_deserialize(text)
        elif 'text/' in content_type:
            return await response.text()
        else:
            return await response.read()

    async def get(
        self,
        session: aiohttp.ClientSession,
        path: str,
        params: Params | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> Any:  # noqa: ANN401
        """
        Perform an HTTP GET request with retries.

        Args:
            session: Active aiohttp client session.
            path: URL path (will be appended to base_url).
            params: Optional query parameters.
            **kwargs: Additional arguments for the request (e.g., headers).

        Returns:
            Deserialized response data (JSON, text, or bytes).

        Raises:
            aiohttp.ClientResponseError: If the response status is not 2xx.
            Exceptions from _request_with_retry.
        """

        resp = await self._request_with_retry(
            session=session,
            method='GET',
            path=path,
            params=params,
            **kwargs,
        )
        resp.raise_for_status()

        return await self._handle_response(resp)

    async def post(
        self,
        session: aiohttp.ClientSession,
        path: str,
        data: RequestDataType = None,
        json: JSONDataType = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> Any:  # noqa: ANN401
        """
        Perform an HTTP POST request with retries.

        Args:
            session: Active aiohttp client session.
            path: URL path.
            data: Raw data to send in the body (form data, bytes, etc.).
            json: JSON-serializable object to send as JSON body.
            **kwargs: Additional request arguments.

        Returns:
            Deserialized response data.
        """

        resp = await self._request_with_retry(
            session=session,
            method="POST",
            path=path,
            data=data,
            json=json,
            **kwargs,
        )
        resp.raise_for_status()

        return await self._handle_response(resp)

    async def put(
        self,
        session: aiohttp.ClientSession,
        path: str,
        data: RequestDataType = None,
        json: JSONDataType = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> Any:  # noqa: ANN401
        resp = await self._request_with_retry(
            session=session,
            method='PUT',
            path=path,
            data=data,
            json=json,
            **kwargs,
        )
        resp.raise_for_status()

        return await self._handle_response(resp)

    async def patch(
        self,
        session: aiohttp.ClientSession,
        path: str,
        data: RequestDataType = None,
        json: JSONDataType = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> Any:  # noqa: ANN401
        resp = await self._request_with_retry(
            session=session,
            method='PATCH',
            path=path,
            data=data,
            json=json,
            **kwargs,
        )
        resp.raise_for_status()

        return await self._handle_response(resp)

    async def delete(
        self,
        session: aiohttp.ClientSession,
        path: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> Any:  # noqa: ANN401
        resp = await self._request_with_retry(
            session=session,
            method='DELETE',
            path=path,
            **kwargs,
        )
        resp.raise_for_status()

        return await self._handle_response(resp)

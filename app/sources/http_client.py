from __future__ import annotations

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import Settings

USER_AGENT = "graphics-research-agent/0.1"


def decode_response_text(response: httpx.Response) -> str:
    if response.charset_encoding:
        return response.content.decode(response.charset_encoding, errors="replace")
    try:
        return response.content.decode("utf-8")
    except UnicodeDecodeError:
        return response.content.decode("windows-1252")


def build_http_client(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(settings.http_timeout_seconds),
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    )


async def fetch_text(
    client: httpx.AsyncClient,
    settings: Settings,
    url: str,
    *,
    allow_not_found: bool = False,
) -> str | None:
    async for attempt in AsyncRetrying(
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(settings.http_retry_attempts),
        reraise=True,
    ):
        with attempt:
            response = await client.get(url)
            if allow_not_found and response.status_code == httpx.codes.NOT_FOUND:
                return None
            response.raise_for_status()
            return decode_response_text(response)
    raise RuntimeError(f"HTTP fetch did not return for {url}")

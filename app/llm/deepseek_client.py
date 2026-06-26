from __future__ import annotations

import json
import logging
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import Settings
from app.llm.prompts import build_classification_prompt, build_summary_prompt
from app.llm.schemas import ClassificationResult, SummaryResult
from app.sources.models import PaperItem

logger = logging.getLogger(__name__)

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class DeepSeekError(RuntimeError):
    """Base DeepSeek client error."""


class DeepSeekConfigurationError(DeepSeekError):
    """Raised when DeepSeek is required but not configured."""


class DeepSeekResponseError(DeepSeekError):
    """Raised when DeepSeek response content cannot be validated."""


class DeepSeekClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def is_configured(self) -> bool:
        return self._settings.deepseek_configured

    async def check_model_available(self) -> bool:
        if not self.is_configured:
            return False
        headers = {"Authorization": f"Bearer {self._settings.deepseek_api_key}"}
        try:
            async with httpx.AsyncClient(timeout=self._settings.http_timeout_seconds) as client:
                response = await client.get(
                    f"{self._settings.deepseek_base_url}/models",
                    headers=headers,
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            logger.warning("DeepSeek model availability check failed: %s", exc)
            return False

        models = payload.get("data", []) if isinstance(payload, dict) else []
        return any(
            item.get("id") == self._settings.deepseek_model
            for item in models
            if isinstance(item, dict)
        )

    async def classify_paper(self, paper: PaperItem) -> ClassificationResult:
        prompt = build_classification_prompt(paper)
        return await self._request_validated_json(prompt, ClassificationResult)

    async def summarize_paper(
        self, paper: PaperItem, classification: ClassificationResult
    ) -> SummaryResult:
        prompt = build_summary_prompt(paper, classification)
        return await self._request_validated_json(prompt, SummaryResult)

    async def _request_validated_json(self, prompt: str, schema: type[SchemaT]) -> SchemaT:
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                content = await self._chat_completion_content(prompt)
                payload = _parse_json_object(content)
                return schema.model_validate(payload)
            except (json.JSONDecodeError, ValidationError, DeepSeekResponseError) as exc:
                last_error = exc
                logger.warning(
                    "DeepSeek JSON validation failed on attempt %s: %s",
                    attempt + 1,
                    exc,
                )

        raise DeepSeekResponseError(
            f"DeepSeek response failed validation twice: {last_error}"
        ) from last_error

    async def _chat_completion_content(self, prompt: str) -> str:
        if not self.is_configured:
            raise DeepSeekConfigurationError("DEEPSEEK_API_KEY is not configured")

        payload = {
            "model": self._settings.deepseek_model,
            "messages": [
                {
                    "role": "system",
                    "content": "Return strict JSON only. Do not wrap JSON in Markdown.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self._settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }

        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            stop=stop_after_attempt(self._settings.http_retry_attempts),
            reraise=True,
        ):
            with attempt:
                async with httpx.AsyncClient(timeout=self._settings.http_timeout_seconds) as client:
                    response = await client.post(
                        f"{self._settings.deepseek_base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()
                    return _extract_message_content(data)

        raise DeepSeekResponseError("DeepSeek chat completion did not return content")


def _extract_message_content(payload: object) -> str:
    if not isinstance(payload, dict):
        raise DeepSeekResponseError("DeepSeek response is not a JSON object")
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise DeepSeekResponseError("DeepSeek response has no choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise DeepSeekResponseError("DeepSeek choice is not an object")
    message = first.get("message")
    if not isinstance(message, dict):
        raise DeepSeekResponseError("DeepSeek choice has no message")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise DeepSeekResponseError("DeepSeek message content is empty")
    return content


def _parse_json_object(content: str) -> dict[str, object]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()
    payload = json.loads(stripped)
    if not isinstance(payload, dict):
        raise DeepSeekResponseError("DeepSeek response JSON must be an object")
    return payload

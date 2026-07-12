from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field(default="deepseek-v4-flash", alias="DEEPSEEK_MODEL")

    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = Field(default=None, alias="TELEGRAM_CHAT_ID")

    app_env: str = Field(default="development", alias="APP_ENV")
    database_url: str = Field(default="sqlite:///./data/agent.sqlite3", alias="DATABASE_URL")
    dry_run: bool = Field(default=True, alias="DRY_RUN")
    timezone: str = Field(default="Asia/Tokyo", alias="TIMEZONE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    max_arxiv_results: int = Field(default=80, ge=1, le=500, alias="MAX_ARXIV_RESULTS")
    max_feed_results: int = Field(default=20, ge=1, le=200, alias="MAX_FEED_RESULTS")
    max_push_must_read: int = Field(default=3, ge=0, alias="MAX_PUSH_MUST_READ")
    max_push_read_later: int = Field(default=5, ge=0, alias="MAX_PUSH_READ_LATER")
    rule_filter_threshold: int = Field(default=5, alias="RULE_FILTER_THRESHOLD")
    arxiv_categories_raw: str = Field(default="cs.GR,cs.CV,cs.LG", alias="ARXIV_CATEGORIES")
    enabled_sources_raw: str = Field(
        default=("arxiv,unreal,nvidia,gpuopen,directx,vulkan,siggraph_realtime,siggraph_research"),
        alias="ENABLED_SOURCES",
    )
    unreal_feed_url: str = Field(
        default="https://www.unrealengine.com/rss",
        alias="UNREAL_FEED_URL",
    )
    nvidia_feed_url: str = Field(
        default="https://developer.nvidia.com/blog/feed/",
        alias="NVIDIA_FEED_URL",
    )
    gpuopen_feed_url: str = Field(
        default="https://gpuopen.com/feed.xml",
        alias="GPUOPEN_FEED_URL",
    )
    directx_feed_url: str = Field(
        default="https://devblogs.microsoft.com/directx/feed/",
        alias="DIRECTX_FEED_URL",
    )
    vulkan_feed_url: str = Field(
        default="https://www.khronos.org/feeds/vulkan_news_feed",
        alias="VULKAN_FEED_URL",
    )
    siggraph_realtime_feed_url: str = Field(
        default="https://blog.siggraph.org/category/realtime/feed/",
        alias="SIGGRAPH_REALTIME_FEED_URL",
    )
    siggraph_research_feed_url: str = Field(
        default="https://blog.siggraph.org/category/research/feed/",
        alias="SIGGRAPH_RESEARCH_FEED_URL",
    )

    schedule_hour: int = Field(default=9, ge=0, le=23, alias="SCHEDULE_HOUR")
    schedule_minute: int = Field(default=0, ge=0, le=59, alias="SCHEDULE_MINUTE")

    http_timeout_seconds: float = Field(default=20.0, gt=0, alias="HTTP_TIMEOUT_SECONDS")
    http_retry_attempts: int = Field(default=3, ge=1, alias="HTTP_RETRY_ATTEMPTS")

    @field_validator("deepseek_api_key", "telegram_bot_token", "telegram_chat_id", mode="before")
    @classmethod
    def blank_or_placeholder_to_none(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        if stripped == "" or stripped.lower() in {"replace_me", "changeme", "none", "null"}:
            return None
        return stripped

    @field_validator("deepseek_base_url")
    @classmethod
    def trim_base_url(cls, value: str) -> str:
        return value.rstrip("/")

    @property
    def arxiv_categories(self) -> list[str]:
        return [item.strip() for item in self.arxiv_categories_raw.split(",") if item.strip()]

    @property
    def enabled_sources(self) -> list[str]:
        return [
            item.strip().casefold() for item in self.enabled_sources_raw.split(",") if item.strip()
        ]

    @property
    def database_path(self) -> Path:
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            raise ValueError("Only sqlite:/// DATABASE_URL values are supported in the MVP")
        raw_path = self.database_url.removeprefix(prefix)
        return Path(raw_path)

    @property
    def deepseek_configured(self) -> bool:
        return bool(self.deepseek_api_key)

    @property
    def telegram_configured(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()

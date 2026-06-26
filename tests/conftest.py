from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.sources.arxiv_source import parse_arxiv_feed
from app.sources.models import PaperItem
from app.storage.db import Database


@pytest.fixture
def fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_papers(fixture_dir: Path) -> list[PaperItem]:
    return parse_arxiv_feed((fixture_dir / "arxiv_sample.xml").read_text(encoding="utf-8"))


@pytest.fixture
def temp_settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'agent.sqlite3'}",
        dry_run=True,
        deepseek_api_key=None,
        telegram_bot_token=None,
        telegram_chat_id=None,
        max_arxiv_results=10,
        rule_filter_threshold=5,
    )


@pytest.fixture
def temp_database(temp_settings: Settings) -> Database:
    database = Database.from_settings(temp_settings)
    database.init_schema()
    try:
        yield database
    finally:
        database.close()

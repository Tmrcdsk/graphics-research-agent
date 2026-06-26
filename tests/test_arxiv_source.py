from __future__ import annotations

from pathlib import Path

import pytest

from app.sources.arxiv_source import ArxivParseError, extract_arxiv_id, parse_arxiv_feed
from app.utils.hashing import stable_title_hash


def test_parse_arxiv_fixture_extracts_expected_fields(fixture_dir: Path) -> None:
    papers = parse_arxiv_feed((fixture_dir / "arxiv_sample.xml").read_text(encoding="utf-8"))

    assert len(papers) == 2
    first = papers[0]
    assert first.arxiv_id == "2606.00001"
    assert first.title == "Reservoir Path Tracing for Real-Time Global Illumination"
    assert first.authors == ["Alice Renderer", "Bob Shader"]
    assert first.categories == ["cs.GR", "cs.CV"]
    assert first.abs_url == "http://arxiv.org/abs/2606.00001v1"
    assert first.pdf_url == "http://arxiv.org/pdf/2606.00001v1"
    assert first.title_hash == stable_title_hash(first.title)


def test_extract_arxiv_id_removes_version_suffix() -> None:
    assert extract_arxiv_id("http://arxiv.org/abs/2606.00001v3") == "2606.00001"


def test_parse_malformed_feed_raises() -> None:
    with pytest.raises(ArxivParseError):
        parse_arxiv_feed("<feed><entry>")


def test_parse_entry_with_missing_required_fields_is_skipped() -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry><title>Missing required fields</title></entry>
    </feed>
    """
    assert parse_arxiv_feed(xml) == []

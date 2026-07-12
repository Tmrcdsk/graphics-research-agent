from __future__ import annotations

import logging

import httpx

from app.logging_config import SecretRedactionFilter


def test_secret_filter_redacts_token_embedded_in_httpx_url() -> None:
    token = "123456:fake-telegram-token"
    record = logging.LogRecord(
        name="httpx",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='HTTP Request: %s %s "HTTP/1.1 200 OK"',
        args=("POST", httpx.URL(f"https://api.telegram.org/bot{token}/sendMessage")),
        exc_info=None,
    )

    assert SecretRedactionFilter([token]).filter(record)

    message = record.getMessage()
    assert token not in message
    assert "bot[REDACTED]/sendMessage" in message

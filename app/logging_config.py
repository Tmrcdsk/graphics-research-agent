from __future__ import annotations

import logging
import sys
from collections.abc import Iterable


class SecretRedactionFilter(logging.Filter):
    def __init__(self, secrets: Iterable[str | None]) -> None:
        super().__init__()
        self._secrets = [secret for secret in secrets if secret]

    def _redact(self, value: object) -> object:
        if not isinstance(value, str):
            return value
        redacted = value
        for secret in self._secrets:
            if secret and secret in redacted:
                redacted = redacted.replace(secret, "[REDACTED]")
        return redacted

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._redact(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(self._redact(arg) for arg in record.args)
        elif isinstance(record.args, dict):
            record.args = {key: self._redact(value) for key, value in record.args.items()}
        return True


def configure_logging(
    log_level: str,
    *,
    deepseek_api_key: str | None = None,
    telegram_bot_token: str | None = None,
) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))
    handler.addFilter(SecretRedactionFilter([deepseek_api_key, telegram_bot_token]))
    root.addHandler(handler)
    root.setLevel(log_level.upper())

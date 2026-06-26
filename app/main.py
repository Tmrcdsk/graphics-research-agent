from __future__ import annotations

import argparse
import asyncio
import logging

from app.config import get_settings
from app.logging_config import configure_logging
from app.pipeline.run_pipeline import run_once
from app.scheduler import serve

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="graphics-research-agent")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("run-once", help="Run the pipeline once.")
    subparsers.add_parser("serve", help="Run the daily scheduler.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = get_settings()
    configure_logging(
        settings.log_level,
        deepseek_api_key=settings.deepseek_api_key,
        telegram_bot_token=settings.telegram_bot_token,
    )

    if args.command == "run-once":
        stats = asyncio.run(run_once(settings=settings))
        logger.info(
            "run-once status=%s pushed=%s error=%s",
            stats.status,
            stats.pushed_count,
            stats.error,
        )
        return

    if args.command == "serve":
        asyncio.run(serve(settings))
        return

    parser.error(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()

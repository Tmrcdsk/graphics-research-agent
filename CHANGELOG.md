# CHANGELOG.md

## Unreleased

### Added

- Initial Python MVP skeleton with config, logging, arXiv parsing, SQLite storage, rule filtering, DeepSeek schema/client, Telegram publisher, scheduler, and `run-once` CLI.
- Fixture-based unit tests for arXiv parsing, deduplication, rule filtering, DeepSeek schema validation, Telegram dry-run, and end-to-end dry-run pipeline.
- Dockerfile, Docker Compose configuration, environment example, line-ending controls, and AI-maintained project documents.
- `.dockerignore` to keep local virtual environments, caches, secrets, and SQLite files out of Docker build context.
- `PYTHON_IMAGE` Docker build override for networks that cannot pull directly from Docker Hub.
- AGENTS.md rule requiring conventional commit style.

### Changed

- arXiv HTTP retry now uses the configured retry attempt count.
- arXiv parsed timestamps are converted as UTC.
- Long Python lines were wrapped for lint compatibility.
- Pytest now writes temporary files under `.pytest_tmp` inside the repository and disables the pytest cache provider to avoid Windows user-temp permission issues in restricted environments.
- The dry-run fallback summary text is ASCII-only placeholder text to avoid Windows console encoding corruption.

### Fixed

- Avoid storing feedparser-specific objects in `PaperItem.raw`, keeping SQLite JSON storage safe.
- Malformed arXiv feeds now raise `ArxivParseError` whenever `feedparser` reports a bozo parse state.
- Docker build can now use a reachable Python image mirror through `PYTHON_IMAGE`.

### Removed

- None.

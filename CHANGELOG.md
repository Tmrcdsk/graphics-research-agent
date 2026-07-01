# CHANGELOG.md

## Unreleased

### Added

- Initial Python MVP skeleton with config, logging, arXiv parsing, SQLite storage, rule filtering, DeepSeek schema/client, Telegram publisher, scheduler, and `run-once` CLI.
- Fixture-based unit tests for arXiv parsing, deduplication, rule filtering, DeepSeek schema validation, Telegram dry-run, and end-to-end dry-run pipeline.
- Dockerfile, Docker Compose configuration, environment example, line-ending controls, and AI-maintained project documents.
- `.dockerignore` to keep local virtual environments, caches, secrets, and SQLite files out of Docker build context.
- `PYTHON_IMAGE` Docker build override for networks that cannot pull directly from Docker Hub.
- AGENTS.md rule requiring conventional commit style.
- Official Unreal Engine / Epic RSS feed source.
- Official NVIDIA Developer Blog RSS feed source.
- Multi-source orchestration for arXiv plus official feeds.
- SQLite source metadata fields and migration path for `source_name` and `source_id`.
- Feed parser fixture tests and source factory tests.
- Troubleshooting note warning that `docker compose config` can print real `.env` secrets.
- Live dry-run smoke test coverage for official Unreal and NVIDIA feed fetching.

### Changed

- arXiv HTTP retry now uses the configured retry attempt count.
- arXiv parsed timestamps are converted as UTC.
- Long Python lines were wrapped for lint compatibility.
- Pytest now writes temporary files under `.pytest_tmp` inside the repository and disables the pytest cache provider to avoid Windows user-temp permission issues in restricted environments.
- The dry-run fallback summary text is ASCII-only placeholder text to avoid Windows console encoding corruption.
- DeepSeek prompts are now generalized from arXiv papers to rendering research items and official technical posts.
- Telegram messages now show a generic source and link instead of arXiv-only labels.
- Rule filtering now includes Unreal Engine and NVIDIA rendering keywords such as UE5, Mega Lights, RTX, DLSS, mesh shader, and neural radiance cache.
- Unreal default feed URL now uses `https://www.unrealengine.com/rss`, because `/en-US/feed` returned Cloudflare 403 during live testing.

### Fixed

- Avoid storing feedparser-specific objects in `PaperItem.raw`, keeping SQLite JSON storage safe.
- Malformed arXiv feeds now raise `ArxivParseError` whenever `feedparser` reports a bozo parse state.
- Docker build can now use a reachable Python image mirror through `PYTHON_IMAGE`.
- Replaced mojibake in the Telegram message template with valid Chinese labels.
- Feed titles are stripped of HTML before storage and Telegram rendering.

### Removed

- None.

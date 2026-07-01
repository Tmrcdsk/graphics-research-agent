# CURRENT_STATUS.md

## Project State

Status: MVP implemented; official Unreal/NVIDIA feed extension validated locally

## Current Goal

Extend the validated arXiv + DeepSeek + Telegram MVP with official Unreal/Epic and NVIDIA rendering news feeds.

## Implemented

- [x] Project skeleton
- [x] Config loading
- [x] SQLite schema
- [x] arXiv source
- [x] Unreal Engine / Epic official feed source
- [x] NVIDIA Developer Blog official feed source
- [x] Multi-source orchestration
- [x] Rule filter
- [x] DeepSeek client
- [x] DeepSeek schema validation
- [x] Telegram publisher
- [x] Dry-run pipeline
- [x] Docker Compose runtime
- [x] Unit tests

## Not Implemented Yet

- [ ] Production Telegram send verified with real credentials
- [ ] Production DeepSeek call verified with real credentials
- [ ] Scheduler verified as a long-running container service
- [ ] VPS deployment
- [ ] GitHub Actions
- [ ] Feishu publisher
- [ ] Koishi bridge
- [ ] Semantic Scholar
- [ ] GitHub repository discovery

## Known Issues

- Production Telegram send has not been verified with real credentials.
- Production DeepSeek behavior has not been verified beyond the successful local `run-once` call observed in PowerShell output.
- Direct Docker Hub access failed for `python:3.11-slim`; use `PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.11-slim` or another reachable mirror on affected networks.
- `data/agent.sqlite3` may be created by local or Docker dry-runs. It is ignored by Git and should not be committed.
- Official website feed URLs can change. Defaults are configurable through `UNREAL_FEED_URL` and `NVIDIA_FEED_URL`.
- Docker Linux validation for the feed extension was attempted but Docker Desktop Linux engine was not running: `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.`
- `https://www.unrealengine.com/en-US/feed` returned Cloudflare 403 in live testing; the working official default is `https://www.unrealengine.com/rss`.

## Important Decisions

- First push channel: Telegram.
- First runtime target: VPS with Docker Compose.
- First local development environment: native Windows with PowerShell and Docker Desktop. WSL2 is optional.
- Final validation target before GitHub/VPS: Docker Linux container.
- First LLM model: deepseek-v4-flash.
- First source was arXiv; official Unreal/NVIDIA feeds were added after the MVP was validated.
- Current default sources: arXiv, Unreal Engine official feed, and NVIDIA Developer Blog feed.
- Official feed sources reuse the same SQLite dedupe, rule filter, DeepSeek schema validation, Telegram renderer, and publish log path as arXiv.
- Existing SQLite databases are migrated in place with `source_name` and `source_id` columns.
- If `DRY_RUN=true` and `DEEPSEEK_API_KEY` is missing, `run_once` uses a conservative local fallback classification and summary so the local dry-run pipeline can be validated without secrets. `DRY_RUN=false` never uses this fallback.
- Unit tests use fixture XML, mocked DeepSeek content, and Telegram dry-run only; they do not call real external APIs.
- Pytest uses `.pytest_tmp` inside the repository to avoid Windows user-temp permission issues under sandboxed runners.
- Docker builds can override the base image with `PYTHON_IMAGE` while keeping `python:3.11-slim` as the default.

## Recent Test Command

- `.\.venv\Scripts\python.exe -m pytest`
- `.\.venv\Scripts\python.exe -m ruff check .`
- `.\.venv\Scripts\python.exe -m ruff format --check .`
- `$env:PYTHON_IMAGE='docker.m.daocloud.io/library/python:3.11-slim'; docker compose build`
- `$env:ENABLED_SOURCES='unreal,nvidia'; $env:DATABASE_URL='sqlite:///./data/news-feed-smoke-local-3.sqlite3'; $env:DRY_RUN='true'; $env:DEEPSEEK_API_KEY='replace_me'; $env:TELEGRAM_BOT_TOKEN='replace_me'; $env:TELEGRAM_CHAT_ID='replace_me'; $env:MAX_FEED_RESULTS='3'; .\.venv\Scripts\python.exe -m app.main run-once`
- `$env:PYTHON_IMAGE='docker.m.daocloud.io/library/python:3.11-slim'; docker compose run --rm graphics-agent pytest`
- `$env:PYTHON_IMAGE='docker.m.daocloud.io/library/python:3.11-slim'; docker compose run --rm graphics-agent python -m app.main run-once`
- `.\.venv\Scripts\python.exe -m pytest`
- `.\.venv\Scripts\python.exe -m ruff check .`
- `.\.venv\Scripts\python.exe -m ruff format --check .`

## Recent Test Result

- Windows pytest: passed, 16 tests.
- Windows ruff check: passed.
- Windows ruff format check: passed.
- Docker Compose build: passed using `PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.11-slim`.
- Docker Linux pytest: passed, 16 tests.
- Docker Linux `run-once`: passed in dry-run mode with 80 fetched arXiv items, 80 duplicates, 0 candidates, and 0 pushed messages.
- Windows pytest after feed extension and storage migration test: passed, 23 tests.
- Windows ruff check after feed extension: passed.
- Windows ruff format check after feed extension: passed.
- Docker Compose build after feed extension: not run because Docker Desktop Linux engine was unavailable.
- Live official feed smoke test: passed in dry-run mode. Unreal feed fetched 10 items from `https://www.unrealengine.com/rss`; NVIDIA feed fetched 100 items from `https://developer.nvidia.com/blog/feed/`; 6 items were stored, 2 dry-run messages were rendered, and no Telegram message was sent.

## Next Recommended Task

Start Docker Desktop, run Docker Linux validation for the feed extension, then run a dry-run feed smoke test:

```powershell
$env:PYTHON_IMAGE="docker.m.daocloud.io/library/python:3.11-slim"
docker compose build
docker compose run --rm graphics-agent pytest
$env:ENABLED_SOURCES="unreal,nvidia"
$env:DATABASE_URL="sqlite:///./data/news-feed-smoke.sqlite3"
.\.venv\Scripts\python.exe -m app.main run-once
```

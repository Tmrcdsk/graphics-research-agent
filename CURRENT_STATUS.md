# CURRENT_STATUS.md

## Project State

Status: Multi-source rendering news MVP implemented, validated on Windows and Docker Linux, and running locally in Docker Desktop production mode

## Current Goal

Broaden the validated arXiv + DeepSeek + Telegram pipeline with high-signal official rendering engineering and SIGGRAPH feeds while preserving deduplication, dry-run safety, and Docker Linux deployability.

## Implemented

- [x] Config loading and secret redaction
- [x] SQLite schema, in-place migration, deduplication, and publish logs
- [x] arXiv source
- [x] Unreal Engine / Epic official feed source
- [x] NVIDIA Developer Blog official feed source
- [x] AMD GPUOpen official feed source
- [x] Microsoft DirectX Developer Blog official feed source
- [x] Khronos Vulkan News official feed source
- [x] ACM SIGGRAPH Real-Time official feed source
- [x] ACM SIGGRAPH Research official feed source
- [x] Data-driven official feed registry and unknown-source validation
- [x] Multi-source failure isolation
- [x] Rendering rule filter
- [x] DeepSeek client and schema validation
- [x] Telegram publisher and strict dry-run behavior
- [x] Telegram URL token log redaction
- [x] Docker Compose scheduler runtime
- [x] Fixture-based offline unit tests for every source
- [x] Windows-native test validation
- [x] Docker Linux test and live-feed dry-run validation
- [x] Local Docker Desktop production service deployment

## Not Implemented Yet

- [ ] VPS deployment
- [ ] CI/CD or GitHub Actions
- [ ] Docker healthcheck or external alerting
- [ ] Per-source run status rows and metrics
- [ ] Automatic retry of items that were stored before an LLM failure
- [ ] Sources outside the documented official-feed scope

## Known Issues

- The running production container is local to Docker Desktop. It stops when the Windows host or Docker Desktop is unavailable and is not a VPS deployment.
- Official feed URLs and formats can change. Every URL is configurable through its matching `*_FEED_URL` variable.
- Direct Docker Hub access can fail on the current network. The validated build used `docker.m.daocloud.io/library/python:3.11-slim` through `PYTHON_IMAGE`.
- `feedparser` emits a deprecation warning about its temporary `updated_parsed` fallback. Parsing behavior remains correct in current tests.
- `source_runs` records one aggregate multi-source run. Individual source failures are visible in logs but not stored as separate run rows.
- Items are stored before rule filtering and DeepSeek calls. A later LLM failure is not automatically retried on the next run because the item is already deduplicated.
- SIGGRAPH category feeds intentionally include adjacent research. Recent non-rendering entries can score below the rule threshold and are stored without calling DeepSeek.
- Full `docker compose config`, `docker inspect`, environment dumps, and `.env` output can expose credentials and must not be shared.

## Important Decisions

- Default sources are arXiv, Unreal Engine, NVIDIA, GPUOpen, DirectX, Khronos Vulkan News, SIGGRAPH Real-Time, and SIGGRAPH Research.
- Unity was not enabled because its official feed is very large and currently dominated by advertising, business, and general product content.
- Khronos Blog was not enabled because it overlaps with the selected Vulkan News feed.
- Intel graphics feeds were not enabled because the relevant official endpoint returned HTTP 403 to the project client during research.
- New standard RSS/Atom sources reuse `NewsFeedSource`; source metadata is registered through `OFFICIAL_FEED_SPECS`.
- Unknown `ENABLED_SOURCES` values fail fast to prevent silent deployment mistakes.
- The existing SQLite identity and migration strategy is unchanged; no database migration was required for these sources.
- Production Telegram and DeepSeek credentials remain environment-only and are never written to tracked files.
- Local production deployment uses `APP_ENV=production`, `DRY_RUN=false`, and the daily 09:00 Asia/Tokyo schedule.

## Recent Test Commands

- `.\.venv\Scripts\python.exe -m pytest`
- `.\.venv\Scripts\python.exe -m ruff check --no-cache .`
- `.\.venv\Scripts\python.exe -m ruff format --check --no-cache .`
- `.\.venv\Scripts\python.exe -m mypy app`
- Local live-feed run with explicit `DRY_RUN=true`, placeholder credentials, five new sources, and an isolated SQLite file
- `docker compose build --build-arg PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.11-slim`
- `docker compose run --rm --no-deps ... graphics-agent python -m pytest`
- `docker compose run --rm --no-deps ... graphics-agent python -m ruff check .`
- `docker compose run --rm --no-deps ... graphics-agent python -m mypy app`
- Docker live-feed run with explicit `DRY_RUN=true`, placeholder credentials, five new sources, and `/tmp/new-sources-smoke-docker.sqlite3`
- `docker compose up -d --force-recreate`
- `docker compose ps`
- `docker compose logs --no-color --tail 50 graphics-agent`

## Recent Test Result

- Windows pytest: passed, 38 tests.
- Windows ruff check: passed.
- Windows ruff format check: passed.
- Windows mypy: passed for 30 source files.
- Local live-feed dry-run: passed. All five new feeds returned HTTP 200; 10 limited items were stored, 6 were rule candidates, and 2 dry-run messages were rendered without DeepSeek or Telegram network calls.
- Docker Compose build: passed on Linux/amd64 using the configured mirror image.
- Docker Linux pytest: passed, 38 tests on Python 3.11.15.
- Docker Linux ruff check: passed.
- Docker Linux mypy: passed for 30 source files.
- Docker Linux live-feed dry-run: passed with the same 10 fetched items, 6 candidates, and 2 dry-run publish-log records. No Telegram message was sent.
- Local production deployment: passed. Container `graphics-research-agent` is running and the scheduler started for 09:00 Asia/Tokyo.
- Runtime configuration check: `production`, `DRY_RUN=false`, and all eight sources enabled.

## Next Recommended Task

Commit and push this validated source expansion. For a real VPS deployment, provide the VPS host, SSH user/port/key path, repository access method, and desired deployment directory; then run the documented Docker Compose deployment with the VPS production `.env`.

# CURRENT_STATUS.md

## Project State

Status: Multi-source rendering news MVP implemented and validated on Windows and Docker Linux. GDC-related coverage is implemented locally but has not yet been pushed or deployed to the existing VPS.

## Current Goal

Track rendering-related GDC articles without scraping browser-protected GDC pages, while preserving source isolation, conservative rule filtering, dry-run safety, and Linux container deployability.

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
- [x] GDC-related coverage through the GameDeveloper.com official RSS feed
- [x] Source-level required-term filtering for broad feeds
- [x] Data-driven feed registry and unknown-source validation
- [x] Multi-source failure isolation
- [x] Rendering rule filter with GDC graphics terminology
- [x] DeepSeek client and schema validation
- [x] Telegram publisher and strict dry-run behavior
- [x] Telegram URL token log redaction
- [x] Docker Compose scheduler runtime
- [x] Fixture-based offline unit tests for every source
- [x] Windows-native test and GDC live-feed validation
- [x] Docker Linux test and GDC live-feed validation

## Not Implemented Yet

- [ ] Direct GDC schedule or GDC Vault ingestion
- [ ] CI/CD or GitHub Actions
- [ ] Docker healthcheck or external alerting
- [ ] Per-source run status rows and metrics
- [ ] Automatic retry of items stored before an LLM failure
- [ ] Sources outside the documented feed-based scope

## Known Issues

- The GDC website still links to legacy FeedBurner endpoints, but both tested endpoints return the GDC HTML homepage with zero RSS entries.
- The official GDC schedule offers CSV and iCal exports, but server-side clients receive a Cloudflare HTTP 403 challenge. It is unsuitable for the current VPS worker without browser automation.
- The `gdc` source therefore tracks GameDeveloper.com RSS entries that explicitly mention `GDC` or `Game Developers Conference`. It does not provide a complete mirror of the GDC schedule or Vault.
- GameDeveloper.com publishes high-volume industry coverage. Source-level GDC filtering runs before storage, and the rendering rule filter runs afterward to control noise and DeepSeek usage.
- Existing deployments with an explicit `ENABLED_SOURCES` value must append `gdc`; changing the code default does not override their `.env`.
- Official feed URLs and formats can change. Every URL is configurable through its matching `*_FEED_URL` variable.
- Direct Docker Hub access can fail on the current network. The validated build used `docker.m.daocloud.io/library/python:3.11-slim` through `PYTHON_IMAGE`.
- `feedparser` emits a deprecation warning about its temporary `updated_parsed` fallback. Parsing behavior remains correct in current tests.
- `source_runs` records one aggregate multi-source run. Individual source failures are visible in logs but not stored as separate run rows.
- Items are stored before rule filtering and DeepSeek calls. A later LLM failure is not automatically retried on the next run because the item is already deduplicated.
- SIGGRAPH category feeds intentionally include adjacent research. Recent non-rendering entries can score below the rule threshold and are stored without calling DeepSeek.
- Full `docker compose config`, `docker inspect`, environment dumps, and `.env` output can expose credentials and must not be shared.

## Important Decisions

- Default sources are arXiv, Unreal Engine, NVIDIA, GPUOpen, DirectX, Khronos Vulkan News, SIGGRAPH Real-Time, SIGGRAPH Research, and GDC-related GameDeveloper.com coverage.
- `GDC_FEED_URL` defaults to `https://www.gamedeveloper.com/rss.xml`.
- The GDC source requires an explicit GDC marker before an item enters SQLite. The term `GDC` itself is not a rendering score signal.
- GDC-oriented rendering signals include real-time graphics, rendering/graphics pipelines, rendering architecture, physically based rendering, GPU optimization, occlusion culling, and Advanced Graphics Summit.
- GDC schedule HTML scraping and browser automation remain out of scope because they would be fragile and unsuitable for the lightweight VPS worker.
- Unity was not enabled because its official feed is very large and dominated by advertising, business, and general product content during source research.
- Khronos Blog was not enabled because it overlaps with the selected Vulkan News feed.
- Intel graphics feeds were not enabled because the relevant official endpoint returned HTTP 403 to the project client during source research.
- New standard RSS/Atom sources reuse `NewsFeedSource`; source metadata and optional source constraints are registered through `OFFICIAL_FEED_SPECS`.
- Unknown `ENABLED_SOURCES` values fail fast to prevent silent deployment mistakes.
- No database migration or DeepSeek prompt-schema change was required for the GDC source.
- Production Telegram and DeepSeek credentials remain environment-only and were replaced with placeholders in all smoke tests.
- The existing long-running Compose service was not recreated during this change; all Docker validation used one-off containers with `DRY_RUN=true`.

## Recent Test Commands

- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m ruff check --no-cache .`
- `.\.venv\Scripts\python.exe -m ruff format --check --no-cache .`
- `.\.venv\Scripts\python.exe -m mypy app`
- Windows GDC-only `run-once` with `ENABLED_SOURCES=gdc`, `DRY_RUN=true`, placeholder credentials, `MAX_FEED_RESULTS=50`, and an isolated SQLite file
- `docker version --format '{{.Server.Os}}/{{.Server.Arch}} {{.Server.Version}}'`
- `docker compose build --build-arg PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.11-slim`
- `docker compose run --rm --no-deps ... graphics-agent python -m pytest -q`
- `docker compose run --rm --no-deps ... graphics-agent python -m ruff check --no-cache .`
- `docker compose run --rm --no-deps ... graphics-agent python -m ruff format --check --no-cache .`
- `docker compose run --rm --no-deps ... graphics-agent python -m mypy app`
- Docker GDC-only `run-once` with placeholder credentials, `DRY_RUN=true`, and `/tmp/gdc-live-smoke.sqlite3`
- `docker compose config --quiet`

## Recent Test Result

- Windows pytest: passed, 42 tests with 13 known `feedparser` deprecation warnings.
- Windows Ruff lint: passed.
- Windows Ruff format check: passed for 41 files.
- Windows mypy: passed for 30 source files.
- Windows GDC live-feed dry-run: passed. RSS returned HTTP 200 with 50 entries; source constraints selected one GDC article, which scored below the rendering threshold. No DeepSeek or Telegram request was made.
- Docker daemon: Linux/amd64, Docker 27.5.1.
- Docker Compose build: passed using the configured mirror image.
- Docker Linux pytest: passed, 42 tests with 13 known warnings.
- Docker Linux Ruff lint and format checks: passed.
- Docker Linux mypy: passed for 30 source files.
- Docker Linux GDC live-feed dry-run: passed with the same 50 parsed entries, one GDC-selected article, zero rendering candidates, and zero pushes. No DeepSeek or Telegram request was made.
- Docker Compose configuration validation: passed.

## Next Recommended Task

Review and push the conventional commit. On the VPS, pull the new commit, append `gdc` to `ENABLED_SOURCES` in `.env`, rebuild the image, recreate the service, and inspect logs for `Fetching gdc feed` plus the selected-item count.

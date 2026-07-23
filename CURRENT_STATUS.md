# CURRENT_STATUS.md

## Project State

Status: GDC Vault and Advances in Real-Time Rendering catalog ingestion is implemented and validated on Windows and Docker Linux. Deployment still requires pushing the local commits and rebuilding the existing VPS service.

## Current Goal

Deploy the two new official catalog sources without weakening source isolation, conservative rendering filtering, dry-run safety, or Linux container portability.

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
- [x] GDC Vault current/previous annual catalog ingestion
- [x] GDC Vault media-variant deduplication and rendering-title prefiltering
- [x] GDC Vault candidate detail enrichment with catalog fallback
- [x] Advances in Real-Time Rendering current/previous annual course ingestion
- [x] Advances per-talk abstracts and presentation material links
- [x] Legacy Windows-1252 HTML decoding fallback
- [x] Source-level required-term filtering for broad feeds
- [x] Data-driven feed registry and unknown-source validation
- [x] Multi-source failure isolation
- [x] Rendering rule filter with GDC graphics terminology
- [x] DeepSeek client and schema validation
- [x] Telegram publisher and strict dry-run behavior
- [x] Telegram URL token log redaction
- [x] Docker Compose scheduler runtime
- [x] Fixture-based offline unit tests for every source
- [x] Windows-native tests and live catalog dry-run validation
- [x] Docker Linux tests and live catalog dry-run validation

## Not Implemented Yet

- [ ] Direct browser-protected GDC schedule ingestion
- [ ] CI/CD or GitHub Actions
- [ ] Docker healthcheck or external alerting
- [ ] Per-source run status rows and metrics
- [ ] Automatic retry of items stored before an LLM failure
- [ ] Sources outside the documented feed and allowlisted-catalog scope

## Known Issues

- GDC Vault and Advances do not publish RSS/Atom feeds for these catalogs. The project uses two
  dedicated parsers for their explicitly allowlisted official annual pages; this is not a general
  scraping framework.
- GDC Vault annual catalogs expose a conference year but no exact publication date. Stored items use
  January 1 of that year and record `date_precision=year`.
- GDC Vault rendering prefiltering uses catalog titles before detail requests. Talks with
  non-descriptive titles can be missed; broadening it must be balanced against HTTP and DeepSeek cost.
- Both catalog sources depend on stable official HTML structures. Fixture tests detect known
  regressions, but future site redesigns may require parser updates.
- Advances currently serves legacy Windows-1252 punctuation without an HTTP charset. The shared
  decoder now falls back from strict UTF-8 to Windows-1252 and has regression coverage.
- Existing deployments with an explicit `ENABLED_SOURCES` value must append `gdc_vault,advances`;
  changing the code default does not override their `.env`.
- Official feed and catalog URLs or formats can change. Base URLs are configurable through
  environment variables, and catalog year lists can be pinned for recovery.
- Direct Docker Hub access can fail on the current network. The validated build used `docker.m.daocloud.io/library/python:3.11-slim` through `PYTHON_IMAGE`.
- `feedparser` emits a deprecation warning about its temporary `updated_parsed` fallback. Parsing behavior remains correct in current tests.
- `source_runs` records one aggregate multi-source run. Individual source failures are visible in logs but not stored as separate run rows.
- Items are stored before rule filtering and DeepSeek calls. A later LLM failure is not automatically retried on the next run because the item is already deduplicated.
- SIGGRAPH category feeds intentionally include adjacent research. Recent non-rendering entries can score below the rule threshold and are stored without calling DeepSeek.
- Full `docker compose config`, `docker inspect`, environment dumps, and `.env` output can expose credentials and must not be shared.
- The live catalog smoke tests intentionally used placeholder DeepSeek and Telegram values. They
  validated fetching, parsing, SQLite, filtering, dry-run rendering, and publish logs, but did not
  call either external API.

## Important Decisions

- Default sources are arXiv, Unreal Engine, NVIDIA, GPUOpen, DirectX, Khronos Vulkan News, SIGGRAPH
  Real-Time, SIGGRAPH Research, GDC-related GameDeveloper.com coverage, GDC Vault, and Advances in
  Real-Time Rendering.
- `GDC_FEED_URL` defaults to `https://www.gamedeveloper.com/rss.xml`.
- The GDC source requires an explicit GDC marker before an item enters SQLite. The term `GDC` itself is not a rendering score signal.
- GDC-oriented rendering signals include real-time graphics, rendering/graphics pipelines, rendering architecture, physically based rendering, GPU optimization, occlusion culling, and Advanced Graphics Summit.
- GDC schedule HTML scraping and browser automation remain out of scope because they are fragile and
  unsuitable for the lightweight VPS worker.
- GDC Vault and Advances are narrow exceptions to the feed-only rule because they are stable,
  official, allowlisted technical catalogs requested by the project owner.
- Empty `GDC_VAULT_YEARS` and `ADVANCES_YEARS` values resolve to the current and previous calendar
  years. Explicit comma-separated values preserve order and remove duplicates.
- GDC Vault slide/video variants are deduplicated by normalized title with slides preferred.
- Advances talks are accepted only when a named syllabus anchor has an abstract or downloadable
  material. Rule scoring includes source categories, so every curated course talk reaches DeepSeek
  classification without altering the source abstract.
- Unity was not enabled because its official feed is very large and dominated by advertising, business, and general product content during source research.
- Khronos Blog was not enabled because it overlaps with the selected Vulkan News feed.
- Intel graphics feeds were not enabled because the relevant official endpoint returned HTTP 403 to the project client during source research.
- New standard RSS/Atom sources reuse `NewsFeedSource`; source metadata and optional source constraints are registered through `OFFICIAL_FEED_SPECS`.
- Unknown `ENABLED_SOURCES` values fail fast to prevent silent deployment mistakes.
- No database migration or DeepSeek prompt-schema change was required for either catalog source.
- Production Telegram and DeepSeek credentials remain environment-only and were replaced with placeholders in all smoke tests.
- The existing long-running Compose service was not recreated during this change; all Docker
  validation used one-off containers with `DRY_RUN=true`.

## Recent Test Commands

- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m ruff check app tests`
- `.\.venv\Scripts\python.exe -m ruff format --check app tests`
- `.\.venv\Scripts\python.exe -m mypy app`
- Windows catalog-only `run-once` with `ENABLED_SOURCES=gdc_vault,advances`,
  `DRY_RUN=true`, placeholder credentials, `MAX_FEED_RESULTS=5`, and isolated SQLite files
- `docker version --format '{{.Server.Os}}/{{.Server.Arch}} {{.Server.Version}}'`
- `docker compose config --quiet`
- `docker compose build --build-arg PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.11-slim`
- `docker compose run --rm --no-deps ... graphics-agent python -m pytest -q`
- `docker compose run --rm --no-deps ... graphics-agent python -m ruff check --no-cache .`
- `docker compose run --rm --no-deps ... graphics-agent python -m ruff format --check --no-cache .`
- `docker compose run --rm --no-deps ... graphics-agent python -m mypy app`
- Docker catalog-only `run-once` with placeholder credentials, `DRY_RUN=true`, explicit 2026/2025
  years, and `/tmp/catalog-live-smoke.sqlite3`

## Recent Test Result

- Windows pytest: passed, 56 tests with 13 known `feedparser` deprecation warnings.
- Windows Ruff lint and format checks: passed for 48 files.
- Windows mypy: passed for 33 source files.
- Windows live catalog dry-run: passed. GDC Vault yielded 561 deduplicated catalog entries and
  enriched the five newest rendering-title candidates. Advances yielded 14 talks and selected five.
  The pipeline stored 10 new items, found seven rule candidates, and dry-run logged seven messages.
  No DeepSeek or Telegram request was made.
- Windows legacy-page encoding recheck: passed. The live `Smolder` title retained its em dash and no
  logging encoding exception occurred with `PYTHONUTF8=1`.
- Docker daemon: Linux/amd64, Docker 27.5.1.
- Docker Compose configuration validation and image build: passed using the configured mirror image.
- Docker Linux pytest: passed, 56 tests with 13 known warnings.
- Docker Linux Ruff lint and format checks: passed for 48 files.
- Docker Linux mypy: passed for 33 source files.
- Docker Linux live catalog dry-run: passed with the same 10 selected source items and seven rule
  candidates. Push caps produced two dry-run publish-log entries and `status=success pushed=2`.
  No DeepSeek or Telegram request was made.

## Next Recommended Task

Push the local conventional commits. On the VPS, pull `main`, append `gdc_vault,advances` to the
explicit `ENABLED_SOURCES` value in `.env`, rebuild the image, recreate the service, and inspect logs
for both catalog source names.

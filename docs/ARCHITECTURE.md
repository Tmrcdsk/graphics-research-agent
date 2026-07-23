# Architecture

## Pipeline Flow

The MVP pipeline is:

```text
arXiv / official rendering feeds / allowlisted official catalogs
  -> parse/normalize
  -> SQLite dedupe
  -> rule filter
  -> DeepSeek JSON classification
  -> DeepSeek JSON summary
  -> Telegram publisher
  -> publish_logs
```

`app.pipeline.run_pipeline.run_once` owns the orchestration and records each run in `source_runs`.

## Source Interface

A source exposes `source_name` and `fetch_recent() -> list[PaperItem]`.

Current sources:

- `ArxivSource`: fetches Atom XML from the arXiv API.
- `NewsFeedSource`: fetches official RSS/Atom feeds for Unreal Engine, NVIDIA, AMD GPUOpen, DirectX, Khronos Vulkan News, ACM SIGGRAPH categories, and GDC-related GameDeveloper.com coverage.
- `GdcVaultSource`: fetches current and previous GDC Vault annual catalogs, deduplicates media variants, filters catalog titles for rendering signals, and fetches detail pages only for selected sessions.
- `AdvancesSource`: fetches current and previous Advances in Real-Time Rendering course pages and emits one item per talk with available abstract and presentation links.
- `MultiSource`: combines enabled sources and isolates source-level failures.
- `OFFICIAL_FEED_SPECS`: data-driven registry that maps source names to configurable URLs and labels. Unknown configured source names fail before fetching.

Feed specs may define `required_any_terms`. The GDC source uses this source-level constraint to keep
only RSS entries that explicitly mention `GDC` or `Game Developers Conference` before SQLite storage
and rendering relevance scoring. This prevents unrelated GameDeveloper.com industry news from
entering the pipeline.

GDC Vault exposes no exact publication date in its annual catalog. Items therefore use January 1 of
the conference year and record `date_precision=year` in raw metadata. Slides and video variants of
the same title are deduplicated with slides preferred.

Advances course pages use a stable `sYYYY/index.html` layout. A talk is accepted only when its named
anchor has an abstract or downloadable material. The course date is parsed when available; otherwise
August 1 of the page year is used. Its course category is included in rule scoring, so curated talks
reach DeepSeek classification without changing the source abstract.

The catalog sources use a shared text decoder. Explicit HTTP charsets are honored; otherwise UTF-8
is attempted first with a Windows-1252 fallback for legacy conference pages.

Unit tests call parser functions directly with fixture XML or HTML. Network access is mocked in all
source tests.

## Item Model

`PaperItem` contains source name, source ID, legacy arXiv-compatible ID, title, authors, abstract/excerpt, categories, published/updated timestamps, link/PDF URLs, a stable title hash, and optional raw metadata.

## Storage Model

SQLite tables:

- `papers`: normalized papers and official feed items
- `summaries`: validated classification and summary JSON
- `publish_logs`: Telegram success, dry-run, or failed publish attempts
- `source_runs`: pipeline run accounting

Deduplication happens before DeepSeek calls by matching `arxiv_id`, `abs_url`, or `title_hash`.

For website feeds, `arxiv_id` is a stable synthetic source-prefixed ID and `abs_url` is the article URL.

## Classifier and Summarizer

DeepSeek is called through an OpenAI-compatible `/chat/completions` request. The model must return JSON only. Responses are parsed and validated with Pydantic schemas. Invalid JSON or schema failures are retried once and never published if still invalid.

Prompt versions:

- `classification_v2`
- `summary_v2`

## Publisher Interface

The Telegram publisher renders Chinese HTML messages, splits long messages under Telegram limits, and supports dry-run. `DRY_RUN=true` never calls Telegram.

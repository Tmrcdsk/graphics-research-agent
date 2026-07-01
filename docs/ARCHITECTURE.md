# Architecture

## Pipeline Flow

The MVP pipeline is:

```text
arXiv / official RSS feeds
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
- `NewsFeedSource`: fetches official RSS/Atom feeds such as Unreal Engine and NVIDIA Developer Blog.
- `MultiSource`: combines enabled sources and isolates source-level failures.

Unit tests call parser functions directly with fixture XML.

## Item Model

`PaperItem` contains source name, source ID, legacy arXiv-compatible ID, title, authors, abstract/excerpt, categories, published/updated timestamps, link/PDF URLs, a stable title hash, and optional raw metadata.

## Storage Model

SQLite tables:

- `papers`: normalized arXiv papers
- `summaries`: validated classification and summary JSON
- `publish_logs`: Telegram success, dry-run, or failed publish attempts
- `source_runs`: pipeline run accounting

Deduplication happens before DeepSeek calls by matching `arxiv_id`, `abs_url`, or `title_hash`.

For website feeds, `arxiv_id` is a stable synthetic source-prefixed ID and `abs_url` is the article URL.

## Classifier and Summarizer

DeepSeek is called through an OpenAI-compatible `/chat/completions` request. The model must return JSON only. Responses are parsed and validated with Pydantic schemas. Invalid JSON or schema failures are retried once and never published if still invalid.

Prompt versions:

- `classification_v1`
- `summary_v1`

## Publisher Interface

The Telegram publisher renders Chinese HTML messages, splits long messages under Telegram limits, and supports dry-run. `DRY_RUN=true` never calls Telegram.

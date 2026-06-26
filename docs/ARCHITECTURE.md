# Architecture

## Pipeline Flow

The MVP pipeline is:

```text
arXiv -> parse/normalize -> SQLite dedupe -> rule filter -> DeepSeek JSON classification -> DeepSeek JSON summary -> Telegram publisher -> publish_logs
```

`app.pipeline.run_pipeline.run_once` owns the orchestration and records each run in `source_runs`.

## Source Interface

A source exposes `source_name` and `fetch_recent() -> list[PaperItem]`. The only MVP source is `ArxivSource`, which fetches Atom XML from the arXiv API and parses it with `feedparser`.

Unit tests call `parse_arxiv_feed` directly with fixture XML.

## Item Model

`PaperItem` contains arXiv ID, title, authors, abstract, categories, published/updated timestamps, abstract/PDF URLs, a stable title hash, and optional raw metadata.

## Storage Model

SQLite tables:

- `papers`: normalized arXiv papers
- `summaries`: validated classification and summary JSON
- `publish_logs`: Telegram success, dry-run, or failed publish attempts
- `source_runs`: pipeline run accounting

Deduplication happens before DeepSeek calls by matching `arxiv_id`, `abs_url`, or `title_hash`.

## Classifier and Summarizer

DeepSeek is called through an OpenAI-compatible `/chat/completions` request. The model must return JSON only. Responses are parsed and validated with Pydantic schemas. Invalid JSON or schema failures are retried once and never published if still invalid.

Prompt versions:

- `classification_v1`
- `summary_v1`

## Publisher Interface

The Telegram publisher renders Chinese HTML messages, splits long messages under Telegram limits, and supports dry-run. `DRY_RUN=true` never calls Telegram.

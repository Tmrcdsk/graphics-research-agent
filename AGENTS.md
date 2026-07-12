# AGENTS.md

## Project Mission

This project tracks computer graphics papers and official rendering engineering news, summarizes selected items with DeepSeek, and pushes concise Chinese summaries to Telegram.

## Current MVP Scope

- arXiv source
- Unreal Engine / Epic official feed source
- NVIDIA Developer Blog official feed source
- AMD GPUOpen official feed source
- Microsoft DirectX Developer Blog official feed source
- Khronos Vulkan News official feed source
- ACM SIGGRAPH Real-Time and Research official feed sources
- DeepSeek V4 Flash classification and summarization
- SQLite persistence
- Telegram publisher
- Docker Compose runtime
- Windows-native or optional WSL2 local development
- Docker Linux container validation before GitHub push or VPS deployment

## Out of Scope for MVP

- X / Twitter
- RSSHub
- Feishu
- QQ / Koishi
- PDF full-text parsing
- GitHub discovery
- Semantic Scholar
- Web dashboard
- Scraping pages without an official feed

## Hard Rules for AI Agents

1. Do not hard-code secrets.
2. Do not commit `.env`.
3. Do not add new external services without updating docs.
4. Do not remove dry-run support.
5. Do not make real network calls in unit tests.
6. Do not break existing database compatibility without documenting migration steps.
7. Do not silently change prompt schemas.
8. Every new source must include fixtures and tests.
9. Every new publisher must support dry-run mode.
10. Every significant change must update CURRENT_STATUS.md and CHANGELOG.md.
11. Use conventional commit style for Git commits, for example `feat: add arxiv source` or `fix: handle malformed arxiv feeds`.

## Before Making Changes

1. Read CURRENT_STATUS.md.
2. Read CHANGELOG.md.
3. Read docs/ARCHITECTURE.md.
4. Check existing tests.
5. Identify whether the change affects config, storage, prompts, or publishers.

## After Making Changes

1. Run formatting and linting.
2. Run tests.
3. Update CURRENT_STATUS.md.
4. Update CHANGELOG.md.
5. If behavior changed, update README.md or docs/.
6. Summarize changed files and test results.

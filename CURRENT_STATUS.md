# CURRENT_STATUS.md

## Project State

Status: MVP implemented and validated locally plus Docker Linux container

## Current Goal

Build and validate the arXiv + DeepSeek + Telegram MVP.

## Implemented

- [x] Project skeleton
- [x] Config loading
- [x] SQLite schema
- [x] arXiv source
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

## Important Decisions

- First push channel: Telegram.
- First runtime target: VPS with Docker Compose.
- First local development environment: native Windows with PowerShell and Docker Desktop. WSL2 is optional.
- Final validation target before GitHub/VPS: Docker Linux container.
- First LLM model: deepseek-v4-flash.
- First source: arXiv only.
- If `DRY_RUN=true` and `DEEPSEEK_API_KEY` is missing, `run_once` uses a conservative local fallback classification and summary so the local dry-run pipeline can be validated without secrets. `DRY_RUN=false` never uses this fallback.
- Unit tests use fixture XML, mocked DeepSeek content, and Telegram dry-run only; they do not call real external APIs.
- Pytest uses `.pytest_tmp` inside the repository to avoid Windows user-temp permission issues under sandboxed runners.
- Docker builds can override the base image with `PYTHON_IMAGE` while keeping `python:3.11-slim` as the default.

## Recent Test Command

- `.\.venv\Scripts\python.exe -m pytest`
- `.\.venv\Scripts\python.exe -m ruff check .`
- `.\.venv\Scripts\python.exe -m ruff format --check .`
- `$env:PYTHON_IMAGE='docker.m.daocloud.io/library/python:3.11-slim'; docker compose build`
- `$env:PYTHON_IMAGE='docker.m.daocloud.io/library/python:3.11-slim'; docker compose run --rm graphics-agent pytest`
- `$env:PYTHON_IMAGE='docker.m.daocloud.io/library/python:3.11-slim'; docker compose run --rm graphics-agent python -m app.main run-once`

## Recent Test Result

- Windows pytest: passed, 16 tests.
- Windows ruff check: passed.
- Windows ruff format check: passed.
- Docker Compose build: passed using `PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.11-slim`.
- Docker Linux pytest: passed, 16 tests.
- Docker Linux `run-once`: passed in dry-run mode with 80 fetched arXiv items, 80 duplicates, 0 candidates, and 0 pushed messages.

## Next Recommended Task

Create a local `.env` from placeholders, fill real credentials when ready, and run a live dry-run smoke test before enabling Telegram sends:

```powershell
Copy-Item .env.example .env
# Edit .env and keep DRY_RUN=true while testing.
.\.venv\Scripts\python.exe -m app.main run-once
```

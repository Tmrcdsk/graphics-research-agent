# Graphics Research Agent

Graphics Research Agent tracks recent computer graphics papers and official rendering engineering news, filters them for relevance to real-time rendering and game-engine learning, summarizes selected items with DeepSeek, and publishes concise Chinese summaries to Telegram.

## MVP Scope

Implemented MVP scope:

- arXiv source
- Unreal Engine / Epic official feed source
- NVIDIA Developer Blog official feed source
- AMD GPUOpen official feed source
- Microsoft DirectX Developer Blog official feed source
- Khronos Vulkan News official feed source
- ACM SIGGRAPH Real-Time official feed source
- ACM SIGGRAPH Research official feed source
- SQLite deduplication and publish logs
- Rule-based first-pass filtering
- DeepSeek-compatible structured classification and summarization
- Telegram publisher with mandatory dry-run support
- `python -m app.main run-once`
- `python -m app.main serve`
- Docker Compose runtime
- Fixture-based tests without real external API calls

Out of scope for MVP: Feishu, RSSHub, X/Twitter, Reddit, Semantic Scholar, Crossref, GitHub repo discovery, PDF full-text parsing, web dashboard, and VPS automation.

## Windows PowerShell Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
Copy-Item .env.example .env
```

Keep `DRY_RUN=true` until DeepSeek and Telegram credentials are configured and you intentionally want live Telegram sends.

## Environment Variables

All secrets are read from environment variables or a local `.env` file. Do not commit `.env`.

Required for live LLM and Telegram:

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Useful runtime settings:

- `ENABLED_SOURCES=arxiv,unreal,nvidia,gpuopen,directx,vulkan,siggraph_realtime,siggraph_research`
- `UNREAL_FEED_URL=https://www.unrealengine.com/rss`
- `NVIDIA_FEED_URL=https://developer.nvidia.com/blog/feed/`
- `GPUOPEN_FEED_URL=https://gpuopen.com/feed.xml`
- `DIRECTX_FEED_URL=https://devblogs.microsoft.com/directx/feed/`
- `VULKAN_FEED_URL=https://www.khronos.org/feeds/vulkan_news_feed`
- `SIGGRAPH_REALTIME_FEED_URL=https://blog.siggraph.org/category/realtime/feed/`
- `SIGGRAPH_RESEARCH_FEED_URL=https://blog.siggraph.org/category/research/feed/`
- `DATABASE_URL=sqlite:///./data/agent.sqlite3`
- `DRY_RUN=true`
- `MAX_ARXIV_RESULTS=80`
- `MAX_FEED_RESULTS=20`
- `RULE_FILTER_THRESHOLD=5`
- `MAX_PUSH_MUST_READ=3`
- `MAX_PUSH_READ_LATER=5`

## Dry-Run Usage

```powershell
python -m app.main run-once
```

When `DRY_RUN=true`, Telegram messages are logged but never sent. If DeepSeek is not configured, the pipeline uses a local dry-run fallback summary so the arXiv to SQLite to publish-log loop can be tested without secrets.

To test only the new high-signal official feeds:

```powershell
$env:ENABLED_SOURCES="gpuopen,directx,vulkan,siggraph_realtime,siggraph_research"
$env:DATABASE_URL="sqlite:///./data/news-feed-smoke.sqlite3"
python -m app.main run-once
```

Remove those temporary environment variables after the smoke test:

```powershell
Remove-Item Env:\ENABLED_SOURCES -ErrorAction SilentlyContinue
Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue
```

Unknown names in `ENABLED_SOURCES` fail fast so a misspelled source cannot be silently skipped.

## Tests and Linting

```powershell
pytest
ruff check .
ruff format --check .
```

Unit tests use fixtures and mocks only. They must not call arXiv, DeepSeek, or Telegram.

## Docker Desktop Validation

Docker Linux container validation is the authoritative local proof before pushing to GitHub or deploying to a VPS:

```powershell
docker compose build
docker compose run --rm graphics-agent pytest
docker compose run --rm graphics-agent python -m app.main run-once
docker compose up -d
```

The compose file treats `.env` as optional for dry-run development. Create `.env` from `.env.example` before live use.

If Docker Hub is blocked or slow, override the base image before building:

```powershell
$env:PYTHON_IMAGE="docker.m.daocloud.io/library/python:3.11-slim"
docker compose build
```

You can also place `PYTHON_IMAGE=<reachable-python-3.11-slim-image>` in `.env`.

## Optional WSL2

WSL2 can be used if available, but it is not required. Use the same Python and Docker commands from a Linux shell:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e '.[dev]'
pytest
python -m app.main run-once
```

## Deployment Outline

On a Linux VPS:

```bash
git clone git@github.com:<your-user>/graphics-research-agent.git
cd graphics-research-agent
cp .env.example .env
nano .env
docker compose build
docker compose up -d
docker compose logs -f graphics-agent
```

Set `APP_ENV=production`, `DRY_RUN=false`, and real DeepSeek/Telegram credentials only when you are ready to send live messages.

## Live API Smoke Tests

Create placeholder configuration first:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` and keep placeholders until you are ready:

```text
DEEPSEEK_API_KEY=replace_me
TELEGRAM_BOT_TOKEN=replace_me
TELEGRAM_CHAT_ID=replace_me
DRY_RUN=true
```

After replacing placeholders with real values, test DeepSeek without sending Telegram:

```powershell
.\.venv\Scripts\python.exe -m app.main run-once
```

Only after inspecting dry-run logs, set `DRY_RUN=false` and run the same command to send Telegram messages.

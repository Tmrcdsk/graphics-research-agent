# Troubleshooting

## arXiv Fetch Failure

Check network access from the host or container:

```powershell
python -m app.main run-once
docker compose run --rm graphics-agent python -m app.main run-once
```

The scheduler should log the failure and continue running.

## DeepSeek API Failure

Verify:

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`
- outbound network access from Docker

Invalid JSON or schema failures are retried once. Unvalidated output is never published.

## JSON Parse Failure

Inspect logs for schema validation messages. Do not publish raw model text. Update prompts or schemas together if required fields change.

## Telegram Send Failure

Verify:

- `DRY_RUN=false` only when live send is intended
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- bot permission to send to the target chat

Failed sends are recorded in `publish_logs` with status `failed`.

## SQLite Permission Issue

Check that `data/` exists and is writable:

```powershell
Get-ChildItem data
```

In Docker, `./data` is mounted to `/app/data`.

## Docker Volume Issue

Recreate the container after checking the local `data/` path:

```powershell
docker compose down
docker compose up -d
```

Do not delete SQLite files unless you intentionally want to reset local state.

## Docker Hub Pull Failure

If `docker compose build` fails while resolving `python:3.11-slim`, the host cannot reach Docker Hub or Docker Hub auth. The application code has not started building yet.

Use a reachable Python 3.11 slim mirror:

```powershell
$env:PYTHON_IMAGE="docker.m.daocloud.io/library/python:3.11-slim"
docker compose build
```

Or add this to `.env`:

```text
PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.11-slim
```

## Windows / Docker Desktop / WSL2 Networking

Windows native development is supported. WSL2 is optional. If WSL2 networking fails, validate with Docker Desktop from PowerShell first.

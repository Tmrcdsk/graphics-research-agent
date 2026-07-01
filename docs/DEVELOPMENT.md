# Development

## Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
Copy-Item .env.example .env
```

Use `DRY_RUN=true` during local development.

## Test Workflow

```powershell
pytest
ruff check .
ruff format --check .
python -m app.main run-once
```

Unit tests must not call real external APIs. Add fixtures or mocks for any new source, LLM client, or publisher.

## Docker Desktop Linux Validation

```powershell
docker compose build
docker compose run --rm graphics-agent pytest
docker compose run --rm graphics-agent python -m app.main run-once
```

Docker validation is more authoritative than Windows-native Python tests because production runs on Linux.

## Optional WSL2

WSL2 is optional. If used, install with:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e '.[dev]'
pytest
```

Do not block MVP work only because WSL2 is unavailable.

## Formatting

```powershell
ruff format .
ruff check .
```

The repository uses `.gitattributes` and `.editorconfig` to keep Linux-safe LF line endings.

## Adding a Source

1. Add a module under `app/sources`.
2. Return `PaperItem` objects.
3. Add fixture files under `tests/fixtures`.
4. Add tests that do not call the real network.
5. Update `docs/ARCHITECTURE.md`, `CURRENT_STATUS.md`, and `CHANGELOG.md`.

Official website feeds should use `NewsFeedSource` with fixture tests. Do not add RSSHub or scraping-only sources unless the project scope changes.

## Adding a Publisher

1. Keep `DRY_RUN=true` behavior.
2. Read all secrets from environment variables.
3. Redact secrets from logs.
4. Record publish attempts in `publish_logs`.
5. Add mocked tests.
6. Update docs and status files.

# Graphics Research Agent MVP Specification

## 0. Purpose

Build a small, reliable research-tracking agent that monitors new arXiv papers related to computer graphics and rendering, filters them for relevance to real-time rendering / game engine learning, summarizes selected items with DeepSeek V4 Flash, and pushes concise Chinese summaries to Telegram.

This document is intended to be given directly to Codex as the project development specification.

The project may be developed on native Windows or WSL2. The current recommended workflow is native Windows development with PowerShell and Docker Desktop, followed by Linux-container validation with Docker Compose. After tests pass in the Docker Linux container, the project should be pushed to GitHub and then deployed on a VPS with Docker Compose.

---

## 1. Non-negotiable Design Goals

1. Keep the first version small and maintainable.
2. Prioritize signal quality over coverage.
3. Avoid information overload.
4. Never hard-code secrets.
5. Every external call must have timeout, retry, and error handling.
6. Every publisher must support dry-run mode.
7. The system must avoid duplicate pushes.
8. Codex must maintain project documentation continuously.
9. The project must be testable without real external network calls.
10. The runtime service should be ordinary Python code, not Codex itself.

---

## 2. MVP Scope

### 2.1 Included in MVP

- arXiv paper fetching
- Basic rule-based filtering
- DeepSeek V4 Flash classification and summarization
- SQLite persistence
- Telegram push notifications
- Docker Compose runtime
- Windows-native development workflow with Docker Linux container validation
- Dry-run mode
- Unit tests with mocked external APIs
- Documentation files for AI-assisted development

### 2.2 Not Included in MVP

Do not implement these in the first version:

- X / Twitter crawling
- RSSHub
- Reddit monitoring
- Feishu / Lark push
- QQ / Koishi bridge
- PDF full-text parsing
- GitHub repository discovery
- Semantic Scholar metadata enrichment
- Web dashboard
- Multi-user subscription system
- Vector database / embeddings

These can be added later after the arXiv + Telegram MVP is stable.

---

## 3. Target User Profile

The summaries should be optimized for a user who is learning and building toward:

- game engine / rendering engineering
- real-time rendering
- Vulkan
- Unreal Engine rendering pipeline
- ReSTIR / reservoir-based sampling
- ray tracing / path tracing
- global illumination
- denoising / reconstruction
- GPU rendering systems
- shader and material systems

The system should avoid pushing low-relevance papers from areas such as:

- medical imaging
- remote sensing
- pure 3D vision without rendering relevance
- generic LLM papers
- OCR / document processing
- protein / biology / chemistry
- unrelated robotics perception

---

## 4. High-Level Architecture

```text
arXiv
  |
  v
arxiv_source
  |
  v
normalizer
  |
  v
SQLite deduplication
  |
  v
rule_filter
  |
  v
DeepSeek classifier + summarizer
  |
  v
summary cache
  |
  v
Telegram publisher
```

Codex is used to develop, test, review, and maintain this project. Codex is not the production runtime.

---

## 5. Technology Stack

### 5.1 Language and Runtime

- Python 3.11+
- Native Windows development with PowerShell and Docker Desktop
- WSL2 is optional, not mandatory
- Docker Compose for Linux-container validation and VPS deployment

### 5.2 Core Dependencies

Recommended dependencies:

```text
httpx
pydantic
pydantic-settings
sqlalchemy
feedparser
tenacity
python-dotenv
apscheduler
rich
pytest
pytest-asyncio
respx
ruff
mypy
```

Optional later dependencies:

```text
alembic
beautifulsoup4
openai
```

### 5.3 External Services

- arXiv API / Atom feed
- DeepSeek API
- Telegram Bot API

### 5.4 Development Environment Policy

The current practical development workflow is:

```text
Windows native development
  -> Docker Desktop Linux container validation
  -> GitHub
  -> Linux VPS Docker Compose deployment
```

Rules:

1. Native Windows development is allowed and is the preferred local workflow for the current project state.
2. PowerShell should be the primary shell for local command examples.
3. WSL2 is optional, not mandatory. Do not block development only because WSL2-specific commands fail.
4. The final validation target is Linux, because production deployment will run on a Linux VPS.
5. Docker Compose validation must be treated as more authoritative than native Windows Python validation.
6. The application must not depend on Windows-only behavior.
7. Repository line endings must be controlled with `.gitattributes` and `.editorconfig` to avoid CRLF problems inside Linux containers.

---

## 6. Environment Variables

Create `.env.example` and never commit a real `.env` file.

```bash
# DeepSeek
DEEPSEEK_API_KEY=replace_me
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash

# Telegram
TELEGRAM_BOT_TOKEN=replace_me
TELEGRAM_CHAT_ID=replace_me

# Runtime
APP_ENV=development
# Local Windows and Docker default. For custom production volumes, override this in .env.
DATABASE_URL=sqlite:///./data/agent.sqlite3
DRY_RUN=true
TIMEZONE=Asia/Tokyo
LOG_LEVEL=INFO

# Pipeline
MAX_ARXIV_RESULTS=80
MAX_PUSH_MUST_READ=3
MAX_PUSH_READ_LATER=5
RULE_FILTER_THRESHOLD=5

# Scheduler
SCHEDULE_HOUR=9
SCHEDULE_MINUTE=0
```

Security requirements:

- `.env` must be listed in `.gitignore`.
- Tokens must only be read from environment variables.
- Logs must never print full tokens.
- Error messages must redact secrets.

---

## 7. Required Project Structure

Create this structure:

```text
graphics-research-agent/
|
├─ pyproject.toml
├─ Dockerfile
├─ docker-compose.yml
├─ .env.example
├─ .gitignore
├─ .gitattributes
├─ .editorconfig
├─ README.md
├─ AGENTS.md
├─ CURRENT_STATUS.md
├─ CHANGELOG.md
|
├─ docs/
│  ├─ ARCHITECTURE.md
│  ├─ DEVELOPMENT.md
│  ├─ DEPLOYMENT.md
│  ├─ SCORING.md
│  ├─ PROMPTS.md
│  └─ TROUBLESHOOTING.md
|
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ config.py
│  ├─ scheduler.py
│  ├─ logging_config.py
│  │
│  ├─ sources/
│  │  ├─ __init__.py
│  │  ├─ models.py
│  │  └─ arxiv_source.py
│  │
│  ├─ pipeline/
│  │  ├─ __init__.py
│  │  ├─ normalize.py
│  │  ├─ dedupe.py
│  │  ├─ rule_filter.py
│  │  ├─ classify.py
│  │  ├─ summarize.py
│  │  └─ run_pipeline.py
│  │
│  ├─ llm/
│  │  ├─ __init__.py
│  │  ├─ deepseek_client.py
│  │  ├─ schemas.py
│  │  └─ prompts.py
│  │
│  ├─ publishers/
│  │  ├─ __init__.py
│  │  └─ telegram.py
│  │
│  ├─ storage/
│  │  ├─ __init__.py
│  │  ├─ db.py
│  │  └─ models.py
│  │
│  └─ utils/
│     ├─ __init__.py
│     ├─ hashing.py
│     ├─ markdown_escape.py
│     └─ time.py
|
├─ tests/
│  ├─ fixtures/
│  │  ├─ arxiv_sample.xml
│  │  ├─ deepseek_classification_response.json
│  │  └─ telegram_send_response.json
│  ├─ test_arxiv_source.py
│  ├─ test_dedupe.py
│  ├─ test_rule_filter.py
│  ├─ test_deepseek_schema.py
│  ├─ test_telegram_publisher.py
│  └─ test_pipeline_dry_run.py
|
└─ data/
   └─ .gitkeep
```

---

## 8. Documentation Requirements for Codex Efficiency

The following files are mandatory and must be maintained in English.

### 8.1 AGENTS.md

Purpose: provide stable operating instructions for Codex and other AI coding agents.

`AGENTS.md` must include:

```markdown
# AGENTS.md

## Project Mission

This project tracks arXiv papers related to computer graphics and rendering, summarizes selected papers with DeepSeek, and pushes concise Chinese summaries to Telegram.

## Current MVP Scope

- arXiv source only
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
```

### 8.2 CURRENT_STATUS.md

Purpose: keep Codex oriented across long-running development sessions.

`CURRENT_STATUS.md` must include:

```markdown
# CURRENT_STATUS.md

## Project State

Status: early MVP development

## Current Goal

Build and validate the arXiv + DeepSeek + Telegram MVP.

## Implemented

- [ ] Project skeleton
- [ ] Config loading
- [ ] SQLite schema
- [ ] arXiv source
- [ ] Rule filter
- [ ] DeepSeek client
- [ ] DeepSeek schema validation
- [ ] Telegram publisher
- [ ] Dry-run pipeline
- [ ] Docker Compose runtime
- [ ] Unit tests

## Not Implemented Yet

- [ ] Scheduler
- [ ] VPS deployment
- [ ] GitHub Actions
- [ ] Feishu publisher
- [ ] Koishi bridge
- [ ] Semantic Scholar
- [ ] GitHub repository discovery

## Known Issues

- None yet.

## Important Decisions

- First push channel: Telegram.
- First runtime target: VPS with Docker Compose.
- First local development environment: native Windows with PowerShell and Docker Desktop. WSL2 is optional.
- Final validation target before GitHub/VPS: Docker Linux container.
- First LLM model: deepseek-v4-flash.
- First source: arXiv only.

## Next Recommended Task

Create the Python project skeleton and implement configuration loading.
```

### 8.3 CHANGELOG.md

Purpose: record implementation history in a format that is easy for humans and AI agents to scan.

Use this format:

```markdown
# CHANGELOG.md

## Unreleased

### Added

- Initial project specification.

### Changed

- None.

### Fixed

- None.

### Removed

- None.
```

Update this file after every meaningful task.

### 8.4 README.md

Purpose: help a human run the project.

Must include:

- what the project does
- MVP scope
- setup on native Windows with PowerShell and Docker Desktop
- optional WSL2 notes
- environment variables
- dry-run usage
- test command
- Docker Compose usage
- deployment outline

### 8.5 docs/ARCHITECTURE.md

Must explain:

- pipeline flow
- source interface
- item model
- storage model
- classifier / summarizer design
- publisher interface

### 8.6 docs/DEVELOPMENT.md

Must explain:

- Windows PowerShell setup
- Docker Desktop Linux-container validation
- optional WSL2 setup
- virtual environment setup
- dependency installation
- test workflow
- lint / format commands
- how to add a new source
- how to add a new publisher

### 8.7 docs/DEPLOYMENT.md

Must explain:

- Docker Compose deployment on VPS
- `.env` setup
- volume setup
- service restart
- log inspection
- update process after GitHub push

### 8.8 docs/SCORING.md

Must explain:

- keyword scoring rules
- positive keywords
- negative keywords
- LLM relevance schema
- read priority meaning

### 8.9 docs/PROMPTS.md

Must include:

- prompt versioning policy
- current DeepSeek classification prompt
- current DeepSeek summarization prompt
- JSON schema expectations
- examples of good and bad summaries

### 8.10 docs/TROUBLESHOOTING.md

Must include:

- arXiv fetch failure
- DeepSeek API failure
- JSON parse failure
- Telegram send failure
- SQLite permission issue
- Docker volume issue
- Windows / Docker Desktop / WSL2 networking issue

---

## 9. Data Models

### 9.1 Paper Item

Use a Pydantic model similar to:

```python
class PaperItem(BaseModel):
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    categories: list[str]
    published_at: datetime
    updated_at: datetime | None = None
    abs_url: str
    pdf_url: str | None = None
    title_hash: str
    raw: dict[str, Any] | None = None
```

### 9.2 DeepSeek Classification Result

```python
class ReadPriority(str, Enum):
    MUST_READ = "must_read"
    READ_LATER = "read_later"
    ARCHIVE_ONLY = "archive_only"
    SKIP = "skip"

class ClassificationResult(BaseModel):
    is_graphics_related: bool
    is_rendering_related: bool
    main_category: str
    sub_tags: list[str]
    technical_keywords: list[str]
    novelty_score: int = Field(ge=1, le=5)
    job_relevance_score: int = Field(ge=1, le=5)
    read_priority: ReadPriority
    reason: str
    uncertainty: str
```

### 9.3 Summary Result

```python
class SummaryResult(BaseModel):
    title_zh: str
    one_sentence: str
    problem: str
    method: str
    relation_to_user_goal: str
    likely_usefulness: str
    uncertainty: str
    read_priority: ReadPriority
    job_relevance_score: int = Field(ge=1, le=5)
    novelty_score: int = Field(ge=1, le=5)
```

---

## 10. SQLite Schema

MVP tables:

```sql
CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxiv_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    authors_json TEXT NOT NULL,
    abstract TEXT NOT NULL,
    categories_json TEXT NOT NULL,
    published_at TEXT NOT NULL,
    updated_at TEXT,
    abs_url TEXT NOT NULL,
    pdf_url TEXT,
    title_hash TEXT NOT NULL,
    raw_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    classification_json TEXT NOT NULL,
    summary_json TEXT NOT NULL,
    read_priority TEXT NOT NULL,
    relevance_score INTEGER,
    job_relevance_score INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (paper_id) REFERENCES papers(id)
);

CREATE TABLE IF NOT EXISTS publish_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,
    external_message_id TEXT,
    error TEXT,
    published_at TEXT NOT NULL,
    FOREIGN KEY (paper_id) REFERENCES papers(id)
);

CREATE TABLE IF NOT EXISTS source_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    fetched_count INTEGER DEFAULT 0,
    new_count INTEGER DEFAULT 0,
    candidate_count INTEGER DEFAULT 0,
    pushed_count INTEGER DEFAULT 0,
    error TEXT
);
```

---

## 11. arXiv Source Requirements

### 11.1 Categories

Initial categories:

```text
cs.GR
cs.CV
cs.LG
```

Default maximum results per run:

```text
80
```

### 11.2 Fetch Requirements

The arXiv source must:

1. Fetch recent papers by submitted date.
2. Parse Atom XML safely.
3. Extract title, authors, abstract, categories, published date, updated date, arXiv ID, abstract URL, and PDF URL.
4. Normalize whitespace in title and abstract.
5. Generate a stable `title_hash`.
6. Respect timeout and retry settings.
7. Avoid aggressive request frequency.
8. Support tests using fixture XML files.

### 11.3 Unit Test Requirements

Tests must verify:

- XML parsing
- author extraction
- category extraction
- arXiv ID extraction
- URL extraction
- title hash stability
- behavior with malformed or missing fields

---

## 12. Deduplication Requirements

A paper is considered duplicate if any of these match an existing paper:

- `arxiv_id`
- `abs_url`
- `title_hash`

Deduplication must run before DeepSeek calls to avoid wasting tokens.

---

## 13. Rule-Based Filter

The rule filter should combine title and abstract text.

### 13.1 Positive Keywords

```python
POSITIVE_KEYWORDS = {
    "rendering": 3,
    "real-time rendering": 6,
    "real time rendering": 6,
    "path tracing": 6,
    "ray tracing": 6,
    "global illumination": 6,
    "radiance cache": 6,
    "reservoir": 5,
    "restir": 8,
    "rtxdi": 7,
    "denoising": 5,
    "neural rendering": 5,
    "gaussian splatting": 4,
    "brdf": 4,
    "bsdf": 4,
    "material": 3,
    "shader": 5,
    "vulkan": 6,
    "directx": 5,
    "unreal engine": 6,
    "lumen": 5,
    "nanite": 5,
    "dlss": 5,
    "fsr": 5,
}
```

### 13.2 Negative Keywords

```python
NEGATIVE_KEYWORDS = {
    "medical": -6,
    "ct": -5,
    "mri": -5,
    "remote sensing": -5,
    "satellite": -4,
    "protein": -7,
    "language model": -4,
    "llm": -3,
    "document": -4,
    "ocr": -4,
}
```

### 13.3 Default Threshold

```text
RULE_FILTER_THRESHOLD = 5
```

Papers below the threshold should be stored but not sent to DeepSeek in the MVP.

---

## 14. DeepSeek Integration Requirements

### 14.1 Model

Default model:

```text
deepseek-v4-flash
```

The client must support:

```text
DEEPSEEK_BASE_URL
DEEPSEEK_API_KEY
DEEPSEEK_MODEL
```

### 14.2 API Style

Implement the client in an OpenAI-compatible style if possible, but keep it abstract enough that the HTTP request details can be changed later.

### 14.3 Model Availability Check

At startup, optionally call the model listing endpoint to check whether `DEEPSEEK_MODEL` appears available.

Rules:

- If this check fails in production, log a warning.
- If this check fails in dry-run, do not block startup.
- Do not fail the entire service only because the model listing endpoint is unavailable.

### 14.4 JSON Schema Validation

DeepSeek responses must be parsed and validated with Pydantic.

Rules:

1. Ask DeepSeek to output JSON only.
2. Parse the response.
3. Validate against schema.
4. If parsing or validation fails, retry once.
5. If it still fails, mark the item as `summary_failed` or skip publishing.
6. Never publish an unvalidated model response.

---

## 15. DeepSeek Prompt Requirements

### 15.1 Classification Prompt

Store the prompt in code or a prompt file with a clear prompt version.

Initial prompt version:

```text
classification_v1
```

Prompt:

```text
You are a critical technical assistant for reading computer graphics papers.

User profile:
- The user is learning toward game engine / real-time rendering engineering.
- The user cares about Vulkan, Unreal Engine, ReSTIR, GPU rendering pipelines, ray tracing, path tracing, global illumination, denoising, shaders, materials, and real-time graphics systems.
- The user does not want noisy recommendations from generic AI, medical imaging, remote sensing, pure 3D vision reconstruction, OCR, or unrelated machine learning.

Task:
Given the paper metadata below, decide whether this paper should be pushed to the user.

Paper title:
{title}

Authors:
{authors}

arXiv categories:
{categories}

Abstract:
{abstract}

Return JSON only. Do not wrap the JSON in Markdown.

Required JSON fields:
{
  "is_graphics_related": boolean,
  "is_rendering_related": boolean,
  "main_category": string,
  "sub_tags": string[],
  "technical_keywords": string[],
  "novelty_score": integer from 1 to 5,
  "job_relevance_score": integer from 1 to 5,
  "read_priority": "must_read" | "read_later" | "archive_only" | "skip",
  "reason": string,
  "uncertainty": string
}

Be conservative. Do not overpraise. If the paper is only weakly related to rendering, choose archive_only or skip.
```

### 15.2 Summarization Prompt

Initial prompt version:

```text
summary_v1
```

Prompt:

```text
You are a critical technical assistant summarizing computer graphics and rendering papers for a Chinese-speaking learner.

The user is learning toward game engine / real-time rendering engineering and cares about Vulkan, UE rendering, ReSTIR, GPU rendering pipelines, ray tracing, path tracing, global illumination, denoising, shaders, and materials.

Summarize the paper based only on the provided title and abstract. Do not claim that the paper has code, benchmarks, or production usability unless it is explicitly stated in the metadata.

Paper title:
{title}

Authors:
{authors}

arXiv categories:
{categories}

Abstract:
{abstract}

Classification result:
{classification_json}

Return JSON only. Do not wrap the JSON in Markdown.

Required JSON fields:
{
  "title_zh": string,
  "one_sentence": string,
  "problem": string,
  "method": string,
  "relation_to_user_goal": string,
  "likely_usefulness": string,
  "uncertainty": string,
  "read_priority": "must_read" | "read_later" | "archive_only" | "skip",
  "job_relevance_score": integer from 1 to 5,
  "novelty_score": integer from 1 to 5
}

Write the content in Chinese, but keep technical terms such as ReSTIR, path tracing, BRDF, Vulkan, UE, shader, and GPU in English when appropriate.

Avoid marketing language. Be precise and conservative.
```

---

## 16. Telegram Publisher Requirements

### 16.1 Basic Behavior

Use Telegram Bot API `sendMessage`.

The publisher must:

1. Read token and chat ID from environment variables.
2. Support dry-run mode.
3. Escape Markdown or HTML special characters.
4. Split messages if they exceed Telegram message length limits.
5. Log send success and failure.
6. Never print the full bot token.
7. Record each successful push in `publish_logs`.

### 16.2 Message Format

Initial message format:

```text
🎯 Graphics Research

[Must Read] {title}

一句话：
{one_sentence}

问题：
{problem}

方法：
{method}

为什么推给你：
{relation_to_user_goal}

可能价值：
{likely_usefulness}

不确定点：
{uncertainty}

标签：
{sub_tags}

相关度：
岗位相关度：{job_relevance_score}/5
新颖度：{novelty_score}/5

链接：
arXiv: {abs_url}
PDF: {pdf_url}
```

### 16.3 Push Limits

Default per run:

```text
must_read: at most 3
read_later: at most 5
archive_only: never pushed
skip: never pushed
```

---

## 17. Pipeline Behavior

Implement `run_once()` with the following logic:

```python
async def run_once() -> None:
    # 1. Create source run record.
    # 2. Fetch recent arXiv papers.
    # 3. Normalize to PaperItem.
    # 4. Insert new papers into SQLite.
    # 5. Skip duplicates.
    # 6. Apply rule-based filter.
    # 7. Send candidates to DeepSeek classification.
    # 8. Summarize only items with read_priority must_read or read_later.
    # 9. Save validated summaries.
    # 10. Select top items within push limits.
    # 11. Send to Telegram unless DRY_RUN=true.
    # 12. Write publish logs.
    # 13. Finish source run record.
```

Selection ranking:

```text
1. read_priority: must_read before read_later
2. job_relevance_score: high to low
3. novelty_score: high to low
4. published_at: new to old
```

---

## 18. Scheduler Requirements

MVP should support both:

```bash
python -m app.main run-once
python -m app.main serve
```

`run-once`:

- run the pipeline once
- useful for local dry-run testing and manual VPS debugging

`serve`:

- start scheduler
- run every day at configured time
- default timezone: Asia/Tokyo

Default schedule:

```text
09:00 Asia/Tokyo every day
```

---

## 19. Windows Native + Docker Linux Development Workflow

The preferred local workflow is:

```text
Windows native Codex / VS Code / PowerShell
  -> local quick tests
  -> Docker Desktop Linux-container verification
  -> GitHub
  -> Linux VPS Docker Compose deployment
```

WSL2 is still acceptable as an optional development environment, but it is no longer required.

### 19.1 Initial Setup on Windows PowerShell

Create or enter the repository directory:

```powershell
mkdir D:\Projects
git init D:\Projects\graphics-research-agent
cd D:\Projects\graphics-research-agent
```

Create Python environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
```

Install project:

```powershell
pip install -e ".[dev]"
```

Create local environment file:

```powershell
Copy-Item .env.example .env
```

Set in `.env`:

```bash
DRY_RUN=true
```

### 19.2 Local Windows Commands

```powershell
ruff check .
ruff format .
pytest
python -m app.main run-once
```

Windows-native Python commands are useful for fast feedback, but they are not the final deployment proof.

### 19.3 Docker Linux Container Validation

These commands are the authoritative local verification step before pushing to GitHub or deploying to the VPS:

```powershell
docker compose build
docker compose run --rm graphics-agent pytest
docker compose run --rm graphics-agent python -m app.main run-once
docker compose up -d
```

The project should work in Docker Linux containers even if it is edited on native Windows.

### 19.4 Optional WSL2 Commands

If WSL2 is available and working, these commands may also be used:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e '.[dev]'
pytest
python -m app.main run-once
```

WSL2 failures should not block progress if Windows-native development and Docker validation are working.

### 19.5 Required Line Ending Files

Add `.gitattributes`:

```gitattributes
* text=auto eol=lf

*.bat text eol=crlf
*.cmd text eol=crlf
*.ps1 text eol=crlf
```

Add `.editorconfig`:

```editorconfig
root = true

[*]
end_of_line = lf
insert_final_newline = true
charset = utf-8
indent_style = space
indent_size = 4

[*.{bat,cmd,ps1}]
end_of_line = crlf
```

These files reduce the risk of CRLF-related failures when code edited on Windows runs inside Linux containers.

### 19.6 Local Git Workflow

```powershell
git status
git add .
git commit -m "Initial arXiv Telegram MVP"
```
---

## 20. GitHub Workflow

After local tests pass:

```bash
git remote add origin git@github.com:<your-user>/graphics-research-agent.git
git branch -M main
git push -u origin main
```

Do not push:

- `.env`
- database files
- local logs
- Python cache files
- virtual environment directories

Recommended `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.mypy_cache/
data/*.sqlite3
data/*.db
logs/
.DS_Store
Thumbs.db
.vscode/
.idea/
```

---

## 21. VPS Deployment Workflow

### 21.1 On VPS

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
```

Clone repository:

```bash
mkdir -p ~/services
cd ~/services
git clone git@github.com:<your-user>/graphics-research-agent.git
cd graphics-research-agent
```

Create `.env`:

```bash
cp .env.example .env
nano .env
```

Set:

```bash
DRY_RUN=false
APP_ENV=production
```

Start service:

```bash
docker compose build
docker compose up -d
```

Inspect logs:

```bash
docker compose logs -f graphics-agent
```

Run once manually:

```bash
docker compose run --rm graphics-agent python -m app.main run-once
```

### 21.2 Update After GitHub Push

```bash
cd ~/services/graphics-research-agent
git pull
docker compose build
docker compose up -d
```

---

## 22. Docker Compose Requirements

`docker-compose.yml`:

```yaml
services:
  graphics-agent:
    build: .
    container_name: graphics-research-agent
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    command: ["python", "-m", "app.main", "serve"]
```

`Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY README.md ./
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir .

COPY app ./app

CMD ["python", "-m", "app.main", "serve"]
```

If the package layout requires it, adjust the Dockerfile accordingly, but keep the image simple.

---

## 23. Testing Requirements

Unit tests must not call real external APIs.

Test coverage must include:

1. arXiv XML parsing
2. malformed arXiv response handling
3. deduplication by arXiv ID
4. deduplication by title hash
5. rule filter scoring
6. DeepSeek schema validation
7. DeepSeek invalid JSON fallback
8. Telegram message rendering
9. Telegram dry-run mode
10. end-to-end dry-run pipeline with fixtures

Run locally:

```bash
pytest
ruff check .
ruff format --check .
```

Run final Docker Linux-container validation:

```bash
docker compose build
docker compose run --rm graphics-agent pytest
docker compose run --rm graphics-agent python -m app.main run-once
```

Optional:

```bash
mypy app
```

---

## 24. Error Handling Requirements

### 24.1 arXiv Failure

- log error
- finish source run as failed
- do not crash scheduler permanently

### 24.2 DeepSeek Failure

- retry request
- retry JSON parsing once if necessary
- if still failed, skip publishing that paper
- store error state if storage model supports it

### 24.3 Telegram Failure

- log send failure
- write failed publish log
- do not retry indefinitely
- do not mark as successfully published unless Telegram returns success

### 24.4 SQLite Failure

- log error clearly
- check database path and volume permissions
- do not silently drop records

---

## 25. Logging Requirements

Log events:

- pipeline start
- source fetch start and finish
- fetched count
- new paper count
- candidate count
- DeepSeek classification count
- summary count
- pushed count
- dry-run messages
- external API failures
- scheduler start

Do not log:

- full API keys
- full Telegram bot token
- full `.env` content

---

## 26. Acceptance Criteria for MVP

The MVP is complete when all of these pass:

1. `pytest` passes in the local development environment.
2. `docker compose run --rm graphics-agent pytest` passes in a Docker Linux container.
3. `ruff check .` passes.
4. `python -m app.main run-once` works in dry-run mode locally.
5. arXiv fixture parsing works without network.
6. Duplicate papers are not reprocessed.
7. Papers below rule threshold are stored but not summarized.
8. DeepSeek output is validated by Pydantic.
9. Invalid DeepSeek JSON does not get published.
10. Telegram publisher works in dry-run mode without sending.
11. Real Telegram push works when `DRY_RUN=false` and valid credentials are provided.
12. Docker Compose can run the service.
13. `AGENTS.md`, `CURRENT_STATUS.md`, and `CHANGELOG.md` are present and updated.
14. README includes Windows PowerShell, Docker Desktop, optional WSL2, GitHub, and VPS instructions.
15. `.env` is not committed.

---

## 27. First Codex Task

Give this task to Codex first:

```text
Create the initial Python project skeleton for graphics-research-agent.

Goal:
Build an MVP that tracks arXiv papers related to computer graphics/rendering, filters them, summarizes selected items with DeepSeek V4 Flash, and pushes summaries to Telegram.

Development environment:
- Local development will primarily happen on native Windows using PowerShell and Docker Desktop.
- WSL2 is optional, not mandatory.
- Final validation must pass inside a Docker Linux container before pushing to GitHub.
- Later it will be deployed to a Linux VPS with Docker Compose.

Tech stack:
- Python 3.11+
- SQLite
- Docker Compose
- arXiv API / Atom parsing
- DeepSeek API, default model deepseek-v4-flash
- Telegram Bot API sendMessage
- pytest
- ruff
- pydantic
- httpx

Required files:
- pyproject.toml
- Dockerfile
- docker-compose.yml
- .env.example
- .gitignore
- .gitattributes
- .editorconfig
- README.md
- AGENTS.md
- CURRENT_STATUS.md
- CHANGELOG.md
- docs/ARCHITECTURE.md
- docs/DEVELOPMENT.md
- docs/DEPLOYMENT.md
- docs/SCORING.md
- docs/PROMPTS.md
- docs/TROUBLESHOOTING.md
- app/ package structure
- tests/ package structure

Hard requirements:
1. Do not hard-code secrets.
2. Do not commit `.env`.
3. Support DRY_RUN mode.
4. Unit tests must not call real external APIs.
5. Every external HTTP call must use timeout and retry.
6. Telegram publisher must support dry-run.
7. DeepSeek output must be validated with Pydantic schemas.
8. Invalid DeepSeek JSON must not be published.
9. Deduplicate papers before DeepSeek calls.
10. Maintain AGENTS.md, CURRENT_STATUS.md, and CHANGELOG.md in English.
11. After implementation, run tests and report changed files.
12. Final verification should prefer Docker Compose Linux-container commands over Windows-only test results.

Please implement the skeleton first, with clean interfaces and placeholder implementations where necessary. Do not overbuild features outside the MVP scope.
```

---

## 28. Second Codex Task

After the skeleton is created, give Codex this task:

```text
Implement the arXiv source and rule-based filtering.

Requirements:
1. Fetch recent arXiv papers from configured categories: cs.GR, cs.CV, cs.LG.
2. Parse Atom XML into PaperItem models.
3. Extract arxiv_id, title, authors, abstract, categories, published_at, updated_at, abs_url, pdf_url.
4. Normalize title and abstract whitespace.
5. Generate stable title_hash.
6. Implement deduplication using arxiv_id, abs_url, and title_hash.
7. Implement rule_filter with positive and negative keyword scoring from docs/SCORING.md.
8. Store new papers in SQLite.
9. Add fixture-based unit tests. Do not call the real arXiv API in unit tests.
10. Update CURRENT_STATUS.md and CHANGELOG.md.
```

---

## 29. Third Codex Task

```text
Implement DeepSeek classification and summarization.

Requirements:
1. Read DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, and DEEPSEEK_MODEL from environment variables.
2. Default model should be deepseek-v4-flash.
3. Implement classification_v1 and summary_v1 prompts.
4. Ask the model to return JSON only.
5. Validate responses with Pydantic schemas.
6. Retry once on invalid JSON or schema failure.
7. Skip publishing if validation still fails.
8. Save classification and summary JSON to SQLite.
9. Add mocked tests for valid response, invalid JSON, and schema validation failure.
10. Update docs/PROMPTS.md, CURRENT_STATUS.md, and CHANGELOG.md.
```

---

## 30. Fourth Codex Task

```text
Implement Telegram publisher and end-to-end dry-run pipeline.

Requirements:
1. Read TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from environment variables.
2. Implement sendMessage publisher.
3. Escape Markdown or HTML safely.
4. Support DRY_RUN=true, where messages are printed/logged but not sent.
5. Implement message rendering in Chinese.
6. Enforce push limits: at most 3 must_read and 5 read_later items per run.
7. Record publish_logs in SQLite.
8. Implement python -m app.main run-once.
9. Implement python -m app.main serve with scheduler.
10. Add end-to-end dry-run test using fixtures.
11. Update README.md, docs/DEPLOYMENT.md, CURRENT_STATUS.md, and CHANGELOG.md.
```

---

## 31. Quality Bar

Do not consider the project acceptable if:

- It only works with real APIs and has no fixture tests.
- It sends unvalidated model output to Telegram.
- It can repeatedly push the same paper.
- It requires editing source code to change tokens.
- It mixes source fetching, summarization, and publishing into one large script.
- It does not maintain AI-readable status documentation.
- It implements too many non-MVP features before the core pipeline works.

---

## 32. Future Extensions

After MVP stability, consider these in separate phases:

1. Feishu / Lark custom bot publisher
2. Koishi bridge for QQ
3. GitHub repository discovery
4. Semantic Scholar metadata enrichment
5. NVIDIA / AMD GPUOpen / Unreal / Unity RSS sources
6. RSSHub source
7. Feedback commands: useful, noisy, read_later, mute_keyword
8. Weekly digest
9. PDF full-text parsing for high-priority papers only
10. Web dashboard

Each extension must update:

- AGENTS.md
- CURRENT_STATUS.md
- CHANGELOG.md
- docs/ARCHITECTURE.md
- tests

---

## 33. Final Reminder for Codex

Build the smallest reliable system first.

The correct MVP is not a complete graphics news platform. The correct MVP is:

```text
arXiv + relevance filtering + DeepSeek validated summary + Telegram push + SQLite dedupe + Docker runtime
```

Focus on correctness, maintainability, and low noise.

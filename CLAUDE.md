# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

**abovesky** is a personal computer science tutor agent for a single user (the developer themselves). It exposes an OpenAI-compatible chat API that Open WebUI connects to, backed by a Python/FastAPI agent that routes to Anthropic Claude or local Ollama models. The system ingests the user's own CS textbooks (PDF + OCR), YouTube lecture videos, and syllabi — building a private RAG knowledge base and flashcard system with spaced repetition. Infrastructure runs locally in Docker (Ollama + Open WebUI + n8n).

See `.claude/prd.md` for the full product spec and phase plan.

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Runtime |
| FastAPI | HTTP server; OpenAI-compatible `/v1/chat/completions` |
| Anthropic SDK | Claude API (Sonnet for execution, Opus for ideation only) |
| pydantic-settings | Typed config from `.env` |
| SQLite | Structured storage (documents, flashcards, SRS state, assignments) |
| sqlite-vec | Vector similarity search (embedded in SQLite, no extra service) |
| Ollama | Local LLM inference + `nomic-embed-text` embeddings |
| Open WebUI | Chat interface (registers abovesky as an OpenAI-compatible model) |
| n8n | Google Calendar integration + webhook triggers |
| Docker Compose | Container orchestration |

---

## Commands

```bash
# Start only the abovesky container (other services already running)
docker compose up -d abovesky

# Rebuild after code changes
docker compose up -d --build abovesky

# View logs
docker logs abovesky -f

# Smoke test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/v1/models

# Run ingest CLI (Phase 1+)
docker exec abovesky python -m abovesky_agent.ingest --file /data/book.pdf --title "CLRS"
```

---

## Project Structure

```
abovesky_agent/              # project root
├── abovesky_agent/          # Python package
│   ├── main.py              # FastAPI app + lifespan (DB init on startup)
│   ├── config.py            # pydantic-settings; all config from .env
│   ├── db.py                # SQLite schema init + get_db() context manager
│   ├── chat.py              # /v1/models + /v1/chat/completions (streaming)
│   ├── agent.py             # Tool-use agent loop (Phase 1+, not yet built)
│   └── tools/               # One file per agent tool (Phase 1+, not yet built)
│       ├── search.py        # search_textbooks RAG tool
│       ├── ingest.py        # PDF + OCR ingestion pipeline
│       ├── youtube.py       # summarize_youtube tool
│       ├── flashcards.py    # flashcard gen + SM-2 quiz
│       ├── syllabus.py      # PDF syllabus parser
│       └── calendar.py      # n8n webhook client
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env                     # secrets — gitignored
├── .env.example
└── .claude/
    └── prd.md               # Full PRD with phase plan
```

---

## Architecture

Open WebUI sends chat requests to `http://abovesky:8000/v1/chat/completions` (OpenAI-compat). FastAPI handles it in `chat.py`, which currently forwards directly to the Anthropic API. Once the agent loop is built (`agent.py`), it will intercept the messages, decide which tools to call, run them, and stream back the final response.

**Request flow (Phase 0, current):**
```
Open WebUI → POST /v1/chat/completions → chat.py → Anthropic Sonnet → SSE stream back
```

**Request flow (Phase 1+):**
```
Open WebUI → POST /v1/chat/completions → agent.py (tool loop) → tools/* → Sonnet → SSE stream back
```

**n8n** is only involved for Google Calendar (Phase 4). abovesky posts to an n8n webhook; n8n handles OAuth and writes to Google Calendar. abovesky never holds Google tokens.

---

## Code Patterns

### Naming Conventions
- `snake_case` for all Python (files, functions, variables)
- Module-level constants in `UPPER_SNAKE_CASE` (e.g., `MODEL_ID`, `SYSTEM_PROMPT`)
- Pydantic models in `PascalCase`

### Config
- All configuration via `config.py` → `settings` singleton
- Never hardcode URLs, keys, or model names in business logic — always read from `settings`
- Default model: `claude-sonnet-4-6`. Use Opus (`claude-opus-4-7`) only when the user explicitly asks for ideation/brainstorming

### Database
- Always use `get_db()` context manager from `db.py` — never open raw connections
- Schema changes go in the `SCHEMA` string in `db.py` using `CREATE TABLE IF NOT EXISTS`
- No ORM; plain `sqlite3` with `conn.row_factory = sqlite3.Row`

### API
- Route handlers live in dedicated modules (`chat.py`, future `tools/`), registered on `router = APIRouter()`
- `main.py` only imports routers — no business logic there
- Streaming uses `StreamingResponse` with `media_type="text/event-stream"` and yields `data: ...\n\n` SSE format

### Error Handling
- Streaming generators must catch exceptions and yield an error SSE event before re-raising, so Open WebUI gets a clean stream termination instead of a torn connection (TransferEncodingError)
- API errors from Anthropic should be surfaced as readable error messages in chat, not raw stack traces

### Tools (Phase 1+)
- Each tool is a plain async function in `tools/<name>.py`
- Tool schema (for Anthropic tool use) defined alongside the function in the same file
- Tools registered in `agent.py` — `chat.py` delegates to the agent loop, not individual tools directly

---

## Key Files

| File | Purpose |
|---|---|
| `abovesky_agent/main.py` | FastAPI entrypoint; runs `init_db()` on startup |
| `abovesky_agent/config.py` | All env-var settings; import `settings` from here |
| `abovesky_agent/db.py` | SQLite schema (7 tables) + `get_db()` |
| `abovesky_agent/chat.py` | OpenAI-compat API; currently the whole agent |
| `docker-compose.yml` | `demo` network is `external: true` — other services started separately |
| `.env` | `ANTHROPIC_API_KEY` required; see `.env.example` |
| `.claude/prd.md` | Phase plan, feature specs, architecture decisions |

---

## Docker Notes

- The `demo` network is marked `external: true` because n8n/Ollama/Open WebUI were started by a separate compose project. Only `abovesky` is managed by this compose file.
- Inside Docker, Ollama is reachable at `http://ollama:11434` (Docker DNS on the `demo` network).
- The SQLite DB lives at `/data/abovesky.db` inside the container, backed by the `abovesky_data` Docker volume.
- After code changes: `docker compose up -d --build abovesky` — no need to restart other services.

---

## On-Demand Context

| Topic | File |
|---|---|
| Full PRD + phase plan | `.claude/prd.md` |
| Model routing rationale | Use Sonnet by default; Opus only on explicit user request for ideation |
| SQLite schema | `abovesky_agent/db.py` — `SCHEMA` string |

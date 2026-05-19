# abovesky — Product Requirements Document

**Version:** 0.1  
**Status:** Draft  
**Last Updated:** 2026-05-06

---

## 1. Executive Summary

abovesky is a personal computer science tutor agent built on a self-hosted AI stack. It is designed for a single user — a CS student — who wants a context-aware learning companion that understands their actual coursework: their textbooks, their lecture videos, their syllabus. Unlike generic chatbots, abovesky ingests the user's own learning materials, organizes them into a searchable knowledge base, and surfaces relevant answers with citations. It also handles the operational side of studying: parsing syllabi into calendar assignments and generating flashcard decks with spaced repetition scheduling.

The system runs primarily on local infrastructure (Ollama + Open WebUI + n8n in Docker) with a hybrid routing layer that transparently escalates to Anthropic Claude (Sonnet by default, Opus for ideation) or OpenAI when local models fall short. The result is a cost-conscious, privacy-respecting tutor that gets smarter as more materials are ingested.

**MVP goal:** A single chat interface in Open WebUI where the user can ask CS questions and receive cited answers drawn from their own ingested textbooks, generate flashcard decks, and kick off spaced repetition quizzes — all within a week of setup.

---

## 2. Mission

> **Make studying feel like a conversation with the smartest person who has read all your textbooks.**

### Core Principles

1. **Use your materials.** Answers should cite real pages from the user's actual books and videos, not synthetic knowledge.
2. **Cost-aware by default.** Route to local Ollama or Sonnet first; escalate to Opus only when ideation demands it.
3. **Simple surface, powerful backend.** One chat box in Open WebUI; all complexity lives in the Python agent.
4. **Single-user simplicity.** No auth, no multi-tenancy, no scale theater. Build for one learner, keep it fast and hackable.
5. **Phase-gated.** Deliver something working at the end of each phase; never leave the system in a broken intermediate state.

---

## 3. Target Users

### Primary Persona: The CS Student (single user)

| Attribute | Detail |
|---|---|
| Role | Computer science student |
| Technical level | High — comfortable with Docker, CLI, APIs |
| Goals | Deeply understand CS concepts; stay on top of coursework; retain knowledge long-term |
| Pain points | Textbooks are hard to search; YouTube knowledge doesn't stick; syllabi get lost; flashcard apps don't know your course |
| Usage pattern | Daily study sessions, ad-hoc Q&A, weekly quiz reviews |

**This is a single-user personal tool.** There are no other personas, no admin users, no instructors.

---

## 4. MVP Scope

### Core Functionality

| Feature | MVP | Notes |
|---|---|---|
| ✅ Chat via Open WebUI (OpenAI-compat endpoint) | In scope | Phase 0 — done |
| ✅ Textbook ingestion — digital PDFs | In scope | Phase 1 |
| ✅ Textbook ingestion — scanned PDFs (OCR) | In scope | Phase 1, Tesseract fallback |
| ✅ RAG-powered Q&A with citations | In scope | Phase 1 |
| ✅ YouTube link summarization + indexing | In scope | Phase 2 |
| ✅ Flashcard generation from topics | In scope | Phase 3 |
| ✅ Chat-based quiz with SM-2 spaced repetition | In scope | Phase 3 |
| ✅ Syllabus PDF → Google Calendar (write-only) | In scope | Phase 4 |
| ❌ Two-way Google Calendar (read + study planning) | Out of scope (Phase 5) | Deferred |
| ❌ Voice interface | Out of scope | Deferred |
| ❌ Multi-user / auth | Out of scope | Not needed |
| ❌ Custom UI beyond Open WebUI chat | Out of scope | Chat-only quiz by design |
| ❌ Auto-monitoring YouTube channels/playlists | Out of scope | Point-at-link only |
| ❌ Mobile app | Out of scope | — |

### Technical

| Item | MVP | Notes |
|---|---|---|
| ✅ FastAPI Python service (OpenAI-compat `/v1/chat/completions`) | Done | Phase 0 |
| ✅ SQLite schema (documents, chunks, flashcards, decks, srs_state, assignments, sessions) | Done | Phase 0 |
| ✅ Hybrid model routing (Ollama / Sonnet / Opus) | Partial | Config in Phase 0; routing logic per tool in Phase 1+ |
| ✅ sqlite-vec vector store | Phase 1 | No separate service |
| ✅ Tool-use agent loop (Anthropic SDK native tool use) | Phase 1 | No LangChain |
| ❌ LangChain / LangGraph | Out of scope | Too heavy for single-user |
| ❌ Separate vector DB service (Pinecone, Weaviate, etc.) | Out of scope for MVP | sqlite-vec first |

### Integration

| Item | MVP | Notes |
|---|---|---|
| ✅ Ollama (local embeddings + inference) | In scope | nomic-embed-text |
| ✅ Anthropic Claude (Sonnet default) | In scope | Execution tasks |
| ✅ Google Calendar via n8n (write-only) | Phase 4 | n8n owns OAuth |
| ❌ OpenAI Vision for OCR | Optional fallback | Tesseract preferred (free) |
| ❌ Slack / Discord | Out of scope | — |
| ❌ Notion / Obsidian export | Out of scope | — |

### Deployment

| Item | MVP |
|---|---|
| ✅ Docker Compose (local Mac/Linux) | In scope |
| ✅ Persistent volumes for DB and model data | In scope |
| ❌ Cloud deployment | Out of scope |
| ❌ CI/CD pipeline | Out of scope |

---

## 5. User Stories

### S1 — Ask a textbook question
> As a CS student, I want to ask abovesky a question about dynamic programming, so that I get an explanation that cites the exact page of my textbook where the concept is covered.

Example: "Explain memoization using the example from CLRS." → Agent calls `search_textbooks("memoization CLRS")`, returns answer with `[CLRS p.387]` citation.

### S2 — Ingest a textbook
> As a CS student, I want to drop a PDF of my textbook into a folder and have abovesky index it, so that future questions can reference its contents.

Example: Run `python -m abovesky_agent.ingest --file "CLRS_4th.pdf" --title "CLRS"`. Both digital and scanned PDFs are supported.

### S3 — Summarize a YouTube video
> As a CS student, I want to paste a YouTube link into chat and get a summary, so that the video's content becomes searchable alongside my textbooks.

Example: "Summarize this lecture: https://youtube.com/..." → transcript fetched, summary generated by Sonnet, content indexed in vector store.

### S4 — Generate flashcards
> As a CS student, I want to ask abovesky to make me 10 flashcards on graph traversal, so that I can review the topic systematically.

Example: "Make me 10 flashcards on BFS vs DFS" → agent returns a deck summary and saves cards to SQLite.

### S5 — Take a quiz
> As a CS student, I want to quiz myself on a flashcard deck in chat, so that abovesky tracks my answers and schedules reviews using spaced repetition.

Example: "Quiz me on the graph traversal deck" → agent walks through cards one by one, grades responses, updates SM-2 interval and due date per card.

### S6 — See what's due for review
> As a CS student, I want to ask "what cards are due today?", so that I stay on top of my spaced repetition schedule without opening a separate app.

### S7 — Parse a syllabus into calendar events
> As a CS student, I want to upload my course syllabus PDF and have abovesky extract all assignments and add them to my Google Calendar, so that my due dates are automatically organized.

Example: "Parse this syllabus: [attach PDF]" → agent extracts `[{title, due_date, type}]`, shows confirmation list in chat, on confirm sends to n8n webhook → Google Calendar events created.

### S8 — Look up what's due this week
> As a CS student, I want to ask "what assignments are due this week?", so that abovesky can answer from its local assignments table without needing to read my calendar.

---

## 6. Core Architecture & Patterns

### High-Level Architecture

```
Open WebUI (port 3000)
    │
    │  POST /v1/chat/completions  (OpenAI-compat)
    ▼
abovesky FastAPI (port 8000)
    │
    ├── Tool dispatcher (Anthropic SDK native tool use)
    │       ├── search_textbooks(query)      → sqlite-vec RAG
    │       ├── summarize_youtube(url)       → transcript API + Sonnet + index
    │       ├── generate_flashcards(topic,n) → Sonnet + SQLite
    │       ├── start_quiz(deck_id)          → SM-2 state machine + SQLite
    │       ├── answer_quiz(card_id,response)→ grade + SM-2 update
    │       ├── parse_syllabus(file)         → OCR/extract + Sonnet + confirm
    │       └── add_assignments(events[])    → n8n webhook → Google Calendar
    │
    ├── Model router
    │       ├── Embeddings          → Ollama (nomic-embed-text)
    │       ├── Summarization, RAG  → Ollama (llama3.1:8b) or Sonnet
    │       ├── Execution tasks     → Anthropic Sonnet (claude-sonnet-4-6)
    │       └── Ideation / hard Q&A → Anthropic Opus (claude-opus-4-7) [explicit only]
    │
    └── Storage
            ├── SQLite (abovesky.db)        → structured data
            └── sqlite-vec                  → embeddings / vector search

n8n (port 5678)
    └── Webhook receiver → Google Calendar node (OAuth managed by n8n)

Ollama (port 11434)
    ├── nomic-embed-text  (embeddings)
    └── llama3.1:8b       (local inference)
```

### Directory Structure

```
abovesky_agent/            # project root
├── abovesky_agent/        # Python package
│   ├── __init__.py
│   ├── main.py            # FastAPI app + lifespan
│   ├── config.py          # pydantic-settings (env vars)
│   ├── db.py              # SQLite init + connection context manager
│   ├── chat.py            # /v1/chat/completions + /v1/models
│   ├── agent.py           # tool-use agent loop (Phase 1+)
│   ├── tools/             # one file per tool (Phase 1+)
│   │   ├── __init__.py
│   │   ├── search.py      # search_textbooks
│   │   ├── ingest.py      # PDF + OCR pipeline
│   │   ├── youtube.py     # summarize_youtube
│   │   ├── flashcards.py  # generate + quiz + SM-2
│   │   ├── syllabus.py    # parse_syllabus + add_assignments
│   │   └── calendar.py    # n8n webhook client
│   └── ingest_cli.py      # CLI entrypoint for ingestion jobs
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env                   # secrets (gitignored)
└── .env.example
```

### Key Design Patterns

- **OpenAI-compat passthrough:** Open WebUI treats abovesky as a model, not a plugin. This gives full chat UI for free with zero Open WebUI customization.
- **Native Anthropic tool use:** Define tools as JSON schemas; let the SDK handle the agentic loop. No orchestration framework needed for a single-user tool.
- **Ingest CLI separate from server:** Heavy ingestion jobs run as a one-shot CLI command, not as part of the web request. Keeps the server fast.
- **n8n for OAuth-heavy integrations:** Google Calendar OAuth is handled entirely in n8n — abovesky only fires a webhook and trusts n8n to do the write.

---

## 7. Tools / Features

### Tool: `search_textbooks(query: str, k: int = 5)`
**Purpose:** RAG lookup across all ingested documents (textbooks + YouTube summaries).  
**Operations:** Embed query via Ollama → cosine search in sqlite-vec → retrieve top-k chunks → return content + metadata (source, page).  
**Key features:** Source-tagged results (PDF vs YouTube), page number citations, configurable k.

### Tool: `summarize_youtube(url: str)`
**Purpose:** Ingest a YouTube video's transcript, summarize it, and add it to the vector store.  
**Operations:** `youtube-transcript-api` fetch → chunk transcript → Sonnet summarizes full video → embed + store chunks tagged `source_type=youtube` → return summary in chat.  
**Key features:** No YouTube API key required; content immediately searchable after ingestion.

### Tool: `generate_flashcards(topic: str, n: int)`
**Purpose:** Generate n flashcards on a topic, optionally grounded in RAG context.  
**Operations:** RAG search for topic context → Sonnet generates `[{front, back}]` list → insert into `flashcards` + `decks` tables → insert default SM-2 state into `srs_state`.  
**Key features:** Cards grounded in the user's own materials when relevant; deck persisted for future quizzes.

### Tool: `start_quiz(deck_id: int)` / `answer_quiz(card_id: int, response: str)`
**Purpose:** Drive a chat-based quiz over a flashcard deck with SM-2 spaced repetition.  
**Operations:** Fetch due cards sorted by `due_date` → present card front → user answers → Sonnet grades response (correct / partially correct / incorrect) → SM-2 update (interval, ease_factor, repetitions, next due_date).  
**SM-2 scoring:** quality 0–5 mapped to user's response quality; ease factor adjusted per-card.

### Tool: `parse_syllabus(file_path: str)`
**Purpose:** Extract assignment list from a syllabus PDF and propose calendar events.  
**Operations:** Detect digital vs scanned PDF → extract text (PyMuPDF or Tesseract) → Sonnet structured extraction → return `[{title, due_date, assignment_type}]` in chat for confirmation.  
**Key features:** Confirmation step before writing anywhere; handles scanned syllabi.

### Tool: `add_assignments(events: list[dict])`
**Purpose:** After user confirms, write assignments to Google Calendar via n8n and store locally.  
**Operations:** POST to n8n webhook with events list → n8n Google Calendar node creates events (returns `calendar_event_id`) → store in local `assignments` table.  
**Key features:** Default write-only; local copy enables "what's due this week?" without calendar read.

---

## 8. Technology Stack

### Backend

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.12 | Runtime |
| FastAPI | ≥0.111 | HTTP server + OpenAI-compat API |
| Uvicorn | ≥0.29 | ASGI server |
| Anthropic SDK | ≥0.28 | Claude API (Sonnet + Opus) |
| pydantic-settings | ≥2.2 | Env var config |
| httpx | ≥0.27 | Async HTTP client |
| PyMuPDF (`fitz`) | ≥1.24 | Digital PDF text extraction |
| pytesseract + pdf2image | latest | OCR for scanned PDFs |
| sqlite-vec | latest | Vector similarity search in SQLite |
| youtube-transcript-api | latest | YouTube transcript fetch (no API key) |

### Infrastructure

| Technology | Purpose |
|---|---|
| Docker + Docker Compose | Container orchestration |
| Ollama | Local LLM inference + embeddings |
| Open WebUI | Chat interface |
| n8n | Workflow automation + Google Calendar OAuth |
| SQLite | Structured + vector storage (single file) |

### LLM Models

| Model | Usage | Cost |
|---|---|---|
| `nomic-embed-text` (Ollama) | Embeddings | Free (local) |
| `llama3.1:8b` (Ollama) | Cheap local inference | Free (local) |
| `claude-sonnet-4-6` | Execution: RAG answers, summarization, flashcard gen, syllabus extraction | $ |
| `claude-opus-4-7` | Ideation: architecture questions, hard novel reasoning | $$$ (explicit only) |
| OpenAI Vision (optional) | OCR fallback for extremely low-quality scans | $ (optional) |

### Optional Dependencies

```
pytesseract       # OCR (requires system Tesseract install)
pdf2image         # PDF → images for OCR (requires poppler)
openai            # optional fallback / Vision API
```

---

## 9. Security & Configuration

### Environment Variables (`.env`)

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...           # optional
OLLAMA_URL=http://ollama:11434
DEFAULT_MODEL=claude-sonnet-4-6
DB_PATH=/data/abovesky.db
N8N_WEBHOOK_URL=http://n8n:5678/webhook/calendar  # Phase 4
CALENDAR_TWO_WAY=false          # Phase 5 opt-in flag
```

### Authentication

- **abovesky API:** No authentication. Single-user local tool; the port is not exposed to the internet.
- **Google Calendar:** OAuth managed entirely by n8n. abovesky never sees the token.
- **Anthropic / OpenAI:** API keys via env vars, never committed.

### Security Scope

**In scope:**
- Secrets in `.env` (gitignored)
- No hardcoded keys in code
- SQLite file stored in Docker volume (not host-mounted to a public path)

**Out of scope for MVP:**
- HTTPS / TLS (local only)
- Rate limiting
- Input sanitization beyond Pydantic validation

---

## 10. API Specification

### `GET /health`
Returns service status.
```json
{"status": "ok"}
```

### `GET /v1/models`
OpenAI-compatible model list.
```json
{
  "object": "list",
  "data": [{"id": "abovesky-tutor", "object": "model", "created": 1234567890, "owned_by": "abovesky"}]
}
```

### `POST /v1/chat/completions`
OpenAI-compatible chat completions. Supports streaming (`"stream": true`) and non-streaming.

**Request:**
```json
{
  "model": "abovesky-tutor",
  "messages": [
    {"role": "system", "content": "optional override"},
    {"role": "user", "content": "Explain memoization from CLRS"}
  ],
  "stream": true,
  "max_tokens": 4096
}
```

**Response (non-streaming):**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "abovesky-tutor",
  "choices": [{
    "index": 0,
    "message": {"role": "assistant", "content": "..."},
    "finish_reason": "stop"
  }],
  "usage": {"prompt_tokens": 120, "completion_tokens": 380, "total_tokens": 500}
}
```

**Streaming:** Server-sent events with `data: {...}\n\n` chunks in OpenAI delta format, terminated with `data: [DONE]\n\n`.

### `POST /ingest` *(Phase 1, internal CLI only)*
Triggered by CLI, not Open WebUI. Accepts file path and metadata, runs ingestion pipeline synchronously.

---

## 11. Success Criteria

### MVP Success Definition
The MVP is successful when the user can complete an end-to-end study session entirely in Open WebUI chat: ask a question and get a cited answer from their textbook, generate a flashcard deck, and quiz themselves — all without leaving the chat interface.

### Functional Requirements

| Requirement | Phase |
|---|---|
| ✅ Chat in Open WebUI routes to abovesky agent via OpenAI-compat API | 0 — done |
| ✅ SQLite schema initialized on startup with all 7 tables | 0 — done |
| ✅ Digital PDF ingested, chunked, embedded, and queryable | 1 |
| ✅ Scanned PDF ingested via OCR and queryable | 1 |
| ✅ RAG answers include source + page citation | 1 |
| ✅ YouTube URL summarized and content indexed in same vector store | 2 |
| ✅ Flashcard deck generated on topic request and saved | 3 |
| ✅ Chat quiz walks through cards, grades, updates SM-2 state | 3 |
| ✅ Syllabus PDF parsed and assignment list shown for confirmation | 4 |
| ✅ Confirmed assignments written to Google Calendar via n8n | 4 |
| ✅ "What's due this week?" answered from local assignments table | 4 |

### Quality Indicators
- Streaming responses in Open WebUI feel instant (first token < 1s for cached context)
- Ingesting a 500-page textbook completes in < 5 minutes
- RAG answers are relevant and cited; hallucinations caught by the citation requirement
- SM-2 due dates update correctly after each quiz answer

---

## 12. Implementation Phases

### Phase 0 — Foundation ✅ Complete
**Goal:** Running wire-up; chat round-trips through Open WebUI → Python → Claude.

**Deliverables:**
- ✅ FastAPI service with `/v1/chat/completions` + `/v1/models`
- ✅ OpenAI-compatible streaming + non-streaming
- ✅ Tutor system prompt baked in
- ✅ SQLite schema (7 tables) initialized on startup
- ✅ Config via pydantic-settings + `.env`
- ✅ Docker Compose integration (external `demo` network)
- ✅ Health endpoint

**Validation:** Chat in Open WebUI → Sonnet reply with CS tutor persona. ✅

---

### Phase 1 — Textbook Ingestion + RAG
**Goal:** Ask abovesky a question and get an answer citing a page from an ingested textbook.

**Deliverables:**
- ✅ `ingest_cli.py`: CLI command `python -m abovesky_agent.ingest --file <path> --title <name>`
- ✅ PDF type detection (digital vs scanned via text-layer probe)
- ✅ Digital PDF → PyMuPDF text extraction → chunk (512 tokens, 50-token overlap)
- ✅ Scanned PDF → pdf2image + Tesseract OCR → same chunking pipeline
- ✅ Chunks embedded via Ollama `nomic-embed-text` → stored in sqlite-vec
- ✅ Agent loop wired in `agent.py` using Anthropic tool use
- ✅ `search_textbooks(query, k)` tool registered and callable
- ✅ Agent prompt instructs citation format `[Title p.N]`

**Validation:** Ingest CLRS, ask "what is the master theorem?", get cited answer.

---

### Phase 2 — YouTube Summarization
**Goal:** Paste a YouTube URL in chat and get a summary; future RAG answers surface that content.

**Deliverables:**
- ✅ `tools/youtube.py`: `summarize_youtube(url)` tool
- ✅ `youtube-transcript-api` fetch with language fallback
- ✅ Long transcript → chunked → Sonnet summarizes full video
- ✅ Chunks embedded and stored with `source_type=youtube` + source URL tag
- ✅ Tool registered in agent loop

**Validation:** "Summarize: <MIT 6.006 lecture URL>" → summary returned. Follow-up RAG question surfaces that content.

---

### Phase 3 — Flashcards + Chat Quiz
**Goal:** Generate flashcard decks and quiz in chat with spaced repetition tracking.

**Deliverables:**
- ✅ `tools/flashcards.py`: `generate_flashcards(topic, n)`, `start_quiz(deck_id)`, `answer_quiz(card_id, response)`
- ✅ Flashcard generation optionally grounded in RAG context
- ✅ SM-2 algorithm (~30 lines): quality 0–5 → interval + ease_factor update
- ✅ `srs_state` table updated after every answer
- ✅ "What cards are due today?" query against `srs_state.due_date`
- ✅ All tools registered in agent loop

**Validation:** "Make 10 cards on hash tables" → "quiz me" → 10 Q&A turns → `srs_state` updated with next due dates.

---

### Phase 4 — Syllabus → Google Calendar
**Goal:** Drop a syllabus PDF, confirm the extracted assignments, see them in Google Calendar.

**Deliverables:**
- ✅ `tools/syllabus.py`: `parse_syllabus(file_path)` + `add_assignments(events)`
- ✅ PDF ingestion (digital + OCR same pipeline as Phase 1)
- ✅ Sonnet structured extraction: `[{title, due_date, assignment_type}]`
- ✅ Confirmation step in chat before writing
- ✅ n8n webhook configured: POST `[events]` → Google Calendar node → event IDs returned
- ✅ Assignments stored in local `assignments` table
- ✅ "What's due this week?" answered from local table (no calendar read)

**Validation:** Upload syllabus PDF → see proposed event list → confirm → events appear in Google Calendar.

---

### Phase 5 — Two-Way Calendar (Deferred)
**Goal:** abovesky reads the user's existing calendar to plan study blocks around classes.

**Deliverables:**
- ❌ `CALENDAR_TWO_WAY=true` config flag
- ❌ `read_calendar(date_range)` tool (n8n read webhook or direct Google Calendar API)
- ❌ Study block suggestion: "plan my study time this week"

**Validation:** "When should I study for the midterm given my schedule?" → agent reads calendar and suggests open blocks.

---

## 13. Future Considerations

- **Study plan generation:** Given syllabus + calendar, generate a week-by-week study plan with RAG-grounded reading suggestions.
- **Progress tracking:** Dashboard (Streamlit or simple HTML page served from FastAPI) showing SRS streaks, cards due, ingested materials.
- **Notebook / lecture notes ingestion:** Markdown or `.txt` files ingested alongside PDFs.
- **Export flashcards to Anki:** `.apkg` export for use in the Anki mobile app.
- **Voice interface:** Whisper transcription → abovesky → TTS playback (n8n audio node or Python pipeline).
- **Course-aware context:** Tag ingested materials by course; RAG limited to materials for the course currently being studied.
- **Multi-model quiz grading:** Use a fast local model (Ollama) for grading simple factual answers; escalate to Sonnet only for nuanced concept explanations.

---

## 14. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| OCR quality is too low for scanned textbooks | Medium | High (Phase 1 feature breaks) | Test Tesseract early; add OpenAI Vision as escape hatch behind `USE_VISION_OCR=true` flag |
| sqlite-vec performance degrades at scale (10k+ chunks) | Low | Medium | Monitor query time; migration path to Chroma or pgvector is straightforward since the interface is abstracted |
| YouTube transcript not available (auto-captions off) | Medium | Low (single tool) | Return clear error in chat; suggest manual paste of transcript text |
| n8n Google Calendar OAuth token expires silently | Low | Medium | n8n handles refresh automatically; test token refresh in n8n before Phase 4 |
| Anthropic API costs grow unexpectedly | Low | Medium | Log token counts per request; add `usage` field to chat response; default to Ollama for summarization where quality is acceptable |

---

## 15. Appendix

### Key Dependencies

| Library | Purpose | Notes |
|---|---|---|
| `anthropic` | Claude API SDK | Sonnet default; Opus for ideation |
| `fastapi` | Web framework | OpenAI-compat layer |
| `pymupdf` | PDF text extraction | Digital PDFs |
| `pytesseract` | OCR | Scanned PDFs; requires system Tesseract |
| `pdf2image` | PDF → image | Required for Tesseract; requires poppler |
| `sqlite-vec` | Vector search | SQLite extension; no extra service |
| `youtube-transcript-api` | Transcript fetch | No API key needed |
| `pydantic-settings` | Config management | `.env` → typed settings |

### Related Documents
- Phase plan: in conversation history (2026-05-04 brainstorm)
- Model routing preference: `.claude/projects/memory/feedback_model_routing.md`
- Project overview: `.claude/projects/memory/project_abovesky.md`

### Repository Structure Note
The project root is `/Users/darenv/abovesky_agent/`. The Python package lives in `abovesky_agent/abovesky_agent/`. Phase 0 is complete; Phase 1 tooling goes in `abovesky_agent/tools/`.

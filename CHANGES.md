# What was fixed

## Critical (broken or insecure)

| # | Where | Problem | Fix |
|---|-------|---------|-----|
| 1 | `retrieval/retriever.py`, `hybrid_search.py` | **RBAC leak.** BM25 searched *every* chunk, ignoring the role. An HR user asking about stocks received stock-market text (reproduced on the original code). Only the vector half was filtered. | BM25 indexes are built per permission set; the vector search filters with `$in`. Covered by tests for every role. |
| 2 | `api.py` | **No CORS.** A browser on Vercel can't call the Hugging Face API, so the UI fails with "Failed to fetch". | `CORSMiddleware`, origins configurable via `CORS_ORIGINS`. |
| 3 | `requirements.txt` | `torch --index-url …` replaces PyPI for the *whole* file, so every other package fails to install. | `--extra-index-url`; unused packages removed; version ranges added. |
| 4 | `security/guardrails.py` | Substring allow-list: `"ai"` matched "email/said", `"hr"` matched "through", yet normal questions ("Summarize the latest policy changes…") were blocked. **Two of the three example prompts in the UI were blocked.** README promised malicious-query blocking, which didn't exist. | Whole-word blocklist for malicious / prompt-injection requests; length limits; scope handled by the prompt. |
| 5 | `security/rbac.py` | Never used. `stock_market` (sent by the UI) wasn't defined, `executive` (in Streamlit) mapped to a department that doesn't exist → always zero results. | RBAC is now the single source of truth, used by retrieval; unknown roles raise an error instead of silently returning nothing. |

## Important

| # | Where | Problem | Fix |
|---|-------|---------|-----|
| 6 | `vector_search` | Embedding model + Chroma reloaded on **every request** (seconds each). | Cached; optional start-up warm-up (`RAG_WARMUP`). |
| 7 | `retriever_state.py` | PDFs loaded twice; everything built at import time. | Lazy and cached. |
| 8 | `loaders.py` | 3 of 4 PDFs extract one word per line, wasting chunks and hurting BM25. | Whitespace normalised. **Vector index must be rebuilt** (done automatically, see below). |
| 9 | `chunking.py` | Department by substring of file name. | Whole-word mapping. |
| 10 | `ingest.py` | Ran on import; every run **duplicated** all chunks in Chroma. | `build_index()` recreates the collection; `python -m app.ingestion.ingest`. |
| 11 | `api.py` | Errors returned HTTP 200 `{"error"}`; imported RAGAS (heavy, version-fragile) at start-up although unused; LLM re-created per request; no input validation. | Proper status codes, `/health`, `/roles`, request validation, cached LLM, missing-key → 503. |
| 12 | `prompt_builder.py` | "You are a financial assistant" for every department; no "not found" behaviour. | Neutral prompt, source labels, injection-aware, fixed "couldn't find" reply. |
| 13 | `Dockerfile` | Ran as root, models downloaded on first request, no `.dockerignore`. | Non-root user, models baked in, index built at image build, `$PORT` aware. |
| 14 | BM25 | Case-sensitive, punctuation-sensitive, returned zero-score junk. | Tokenizer lower-cases / strips punctuation; zero scores dropped. |
| 15 | `main.py`, `streamlit_app.py` | Logic copy-pasted 3×; Streamlit lacked the `engineering` / `stock_market` roles; ran on import. | Shared `app/pipeline.py`. |

## Frontend

| # | Problem | Fix |
|---|---------|-----|
| 16 | Hard-coded API URL | `VITE_API_URL` (+ `.env.example`), falls back to the Space. |
| 17 | "Backend online" was a hard-coded lie | Real health check (connecting / online / unreachable). |
| 18 | Example prompts were blocked by the backend | Role-specific examples taken from the real documents. |
| 19 | No timeout / cancel; cryptic "Failed to fetch" | 90 s timeout, cancel on unmount, readable messages (CORS, timeout, backend `detail`). |
| 20 | `executive` role missing (an unused amber theme already existed) | Added. |
| 21 | Sources showed text only | Shows file name + page; accepts old string format too. |
| 22 | No input limit | 2000-char limit with counter; Ctrl/Cmd+Enter submits. |
| 23 | Stale badge/labels, unused assets, package name `frontend` | Cleaned. |

## Needs your action

* **The old `chroma_db/` was not carried over.** It was built from the word-per-line text and would no longer
  match the new chunks. It is rebuilt automatically on first start (and during the Docker build).
* Set `GROQ_API_KEY` (never commit it). Optionally restrict `CORS_ORIGINS`.
* Add real authentication before real use — see *Known limitations* in README.md.

## Verified vs not verified

Verified here: 50 backend tests (real PDFs, chunking, BM25, Chroma; embeddings / cross-encoder / LLM stubbed),
frontend lint + build, and a headless-browser run of the UI against a mock API (loading, answer, sources,
error states, offline detection, mobile width).
**Not** verified (no access to Hugging Face / Groq / Docker from this sandbox): real model downloads and answer
quality, the Docker build, and the live Space. Run the Docker build once and ask a few questions per role.

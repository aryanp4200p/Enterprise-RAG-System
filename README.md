# Enterprise RAG System

Role-aware question answering over company PDFs.
One repository, two deployable parts:

```
enterprise_rag_system/
├── backend/    FastAPI + hybrid retrieval (BM25 + Chroma) + reranker + Groq LLM   -> Hugging Face Space (Docker)
└── frontend/   React + Vite UI                                                     -> Vercel
```

```
Browser (React)  --POST /ask {query, role}-->  FastAPI
                                                 │ guardrails (block malicious / prompt-injection)
                                                 │ RBAC       (role -> allowed departments)
                                                 │ BM25 + vector search, BOTH limited to those departments
                                                 │ cross-encoder rerank -> top 4 chunks
                                                 └ Groq Llama 3.3 70B answers from those chunks only
```

## Roles

| Role           | Can read                                  |
| -------------- | ----------------------------------------- |
| `finance`      | finance_report.pdf                        |
| `hr`           | hr_policy.pdf                             |
| `engineering`  | engineering_docs.pdf                      |
| `stock_market` | Stock_Market_Performance_2024.pdf         |
| `executive`    | all of the above (+ any `general` files)  |

A PDF's department comes from its **file name** (`finance_*`, `hr_*`, `engineering_*`, `stock_*`/`market_*`).
To add a document: drop the PDF into `backend/data/` with a matching name and restart (or run the ingest command).

## Run locally

**Backend** (Python 3.11+)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # put your GROQ_API_KEY in it
uvicorn api:app --reload --port 8000
```
The vector index is built automatically from `data/*.pdf` on first start
(or explicitly: `python -m app.ingestion.ingest`). Re-running it is safe.

Other entry points: `python main.py` (CLI), `streamlit run streamlit_app.py`, `python -m pytest`.

**Frontend** (Node 20+)
```bash
cd frontend
cp .env.example .env.local      # VITE_API_URL=http://localhost:8000
npm install
npm run dev
```

## API

| Method | Path      | Notes                                                                 |
| ------ | --------- | --------------------------------------------------------------------- |
| GET    | `/`       | liveness message                                                      |
| GET    | `/health` | `{"status":"ok"}`                                                     |
| GET    | `/roles`  | list of valid roles                                                   |
| POST   | `/ask`    | body `{"query": "...", "role": "hr"}`                                 |

`/ask` returns
```json
{ "query": "...", "role": "hr", "answer": "...",
  "retrieved_docs": [ { "text": "...", "source": "hr_policy.pdf", "page": 2, "department": "hr" } ] }
```
Errors use normal status codes with `{"detail": "..."}`: `400` blocked query / unknown role, `422` invalid body,
`503` `GROQ_API_KEY` missing, `500` anything else.

## Deploy

**Backend → Hugging Face Space (Docker).** Push the *contents of `backend/`* to the Space repo
(its `README.md` already carries the `sdk: docker` / `app_port: 8000` header). Add the `GROQ_API_KEY` secret.
Optional variable: `CORS_ORIGINS=https://your-app.vercel.app` (default `*`).

**Frontend → Vercel.** Import the repo, set *Root Directory* to `frontend`, add the env var
`VITE_API_URL=https://<your-space>.hf.space`.

## Known limitations

* **The role is chosen by the client and not authenticated.** RBAC is enforced correctly on the server,
  but anyone who can call the API can claim `executive`. Before real use, put real authentication
  (e.g. JWT) in front and derive the role from the token instead of the request body.
* `app/monitoring/evals.py` (RAGAS) is not wired into the API and was written for an older RAGAS API;
  re-check it against the version you install (`requirements-dev.txt`).

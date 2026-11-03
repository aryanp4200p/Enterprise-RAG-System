# Enterprise RAG System

A full-stack Retrieval-Augmented Generation (RAG) application for asking
questions about organizational PDFs, with department-aware retrieval.

## Overview

Combines **BM25 keyword search**, **Chroma vector search**,
**cross-encoder reranking**, and **Groq Llama 3.3 70B** to generate
answers from retrieved document passages.

-   **Backend:** Python + FastAPI; Docker deployment on Hugging Face
    Spaces.
-   **Frontend:** React + Vite; deployment on Vercel.

> **Security limitation:** The API accepts the role from the client.
> Although retrieval is filtered by that role, users are not
> authenticated and can submit another role, including `executive`. Do
> not rely on this demo to protect confidential data. Add authentication
> and derive roles from verified identities before production use.

## Features

-   Role-aware retrieval for Finance, HR, Engineering, Stock Market, and
    Executive users.
-   Hybrid BM25 + Chroma retrieval with department filtering on both
    paths.
-   Cross-encoder reranking; top four chunks are sent to the LLM.
-   Groq-powered answer generation using Llama 3.3 70B.
-   Query guardrails, input validation, and source details (file, page,
    department).
-   React interface with role selection, example prompts, and source
    display.
-   FastAPI, CLI, and Streamlit entry points.

## Architecture

``` text
React + Vite
    | POST /ask { query, role }
    v
FastAPI -> Guardrails -> Role validation -> Department permissions
                                      |
                         +------------+------------+
                         |                         |
                    BM25 search              Chroma search
                         |                         |
                         +------------+------------+
                                      |
                            Cross-encoder reranking
                                      |
                                Top 4 chunks
                                      |
                             Groq Llama 3.3 70B
                                      |
                              Answer + sources
```

## Tech Stack

  Area         Technologies
  ------------ ------------------------------------------
  Frontend     React, Vite
  Backend      Python, FastAPI
  Retrieval    BM25, ChromaDB
  Reranking    Cross-encoder
  LLM          Groq, Llama 3.3 70B
  Embeddings   `sentence-transformers/all-MiniLM-L6-v2`
  Deployment   Vercel, Hugging Face Spaces (Docker)

## Roles and Documents

  -------------------------------------------------------------------------
  Role                                Example documents
  ----------------------------------- -------------------------------------
  `finance`                           `finance_report.pdf`

  `hr`                                `hr_policy.pdf`

  `engineering`                       `engineering_docs.pdf`

  `stock_market`                      `Stock_Market_Performance_2024.pdf`

  `executive`                         All supported department documents
                                      and general documents
  -------------------------------------------------------------------------

Department classification is inferred from PDF filenames. Use filenames
that follow the department naming conventions.

## Run Locally

**Requirements:** Python 3.11+, Node.js 20+, npm, and a Groq API key.

### Backend (PowerShell)

``` powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Add your key to `backend/.env`:

``` env
GROQ_API_KEY=your_groq_api_key
```

Start the API:

``` powershell
uvicorn api:app --reload --port 8000
```

### Frontend (second terminal)

``` powershell
cd frontend
Copy-Item .env.example .env.local
npm install
```

Set `VITE_API_URL=http://localhost:8000` in `frontend/.env.local`, then
run:

``` powershell
npm run dev
```

Open the local URL printed by Vite.

### Rebuild the PDF index

Run from `backend/` after adding or changing PDFs:

``` bash
python -m app.ingestion.ingest
```

The Chroma index is generated from PDFs and should not be committed to
Git.

## API

Local base URL: `http://localhost:8000`

  Method   Endpoint    Purpose
  -------- ----------- -------------------------------
  GET      `/`         Liveness response
  GET      `/health`   Health status
  GET      `/roles`    Supported roles
  POST     `/ask`      Ask about permitted documents

Example request:

``` json
{
  "query": "What does the HR policy say about leave?",
  "role": "hr"
}
```

The response includes the query, role, generated answer, and retrieved
document details (`text`, `source`, `page`, `department`). Interactive
API docs: `/docs`.

## Deployment

-   **Backend:** Deploy `backend/` to a Hugging Face Space using the
    Docker SDK; add `GROQ_API_KEY` as a Space secret.
-   **Frontend:** Import the repository into Vercel and set the root
    directory to `frontend`.
-   Set Vercel's `VITE_API_URL` to your Hugging Face Space URL.
-   Set backend `CORS_ORIGINS` to the deployed frontend origin.

Use `.env.example` as the configuration template. Never commit real API
keys or put private credentials in frontend `VITE_` variables.

## Testing and Limitations

The project change notes report 50 backend tests, frontend lint/build
checks, and a headless-browser run against a mock API. Embedding,
reranker, and LLM calls were stubbed in backend tests. A complete Docker
build, live Hugging Face deployment, and live model/LLM answer quality
were not verified in that test environment.

Other limitations: - Roles are client-selected; authentication and
server-side role mapping are needed for confidential data. - The RAGAS
evaluation module is not wired into the API and may need compatibility
updates. - Initial model downloads require network access, disk space,
and memory. - PDF extraction and chunking quality affect retrieval and
answers.

## Add Documents

1.  Add an authorized PDF to `backend/data/`.
2.  Use a filename that identifies its department.
3.  Run `python -m app.ingestion.ingest` from `backend/`.
4.  Restart the backend and test with the relevant role.

Only use documents you have permission to store and publish.

## License

No license is specified. Add a `LICENSE` file to define reuse,
modification, and redistribution permissions.

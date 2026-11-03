# Enterprise RAG System

A full-stack Retrieval-Augmented Generation (RAG) application for asking
questions about organizational PDFs, with department-level retrieval
filtering.

## Overview

Enterprise RAG combines **BM25 keyword search**, **Chroma vector
search**, **cross-encoder reranking**, and **Groq Llama 3.3 70B** to
answer questions using relevant passages from uploaded PDFs.

-   **Frontend:** React + Vite, deployed on Vercel.
-   **Backend:** Python + FastAPI, deployed as a Docker Space on Hugging
    Face.

## Key Features

-   Role-based document retrieval for Finance, HR, Engineering, Stock
    Market, and Executive roles.
-   Hybrid retrieval using BM25 and ChromaDB.
-   Department filtering applied to both keyword and vector retrieval.
-   Cross-encoder reranking to select the four most relevant chunks.
-   Groq Llama 3.3 70B answer generation.
-   Query guardrails, request validation, and source references
    (filename, page, department).
-   React interface with role selection, example questions, and
    retrieved-source display.

## System Architecture

``` mermaid
flowchart TD
    A[User - React + Vite] -->|POST /ask: query and role| B[FastAPI]
    B --> C[Query Guardrails and Validation]
    C --> D[Role Validation]
    D --> E[RBAC: Role to Allowed Departments]
    E --> F[BM25 Keyword Search]
    E --> G[Chroma Vector Search]
    F --> H[Combine Retrieved Candidates]
    G --> H
    H --> I[Cross-Encoder Reranking]
    I --> J[Select Top 4 Chunks]
    J --> K[Groq - Llama 3.3 70B]
    K --> L[Answer and Source Details]
    L --> A
```

### Request flow

1.  The user selects a role and submits a question from the React
    frontend.
2.  The frontend sends the question and role to the FastAPI `/ask`
    endpoint.
3.  The backend checks the request and applies query guardrails.
4.  The role is validated and mapped to its permitted departments.
5.  BM25 and Chroma independently retrieve relevant passages within
    those permissions.
6.  The results are combined and ranked by a cross-encoder.
7.  The four highest-ranked chunks are sent to Groq for answer
    generation.
8.  The API returns the answer with retrieved source information.

## RBAC: How It Works

The system uses **Role-Based Access Control (RBAC)** to limit which
document departments are searched for a selected role.

### Role-to-department mapping

  Role             Allowed document departments
  ---------------- -------------------------------------------------
  `finance`        Finance
  `hr`             HR
  `engineering`    Engineering
  `stock_market`   Stock Market
  `executive`      All supported departments and general documents

### Retrieval-level enforcement

RBAC is applied to both retrieval methods, not just to the final answer:

-   **BM25:** Uses department-specific indexes based on the role's
    permitted departments.
-   **ChromaDB:** Applies a department metadata filter so vector search
    only considers permitted documents.
-   **Combined retrieval:** Only the permitted results proceed to
    reranking and answer generation.

**Example:** If a user selects `hr`, the backend maps that role to the
HR department. BM25 searches the HR index and Chroma searches only
documents tagged as HR. Finance or Engineering passages are excluded
from those retrieval results.

### Important security limitation

The current application receives the selected role from the client. The
backend validates the role and filters retrieval accordingly, but it
does **not authenticate the user** or verify that the user is entitled
to that role. A caller could submit `executive` instead of `hr`.

Therefore, this is role-aware retrieval for a project demo, not complete
enterprise identity security. Before using confidential data, add
authentication (for example, JWT or an identity provider) and derive the
user's role on the server from a verified identity.

## Tech Stack

  Component           Technology
  ------------------- ------------------------------------------
  Frontend            React, Vite
  Backend             Python, FastAPI
  Keyword retrieval   BM25
  Vector database     ChromaDB
  Embedding model     `sentence-transformers/all-MiniLM-L6-v2`
  Reranking           Cross-encoder
  LLM                 Groq, Llama 3.3 70B
  Deployment          Vercel, Hugging Face Spaces (Docker)

## Roles and Sample Documents

  -------------------------------------------------------------------------
  Role                                Example PDF
  ----------------------------------- -------------------------------------
  `finance`                           `finance_report.pdf`

  `hr`                                `hr_policy.pdf`

  `engineering`                       `engineering_docs.pdf`

  `stock_market`                      `Stock_Market_Performance_2024.pdf`

  `executive`                         All supported department documents
                                      and general documents
  -------------------------------------------------------------------------

Document departments are inferred from PDF filenames. Use filenames that
follow the department naming conventions.

## Run Locally

**Requirements:** Python 3.11+, Node.js 20+, npm, and a Groq API key.

### 1. Backend

In PowerShell:

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

### 2. Frontend

Open a second terminal:

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

After adding or changing PDFs, run this from `backend/`:

``` bash
python -m app.ingestion.ingest
```

The Chroma index is generated from the PDFs and should not be committed
to Git.

## API

Local base URL: `http://localhost:8000`

  Method   Endpoint    Description
  -------- ----------- ------------------------------------------------------
  GET      `/`         Liveness response
  GET      `/health`   Health status
  GET      `/roles`    Lists supported roles
  POST     `/ask`      Retrieves permitted passages and generates an answer

Example request:

``` json
{
  "query": "What does the HR policy say about leave?",
  "role": "hr"
}
```

The response includes the query, role, generated answer, and retrieved
document details (`text`, `source`, `page`, and `department`).
Interactive API documentation is available at `/docs`.

## Deployment

-   **Backend:** Deploy the contents of `backend/` to a Hugging Face
    Space using the Docker SDK. Add `GROQ_API_KEY` as a Space secret.
-   **Frontend:** Import the repository into Vercel and set the root
    directory to `frontend`.
-   Set Vercel's `VITE_API_URL` to your Hugging Face Space URL.
-   Set backend `CORS_ORIGINS` to your deployed frontend origin.

Use the `.env.example` files as templates. Never commit real API keys or
put private credentials in frontend `VITE_` variables.

## Testing and Limitations

The project change notes report 50 backend tests, frontend lint/build
checks, and a headless-browser run against a mock API. Embedding,
reranker, and LLM calls were stubbed in the backend tests. A complete
Docker build, live Hugging Face deployment, and live model/LLM answer
quality were not verified in that test environment.

Other limitations: - Client-selected roles are not authenticated; see
the RBAC security note above. - The RAGAS evaluation module is not wired
into the API request path and may need compatibility updates. - Initial
model downloads require network access, disk space, and memory. - PDF
extraction and chunking quality affect retrieval and answer quality.

## Add Documents

1.  Add an authorized PDF to `backend/data/`.
2.  Use a filename that identifies its department.
3.  Run `python -m app.ingestion.ingest` from `backend/`.
4.  Restart the backend and test with the relevant role.

Only add documents you have permission to store and publish.

## License

No license is specified. Add a `LICENSE` file if you want to define
reuse, modification, and redistribution permissions.

# Enterprise RAG System

Role-aware question answering over company PDFs, built with
Retrieval-Augmented Generation (RAG).

Enterprise RAG System is a full-stack application that lets users ask
natural-language questions about organizational documents. It combines
keyword search, semantic vector search, reranking, department-based
retrieval permissions, and an LLM-powered answer generator.

The repository contains two independently deployable applications:

-   **Backend:** FastAPI, deployed as a Docker Space on Hugging Face.
-   **Frontend:** React + Vite, deployed on Vercel.

> **Security note:** Department filtering is enforced by the backend
> retrieval pipeline, but the current API accepts the requested role
> from the client. This is a role-aware demo, not a complete
> authenticated enterprise authorization system. Anyone who can call the
> API may submit another role, including `executive`. Add authentication
> and derive roles from verified identities before using it with
> confidential documents.

------------------------------------------------------------------------

## Contents

-   [Features](#features)
-   [Architecture](#architecture)
-   [Supported roles and documents](#supported-roles-and-documents)
-   [How retrieval works](#how-retrieval-works)
-   [Repository structure](#repository-structure)
-   [Requirements](#requirements)
-   [Run locally](#run-locally)
-   [API reference](#api-reference)
-   [Deploy](#deploy)
-   [Configuration](#configuration)
-   [Tests and verification](#tests-and-verification)
-   [Known limitations](#known-limitations)
-   [Adding documents](#adding-documents)
-   [Future improvements](#future-improvements)

## Features

-   **Role-aware document retrieval:** restricts retrieval to
    departments allowed for the requested role.
-   **Hybrid search:** combines BM25 keyword search with Chroma vector
    search.
-   **Permission-aware retrieval:** both BM25 and vector retrieval are
    limited to the permitted departments.
-   **Cross-encoder reranking:** reranks retrieved passages before
    generation and selects the top four chunks for the answer context.
-   **LLM answer generation:** uses Groq with the Llama 3.3 70B model.
-   **Query guardrails:** blocks detected malicious and
    prompt-injection-style requests and applies input-length limits.
-   **PDF ingestion:** loads PDFs, extracts text, normalizes whitespace,
    chunks content, and builds the vector index.
-   **Source information:** API responses include retrieved document
    text, source filename, page, and department metadata.
-   **Web interface:** React + Vite frontend with role selection,
    example prompts, request timeout/cancellation handling, source
    display, and backend health status.
-   **Multiple entry points:** FastAPI API, command-line entry point,
    and Streamlit interface.
-   **Docker deployment:** backend is structured for Hugging Face Spaces
    using Docker.

## Architecture

``` text
                         Browser
                    React + Vite UI
                           |
                           | POST /ask
                           | { "query": "...", "role": "hr" }
                           v
                    FastAPI Backend
                           |
                           v
                       Guardrails
              (query checks and input limits)
                           |
                           v
                     Role Validation
                           |
                           v
                Department Permissions
                           |
                +----------+----------+
                |                     |
                v                     v
          BM25 Keyword Search    Chroma Vector Search
          permission-filtered    metadata-filtered
                |                     |
                +----------+----------+
                           |
                           v
                  Candidate Retrieval
                           |
                           v
                Cross-Encoder Reranking
                           |
                           v
                   Top 4 Text Chunks
                           |
                           v
                 Groq Llama 3.3 70B
                           |
                           v
                Answer + Retrieved Sources
```

The backend is responsible for query validation, role-to-department
mapping, retrieval filtering, reranking, and answer generation. The
frontend sends the query and selected role to the API and displays the
answer and source information.

## Supported roles and documents

The current sample data uses four department-specific PDF files and an
executive role.

  -------------------------------------------------------------------------
  Role                                Documents the role can retrieve
  ----------------------------------- -------------------------------------
  `finance`                           `finance_report.pdf` and finance
                                      documents

  `hr`                                `hr_policy.pdf` and HR documents

  `engineering`                       `engineering_docs.pdf` and
                                      engineering documents

  `stock_market`                      `Stock_Market_Performance_2024.pdf`
                                      and stock-market documents

  `executive`                         All supported department documents,
                                      plus documents classified as
                                      `general`
  -------------------------------------------------------------------------

Document departments are inferred from filenames. The current filename
mapping recognizes finance, HR, engineering, and stock/market naming
patterns. Use descriptive filenames that match these conventions when
adding documents.

**Important:** The role is currently supplied in the API request body.
The backend applies the corresponding retrieval filter, but it does not
authenticate the caller or prove that the caller is entitled to select
that role. See [Known limitations](#known-limitations).

## How retrieval works

### 1. PDF loading

PDF files are read from `backend/data/`. The ingestion pipeline extracts
their text and records source metadata such as filename and page.

### 2. Text normalization and chunking

Extracted text is normalized to reduce extraction artifacts, then split
into smaller passages using the configured text splitter. This makes
passages more useful for keyword and semantic retrieval.

### 3. Embeddings and Chroma

The configured embedding model is:

``` text
sentence-transformers/all-MiniLM-L6-v2
```

The generated embeddings are stored in ChromaDB with document metadata,
including the department. The vector search uses department metadata
filters.

### 4. BM25 keyword search

BM25 finds passages that contain terms relevant to the user's query. The
implementation uses department-specific indexes so keyword retrieval
follows the same department permissions as vector retrieval.

### 5. Hybrid retrieval and reranking

The system combines the keyword and vector retrieval paths, then uses a
cross-encoder reranker to order candidate passages by relevance. The top
four chunks are passed to the answer-generation step.

### 6. Answer generation

The selected context is sent to Groq using the configured Llama 3.3 70B
model. The prompt instructs the model to answer from the retrieved
context and to indicate when the available documents do not contain the
answer.

## Repository structure

``` text
Enterprise_Rag_System/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── ingestion/
│   │   ├── llm/
│   │   ├── monitoring/
│   │   ├── retrieval/
│   │   ├── security/
│   │   └── pipeline.py
│   ├── data/                  # Sample PDF documents
│   ├── tests/
│   ├── .dockerignore
│   ├── .env.example
│   ├── Dockerfile
│   ├── api.py                 # FastAPI application entry point
│   ├── main.py                # CLI entry point
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── streamlit_app.py
├── frontend/
│   ├── public/
│   ├── src/
│   ├── .env.example
│   ├── package.json
│   └── vite.config.js
├── .gitignore
├── CHANGES.md
└── README.md
```

The Chroma index is generated from the PDFs and is not intended to be
committed to the repository.

## Requirements

-   Python 3.11 or newer
-   Node.js 20 or newer
-   npm
-   A Groq API key for LLM-powered answers

The first backend startup or ingestion run may need to download
embedding and reranking model files. Allow network access and sufficient
disk space for those model files.

## Run locally

Open two terminal windows from the repository root.

### 1. Backend setup

#### Windows PowerShell

``` powershell
cd backend

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Open `backend/.env` and set your Groq API key:

``` env
GROQ_API_KEY=your_groq_api_key
```

Start the API:

``` powershell
uvicorn api:app --reload --port 8000
```

If PowerShell prevents virtual-environment activation, use the Python
executable directly:

``` powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m uvicorn api:app --reload --port 8000
```

#### macOS / Linux

``` bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements-dev.txt
cp .env.example .env
```

Add your Groq key to `backend/.env`:

``` env
GROQ_API_KEY=your_groq_api_key
```

Start the API:

``` bash
uvicorn api:app --reload --port 8000
```

### 2. Build or rebuild the document index

The index is built automatically on first startup when required. To
rebuild it explicitly, run this from the `backend/` directory with the
virtual environment active:

``` bash
python -m app.ingestion.ingest
```

The ingestion command recreates the Chroma collection from the current
PDFs rather than appending duplicate chunks. Rebuild the index after
changing or adding source PDFs.

### 3. Frontend setup

Open a second terminal.

#### Windows PowerShell

``` powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

#### macOS / Linux

``` bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

For local development, set the following in `frontend/.env.local`:

``` env
VITE_API_URL=http://localhost:8000
```

Open the local URL printed by Vite in your browser.

### Other backend entry points

From the `backend/` directory with the virtual environment active:

``` bash
python main.py
streamlit run streamlit_app.py
python -m pytest
```

These are alternative entry points; the React frontend uses the FastAPI
API.

## API reference

The API is served by FastAPI. When running locally, the base URL is:

``` text
http://localhost:8000
```

### Endpoints

  -----------------------------------------------------------------------
  Method                  Path                    Description
  ----------------------- ----------------------- -----------------------
  `GET`                   `/`                     Basic liveness message

  `GET`                   `/health`               Health status

  `GET`                   `/roles`                Lists supported roles

  `POST`                  `/ask`                  Retrieves permitted
                                                  document passages and
                                                  generates an answer
  -----------------------------------------------------------------------

### Ask request

``` http
POST /ask
Content-Type: application/json
```

``` json
{
  "query": "What does the HR policy say about leave?",
  "role": "hr"
}
```

### Example response

The response includes the original query, requested role, generated
answer, and retrieved source passages. A representative response shape
is:

``` json
{
  "query": "What does the HR policy say about leave?",
  "role": "hr",
  "answer": "The retrieved HR policy describes ...",
  "retrieved_docs": [
    {
      "text": "Relevant passage extracted from the document...",
      "source": "hr_policy.pdf",
      "page": 2,
      "department": "hr"
    }
  ]
}
```

The answer and retrieved passage content depend on the question and the
indexed PDFs.

### Error responses

The API uses HTTP status codes and FastAPI-style `detail` error
responses.

  Status   Meaning
  -------- -------------------------------------------------------
  `400`    Query blocked by guardrails or role is not recognized
  `422`    Request body failed validation
  `503`    Required `GROQ_API_KEY` configuration is missing
  `500`    Unexpected server-side error

For interactive API documentation during local development, open:

``` text
http://localhost:8000/docs
```

## Deploy

The project is deployed as two separate applications. Configure the
backend first, then point the frontend to its public URL.

### Backend: Hugging Face Spaces (Docker)

1.  Create a new Hugging Face Space and select **Docker** as the SDK.

2.  Use the contents of the repository's `backend/` directory as the
    Space repository contents. The backend README contains the Docker
    Space metadata, including `sdk: docker` and `app_port: 8000`.

3.  Configure `GROQ_API_KEY` as a Space secret. Do not put the real key
    in source code or commit it.

4.  Set `CORS_ORIGINS` to the deployed frontend origin, for example:

    ``` text
    https://your-app.vercel.app
    ```

5.  Wait for the Space image to build and the application to start.
    Check the `/health` endpoint.

The Dockerfile is configured to run the API using the container's port
configuration. The initial image build can take time because model
assets and dependencies may need to be installed or downloaded.

### Frontend: Vercel

1.  Import the GitHub repository into Vercel.

2.  Set **Root Directory** to `frontend`.

3.  Configure the build settings using the frontend's Vite project
    defaults.

4.  Add the environment variable:

    ``` env
    VITE_API_URL=https://<your-space-name>.hf.space
    ```

    Replace the example value with the actual URL of your Hugging Face
    Space.

5.  Deploy the frontend.

6.  Add the final Vercel origin to the backend's `CORS_ORIGINS` setting
    and restart/redeploy the backend if required.

### CORS configuration

For a deployed frontend, restrict `CORS_ORIGINS` to the exact trusted
frontend origin or origins. Avoid using a wildcard origin for a public
deployment unless you intentionally want any website to be able to make
browser requests to the API.

## Configuration

### Backend environment variables

  -----------------------------------------------------------------------
  Variable                            Purpose
  ----------------------------------- -----------------------------------
  `GROQ_API_KEY`                      Required API key used by the Groq
                                      LLM client

  `CORS_ORIGINS`                      Optional comma-separated list of
                                      allowed browser origins

  `RAG_WARMUP`                        Optional setting to warm up RAG
                                      components during application
                                      startup
  -----------------------------------------------------------------------

Use `backend/.env.example` as the template for local configuration. In
Hugging Face Spaces, configure secrets and variables through the Space
settings.

### Frontend environment variables

  Variable         Purpose
  ---------------- ---------------------------------
  `VITE_API_URL`   Base URL of the FastAPI backend

Use `frontend/.env.example` as the template. Vite exposes variables
prefixed with `VITE_` to browser-side code, so never place private
credentials in frontend environment variables.

## Tests and verification

The project change notes report the following checks:

-   50 backend tests covering API behavior, ingestion, retrieval, and
    security. Embedding, cross-encoder, and LLM calls are stubbed in
    these tests.
-   Frontend lint and production build.
-   A headless-browser run against a mock API covering loading, answers,
    sources, error states, offline detection, and mobile-width layout.

These checks do not establish that the live external services work in
every deployment environment. The change notes also state that the
following were not verified in that environment:

-   A complete Docker image build.
-   The live Hugging Face Space.
-   Real model downloads and live Groq answer quality.

Run the tests and build in your own environment, and verify the deployed
Space with representative questions for every role.

## Known limitations

1.  **The requested role is not authenticated.** The API accepts `role`
    from the request body. The backend applies department filtering for
    that role, but a caller can submit a different role, including
    `executive`. Do not use this as the sole protection for confidential
    company data. Add authentication (for example, JWT or an
    identity-provider integration), validate the user's identity, and
    derive the role on the server.
2.  **RAGAS evaluation is not part of the API request path.**
    `app/monitoring/evals.py` is not wired into the API and, according
    to the change notes, was written against an older RAGAS API. Check
    compatibility with the installed version before relying on it.
3.  **Model availability affects startup and first use.** Embedding and
    reranking model assets may need to be downloaded. Deployment
    environments need sufficient memory, storage, and network access.
4.  **Answers depend on indexed document quality.** Poor PDF text
    extraction, missing content, or unsuitable chunking can reduce
    retrieval quality. Review ingestion output and rebuild the index
    after document changes.

## Adding documents

1.  Place the PDF in `backend/data/`.

2.  Use a filename that identifies its department, following the naming
    patterns described in [Supported roles and
    documents](#supported-roles-and-documents).

3.  Rebuild the index from the `backend/` directory:

    ``` bash
    python -m app.ingestion.ingest
    ```

4.  Restart the backend if it is running and test retrieval with the
    relevant role.

Only add documents that you have permission to store and publish in the
repository or deployment environment. Do not commit confidential
company, employee, customer, or personal information.

## Future improvements

Potential next steps include:

-   Authentication and server-side identity-to-role mapping.
-   Conversation memory with appropriate data controls.
-   Streaming responses.
-   Expanded evaluation and monitoring integrated with the current RAGAS
    API.
-   Admin tools for document management and access-policy configuration.
-   Additional vector database options such as Qdrant or Pinecone.
-   More comprehensive deployment and integration tests.

------------------------------------------------------------------------

## License

No license is specified yet. Add a `LICENSE` file before inviting others
to reuse, modify, or redistribute this project. Without an explicit
license, normal copyright restrictions apply.

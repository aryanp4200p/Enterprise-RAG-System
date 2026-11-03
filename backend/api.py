import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import CORS_ORIGINS, MAX_QUERY_CHARS, WARMUP
from app.llm.generator import LLMNotConfiguredError
from app.pipeline import QueryBlockedError, answer_question, warm_up
from app.security.rbac import UnknownRoleError, list_roles

logger = logging.getLogger("rag.api")


@asynccontextmanager
async def lifespan(_app):
    if WARMUP:
        logger.info("Warming up models...")
        warm_up()
    yield


app = FastAPI(title="Enterprise RAG API", lifespan=lifespan)

# Without this the browser blocks the React app (a different origin) from calling /ask.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=MAX_QUERY_CHARS)
    role: str = Field(..., min_length=1, max_length=50)


@app.get("/")
def home():
    return {"message": "Enterprise RAG API Running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/roles")
def roles():
    return {"roles": list_roles()}


# A plain `def` endpoint runs in FastAPI's thread pool, so the blocking
# retrieval + LLM call does not freeze the event loop.
@app.post("/ask")
def ask_question(request: QueryRequest):
    try:
        return answer_question(request.query, request.role)
    except QueryBlockedError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except UnknownRoleError as exc:
        raise HTTPException(status_code=400, detail=f"{exc}. Valid roles: {', '.join(list_roles())}")
    except LLMNotConfiguredError as exc:
        logger.error("%s", exc)
        raise HTTPException(status_code=503, detail="The language model is not configured on the server.")
    except Exception:
        logger.exception("Unhandled error while answering a question")
        raise HTTPException(status_code=500, detail="Something went wrong while answering. Please try again.")

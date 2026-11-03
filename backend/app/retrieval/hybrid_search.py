"""BM25 (keyword) + vector (semantic) search, both restricted to the departments
the caller's role is allowed to read."""
import logging
import re
from functools import lru_cache

from langchain_chroma import Chroma

from app.config import CHROMA_DIR, RETRIEVAL_K
from app.ingestion.ingest import build_index, load_chunks
from app.retrieval.embeddings import get_embeddings

logger = logging.getLogger(__name__)

_TOKEN = re.compile(r"\w+")


def tokenize(text):
    # Lower-casing + stripping punctuation: "Revenue," must match "revenue".
    return _TOKEN.findall(text.lower())


@lru_cache(maxsize=1)
def get_chunks():
    return load_chunks()


@lru_cache(maxsize=16)
def _bm25_index(departments):
    """BM25 index built ONLY from chunks of `departments` (a sorted tuple).
    Building per-permission-set indexes means a role can never see (or even
    influence the scoring with) documents it is not allowed to read."""
    from rank_bm25 import BM25Okapi

    docs = [c for c in get_chunks() if c.metadata.get("department") in departments]
    if not docs:
        return None, []
    return BM25Okapi([tokenize(d.page_content) for d in docs]), docs


def bm25_search(query, departments, top_k=RETRIEVAL_K):
    bm25, docs = _bm25_index(tuple(sorted(departments)))
    tokens = tokenize(query)
    if bm25 is None or not tokens:
        return []
    scores = bm25.get_scores(tokens)
    ranked = sorted(zip(docs, scores), key=lambda pair: pair[1], reverse=True)
    return [doc for doc, score in ranked[:top_k] if score > 0]


@lru_cache(maxsize=1)
def get_vector_store():
    store = Chroma(persist_directory=str(CHROMA_DIR), embedding_function=get_embeddings())
    if not store.get(limit=1)["ids"]:
        logger.warning("Vector store at %s is empty - ingesting PDFs now", CHROMA_DIR)
        store = build_index()
    return store


def vector_search(query, departments, top_k=RETRIEVAL_K):
    return get_vector_store().similarity_search(
        query, k=top_k, filter={"department": {"$in": list(departments)}}
    )

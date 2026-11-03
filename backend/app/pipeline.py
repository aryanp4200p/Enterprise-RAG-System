"""The single place that implements: guardrails -> RBAC -> retrieval -> prompt -> LLM.
api.py, main.py and streamlit_app.py all call this instead of repeating the logic."""
from app.llm.generator import get_llm
from app.llm.prompt_builder import build_prompt
from app.retrieval.retriever import hybrid_retriever
from app.security.guardrails import check_query
from app.security.rbac import normalize_role


class QueryBlockedError(ValueError):
    """The guardrails rejected the query."""


def answer_question(query, role):
    query = (query or "").strip()
    role = normalize_role(role)

    allowed, reason = check_query(query)
    if not allowed:
        raise QueryBlockedError(reason)

    docs = hybrid_retriever(query, user_role=role)  # raises UnknownRoleError
    response = get_llm().invoke(build_prompt(query, docs))

    return {"query": query, "role": role, "answer": response.content, "retrieved_docs": docs}


def warm_up():
    """Load every model once so the first real request is fast."""
    from app.retrieval.hybrid_search import get_chunks, get_vector_store
    from app.retrieval.reranker import get_reranker

    get_chunks()
    get_vector_store()
    get_reranker()

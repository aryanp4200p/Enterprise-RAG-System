import pytest

from app.retrieval.hybrid_search import bm25_search, vector_search
from app.retrieval.retriever import hybrid_retriever
from app.security.rbac import UnknownRoleError, allowed_departments

ROLES = ["finance", "hr", "engineering", "stock_market", "executive"]


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize(
    "query",
    ["stock market S&P 500 performance 2024", "remote work leave policy", "vector database architecture", "revenue growth"],
)
def test_role_never_sees_other_departments(indexed, role, query):
    allowed = set(allowed_departments(role))
    results = hybrid_retriever(query, role)
    assert results
    assert {r["department"] for r in results} <= allowed


def test_bm25_is_filtered_by_department(indexed):
    # The original BM25 searched ALL chunks, so an HR user could read stock-market text.
    query = "S&P 500 stock market performance"
    everything = bm25_search(query, ["finance", "hr", "engineering", "stock_market"])
    assert any(h.metadata["department"] == "stock_market" for h in everything)  # the text exists...
    hits = bm25_search(query, ["hr"])                                           # ...but HR must not get it
    assert all(h.metadata["department"] == "hr" for h in hits)


def test_vector_search_filter_and_executive_union(indexed):
    docs = vector_search("anything", ["finance", "hr"])
    assert {d.metadata["department"] for d in docs} <= {"finance", "hr"}
    assert {r["department"] for r in hybrid_retriever("policy report revenue employee", "executive")} - {"general"}


def test_result_shape_and_dedup(indexed):
    results = hybrid_retriever("remote work policy", "hr")
    texts = [r["text"] for r in results]
    assert len(texts) == len(set(texts))
    assert all(set(r) == {"text", "source", "page", "department"} for r in results)
    assert all(r["source"] == "hr_policy.pdf" and r["page"] >= 1 for r in results)


def test_unknown_role_is_rejected(indexed):
    with pytest.raises(UnknownRoleError):
        hybrid_retriever("anything", "intern")


def test_reingest_does_not_duplicate(indexed):
    from app.ingestion.ingest import build_index, load_chunks
    from app.retrieval.hybrid_search import get_vector_store

    expected = len(load_chunks())
    build_index()
    build_index()
    get_vector_store.cache_clear()
    assert len(get_vector_store().get()["ids"]) == expected

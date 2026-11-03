from app.config import RERANK_TOP_K
from app.retrieval.hybrid_search import bm25_search, vector_search
from app.retrieval.reranker import rerank_results
from app.security.rbac import allowed_departments


def _key(text):
    return " ".join(text.split())


def hybrid_retriever(query, user_role, top_k=RERANK_TOP_K):
    """Retrieve the most relevant chunks the given role is allowed to read.

    Returns a list of dicts: {text, source, page, department}.
    Raises app.security.rbac.UnknownRoleError for an unknown role.
    """
    departments = allowed_departments(user_role)  # RBAC: raises for unknown roles

    candidates = bm25_search(query, departments) + vector_search(query, departments)

    # De-duplicate (whitespace-insensitive) while keeping order.
    unique = {}
    for doc in candidates:
        unique.setdefault(_key(doc.page_content), doc)

    best = rerank_results(query, list(unique.values()), top_k=top_k)

    results = []
    for doc in best:
        page = doc.metadata.get("page")
        results.append(
            {
                "text": _key(doc.page_content),
                "source": doc.metadata.get("source_file"),
                "page": page + 1 if isinstance(page, int) else None,  # PyPDF pages are 0-based
                "department": doc.metadata.get("department"),
            }
        )
    return results

from functools import lru_cache

from app.config import RERANKER_MODEL, RERANK_TOP_K


@lru_cache(maxsize=1)
def get_reranker():
    """Lazy-load the cross-encoder so importing this module is cheap."""
    from sentence_transformers import CrossEncoder

    return CrossEncoder(RERANKER_MODEL)


def rerank_results(query, docs, top_k=RERANK_TOP_K):
    """Re-order candidate Documents by cross-encoder relevance and keep the best top_k."""
    if not docs:
        return []  # CrossEncoder.predict([]) is not safe on an empty list

    scores = get_reranker().predict([[query, d.page_content] for d in docs])
    ranked = sorted(zip(docs, scores), key=lambda pair: float(pair[1]), reverse=True)
    return [doc for doc, _ in ranked[:top_k]]

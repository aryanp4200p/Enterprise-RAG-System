from functools import lru_cache

from app.config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_embeddings():
    """Load the embedding model once. (It used to be reloaded on every request.)"""
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

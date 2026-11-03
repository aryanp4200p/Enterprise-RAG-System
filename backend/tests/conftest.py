"""Test setup.

Real PDFs, real chunking, real BM25 and a real Chroma store are used. Only the two
things that need a model download (embeddings, cross-encoder) and the Groq LLM are
replaced by small stand-ins, so the suite runs offline in seconds.
"""
import os
import sys
import tempfile
import types

_TMP = tempfile.mkdtemp(prefix="rag_test_chroma_")
os.environ["RAG_CHROMA_DIR"] = _TMP
os.environ.setdefault("GROQ_API_KEY", "test-key")

import pytest  # noqa: E402
from langchain_core.embeddings import DeterministicFakeEmbedding  # noqa: E402


class FakeCrossEncoder:
    """Scores by word overlap with the query."""

    def __init__(self, *_a, **_k):
        pass

    def predict(self, pairs):
        out = []
        for query, text in pairs:
            q = set(query.lower().split())
            out.append(float(len(q & set(text.lower().split()))))
        return out


class FakeLLM:
    def invoke(self, prompt):
        return types.SimpleNamespace(content="FAKE ANSWER", prompt=prompt)


@pytest.fixture(scope="session", autouse=True)
def _stand_ins():
    import langchain_huggingface

    langchain_huggingface.HuggingFaceEmbeddings = lambda **_k: DeterministicFakeEmbedding(size=384)
    fake_st = types.ModuleType("sentence_transformers")
    fake_st.CrossEncoder = FakeCrossEncoder
    sys.modules["sentence_transformers"] = fake_st

    import app.llm.generator as generator

    generator.get_llm.cache_clear()
    generator.get_llm = lambda: FakeLLM()
    import app.pipeline as pipeline

    pipeline.get_llm = lambda: FakeLLM()
    yield


@pytest.fixture(scope="session")
def indexed(_stand_ins):
    from app.ingestion.ingest import build_index

    build_index()
    return True

"""Build the Chroma vector store from the PDFs in data/.

    python -m app.ingestion.ingest

Re-running is safe: the collection is rebuilt from scratch (the old script
appended every time, so each run duplicated all chunks).
"""
import logging

from langchain_chroma import Chroma

from app.config import CHROMA_DIR, DATA_DIR
from app.ingestion.chunking import chunk_documents
from app.ingestion.loaders import load_pdfs
from app.retrieval.embeddings import get_embeddings

logger = logging.getLogger(__name__)


def load_chunks(data_dir=DATA_DIR):
    return chunk_documents(load_pdfs(data_dir))


def build_index(data_dir=DATA_DIR, persist_directory=CHROMA_DIR):
    chunks = load_chunks(data_dir)
    if not chunks:
        raise RuntimeError(f"No PDF text found in {data_dir}")

    store = Chroma(persist_directory=str(persist_directory), embedding_function=get_embeddings())
    store.delete_collection()  # start clean so re-ingesting never duplicates chunks
    store = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=str(persist_directory),
    )
    logger.info("Indexed %d chunks into %s", len(chunks), persist_directory)
    return store


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_index()

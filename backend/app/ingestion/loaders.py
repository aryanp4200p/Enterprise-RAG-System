import re
from pathlib import Path

from langchain_core.documents import Document
from pypdf import PdfReader

_WHITESPACE = re.compile(r"\s+")


def clean_text(text):
    """Collapse all whitespace. Several of the sample PDFs extract with every word
    on its own line ("Engineering\\n \\nArchitecture\\n ..."), which wasted the
    chunk budget and broke BM25 phrase matching."""
    return _WHITESPACE.sub(" ", text).strip()


def load_pdfs(data_folder):
    data_folder = Path(data_folder)
    if not data_folder.is_dir():
        raise FileNotFoundError(f"Data folder not found: {data_folder}")

    all_docs = []
    for path in sorted(data_folder.glob("*.pdf")):
        reader = PdfReader(str(path))
        for page_number, page in enumerate(reader.pages):  # 0-based, like PyPDFLoader
            text = clean_text(page.extract_text() or "")
            if not text:
                continue  # blank / image-only page
            all_docs.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": str(path),
                        "source_file": path.name,
                        "page": page_number,
                        "total_pages": len(reader.pages),
                    },
                )
            )
    return all_docs

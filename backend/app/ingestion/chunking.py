import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import CHUNK_OVERLAP, CHUNK_SIZE

# A file belongs to the first department whose keyword is a whole word in its name
# (hr_policy.pdf -> hr). The old code used substring checks, so "hr" would also
# have matched names like "chroma" or "three".
_DEPARTMENT_KEYWORDS = [
    ("finance", "finance"),
    ("hr", "hr"),
    ("engineering", "engineering"),
    ("stock", "stock_market"),
    ("market", "stock_market"),
]


def department_for_file(filename):
    stem = filename.lower().rsplit(".", 1)[0]
    words = set(re.split(r"[^a-z0-9]+", stem))
    for keyword, department in _DEPARTMENT_KEYWORDS:
        if keyword in words:
            return department
    return "general"


def chunk_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(documents)
    for chunk in chunks:
        chunk.metadata["department"] = department_for_file(
            chunk.metadata.get("source_file", "")
        )
    return chunks

from app.config import DATA_DIR
from app.ingestion.chunking import chunk_documents, department_for_file
from app.ingestion.loaders import load_pdfs


def test_department_mapping_uses_whole_words():
    assert department_for_file("finance_report.pdf") == "finance"
    assert department_for_file("hr_policy.pdf") == "hr"
    assert department_for_file("engineering_docs.pdf") == "engineering"
    assert department_for_file("Stock_Market_Performance_2024.pdf") == "stock_market"
    assert department_for_file("chroma_three.pdf") == "general"  # old substring check said "hr"


def test_loader_removes_one_word_per_line_text():
    docs = load_pdfs(DATA_DIR)
    assert docs
    for d in docs:
        assert "\n" not in d.page_content
        assert "  " not in d.page_content


def test_every_chunk_has_known_department():
    chunks = chunk_documents(load_pdfs(DATA_DIR))
    assert {c.metadata["department"] for c in chunks} == {"finance", "hr", "engineering", "stock_market"}

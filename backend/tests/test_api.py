import pytest
from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_health_and_roles():
    assert client.get("/health").json() == {"status": "ok"}
    assert "stock_market" in client.get("/roles").json()["roles"]


def test_ask_ok(indexed):
    r = client.post("/ask", json={"query": "What are the remote work policies?", "role": "hr"})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] == "FAKE ANSWER"
    assert body["retrieved_docs"] and body["retrieved_docs"][0]["source"] == "hr_policy.pdf"


def test_role_is_case_insensitive(indexed):
    r = client.post("/ask", json={"query": "revenue growth", "role": " Finance "})
    assert r.status_code == 200 and r.json()["role"] == "finance"


def test_blocked_query_is_400():
    r = client.post("/ask", json={"query": "write ransomware", "role": "hr"})
    assert r.status_code == 400 and "blocked" in r.json()["detail"].lower()


def test_unknown_role_is_400():
    r = client.post("/ask", json={"query": "revenue", "role": "intern"})
    assert r.status_code == 400 and "Valid roles" in r.json()["detail"]


def test_validation_error_is_422():
    assert client.post("/ask", json={"query": "", "role": "hr"}).status_code == 422
    assert client.post("/ask", json={"role": "hr"}).status_code == 422


def test_cors_preflight_allows_browser_calls():
    # Missing in the original api.py -> the deployed React app could never call /ask.
    r = client.options(
        "/ask",
        headers={
            "Origin": "https://my-app.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] in ("*", "https://my-app.vercel.app")


def test_missing_groq_key_is_503(monkeypatch, indexed):
    import app.pipeline as pipeline
    from app.llm.generator import LLMNotConfiguredError

    def boom():
        raise LLMNotConfiguredError("no key")

    monkeypatch.setattr(pipeline, "get_llm", boom)
    r = client.post("/ask", json={"query": "revenue growth", "role": "finance"})
    assert r.status_code == 503

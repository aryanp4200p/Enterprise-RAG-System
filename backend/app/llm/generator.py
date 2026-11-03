import os
from functools import lru_cache

from dotenv import load_dotenv

from app.config import LLM_MODEL

load_dotenv()


class LLMNotConfiguredError(RuntimeError):
    """GROQ_API_KEY is missing."""


@lru_cache(maxsize=1)
def get_llm():
    from langchain_groq import ChatGroq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise LLMNotConfiguredError(
            "GROQ_API_KEY is not set. Add it to backend/.env (local) or to the "
            "Space secrets (Hugging Face)."
        )
    return ChatGroq(api_key=api_key, model=LLM_MODEL, temperature=0, max_retries=2, timeout=60)

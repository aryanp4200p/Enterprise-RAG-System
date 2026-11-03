"""Input guardrails.

The old implementation was a keyword *allow-list* using substring matching, so
"ai" matched "email"/"said" (almost everything passed) while perfectly normal
questions such as "Summarize the latest policy changes" were blocked. The README
also promises that *malicious* requests are blocked, which it never did.

This version blocks clearly malicious / prompt-injection requests using
whole-word patterns. Questions that are simply outside the documents are handled
by the prompt (the model answers that it cannot find it in the context).
"""
import re

from app.config import MAX_QUERY_CHARS

_BLOCKED_PATTERNS = [
    r"\b(malware|ransomware|keylogger|spyware|rootkit|botnet|ddos)\b",
    r"\bphishing\b",
    r"\b(hack|hacking|crack)\b.{0,40}\b(into|account|password|system|server|wifi)\b",
    r"\b(write|create|build|generate)\b.{0,30}\b(exploit|virus|trojan|worm)\b",
    r"\bignore\b.{0,30}\b(previous|prior|above|earlier|all)\b.{0,30}\b(instructions?|prompts?|rules)\b",
    r"\b(reveal|show|print|repeat)\b.{0,30}\b(system|hidden|initial)\b.{0,15}\bprompt\b",
    r"\bjailbreak\b",
]
_BLOCKED = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _BLOCKED_PATTERNS]


def check_query(query):
    """Return (allowed, reason). `reason` is None when the query is allowed."""
    if query is None or not query.strip():
        return False, "Query is empty."
    if len(query) > MAX_QUERY_CHARS:
        return False, f"Query is too long (max {MAX_QUERY_CHARS} characters)."
    for pattern in _BLOCKED:
        if pattern.search(query):
            return False, "Query blocked: it looks malicious or tries to override the assistant's instructions."
    return True, None


def is_allowed_query(query):
    return check_query(query)[0]

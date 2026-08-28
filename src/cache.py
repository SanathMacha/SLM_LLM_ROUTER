"""Thread-safe SQLite-backed caching layer for model responses."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

# Allow executing this file directly as a script without PYTHONPATH issues
if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.config import CACHE_PATH, PROMPT_VERSION


def _get_conn() -> sqlite3.Connection:
    """Initialize database directory, open connection with 30s timeout, enable WAL, and create schema."""
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CACHE_PATH), timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            cache_key TEXT PRIMARY KEY,
            model TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            cost_usd REAL,
            latency_s REAL,
            raw_response TEXT,
            parsed_answer TEXT,
            prompt_version TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    return conn


def make_cache_key(
    model: str,
    system_prompt: str,
    query: str,
    temperature: float,
    prompt_version: str
) -> str:
    """Generate a unique SHA-256 cache key for a model call configuration."""
    payload = json.dumps({
        "model": model,
        "system_prompt": system_prompt,
        "query": query,
        "temperature": temperature,
        "prompt_version": prompt_version
    }, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_cached_response(cache_key: str) -> dict | None:
    """Retrieve a cached response dictionary by its cache key, or None on miss."""
    with _get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                model, 
                prompt_tokens, 
                completion_tokens, 
                cost_usd, 
                latency_s, 
                raw_response, 
                parsed_answer, 
                prompt_version,
                created_at
            FROM responses 
            WHERE cache_key = ?
            """,
            (cache_key,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            "model": row[0],
            "prompt_tokens": row[1],
            "completion_tokens": row[2],
            "cost_usd": row[3],
            "latency_s": row[4],
            "raw_response": row[5],
            "parsed_answer": row[6],
            "prompt_version": row[7],
            "created_at": row[8]
        }


def set_cached_response(cache_key: str, data: dict) -> None:
    """Insert or replace a cached response."""
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO responses (
                cache_key,
                model,
                prompt_tokens,
                completion_tokens,
                cost_usd,
                latency_s,
                raw_response,
                parsed_answer,
                prompt_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cache_key,
                data.get("model"),
                data.get("prompt_tokens"),
                data.get("completion_tokens"),
                data.get("cost_usd"),
                data.get("latency_s"),
                data.get("raw_response"),
                data.get("parsed_answer"),
                data.get("prompt_version", PROMPT_VERSION)
            )
        )


if __name__ == "__main__":
    print("Running cache smoke tests...")
    
    # 1. Hashing test
    test_key = make_cache_key(
        model="qwen3.5:4b",
        system_prompt="Test system prompt",
        query="What is 2+2?",
        temperature=0.0,
        prompt_version=PROMPT_VERSION
    )
    print(f"Generated cache key: {test_key}")
    assert len(test_key) == 64, "Cache key should be a 64-character SHA-256 hex digest"

    # Clean potential old test record to ensure clean state
    with _get_conn() as connection:
        connection.execute("DELETE FROM responses WHERE cache_key = ?", (test_key,))

    # 2. Cache miss test
    missing = get_cached_response(test_key)
    print(f"Cache miss check: {missing}")
    assert missing is None, "Cache query for a non-existent key should return None"

    # 3. Cache write test
    dummy_data = {
        "model": "qwen3.5:4b",
        "prompt_tokens": 15,
        "completion_tokens": 5,
        "cost_usd": 0.0,
        "latency_s": 0.123,
        "raw_response": '{"answer": "4"}',
        "parsed_answer": "4",
        "prompt_version": PROMPT_VERSION
    }
    set_cached_response(test_key, dummy_data)
    print("Cached dummy response successfully.")

    # 4. Cache hit test
    hit = get_cached_response(test_key)
    print(f"Cache hit check: {hit}")
    assert hit is not None, "Cache query should return the cached response"
    assert hit["model"] == dummy_data["model"], "Model mismatch"
    assert hit["prompt_tokens"] == dummy_data["prompt_tokens"], "Prompt tokens mismatch"
    assert hit["completion_tokens"] == dummy_data["completion_tokens"], "Completion tokens mismatch"
    assert hit["cost_usd"] == dummy_data["cost_usd"], "Cost USD mismatch"
    assert hit["latency_s"] == dummy_data["latency_s"], "Latency mismatch"
    assert hit["raw_response"] == dummy_data["raw_response"], "Raw response mismatch"
    assert hit["parsed_answer"] == dummy_data["parsed_answer"], "Parsed answer mismatch"
    assert hit["prompt_version"] == dummy_data["prompt_version"], "Prompt version mismatch"
    assert hit["created_at"] is not None, "Created_at should be auto-populated"

    print("All cache smoke tests passed successfully!")

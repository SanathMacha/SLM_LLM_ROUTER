"""Central configuration for the SLM+LLM router.

Inputs: environment variables from .env (GROQ_API_KEY, optional overrides).
Outputs: model IDs, tier settings, filesystem paths, and the verifier 
         strictness grid that generates the deferral curve.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# On Windows `uv run` does not inherit the shell's environment, so this call is
# mandatory and must come before any os.getenv below.
load_dotenv()

def _force_utf8_console() -> None:
    """Stop Windows cp1252 consoles crashing on model output."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")

_force_utf8_console()

# --- Paths ---
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
QUERIES_PATH = DATA_DIR / "queries.json"
CACHE_PATH = Path(os.getenv("CACHE_DB_PATH", str(OUTPUT_DIR / "cache.sqlite")))
LEADERBOARD_PATH = OUTPUT_DIR / "leaderboard.md"
CURVE_PATH = OUTPUT_DIR / "deferral_curve.png"
RESULTS_PATH = OUTPUT_DIR / "results.json"

OUTPUT_DIR.mkdir(exist_ok=True)

# --- API Keys and Models ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# The big model. $0.15 in / $0.60 out per 1M, 131K context.
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

# SLM_PROVIDER selects the cheap tier.
# "ollama" -> local model, $0 marginal API cost.
# "groq"   -> openai/gpt-oss-20b. No local install, but only 2x cheaper.
SLM_PROVIDER = os.getenv("SLM_PROVIDER", "ollama").strip().lower()

SLM_OLLAMA_MODEL = os.getenv("SLM_OLLAMA_MODEL", "qwen3.5:4b")
SLM_GROQ_MODEL = os.getenv("SLM_GROQ_MODEL", "openai/gpt-oss-20b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST") or None

# --- Generation Settings ---
SLM_MAX_TOKENS = int(os.getenv("SLM_MAX_TOKENS", "1024"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "320"))
TEMPERATURE = 0.0

SELF_CONSISTENCY_K = int(os.getenv("SELF_CONSISTENCY_K", "3"))
SELF_CONSISTENCY_TEMP = 0.7

# --- Strictness & Routing ---
# Each level escalates on a superset of the level below, so escalation rate is
# monotonic in strictness.
# 0 never escalate                               -> the all_slm floor
# 1 escalate on empty/unparseable output
# 2 + escalate when the answer fails its item's format constraint
# 3 + escalate on hedging language
# 4 + escalate when self-consistency samples disagree
# 5 always escalate                              -> the baseline ceiling
STRICTNESS_LEVELS = [0, 1, 2, 3, 4, 5]

HEADLINE_STRICTNESS = int(os.getenv("HEADLINE_STRICTNESS", "4"))

# --- Prompts ---
ANSWER_PREFIX = "Answer:"
SYSTEM_PROMPT = (
    "You are a concise assistant. Think briefly, then give the shortest "
    "correct answer.\n"
    f"You MUST end your reply with a final line of the form '{ANSWER_PREFIX} <answer>'.\n"
    "The answer must be the bare value only - no units unless asked, no "
    "explanation, no punctuation at the end."
)

PROMPT_VERSION = "v1"

MAX_CONCURRENCY = 2
REQUEST_SPACING_S = 2.1

# --- Helpers ---
def require_keys() -> None:
    """Fail fast with an actionable message when the Groq key is missing."""
    if not GROQ_API_KEY:
        raise SystemExit(
            "GROQ_API_KEY is not set.\n"
            "Create a .env file next to pyproject.toml containing:\n"
            "    GROQ_API_KEY=gsk_...\n"
            "Get a free key at https://console.groq.com/keys"
        )

def slm_label() -> str:
    """Human-readable name of the active small tier, for tables and logs."""
    if SLM_PROVIDER == "ollama":
        return f"{SLM_OLLAMA_MODEL} (local)"
    return f"{SLM_GROQ_MODEL} (groq)"

# --- Smoke Test ---
if __name__ == "__main__":
    print(f"root           : {ROOT_DIR}")
    print(f"llm tier       : {LLM_MODEL}")
    print(f"slm tier       : {slm_label()}")
    print(f"slm provider   : {SLM_PROVIDER}")
    print(f"strictness     : {STRICTNESS_LEVELS} (headline={HEADLINE_STRICTNESS})")
    print(f"groq key       : {'set' if GROQ_API_KEY else 'MISSING'}")
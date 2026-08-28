"""Cost accounting for every model call.

Inputs: a model ID plus prompt/completion token counts.
Outputs: cost in USD.
"""

from __future__ import annotations

# USD per 1M tokens, as (input_rate, output_rate).
PRICING: dict[str, tuple[float, float]] = {
    "openai/gpt-oss-120b": (0.15, 0.60),
    "openai/gpt-oss-20b": (0.075, 0.30),
}

LOCAL_RATE = (0.0, 0.0)


def rates_for(model: str) -> tuple[float, float]:
    """Look up (input, output) USD-per-1M rates for a model."""
    if model in PRICING:
        return PRICING[model]
    
    if is_local(model):
        return LOCAL_RATE
        
    raise KeyError(
        f"No price on file for model {model!r}. "
        f"Add a row to PRICING in src/pricing.py. "
        f"Known models: {sorted(PRICING)}"
    )


def is_local(model: str) -> bool:
    """True for models served by local Ollama, which cost nothing per token."""
    return model.startswith("local:")


def calculate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Compute the real-money cost of one call from its token counts."""
    input_rate, output_rate = rates_for(model)
    return (prompt_tokens * input_rate + completion_tokens * output_rate) / 1_000_000


if __name__ == "__main__":
    # A typical routed query: ~250 prompt tokens, ~60 completion tokens.
    for model in ("openai/gpt-oss-120b", "openai/gpt-oss-20b", "local:qwen3.5:4b"):
        cost = calculate_cost_usd(model, 250, 60)
        print(f"{model:24s} {cost:.8f} USD  ({cost * 1000:.5f} USD per 1k queries)")

    try:
        calculate_cost_usd("some/unpriced-model", 1, 1)
    except KeyError as exc:
        print(f"\nunpriced model raises cleanly: {exc}")
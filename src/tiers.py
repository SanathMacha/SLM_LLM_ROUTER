"""Unified execution wrappers for local Ollama and Groq Cloud API inference with cache interception."""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Allow executing this file directly as a script without PYTHONPATH issues
if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

import groq
import ollama

from src.cache import get_cached_response, make_cache_key, set_cached_response
from src.config import (
    LLM_MODEL,
    LLM_MAX_TOKENS,
    PROMPT_VERSION,
    SELF_CONSISTENCY_TEMP,
    SLM_MAX_TOKENS,
    SLM_OLLAMA_MODEL,
    SYSTEM_PROMPT,
    TEMPERATURE,
)
from src.pricing import calculate_cost_usd


def call_slm(query: str) -> dict:
    """Invoke the local small model (Ollama) with caching. Uses temperature=0.0."""
    model_name = SLM_OLLAMA_MODEL
    cost_model_name = f"local:{model_name}"
    
    # Generate cache key for deterministic call (temp=0.0)
    cache_key = make_cache_key(
        model=model_name,
        system_prompt=SYSTEM_PROMPT,
        query=query,
        temperature=0.0,
        prompt_version=PROMPT_VERSION
    )
    
    # Check cache
    cached = get_cached_response(cache_key)
    if cached is not None:
        return {
            "answer": cached["parsed_answer"],
            "in_tok": cached["prompt_tokens"],
            "out_tok": cached["completion_tokens"],
            "cost_usd": cached["cost_usd"],
            "latency_s": cached["latency_s"],
            "server_s": cached["latency_s"],
            "model": cached["model"],
            "cached": True
        }
        
    # On cache miss, call Ollama
    start_time = time.perf_counter()
    response = ollama.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ],
        options={
            "temperature": 0.0,
            "num_predict": SLM_MAX_TOKENS
        }
    )
    latency = time.perf_counter() - start_time
    
    # Extract response content and tokens
    answer = response["message"]["content"]
    prompt_tokens = response.get("prompt_eval_count", 0)
    completion_tokens = response.get("eval_count", 0)
    
    # Total duration from ollama is in nanoseconds
    server_s = response.get("total_duration", 0) / 1e9
    if server_s == 0:
        server_s = latency

    cost_usd = calculate_cost_usd(cost_model_name, prompt_tokens, completion_tokens)
    
    # Save to cache using the cost_model_name to ensure pricing matches on reload
    cache_data = {
        "model": cost_model_name,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": cost_usd,
        "latency_s": latency,
        "raw_response": json_dump_safe(response),
        "parsed_answer": answer,
        "prompt_version": PROMPT_VERSION
    }
    set_cached_response(cache_key, cache_data)
    
    return {
        "answer": answer,
        "in_tok": prompt_tokens,
        "out_tok": completion_tokens,
        "cost_usd": cost_usd,
        "latency_s": latency,
        "server_s": server_s,
        "model": cost_model_name,
        "cached": False
    }


def call_llm(query: str) -> dict:
    """Invoke the cloud large model (Groq) with caching. Uses temperature=0.0."""
    model_name = LLM_MODEL
    
    # Generate cache key for deterministic call (temp=0.0)
    cache_key = make_cache_key(
        model=model_name,
        system_prompt=SYSTEM_PROMPT,
        query=query,
        temperature=0.0,
        prompt_version=PROMPT_VERSION
    )
    
    # Check cache
    cached = get_cached_response(cache_key)
    if cached is not None:
        return {
            "answer": cached["parsed_answer"],
            "in_tok": cached["prompt_tokens"],
            "out_tok": cached["completion_tokens"],
            "cost_usd": cached["cost_usd"],
            "latency_s": cached["latency_s"],
            "server_s": cached["latency_s"],
            "model": cached["model"],
            "cached": True
        }
        
    # On cache miss, call Groq
    start_time = time.perf_counter()
    client = groq.Groq()
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ],
        temperature=0.0,
        max_tokens=LLM_MAX_TOKENS
    )
    latency = time.perf_counter() - start_time
    
    # Extract response content and tokens
    answer = response.choices[0].message.content
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    
    # Groq API doesn't provide total server duration directly in a standard field, so we use latency
    server_s = latency
    cost_usd = calculate_cost_usd(model_name, prompt_tokens, completion_tokens)
    
    # Serialize response helper
    raw_response_str = ""
    try:
        raw_response_str = response.model_dump_json()
    except Exception:
        raw_response_str = str(response)

    cache_data = {
        "model": model_name,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": cost_usd,
        "latency_s": latency,
        "raw_response": raw_response_str,
        "parsed_answer": answer,
        "prompt_version": PROMPT_VERSION
    }
    set_cached_response(cache_key, cache_data)
    
    return {
        "answer": answer,
        "in_tok": prompt_tokens,
        "out_tok": completion_tokens,
        "cost_usd": cost_usd,
        "latency_s": latency,
        "server_s": server_s,
        "model": model_name,
        "cached": False
    }


def sample_slm(query: str, k: int = 3) -> list[dict]:
    """Make k independent stochastically sampled calls to Ollama using SELF_CONSISTENCY_TEMP."""
    results = []
    model_name = SLM_OLLAMA_MODEL
    cost_model_name = f"local:{model_name}"
    
    for i in range(k):
        # We append a unique sample index suffix to the query inside make_cache_key 
        # so that different samples have different cache entries.
        cache_key = make_cache_key(
            model=model_name,
            system_prompt=SYSTEM_PROMPT,
            query=f"{query} [sample {i}]",
            temperature=SELF_CONSISTENCY_TEMP,
            prompt_version=PROMPT_VERSION
        )
        
        # Check cache
        cached = get_cached_response(cache_key)
        if cached is not None:
            results.append({
                "answer": cached["parsed_answer"],
                "in_tok": cached["prompt_tokens"],
                "out_tok": cached["completion_tokens"],
                "cost_usd": cached["cost_usd"],
                "latency_s": cached["latency_s"],
                "server_s": cached["latency_s"],
                "model": cached["model"],
                "cached": True
            })
            continue
            
        # On cache miss, call Ollama with SELF_CONSISTENCY_TEMP
        start_time = time.perf_counter()
        response = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query}
            ],
            options={
                "temperature": SELF_CONSISTENCY_TEMP,
                "num_predict": SLM_MAX_TOKENS
            }
        )
        latency = time.perf_counter() - start_time
        
        answer = response["message"]["content"]
        prompt_tokens = response.get("prompt_eval_count", 0)
        completion_tokens = response.get("eval_count", 0)
        
        server_s = response.get("total_duration", 0) / 1e9
        if server_s == 0:
            server_s = latency

        cost_usd = calculate_cost_usd(cost_model_name, prompt_tokens, completion_tokens)
        
        cache_data = {
            "model": cost_model_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_usd": cost_usd,
            "latency_s": latency,
            "raw_response": json_dump_safe(response),
            "parsed_answer": answer,
            "prompt_version": PROMPT_VERSION
        }
        set_cached_response(cache_key, cache_data)
        
        results.append({
            "answer": answer,
            "in_tok": prompt_tokens,
            "out_tok": completion_tokens,
            "cost_usd": cost_usd,
            "latency_s": latency,
            "server_s": server_s,
            "model": cost_model_name,
            "cached": False
        })
        
    return results


def json_dump_safe(obj: any) -> str:
    """Helper to safely serialize arbitrary objects to JSON strings."""
    try:
        return json.dumps(obj)
    except Exception:
        import json as json_mod
        try:
            return json_mod.dumps(obj)
        except Exception:
            return str(obj)


if __name__ == "__main__":
    import json
    
    print("Running tiers smoke test...")
    test_query = "What is the capital of France?"
    
    print("\n--- Testing call_slm (Local Ollama) ---")
    try:
        slm_res = call_slm(test_query)
        print(json.dumps(slm_res, indent=2))
        
        print("\n--- Testing call_slm (Cache Hit Verification) ---")
        slm_res_cached = call_slm(test_query)
        print(json.dumps(slm_res_cached, indent=2))
        assert slm_res_cached["cached"] is True, "Second call should be cached"
        
    except Exception as e:
        print(f"Ollama Call failed: {e}")
        print("Please ensure the Ollama background daemon is running and qwen3.5:4b is pulled.")
        
    print("\n--- Testing call_llm (Cloud Groq) ---")
    try:
        llm_res = call_llm(test_query)
        print(json.dumps(llm_res, indent=2))
        
        print("\n--- Testing call_llm (Cache Hit Verification) ---")
        llm_res_cached = call_llm(test_query)
        print(json.dumps(llm_res_cached, indent=2))
        assert llm_res_cached["cached"] is True, "Second call should be cached"
        
    except Exception as e:
        print(f"Groq Call failed: {e}")
        print("Please ensure GROQ_API_KEY is correct in your .env file.")

    print("\n--- Testing sample_slm (Consistency Sampling) ---")
    try:
        samples = sample_slm(test_query, k=2)
        for idx, sample in enumerate(samples):
            print(f"Sample {idx}:")
            print(json.dumps(sample, indent=2))
    except Exception as e:
        print(f"Ollama sampling failed: {e}")

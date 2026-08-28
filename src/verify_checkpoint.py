"""Integration checkpoint verification script to check end-to-end routing modules communication."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow executing this file directly as a script without PYTHONPATH issues
if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.grader import extract_answer, grade_answer
from src.tiers import call_llm, call_slm


def run_checkpoint():
    query = "A train travels at 60 mph for 2.5 hours. How many miles does it travel in total?"
    target = "150"

    print("=" * 60)
    print("SLM+LLM ROUTER INTEGRATION CHECKPOINT")
    print("=" * 60)
    print(f"Query  : {query}")
    print(f"Target : {target}")
    print("-" * 60)

    # 1. Run local SLM (Ollama)
    print("Executing query on local SLM...")
    try:
        slm_res = call_slm(query)
        slm_extracted = extract_answer(slm_res["answer"])
        slm_grade = grade_answer(slm_res["answer"], target)
        
        print("\n[LOCAL SLM RESULT]")
        print(f"  Model Name       : {slm_res['model']}")
        print(f"  Cache Status     : {'Hit' if slm_res['cached'] else 'Miss'}")
        print(f"  Latency          : {slm_res['latency_s']:.4f} s")
        print(f"  Exact Cost       : ${slm_res['cost_usd']:.8f}")
        print(f"  Extracted Answer : '{slm_extracted}'")
        print(f"  Boolean Grade    : {slm_grade}")
    except Exception as e:
        print(f"\n[LOCAL SLM ERROR] Failed to invoke SLM: {e}")

    print("-" * 60)

    # 2. Run cloud LLM (Groq)
    print("Executing query on cloud LLM...")
    try:
        llm_res = call_llm(query)
        llm_extracted = extract_answer(llm_res["answer"])
        llm_grade = grade_answer(llm_res["answer"], target)
        
        print("\n[CLOUD LLM RESULT]")
        print(f"  Model Name       : {llm_res['model']}")
        print(f"  Cache Status     : {'Hit' if llm_res['cached'] else 'Miss'}")
        print(f"  Latency          : {llm_res['latency_s']:.4f} s")
        print(f"  Exact Cost       : ${llm_res['cost_usd']:.8f}")
        print(f"  Extracted Answer : '{llm_extracted}'")
        print(f"  Boolean Grade    : {llm_grade}")
    except Exception as e:
        print(f"\n[CLOUD LLM ERROR] Failed to invoke LLM: {e}")

    print("=" * 60)


if __name__ == "__main__":
    run_checkpoint()
